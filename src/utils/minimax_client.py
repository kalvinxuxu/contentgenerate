"""
Minimax 图片生成客户端
支持文生图和图生图（主体参考）功能

API 文档参考：
- 端点：https://api.minimaxi.com/v1/image_generation
- 模型：image-01
"""

import os
import base64
import requests
from typing import Dict, Any, Optional, List
from pathlib import Path
import time
import logging

logger = logging.getLogger(__name__)


class MinimaxImageClient:
    """Minimax 图片生成客户端"""

    # Minimax 图片生成 API 端点
    IMAGE_GENERATION_URL = "https://api.minimaxi.com/v1/image_generation"

    # 平台对应的默认宽高比
    PLATFORM_ASPECT_RATIOS = {
        "xiaohongshu": "3:4",  # 小红书竖版
        "wechat": "16:9",  # 微信公众号横版
        "blog": "16:9",  # 博客横版
        "default": "1:1"  # 默认方形
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Minimax 客户端

        Args:
            api_key: Minimax API Key，默认从环境变量读取
        """
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY 环境变量未设置")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 重试配置
        self.max_retries = 2
        self.retry_delay = 5  # 秒

    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        将图片编码为 base64

        Args:
            image_path: 图片路径

        Returns:
            base64 编码的图片字符串
        """
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        return image_data

    def _get_image_mime_type(self, image_path: str) -> str:
        """获取图片的 MIME 类型"""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif"
        }
        return mime_types.get(ext, "image/jpeg")

    def _get_aspect_ratio(self, size: str) -> str:
        """
        将尺寸转换为宽高比格式

        Args:
            size: 尺寸字符串，如 "1024x1024"

        Returns:
            宽高比字符串，如 "1:1"
        """
        width, height = map(int, size.split("x"))

        # 简化比例
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a

        common = gcd(width, height)
        return f"{width // common}:{height // common}"

    def generate_text_to_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        num_images: int = 1,
        model_version: str = "image-01"
    ) -> Dict[str, Any]:
        """
        文生图功能

        Args:
            prompt: 文字描述（提示词）
            aspect_ratio: 宽高比，支持 "16:9", "3:4", "1:1" 等
            num_images: 生成图片数量（1-4）
            model_version: 模型版本，默认 "image-01"

        Returns:
            包含图片 URL 和元数据的字典
        """
        return self._generate_with_retry(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            num_images=num_images,
            model_version=model_version,
            subject_reference=None
        )

    def _generate_with_retry(
        self,
        prompt: str,
        aspect_ratio: str,
        num_images: int,
        model_version: str,
        subject_reference: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        带重试的图片生成

        Args:
            prompt: 文字描述
            aspect_ratio: 宽高比
            num_images: 图片数量
            model_version: 模型版本
            subject_reference: 主体参考（可选）

        Returns:
            包含图片 URL 和元数据的字典
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"重试图片生成 (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)

                payload = {
                    "model": model_version,
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "n": num_images
                }

                # 如果有主体参考，添加到 payload
                if subject_reference:
                    payload["subject_reference"] = subject_reference

                logger.info(f"正在生成图片：{prompt[:50]}...")
                response = requests.post(
                    self.IMAGE_GENERATION_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=120
                )

                if response.status_code != 200:
                    raise Exception(f"API 请求失败：{response.status_code} - {response.text}")

                result = response.json()
                logger.info(f"图片生成成功")
                return self._parse_response(result)

            except Exception as e:
                last_error = e
                logger.warning(f"图片生成失败 (attempt {attempt + 1}): {e}")

        raise Exception(f"图片生成失败（已重试{self.max_retries}次）: {last_error}")

    def generate_image_with_subject_reference(
        self,
        prompt: str,
        reference_image_path: str,
        subject_type: str = "character",  # 仅支持 "character"
        aspect_ratio: str = "1:1",
        num_images: int = 1,
        model_version: str = "image-01"
    ) -> Dict[str, Any]:
        """
        图生图功能 - 使用主体参考保持形象一致性

        Args:
            prompt: 文字描述，描述希望生成的内容
            reference_image_path: 参考图片路径
            subject_type: 主体类型，目前仅支持 "character" (人物)
            aspect_ratio: 宽高比
            num_images: 生成图片数量
            model_version: 模型版本

        Returns:
            包含图片 URL 和元数据的字典

        Note:
            Minimax API 目前仅支持 character（人物）类型的主体参考
        """
        # 将参考图转换为 URL（可以是本地路径 base64 或在线 URL）
        # Minimax API 支持直接使用图片 URL 或 base64
        reference_image_base64 = self._encode_image_to_base64(reference_image_path)
        mime_type = self._get_image_mime_type(reference_image_path)

        # 构建主体参考
        subject_reference = [
            {
                "type": subject_type,
                "image_file": f"data:{mime_type};base64,{reference_image_base64}"
            }
        ]

        return self._generate_with_retry(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            num_images=num_images,
            model_version=model_version,
            subject_reference=subject_reference
        )

    def get_aspect_ratio_for_platform(self, platform: str) -> str:
        """
        根据平台获取推荐的宽高比

        Args:
            platform: 平台名称

        Returns:
            推荐的宽高比字符串
        """
        return self.PLATFORM_ASPECT_RATIOS.get(platform, self.PLATFORM_ASPECT_RATIOS["default"])

    def _parse_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析 API 响应

        Args:
            result: API 原始响应

        Returns:
            解析后的结果
        """
        images = []

        # Minimax API 返回格式：{"data": {"image_urls": [...]}}
        if "data" in result:
            data = result["data"]
            if isinstance(data, dict):
                # 检查 image_urls 字段
                if "image_urls" in data and isinstance(data["image_urls"], list):
                    for url in data["image_urls"]:
                        images.append({"url": url})
                # 检查 image_url 字段（单个）
                elif "image_url" in data:
                    images.append({"url": data["image_url"]})

        # 检查顶层 images 字段
        if "images" in result:
            if isinstance(result["images"], list):
                for img in result["images"]:
                    if isinstance(img, str):
                        images.append({"url": img})
                    elif isinstance(img, dict):
                        images.append(img)
            elif isinstance(result["images"], dict):
                images.append(result["images"])

        # 检查顶层 image_urls 字段
        if "image_urls" in result:
            for url in result["image_urls"]:
                images.append({"url": url})

        # 检查顶层 image_url 字段
        if "image_url" in result:
            images.append({"url": result["image_url"]})

        return {
            "images": images,
            "raw_response": result,
            "usage": result.get("usage", {}),
            "model": result.get("model", "image-01"),
            "created_at": result.get("created_at", int(time.time())),
            "metadata": result.get("metadata", {})
        }

    def save_image(self, image_url: str, save_path: str) -> str:
        """
        下载并保存图片

        Args:
            image_url: 图片 URL
            save_path: 保存路径

        Returns:
            保存后的文件路径
        """
        # 确保目录存在
        save_dir = Path(save_path).parent
        save_dir.mkdir(parents=True, exist_ok=True)

        # 下载图片
        response = requests.get(image_url, timeout=60)
        if response.status_code != 200:
            raise Exception(f"下载图片失败：{response.status_code}")

        # 保存图片
        with open(save_path, "wb") as f:
            f.write(response.content)

        return save_path

    def generate_and_save(
        self,
        prompt: str,
        save_path: str,
        reference_image_path: Optional[str] = None,
        subject_type: str = "character",
        aspect_ratio: str = "1:1",
        num_images: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成图片并保存到本地

        Args:
            prompt: 文字描述
            save_path: 保存路径
            reference_image_path: 参考图路径（可选，提供则使用主体参考模式）
            subject_type: 主体类型（当使用参考图时）
            aspect_ratio: 宽高比
            num_images: 生成图片数量
            **kwargs: 其他参数

        Returns:
            包含结果的字典
        """
        if reference_image_path:
            # 主体参考模式（图生图）
            print(f"使用主体参考模式，参考图：{reference_image_path}, 主体类型：{subject_type}")
            result = self.generate_image_with_subject_reference(
                prompt=prompt,
                reference_image_path=reference_image_path,
                subject_type=subject_type,
                aspect_ratio=aspect_ratio,
                num_images=num_images,
                **kwargs
            )
        else:
            # 文生图模式
            print(f"使用文生图模式")
            result = self.generate_text_to_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                num_images=num_images,
                **kwargs
            )

        # 保存第一张图片
        if result["images"]:
            image_url = result["images"][0].get("url")
            if image_url:
                saved_path = self.save_image(image_url, save_path)
                result["saved_path"] = saved_path
                # 尝试获取相对路径，如果失败则使用绝对路径
                try:
                    result["saved_path_relative"] = str(Path(saved_path).relative_to(Path.cwd()))
                except ValueError:
                    result["saved_path_relative"] = saved_path

        return result


# 便捷函数
def create_minimax_image_client(api_key: Optional[str] = None) -> MinimaxImageClient:
    """创建 Minimax 图片生成客户端"""
    return MinimaxImageClient(api_key=api_key)
