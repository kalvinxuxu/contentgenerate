"""
Minimax 图片生成客户端测试
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from src.utils.minimax_client import MinimaxImageClient, create_minimax_image_client


class TestMinimaxImageClientInit:
    """测试 MinimaxImageClient 初始化"""

    def test_init_with_api_key(self, monkeypatch):
        """测试使用 API Key 初始化"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")
        client = MinimaxImageClient()
        assert client.api_key == "test-minimax-key"

    def test_init_without_api_key(self, monkeypatch):
        """测试缺少 API Key 时报错"""
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        with pytest.raises(ValueError, match="MINIMAX_API_KEY"):
            MinimaxImageClient()

    def test_init_with_passed_api_key(self):
        """测试传入 API Key 初始化"""
        client = MinimaxImageClient(api_key="test-key")
        assert client.api_key == "test-key"

    def test_create_client_factory(self, monkeypatch):
        """测试工厂函数"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = create_minimax_image_client()
        assert isinstance(client, MinimaxImageClient)


class TestPlatformAspectRatios:
    """测试平台宽高比"""

    def test_xiaohongshu_ratio(self, monkeypatch):
        """测试小红书宽高比"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = MinimaxImageClient()
        ratio = client.get_aspect_ratio_for_platform("xiaohongshu")
        assert ratio == "3:4"

    def test_wechat_ratio(self, monkeypatch):
        """测试微信公众号宽高比"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = MinimaxImageClient()
        ratio = client.get_aspect_ratio_for_platform("wechat")
        assert ratio == "16:9"

    def test_blog_ratio(self, monkeypatch):
        """测试博客宽高比"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = MinimaxImageClient()
        ratio = client.get_aspect_ratio_for_platform("blog")
        assert ratio == "16:9"

    def test_default_ratio(self, monkeypatch):
        """测试默认宽高比"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = MinimaxImageClient()
        ratio = client.get_aspect_ratio_for_platform("unknown")
        assert ratio == "1:1"


class TestImageMimeType:
    """测试图片 MIME 类型"""

    def test_jpg_mime(self, monkeypatch, tmp_path):
        """测试 JPG MIME 类型"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = MinimaxImageClient()
        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"fake image data")
        mime = client._get_image_mime_type(str(img_path))
        assert mime == "image/jpeg"

    def test_png_mime(self, monkeypatch, tmp_path):
        """测试 PNG MIME 类型"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = MinimaxImageClient()
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b"fake image data")
        mime = client._get_image_mime_type(str(img_path))
        assert mime == "image/png"

    def test_webp_mime(self, monkeypatch, tmp_path):
        """测试 WebP MIME 类型"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = MinimaxImageClient()
        img_path = tmp_path / "test.webp"
        img_path.write_bytes(b"fake image data")
        mime = client._get_image_mime_type(str(img_path))
        assert mime == "image/webp"

    def test_default_mime(self, monkeypatch, tmp_path):
        """测试默认 MIME 类型"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = MinimaxImageClient()
        img_path = tmp_path / "test.xyz"
        img_path.write_bytes(b"fake image data")
        mime = client._get_image_mime_type(str(img_path))
        assert mime == "image/jpeg"


class TestResponseParsing:
    """测试响应解析"""

    def test_parse_image_urls_list(self, monkeypatch):
        """测试解析 image_urls 列表"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = MinimaxImageClient()
        result = client._parse_response({
            "data": {
                "image_urls": ["http://example.com/1.jpg", "http://example.com/2.jpg"]
            }
        })
        assert len(result["images"]) == 2
        assert result["images"][0]["url"] == "http://example.com/1.jpg"

    def test_parse_single_image_url(self, monkeypatch):
        """测试解析单个 image_url"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = MinimaxImageClient()
        result = client._parse_response({
            "data": {
                "image_url": "http://example.com/1.jpg"
            }
        })
        assert len(result["images"]) == 1
        assert result["images"][0]["url"] == "http://example.com/1.jpg"

    def test_parse_top_level_images(self, monkeypatch):
        """测试解析顶层 images 字段"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = MinimaxImageClient()
        result = client._parse_response({
            "images": ["http://example.com/1.jpg"]
        })
        assert len(result["images"]) == 1

    def test_parse_empty_response(self, monkeypatch):
        """测试解析空响应"""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = MinimaxImageClient()
        result = client._parse_response({})
        assert len(result["images"]) == 0
        assert result["model"] == "image-01"
