"""
LLM 客户端统一接口
支持 Anthropic Claude 和阿里云百炼云两种后端
"""

import os
import json
import re
import logging
from typing import Dict, Any, Optional
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class LLMBackend(Enum):
    """LLM 后端类型"""
    ANTHROPIC = "anthropic"
    DASHSCOPE = "dashscope"


def get_backend_type() -> LLMBackend:
    """根据环境变量确定后端类型"""
    # 优先使用显式配置
    provider = os.getenv("LLM_PROVIDER", "").lower()

    if provider == "anthropic" or os.getenv("ANTHROPIC_API_KEY"):
        return LLMBackend.ANTHROPIC
    elif provider == "dashscope" or os.getenv("DASHSCOPE_API_KEY"):
        return LLMBackend.DASHSCOPE
    else:
        # 默认使用 Anthropic
        return LLMBackend.ANTHROPIC


def create_llm_client(
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs
):
    """
    创建 LLM 客户端（工厂函数）

    根据可用 API Key 自动选择合适的后端

    Args:
        model: 模型名称
        temperature: 温度参数
        max_tokens: 最大 token 数
        **kwargs: 其他参数

    Returns:
        LLM 客户端实例
    """
    backend_type = get_backend_type()

    if backend_type == LLMBackend.ANTHROPIC:
        from src.utils.claude_client import ClaudeClient

        # 模型映射
        if model is None:
            model = os.getenv("DEFAULT_MODEL", "claude-sonnet-4-6")

        return ClaudeClient(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    else:
        from src.utils.llm_client import LLMClient

        # 模型映射
        if model is None:
            model = os.getenv("DEFAULT_MODEL", "qwen3.5-plus")

        return LLMClient(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )


def call_llm_sync(
    client,
    system_prompt: str,
    user_prompt: str,
    output_schema: Optional[Dict] = None
) -> str:
    """
    同步调用 LLM

    Args:
        client: LLM 客户端
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        output_schema: 输出 Schema（用于结构化输出）

    Returns:
        LLM 响应文本
    """
    from src.utils.claude_client import ClaudeClient

    if isinstance(client, ClaudeClient):
        # Anthropic 后端
        if output_schema:
            result = client.call_with_json_schema(system_prompt, user_prompt, output_schema)
            return json.dumps(result, ensure_ascii=False)
        else:
            response = client.call(system_prompt, user_prompt)
            return response.content
    else:
        # DashScope/OpenAI 后端
        from src.utils.llm_client import call_llm_sync as dashscope_call

        # 如果有 schema，添加到 prompt 中
        if output_schema:
            schema_prompt = f"\n\n请以 JSON 格式输出，符合以下 schema:\n{json.dumps(output_schema, indent=2)}"
            user_prompt = user_prompt + schema_prompt

        return dashscope_call(client, system_prompt, user_prompt)


def parse_json_response(response: str) -> Dict[str, Any]:
    """
    解析 JSON 响应

    Args:
        response: LLM 响应文本

    Returns:
        解析后的字典
    """
    # 尝试提取 JSON 代码块
    json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # 尝试提取 ``` 开头的代码块
        code_block_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
        if code_block_match:
            json_str = code_block_match.group(1)
        else:
            # 尝试直接解析
            json_str = response.strip()

    # 尝试直接解析
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # 尝试修复常见的 JSON 错误
    # 1. 移除末尾的逗号
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)

    # 2. 修复键值对之间缺少逗号的问题
    lines = json_str.split('\n')
    fixed_lines = []
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped and not stripped.endswith(('{', '[', ',', ':')) and not stripped.startswith('}'):
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith(('}', ']')):
                    fixed_lines.append(stripped)
                else:
                    fixed_lines.append(stripped + ',')
            else:
                fixed_lines.append(stripped)
        else:
            fixed_lines.append(stripped)
    json_str = '\n'.join(fixed_lines)

    # 3. 再次尝试修复末尾逗号
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"JSON 解析失败：{e.msg}",
            e.doc,
            e.pos
        )
