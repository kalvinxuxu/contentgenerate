"""
图片上传工具
支持参考图上传和管理
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
import shutil


class ImageUploader:
    """图片上传管理器"""

    def __init__(self, upload_dir: Optional[str] = None):
        """
        初始化图片上传器

        Args:
            upload_dir: 上传目录，默认为 uploads/
        """
        if upload_dir is None:
            # 使用项目根目录下的 uploads 文件夹
            base_dir = Path(__file__).parent.parent.parent
            upload_dir = base_dir / "uploads"

        self.upload_dir = Path(upload_dir)
        self._ensure_upload_dir()

    def _ensure_upload_dir(self):
        """确保上传目录存在"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def upload(self, file_path: str, keep_original_name: bool = False) -> Dict[str, Any]:
        """
        上传图片文件

        Args:
            file_path: 原始文件路径
            keep_original_name: 是否保留原始文件名

        Returns:
            上传结果字典
        """
        source_path = Path(file_path)

        if not source_path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")

        # 验证文件类型
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
        if source_path.suffix.lower() not in valid_extensions:
            raise ValueError(f"不支持的文件类型：{source_path.suffix}")

        # 生成目标文件名
        if keep_original_name:
            dest_filename = source_path.name
        else:
            # 使用 UUID 生成唯一文件名
            dest_filename = f"{uuid.uuid4()}{source_path.suffix.lower()}"

        dest_path = self.upload_dir / dest_filename

        # 复制文件
        shutil.copy2(source_path, dest_path)

        return {
            "success": True,
            "original_name": source_path.name,
            "stored_name": dest_filename,
            "file_path": str(dest_path),
            "file_size": dest_path.stat().st_size,
            "mime_type": self._get_mime_type(dest_path.suffix)
        }

    def upload_base64(self, base64_data: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        上传 base64 编码的图片

        Args:
            base64_data: base64 编码的图片数据
            filename: 可选的文件名

        Returns:
            上传结果字典
        """
        import base64

        # 解码 base64
        try:
            image_data = base64.b64decode(base64_data)
        except Exception as e:
            raise ValueError(f"Base64 解码失败：{e}")

        # 生成文件名
        if filename is None:
            filename = f"{uuid.uuid4()}.png"

        dest_path = self.upload_dir / filename

        # 保存图片
        with open(dest_path, "wb") as f:
            f.write(image_data)

        return {
            "success": True,
            "stored_name": filename,
            "file_path": str(dest_path),
            "file_size": dest_path.stat().st_size
        }

    def _get_mime_type(self, extension: str) -> str:
        """获取 MIME 类型"""
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif"
        }
        return mime_types.get(extension.lower(), "application/octet-stream")

    def get_file_path(self, filename: str) -> str:
        """
        获取文件的完整路径

        Args:
            filename: 文件名

        Returns:
            完整文件路径
        """
        return str(self.upload_dir / filename)

    def list_images(self) -> list:
        """
        列出所有已上传的图片

        Returns:
            图片信息列表
        """
        images = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.gif"]:
            for file_path in self.upload_dir.glob(ext):
                images.append({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "file_size": file_path.stat().st_size,
                    "mime_type": self._get_mime_type(file_path.suffix)
                })
        return images

    def delete(self, filename: str) -> bool:
        """
        删除图片

        Args:
            filename: 文件名

        Returns:
            是否成功删除
        """
        file_path = self.upload_dir / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False


# 便捷函数
def create_image_uploader(upload_dir: Optional[str] = None) -> ImageUploader:
    """创建图片上传器"""
    return ImageUploader(upload_dir=upload_dir)


def upload_image(file_path: str, keep_original_name: bool = False) -> Dict[str, Any]:
    """便捷函数：上传图片"""
    uploader = create_image_uploader()
    return uploader.upload(file_path, keep_original_name)
