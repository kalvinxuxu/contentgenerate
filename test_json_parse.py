"""
测试 JSON 解析函数
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.utils.llm_client import parse_json_response

print("=" * 50)
print("测试 JSON 解析函数")
print("=" * 50)

# 测试 1: 带末尾逗号
test1 = '{"name": "test", "value": 123,}'
print('测试 1 - 末尾逗号:', end=' ')
try:
    result = parse_json_response(test1)
    print(f'OK - {result}')
except Exception as e:
    print(f'FAIL - {e}')

# 测试 2: 带 markdown 代码块
test2 = '```json\n{"name": "test"}\n```'
print('测试 2 - markdown 代码块:', end=' ')
try:
    result = parse_json_response(test2)
    print(f'OK - {result}')
except Exception as e:
    print(f'FAIL - {e}')

# 测试 3: 复杂 JSON（模拟真实响应）
test3 = '''```json
{
    "trend_analysis": "热度上升",
    "pain_points": [
        {"title": "痛点 1"}
    ],
    "angles": [
        {"headline": "标题"}
    ]
}
```'''
print('测试 3 - 复杂 JSON:', end=' ')
try:
    result = parse_json_response(test3)
    print(f'OK - trend_analysis={result.get("trend_analysis")}')
except Exception as e:
    print(f'FAIL - {e}')

# 测试 4: 模拟错误格式（缺少逗号）
test4 = '''```json
{
    "trend_analysis": "热度上升"
    "pain_points": []
}
```'''
print('测试 4 - 缺少逗号:', end=' ')
try:
    result = parse_json_response(test4)
    print(f'OK - {result}')
except Exception as e:
    print(f'FAIL - {e}')

print("\n所有测试完成!")
