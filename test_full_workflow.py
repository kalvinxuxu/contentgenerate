#!/usr/bin/env python
"""
测试完整的工作流 API
"""

import requests
import time
import json

BASE_URL = "http://localhost:8002"

def test_health():
    """测试健康检查"""
    print("=" * 50)
    print("测试 1: 健康检查")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码：{response.status_code}")
    print(f"响应：{response.json()}")
    print()
    return response.status_code == 200


def test_generate():
    """测试文案生成"""
    print("=" * 50)
    print("测试 2: 文案生成 API")
    print("=" * 50)

    payload = {
        "topic": "AI 工具提升工作效率",
        "audience": "职场人士",
        "platform": "xiaohongshu",
        "tone": "casual",
        "priority": "standard",
        "emotion": "hopeful",
        "style": "minimalist",
        "brand_keywords": ["AI", "效率", "职场"]
    }

    response = requests.post(f"{BASE_URL}/api/generate", json=payload)
    print(f"状态码：{response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"响应：{json.dumps(result, indent=2, ensure_ascii=False)}")
        return result.get("task_id")
    else:
        print(f"错误：{response.text}")
        return None


def test_task_status(task_id):
    """测试任务状态查询"""
    print("\n" + "=" * 50)
    print(f"测试 3: 任务状态查询 (task_id: {task_id})")
    print("=" * 50)

    # 轮询任务状态
    max_retries = 30
    for i in range(max_retries):
        response = requests.get(f"{BASE_URL}/api/task/{task_id}")

        if response.status_code == 200:
            status = response.json()
            print(f"\n[第 {i+1} 次轮询] 进度：{status['progress']}% | 状态：{status['status']} | 步骤：{status['current_step']}")

            if status['status'] in ['completed', 'failed']:
                print(f"\n最终结果：")
                print(json.dumps(status.get('result', {}), indent=2, ensure_ascii=False))
                return status['status'] == 'completed'

            time.sleep(2)
        else:
            print(f"查询失败：{response.text}")
            return False

    print("超时：任务未在指定时间内完成")
    return False


def main():
    """运行所有测试"""
    print("\n[TEST] 开始测试后端 API 完整工作流\n")

    # 测试 1: 健康检查
    health_ok = test_health()
    if not health_ok:
        print("[FAIL] 健康检查失败，后端服务可能未启动")
        return

    # 测试 2: 文案生成
    task_id = test_generate()
    if not task_id:
        print("[FAIL] 文案生成请求失败")
        return

    # 测试 3: 任务状态查询
    completed = test_task_status(task_id)

    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    status_ok = "OK" if health_ok else "FAIL"
    status_gen = "OK" if task_id else "FAIL"
    status_full = "OK" if completed else "FAIL"
    print(f"健康检查：{status_ok}")
    print(f"文案生成：{status_gen}")
    print(f"完整流程：{status_full}")
    print()


if __name__ == "__main__":
    main()
