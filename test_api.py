#!/usr/bin/env python
"""
测试百炼云 Claude API 配置
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from src.utils.llm_client import create_llm_client, call_llm_sync

def main():
    # 创建客户端
    client = create_llm_client(
        model="qwen3.5-plus",
        temperature=0.7,
        max_tokens=500
    )

    # 测试调用
    print("正在调用 Claude API...")
    response = call_llm_sync(
        client,
        system_prompt="你是一个简洁的 AI 助手，请用简短的方式回答。",
        user_prompt="你好，请用一句话介绍你自己。"
    )

    print("\n响应内容：")
    print(response)
    print("\nAPI 调用成功!")

if __name__ == "__main__":
    main()
