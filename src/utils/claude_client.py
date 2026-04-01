"""
Anthropic Claude 客户端封装
支持 token 计数、成本追踪、错误处理和重试机制
"""

import os
import time
import json
import logging
from typing import Dict, Any, Optional, List, Generator
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic, RateLimitError, APIStatusError, APITimeoutError
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Claude 模型定价（每 1000 tokens，单位：美元）
# https://docs.anthropic.com/claude/docs/models-overview
PRICING = {
    "claude-opus-4-6": {"input": 0.015, "output": 0.075},
    "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
    "claude-haiku-4-5-20251001": {"input": 0.001, "output": 0.005},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku-20241022": {"input": 0.001, "output": 0.005},
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    # 默认使用 Sonnet 定价
    "default": {"input": 0.003, "output": 0.015},
}


@dataclass
class TokenUsage:
    """Token 使用记录"""
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    timestamp: str
    request_type: str = "chat"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    input_tokens: int
    output_tokens: int
    model: str
    stop_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ClaudeClient:
    """Anthropic Claude 客户端封装"""

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 1.0,
        api_key: Optional[str] = None,
        log_dir: Optional[str] = None
    ):
        """
        初始化 Claude 客户端

        Args:
            model: 模型名称
            temperature: 温度 (0.0-1.0)
            max_tokens: 最大输出 token 数
            top_p: 核采样参数
            api_key: API Key，默认从环境变量读取
            log_dir: 日志目录，默认 ./.planning/logs/
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p

        # API Key
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY 环境变量未设置")

        # 初始化客户端
        self.client = Anthropic(api_key=self.api_key)

        # 日志目录
        self.log_dir = Path(log_dir) if log_dir else Path(".planning/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Token 使用累计
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

        # 重试配置
        self.max_retries = 3
        self.base_delay = 1.0  # 秒
        self.max_delay = 60.0  # 秒

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算 API 调用成本"""
        pricing = PRICING.get(self.model, PRICING["default"])
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    def _log_usage(self, usage: TokenUsage):
        """记录 token 使用日志"""
        # 更新累计
        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens
        self.total_cost += usage.cost

        # 写入日志文件
        log_file = self.log_dir / f"usage_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(usage.to_dict(), ensure_ascii=False) + "\n")

        logger.info(
            f"Token 使用：input={usage.input_tokens}, output={usage.output_tokens}, "
            f"cost=${usage.cost:.6f}, 累计=${self.total_cost:.6f}"
        )

    def _retry_with_backoff(self, func, *args, **kwargs):
        """带指数退避的重试"""
        last_exception = None
        delay = self.base_delay

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except RateLimitError as e:
                last_exception = e
                if attempt == self.max_retries:
                    break
                # 从响应头获取重试时间（如果有）
                retry_after = getattr(e, 'response', None)
                if retry_after:
                    retry_after = retry_after.headers.get('retry-after')
                    if retry_after:
                        delay = float(retry_after)

                logger.warning(f"Rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(delay)
                delay = min(delay * 2, self.max_delay)  # 指数退避

            except APITimeoutError as e:
                last_exception = e
                if attempt == self.max_retries:
                    break
                logger.warning(f"Timeout, retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(delay)
                delay = min(delay * 2, self.max_delay)

            except APIStatusError as e:
                # 5xx 错误可重试
                if 500 <= e.status_code < 600:
                    last_exception = e
                    if attempt == self.max_retries:
                        break
                    logger.warning(f"Server error ({e.status_code}), retrying in {delay:.1f}s")
                    time.sleep(delay)
                    delay = min(delay * 2, self.max_delay)
                else:
                    # 其他状态码错误不可重试
                    raise

        raise last_exception

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: Optional[Dict] = None,
        **kwargs
    ) -> LLMResponse:
        """
        调用 Claude API

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            output_schema: JSON Schema 用于结构化输出
            **kwargs: 其他参数

        Returns:
            LLMResponse 响应对象
        """
        def _make_request():
            # 构建消息
            messages = [{"role": "user", "content": user_prompt}]

            # 调用 API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                system=system_prompt,
                messages=messages,
                **kwargs
            )

            return response

        # 带重试的调用
        response = self._retry_with_backoff(_make_request)

        # 提取响应内容
        content = response.content[0].text if response.content else ""
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # 计算成本
        cost = self._calculate_cost(input_tokens, output_tokens)

        # 记录使用
        usage = TokenUsage(
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            timestamp=datetime.now().isoformat(),
            request_type="chat"
        )
        self._log_usage(usage)

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            stop_reason=response.stop_reason
        )

    def call_with_json_schema(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用 Claude API 并强制 JSON 输出

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            output_schema: JSON Schema

        Returns:
            解析后的 JSON 对象
        """
        # 在 system prompt 中强调 JSON 输出
        json_system_prompt = f"""{system_prompt}

IMPORTANT: You MUST respond with ONLY valid JSON. No explanatory text.
Your response must conform to this schema:
{json.dumps(output_schema, indent=2)}
"""

        response = self.call(json_system_prompt, user_prompt)

        # 解析 JSON
        try:
            # 尝试提取 JSON
            content = response.content.strip()
            # 移除可能的 markdown 代码块标记
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败：{e}")
            logger.error(f"原始响应：{response.content[:500]}")
            raise ValueError(f"JSON 解析失败：{e}")

    def call_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> Generator[str, None, LLMResponse]:
        """
        流式调用 Claude API

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            **kwargs: 其他参数

        Yields:
            文本块
        """
        messages = [{"role": "user", "content": user_prompt}]

        input_tokens = 0
        output_tokens = 0
        content_parts = []

        with self.client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            system=system_prompt,
            messages=messages,
            **kwargs
        ) as stream:
            for text in stream.text_stream:
                content_parts.append(text)
                yield text

        # 获取最终响应
        response = stream.get_final_message()
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # 计算成本
        cost = self._calculate_cost(input_tokens, output_tokens)

        # 记录使用
        usage = TokenUsage(
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            timestamp=datetime.now().isoformat(),
            request_type="stream"
        )
        self._log_usage(usage)

        return LLMResponse(
            content="".join(content_parts),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            stop_reason=response.stop_reason
        )

    def get_usage_summary(self) -> Dict[str, Any]:
        """获取 token 使用汇总"""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 6),
            "model": self.model,
            "timestamp": datetime.now().isoformat()
        }


# 兼容旧代码的函数
def create_llm_client(
    model: str = "claude-sonnet-4-6",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs
) -> ClaudeClient:
    """创建 LLM 客户端"""
    return ClaudeClient(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


def call_llm_sync(
    client: ClaudeClient,
    system_prompt: str,
    user_prompt: str,
    output_schema: Optional[Dict] = None
) -> str:
    """同步调用 LLM"""
    if output_schema:
        result = client.call_with_json_schema(system_prompt, user_prompt, output_schema)
        return json.dumps(result, ensure_ascii=False)
    else:
        response = client.call(system_prompt, user_prompt)
        return response.content
