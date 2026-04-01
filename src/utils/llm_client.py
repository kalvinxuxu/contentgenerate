"""
LLM 客户端封装
使用阿里云百炼云 Coding Plan (OpenAI 兼容接口)
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class LLMClient:
    """LLM 客户端封装类"""

    def __init__(
        self,
        model: str = "qwen3.5-plus",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 确保 API Key 已设置
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY 环境变量未设置")

        # 初始化 OpenAI 客户端，使用百炼云 base_url
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://coding.dashscope.aliyuncs.com/v1"
        )

    def call_sync(self, system_prompt: str, user_prompt: str) -> str:
        """
        同步调用 LLM

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            LLM 响应
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        return response.choices[0].message.content


def create_llm_client(
    model: str = "qwen3.5-plus",
    temperature: float = 0.7,
    max_tokens: int = 2000,
    **kwargs
) -> LLMClient:
    """
    创建 LLM 客户端

    Args:
        model: 模型名称（默认 qwen3.5-plus）
        temperature: 温度参数
        max_tokens: 最大 token 数
        **kwargs: 其他参数

    Returns:
        LLMClient 实例
    """
    return LLMClient(model=model, temperature=temperature, max_tokens=max_tokens)


async def call_llm(
    client: LLMClient,
    system_prompt: str,
    user_prompt: str,
    output_schema: Optional[Dict] = None
) -> str:
    """
    调用 LLM（异步版本）

    Args:
        client: LLM 客户端
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        output_schema: 输出 Schema（用于结构化输出）

    Returns:
        LLM 响应
    """
    return client.call_sync(system_prompt, user_prompt)


def call_llm_sync(
    client: LLMClient,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """
    同步调用 LLM

    Args:
        client: LLM 客户端
        system_prompt: 系统提示词
        user_prompt: 用户提示词

    Returns:
        LLM 响应
    """
    return client.call_sync(system_prompt, user_prompt)


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

    # 2. 修复键值对之间缺少逗号的问题 (行尾缺少逗号)
    lines = json_str.split('\n')
    fixed_lines = []
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        # 检查是否需要在行尾添加逗号
        if stripped and not stripped.endswith(('{', '[', ',', ':')) and not stripped.startswith(('}', ']')):
            # 检查下一行是否是 closing bracket
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

    # 4. 尝试使用 eval 解析（容错性更强）
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        pass

    # 5. 尝试使用 eval 修复（允许单引号等非标准 JSON）
    try:
        # 将单引号替换为双引号（如果必要）
        json_str = json_str.replace("'", '"')
        # 修复 True/False 为 true/false
        json_str = re.sub(r'\bTrue\b', 'true', json_str)
        json_str = re.sub(r'\bFalse\b', 'false', json_str)
        # 修复 None 为 null
        json_str = re.sub(r'\bNone\b', 'null', json_str)

        # 使用 eval 解析（注意：这里只解析字符串，不执行代码）
        import ast
        result = ast.literal_eval(json_str)
        # 转换为 JSON 字符串再解析回来
        return json.loads(json.dumps(result, ensure_ascii=False))
    except Exception:
        pass

    # 6. 如果还是失败，抛出异常并附带原始响应
    try:
        raise json.JSONDecodeError(
            f"JSON 解析失败：{e.msg}",
            e.doc,
            e.pos
        )
    except NameError:
        # e 可能未定义
        raise json.JSONDecodeError("JSON 解析失败，无法修复", json_str, 0)
