"""
LLM 客户端测试
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.utils.claude_client import ClaudeClient, TokenUsage, LLMResponse, PRICING
from src.utils.llm_client_v2 import get_backend_type, LLMBackend


class TestTokenUsage:
    """测试 TokenUsage 数据类"""

    def test_to_dict(self):
        """测试转换为字典"""
        usage = TokenUsage(
            model="claude-sonnet-4-6",
            input_tokens=100,
            output_tokens=50,
            cost=0.00105,
            timestamp="2026-04-01T10:00:00",
            request_type="chat"
        )
        result = usage.to_dict()
        assert result["model"] == "claude-sonnet-4-6"
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["cost"] == 0.00105


class TestLLMResponse:
    """测试 LLMResponse 数据类"""

    def test_to_dict(self):
        """测试转换为字典"""
        response = LLMResponse(
            content="Hello, world!",
            input_tokens=10,
            output_tokens=20,
            model="claude-sonnet-4-6",
            stop_reason="end_turn"
        )
        result = response.to_dict()
        assert result["content"] == "Hello, world!"
        assert result["stop_reason"] == "end_turn"


class TestPricing:
    """测试定价配置"""

    def test_opus_pricing(self):
        """测试 Opus 定价"""
        assert PRICING["claude-opus-4-6"]["input"] == 0.015
        assert PRICING["claude-opus-4-6"]["output"] == 0.075

    def test_sonnet_pricing(self):
        """测试 Sonnet 定价"""
        assert PRICING["claude-sonnet-4-6"]["input"] == 0.003
        assert PRICING["claude-sonnet-4-6"]["output"] == 0.015

    def test_haiku_pricing(self):
        """测试 Haiku 定价"""
        assert PRICING["claude-haiku-4-5-20251001"]["input"] == 0.001
        assert PRICING["claude-haiku-4-5-20251001"]["output"] == 0.005

    def test_default_pricing(self):
        """测试默认定价"""
        assert "input" in PRICING["default"]
        assert "output" in PRICING["default"]


class TestClaudeClientInit:
    """测试 ClaudeClient 初始化"""

    def test_init_with_api_key(self, monkeypatch):
        """测试使用 API Key 初始化"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        client = ClaudeClient()
        assert client.api_key == "test-key"
        assert client.model == "claude-sonnet-4-6"

    def test_init_with_custom_params(self, monkeypatch):
        """测试自定义参数初始化"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        client = ClaudeClient(
            model="claude-opus-4-6",
            temperature=0.5,
            max_tokens=1024
        )
        assert client.model == "claude-opus-4-6"
        assert client.temperature == 0.5
        assert client.max_tokens == 1024

    def test_init_without_api_key(self, monkeypatch):
        """测试缺少 API Key 时报错"""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            ClaudeClient()

    def test_init_with_passed_api_key(self):
        """测试传入 API Key 初始化"""
        client = ClaudeClient(api_key="test-key")
        assert client.api_key == "test-key"


class TestClaudeClientCostCalculation:
    """测试成本计算"""

    def test_calculate_cost_sonnet(self, monkeypatch):
        """测试 Sonnet 成本计算"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        client = ClaudeClient(model="claude-sonnet-4-6")
        cost = client._calculate_cost(1000, 500)
        # 1000 * 0.003/1000 + 500 * 0.015/1000 = 0.003 + 0.0075 = 0.0105
        assert abs(cost - 0.0105) < 0.0001

    def test_calculate_cost_opus(self, monkeypatch):
        """测试 Opus 成本计算"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        client = ClaudeClient(model="claude-opus-4-6")
        cost = client._calculate_cost(1000, 500)
        # 1000 * 0.015/1000 + 500 * 0.075/1000 = 0.015 + 0.0375 = 0.0525
        assert abs(cost - 0.0525) < 0.0001

    def test_calculate_cost_haiku(self, monkeypatch):
        """测试 Haiku 成本计算"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        client = ClaudeClient(model="claude-haiku-4-5-20251001")
        cost = client._calculate_cost(1000, 500)
        # 1000 * 0.001/1000 + 500 * 0.005/1000 = 0.001 + 0.0025 = 0.0035
        assert abs(cost - 0.0035) < 0.0001


class TestGetBackendType:
    """测试后端类型检测"""

    def test_anthropic_explicit(self, monkeypatch):
        """测试显式指定 Anthropic"""
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        assert get_backend_type() == LLMBackend.ANTHROPIC

    def test_anthropic_api_key(self, monkeypatch):
        """测试有 Anthropic API Key"""
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        assert get_backend_type() == LLMBackend.ANTHROPIC

    def test_dashscope_explicit(self, monkeypatch):
        """测试显式指定 DashScope"""
        # 清理可能存在的 API Key
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "dashscope")
        assert get_backend_type() == LLMBackend.DASHSCOPE

    def test_dashscope_api_key(self, monkeypatch):
        """测试有 DashScope API Key"""
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
        assert get_backend_type() == LLMBackend.DASHSCOPE

    def test_default_to_anthropic(self, monkeypatch):
        """测试默认使用 Anthropic"""
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        assert get_backend_type() == LLMBackend.ANTHROPIC
