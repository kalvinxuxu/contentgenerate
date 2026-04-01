"""
测试 Minimax 图片生成功能
"""

import os
from pathlib import Path
from src.utils.minimax_client import MinimaxImageClient
from src.utils.image_uploader import ImageUploader

def test_text_to_image():
    """测试文生图功能"""
    print("=" * 50)
    print("测试文生图功能")
    print("=" * 50)

    client = MinimaxImageClient()

    prompt = "A girl looking into the distance from a library window, warm lighting, peaceful atmosphere"

    print(f"提示词：{prompt}")
    print("正在生成图片...")

    result = client.generate_text_to_image(
        prompt=prompt,
        aspect_ratio="16:9",
        num_images=1
    )

    print(f"生成成功！图片数量：{len(result['images'])}")
    if result['images']:
        print(f"图片 URL: {result['images'][0].get('url')}")

        # 保存图片
        save_path = client.save_image(result['images'][0]['url'], "uploads/generated/text2image_test.png")
        print(f"图片已保存到：{save_path}")

    return result


def test_image_with_subject_reference(reference_image_path: str):
    """测试主体参考功能（图生图）"""
    print("=" * 50)
    print("测试主体参考功能（图生图）")
    print("=" * 50)

    # 验证参考图存在
    if not os.path.exists(reference_image_path):
        print(f"错误：参考图不存在：{reference_image_path}")
        return None

    client = MinimaxImageClient()

    prompt = "A professional product poster design, the same product on a showcase platform, elegant lighting, marketing style"

    print(f"参考图：{reference_image_path}")
    print(f"提示词：{prompt}")
    print("正在生成图片...")

    result = client.generate_image_with_subject_reference(
        prompt=prompt,
        reference_image_path=reference_image_path,
        subject_type="product",  # 产品类型
        aspect_ratio="3:4",
        num_images=1
    )

    print(f"生成成功！图片数量：{len(result['images'])}")
    if result['images']:
        print(f"图片 URL: {result['images'][0].get('url')}")

        # 保存图片
        save_path = client.save_image(result['images'][0]['url'], "uploads/generated/subject_reference_test.png")
        print(f"图片已保存到：{save_path}")

    return result


def test_upload_and_generate():
    """测试上传参考图并生成"""
    print("=" * 50)
    print("测试上传参考图并生成")
    print("=" * 50)

    # 选择一个已有的上传图作为参考
    uploads_dir = Path("uploads")
    jpg_files = list(uploads_dir.glob("*.jpg"))

    if not jpg_files:
        print("uploads 目录没有找到 JPG 文件")
        return None

    reference_image = str(jpg_files[0])
    print(f"使用参考图：{reference_image}")

    # 确保输出目录存在
    generated_dir = Path("uploads/generated")
    generated_dir.mkdir(parents=True, exist_ok=True)

    # 测试主体参考生成
    client = MinimaxImageClient()

    result = client.generate_and_save(
        prompt="A professional portrait photo of the same person in a different setting, studio lighting, professional style",
        reference_image_path=reference_image,
        subject_type="character",  # Minimax API 仅支持 character 类型
        aspect_ratio="3:4",
        save_path=str(generated_dir / "subject_reference_output.png")
    )

    # 调试：打印原始响应
    print(f"原始响应：{result.get('raw_response', {})}")

    if "saved_path" in result:
        print(f"图片已保存到：{result['saved_path']}")
    else:
        print("未找到保存的图片路径")

    return result


if __name__ == "__main__":
    # 确保输出目录存在
    Path("uploads/generated").mkdir(parents=True, exist_ok=True)

    # 测试文生图
    try:
        print("\n>>> 开始测试文生图...\n")
        test_text_to_image()
        print("\n文生图测试完成!\n")
    except Exception as e:
        print(f"文生图测试失败：{e}")

    print("\n" + "=" * 60 + "\n")

    # 测试图生图（如果有参考图）
    uploads_dir = Path("uploads")
    jpg_files = list(uploads_dir.glob("*.jpg"))

    if jpg_files:
        try:
            print(">>> 开始测试主体参考功能（图生图）...\n")
            test_upload_and_generate()
            print("\n主体参考测试完成!\n")
        except Exception as e:
            print(f"主体参考测试失败：{e}")
    else:
        print("uploads 目录没有找到 JPG 文件，跳过主体参考测试")
