"""
配置模块测试
"""
import pytest
import os
from src.utils.config import load_config, get_model_config, get_platform_config


class TestLoadConfig:
    """测试配置加载功能"""

    def test_load_config_exists(self, root_dir):
        """测试配置文件存在"""
        config_path = root_dir / "config" / "settings.yaml"
        assert config_path.exists(), "配置文件不存在"

    def test_load_config_returns_dict(self):
        """测试加载返回字典"""
        config = load_config()
        assert isinstance(config, dict)

    def test_load_config_has_models(self):
        """测试配置包含模型配置"""
        config = load_config()
        assert "models" in config

    def test_load_config_has_platforms(self):
        """测试配置包含平台配置"""
        config = load_config()
        assert "platforms" in config


class TestGetModelConfig:
    """测试获取模型配置"""

    def test_get_default_config(self):
        """测试获取默认配置"""
        config = get_model_config("research")
        assert "model" in config
        assert "temperature" in config
        assert "max_tokens" in config

    def test_get_research_config(self):
        """测试获取调研 Agent 配置"""
        config = get_model_config("research")
        assert config["model"] == "claude-sonnet-4-6"
        assert config["temperature"] == 0.7

    def test_get_creator_config(self):
        """测试获取创作 Agent 配置"""
        config = get_model_config("creator")
        assert config["temperature"] == 0.8

    def test_get_reviewer_config(self):
        """测试获取审核 Agent 配置"""
        config = get_model_config("reviewer")
        assert config["temperature"] == 0.3

    def test_get_optimizer_config(self):
        """测试获取优化 Agent 配置"""
        config = get_model_config("optimizer")
        assert config["temperature"] == 0.5

    def test_get_image_config(self):
        """测试获取配图 Agent 配置"""
        config = get_model_config("image")
        assert config["temperature"] == 0.7

    def test_environment_override(self, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv("DEFAULT_MODEL", "test-model")
        monkeypatch.setenv("TEMPERATURE", "0.9")

        config = get_model_config("research")
        assert config["model"] == "test-model"
        assert config["temperature"] == 0.9


class TestGetPlatformConfig:
    """测试获取平台配置"""

    def test_get_wechat_config(self):
        """测试获取微信公众号配置"""
        config = get_platform_config("wechat")
        assert config["name"] == "微信公众号"
        assert config["cover_ratio"] == "16:9"

    def test_get_xiaohongshu_config(self):
        """测试获取小红书配置"""
        config = get_platform_config("xiaohongshu")
        assert config["name"] == "小红书"
        assert config["cover_ratio"] == "3:4"

    def test_get_blog_config(self):
        """测试获取博客配置"""
        config = get_platform_config("blog")
        assert config["cover_ratio"] == "16:9"

    def test_get_unknown_platform(self):
        """测试获取未知平台配置"""
        config = get_platform_config("unknown")
        assert config == {}
