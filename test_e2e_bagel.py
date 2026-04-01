"""
端到端测试：贝果面包新品发布文案生成

使用 TDD 模式测试完整流程：
1. 上传产品图片
2. 运行 5 个 Agent 阶段（调研 -> 创作 -> 审核 -> 优化 -> 配图）
3. 保存结果到本地目录
"""

import requests
import json
import os
from datetime import datetime

API_BASE = "http://localhost:8002"

# 测试配置
TEST_CONFIG = {
    "topic": "贝果面包新品发布",
    "audience": "年轻妈妈",
    "platform": "xiaohongshu",
    "tone": "casual",
    "priority": "standard",
    "emotion": "hopeful",
    "style": "minimalist",
    "brand_keywords": ["健康", "低脂", "早餐"],
    "product_image_path": r"C:\Users\kalvi\Documents\claude application\claude_content_agents\测试图片\test1.jpg"
}

# 结果保存目录
OUTPUT_DIR = r"C:\Users\kalvi\Documents\claude application\claude_content_agents\test_output\bagel_test"


def test_upload_image():
    """测试 1: 上传产品图片"""
    print("\n" + "="*60)
    print("测试 1: 上传产品图片")
    print("="*60)

    if not os.path.exists(TEST_CONFIG["product_image_path"]):
        print(f"[FAIL] 图片文件不存在：{TEST_CONFIG['product_image_path']}")
        return None

    try:
        with open(TEST_CONFIG["product_image_path"], "rb") as f:
            files = {"file": ("test1.jpg", f, "image/jpeg")}
            response = requests.post(f"{API_BASE}/api/upload-image", files=files, timeout=60)
            response.raise_for_status()

            result = response.json()
            print(f"[OK] 图片上传成功")
            print(f"   文件名：{result['filename']}")
            print(f"   文件路径：{result['filepath']}")
            return result["filepath"]
    except Exception as e:
        print(f"[FAIL] 图片上传失败：{e}")
        return None


def test_generate_content(image_path):
    """测试 2: 启动文案生成工作流"""
    print("\n" + "="*60)
    print("测试 2: 启动文案生成工作流")
    print("="*60)

    payload = {
        "topic": TEST_CONFIG["topic"],
        "audience": TEST_CONFIG["audience"],
        "platform": TEST_CONFIG["platform"],
        "tone": TEST_CONFIG["tone"],
        "emotion": TEST_CONFIG["emotion"],
        "style": TEST_CONFIG["style"],
        "brand_keywords": TEST_CONFIG["brand_keywords"],
        "product_image_path": image_path
    }

    try:
        response = requests.post(f"{API_BASE}/api/generate", json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        task_id = result["task_id"]
        print(f"[OK] 工作流已启动")
        print(f"   任务 ID: {task_id}")
        return task_id
    except Exception as e:
        print(f"[FAIL] 工作流启动失败：{e}")
        return None


def poll_task_status(task_id, max_wait_seconds=1800):
    """测试 3: 轮询任务状态直到完成"""
    print("\n" + "="*60)
    print("测试 3: 轮询任务状态 (最多等待{0}秒)".format(max_wait_seconds))
    print("="*60)

    import time
    start_time = time.time()
    last_step = ""
    poll_count = 0

    while time.time() - start_time < max_wait_seconds:
        try:
            response = requests.get(f"{API_BASE}/api/task/{task_id}", timeout=30)
            response.raise_for_status()
            status = response.json()
            poll_count += 1

            # 显示进度
            if status["current_step"] != last_step:
                last_step = status["current_step"]
                elapsed = int(time.time() - start_time)
                print(f"   进度：{status['progress']}% - {status['current_step']} (已用 {elapsed}秒)")

            # 检查是否需要确认（分阶段模式）
            if status.get("awaiting_confirmation"):
                print(f"   [WAIT] 等待确认：{status['current_step']}")
                # 自动确认继续
                confirm_response = requests.post(
                    f"{API_BASE}/api/task/{task_id}/confirm",
                    json={"action": "continue"},
                    timeout=30
                )
                print(f"   [OK] 已确认，继续下一步")
                time.sleep(1)
                continue

            # 检查完成状态
            if status["status"] == "completed":
                elapsed = int(time.time() - start_time)
                print(f"\n[OK] 任务完成！(共用时 {elapsed}秒，轮询 {poll_count}次)")
                return status
            elif status["status"] == "failed":
                print(f"\n[FAIL] 任务失败：{status['current_step']}")
                return None
            else:
                time.sleep(5)  # 每 5 秒轮询一次

        except requests.exceptions.Timeout as e:
            print(f"[WARN] 请求超时：{e}")
            time.sleep(5)
        except Exception as e:
            print(f"[FAIL] 轮询失败：{e}")
            time.sleep(5)

    print(f"\n[FAIL] 超时：{max_wait_seconds}秒内未完成")
    return None


def save_results(task_status, image_path):
    """测试 4: 保存结果到本地目录"""
    print("\n" + "="*60)
    print("测试 4: 保存结果到本地目录")
    print("="*60)

    try:
        # 创建输出目录
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # 准备完整结果数据
        result_data = {
            "test_info": {
                "name": "贝果面包新品发布文案生成测试",
                "timestamp": datetime.now().isoformat(),
                "test_config": TEST_CONFIG
            },
            "task_status": task_status,
            "final_output": task_status.get("result", {}).get("final_output", {})
        }

        # 保存完整 JSON 结果
        json_path = os.path.join(OUTPUT_DIR, "result.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        print(f"[OK] 结果已保存：{json_path}")

        # 提取并保存文案
        final_content = result_data["final_output"].get("final_content", "")
        if final_content:
            content_path = os.path.join(OUTPUT_DIR, "文案.txt")
            with open(content_path, "w", encoding="utf-8") as f:
                f.write(final_content)
            print(f"[OK] 文案已保存：{content_path}")

        # 保存审核报告
        reviewer = result_data["final_output"].get("reviewer", {})
        if reviewer:
            review_path = os.path.join(OUTPUT_DIR, "审核报告.txt")
            with open(review_path, "w", encoding="utf-8") as f:
                f.write(f"总体评分：{reviewer.get('overall_score', 'N/A')}/6\n")
                f.write(f"审核结论：{reviewer.get('conclusion', 'N/A')}\n\n")
                f.write("亮点:\n")
                for highlight in reviewer.get("highlights", []):
                    f.write(f"  - {highlight}\n")
                if reviewer.get("must_fix_issues"):
                    f.write("\n需改进的问题:\n")
                    for issue in reviewer["must_fix_issues"]:
                        f.write(f"  - [{issue['location']}] {issue['problem']}\n")
            print(f"[OK] 审核报告已保存：{review_path}")

        # 保存配图方案
        image_result = result_data["final_output"].get("image", {})
        if image_result:
            # 保存 Midjourney 提示词
            prompts_path = os.path.join(OUTPUT_DIR, "配图方案.txt")
            with open(prompts_path, "w", encoding="utf-8") as f:
                f.write("Midjourney 配图方案:\n\n")
                for i, prompt in enumerate(image_result.get("mj_prompts", []), 1):
                    f.write(f"方案{i}: {prompt.get('style', 'N/A')}\n")
                    f.write(f"中文：{prompt.get('prompt_cn', 'N/A')}\n")
                    f.write(f"English: {prompt.get('prompt_en', 'N/A')}\n\n")
            print(f"[OK] 配图方案已保存：{prompts_path}")

            # 复制生成的图片到输出目录
            generated_images = image_result.get("generated_images", [])
            if generated_images:
                import shutil
                images_dir = os.path.join(OUTPUT_DIR, "生成的图片")
                os.makedirs(images_dir, exist_ok=True)

                for img_path in generated_images:
                    if os.path.exists(img_path):
                        dest = os.path.join(images_dir, os.path.basename(img_path))
                        shutil.copy2(img_path, dest)
                print(f"[OK] 已复制 {len(generated_images)} 张生成的图片到：{images_dir}")

        # 打印摘要
        print("\n" + "="*60)
        print("测试输出摘要")
        print("="*60)
        print(f"输出目录：{OUTPUT_DIR}")
        print(f"包含文件:")
        for root, dirs, files in os.walk(OUTPUT_DIR):
            level = root.replace(OUTPUT_DIR, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                filepath = os.path.join(root, file)
                size = os.path.getsize(filepath)
                print(f"{subindent}{file} ({size:,} bytes)")

        return True
    except Exception as e:
        print(f"[FAIL] 保存结果失败：{e}")
        return False


def main():
    """运行完整测试流程"""
    print("\n" + "="*60)
    print(" 贝果面包新品发布 - 端到端测试")
    print("="*60)
    print(f"开始时间：{datetime.now().isoformat()}")

    # 测试 1: 上传图片
    image_path = test_upload_image()
    if not image_path:
        print("\n[FAIL] 测试失败：图片上传失败")
        return

    # 测试 2: 启动工作流
    task_id = test_generate_content(image_path)
    if not task_id:
        print("\n[FAIL] 测试失败：工作流启动失败")
        return

    # 测试 3: 轮询状态直到完成
    task_status = poll_task_status(task_id)
    if not task_status:
        print("\n[FAIL] 测试失败：任务未完成")
        return

    # 测试 4: 保存结果
    save_results(task_status, image_path)

    print("\n" + "="*60)
    print("[OK] 完整测试流程结束")
    print("="*60)
    print(f"结束时间：{datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
