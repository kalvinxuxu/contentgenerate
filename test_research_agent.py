"""
测试调研 Agent 的 JSON 解析修复
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# 设置控制台编码为 UTF-8
os.system('chcp 65001 > nul')

from src.agents.research import ResearchAgent
from src.agents.base import AgentEnvelope
from src.utils.config import get_model_config

def test_research_agent():
    """测试调研 Agent"""
    print("=" * 50)
    print("测试调研 Agent")
    print("=" * 50)

    # 创建 Agent
    config = get_model_config("research")
    agent = ResearchAgent(config)
    agent.initialize()

    # 构造输入
    envelope = AgentEnvelope(
        version="1.0",
        source_agent="user",
        target_agent="research_agent",
        payload={
            "topic": "AI 写作工具",
            "target_audience": "自媒体创作者",
            "platform": "xiaohongshu",
            "brand_keywords": ["高效", "智能"]
        }
    )

    # 运行
    print("运行调研 Agent...")
    try:
        output = agent.process(envelope)
        print("[OK] 调研 Agent 运行成功")
        print(f"返回数据类型：{type(output.payload)}")
        print(f"返回数据 keys: {output.payload.keys() if isinstance(output.payload, dict) else 'N/A'}")

        # 检查关键字段
        required_fields = ["trend_analysis", "pain_points", "angles"]
        for field in required_fields:
            if field in output.payload:
                print(f"  [OK] {field}: 存在")
            else:
                print(f"  [FAIL] {field}: 缺失")

        return True
    except Exception as e:
        print(f"[FAIL] 调研 Agent 运行失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_json_parsing():
    """测试 JSON 解析函数"""
    print("\n" + "=" * 50)
    print("测试 JSON 解析函数")
    print("=" * 50)

    from src.utils.llm_client import parse_json_response

    # 测试用例 1: 标准 JSON
    test1 = '{"name": "test", "value": 123}'
    try:
        result = parse_json_response(test1)
        print(f"[OK] 测试 1 通过：{result}")
    except Exception as e:
        print(f"[FAIL] 测试 1 失败：{e}")

    # 测试用例 2: 带末尾逗号的 JSON
    test2 = '{"name": "test", "value": 123,}'
    try:
        result = parse_json_response(test2)
        print(f"[OK] 测试 2 通过（修复末尾逗号）: {result}")
    except Exception as e:
        print(f"[FAIL] 测试 2 失败：{e}")

    # 测试用例 3: 带 markdown 代码块
    test3 = '```json\n{"name": "test", "value": 123}\n```'
    try:
        result = parse_json_response(test3)
        print(f"[OK] 测试 3 通过（解析代码块）: {result}")
    except Exception as e:
        print(f"[FAIL] 测试 3 失败：{e}")

    # 测试用例 4: 模拟真实响应（带有多行和复杂结构）
    test4 = '''```json
{
    "trend_analysis": "过去 7 天热度上升",
    "pain_points": [
        {
            "title": "痛点 1",
            "description": "描述内容"
        }
    ],
    "angles": [
        {
            "headline": "标题",
            "target_audience": "受众"
        }
    ]
}
```'''
    try:
        result = parse_json_response(test4)
        print(f"[OK] 测试 4 通过（复杂 JSON）: {result}")
    except Exception as e:
        print(f"[FAIL] 测试 4 失败：{e}")


if __name__ == "__main__":
    # 测试 JSON 解析
    test_json_parsing()

    # 测试调研 Agent（需要 API Key）
    if os.getenv("DASHSCOPE_API_KEY"):
        test_research_agent()
    else:
        print("\n" + "=" * 50)
        print("未设置 DASHSCOPE_API_KEY，跳过 Agent 测试")
        print("=" * 50)
