"""
Prompt 引擎测试
"""
import pytest
from src.utils.prompt_engine import PromptEngine, PromptTemplate


class TestPromptTemplate:
    """测试 Prompt 模板"""

    def test_template_creation(self):
        """测试创建模板"""
        template = PromptTemplate(
            name="test",
            system_prompt="You are a {role}.",
            user_prompt="Hello, {name}!",
            variables=["role", "name"]
        )
        assert template.name == "test"
        assert template.variables == ["role", "name"]


class TestPromptEngine:
    """测试 Prompt 引擎"""

    def test_engine_creation(self):
        """测试创建引擎"""
        template = PromptTemplate(
            name="test",
            system_prompt="You are a {role}.",
            user_prompt="Hello!",
            variables=["role"]
        )
        engine = PromptEngine(template)
        assert engine.template.name == "test"

    def test_render_basic(self):
        """测试基础渲染"""
        template = PromptTemplate(
            name="test",
            system_prompt="You are a {{ role }}.",
            user_prompt="Hello!",
            variables=["role"]
        )
        engine = PromptEngine(template)
        system, user = engine.render({"role": "developer"})
        # 注意：当前实现 system_prompt 不做渲染，只有 user_prompt 渲染
        assert system == "You are a {{ role }}."
        assert user == "Hello!"

    def test_render_missing_variable(self):
        """测试缺失变量"""
        template = PromptTemplate(
            name="test",
            system_prompt="You are a {{ role }}.",
            user_prompt="Hello {{ name }}!",
            variables=["role", "name"]
        )
        engine = PromptEngine(template)
        # 缺失变量时 Jinja2 会输出空字符串
        system, user = engine.render({"role": "developer"})
        assert user == "Hello !"  # 缺失变量变为空字符串

    def test_render_with_examples(self):
        """测试带示例的渲染"""
        template = PromptTemplate(
            name="test",
            system_prompt="You are a {{ role }}.",
            user_prompt="Hello!",
            variables=["role"],
            examples=[{"input": "test", "output": "result"}]
        )
        engine = PromptEngine(template)
        system, user = engine.render({"role": "developer"}, include_examples=True)
        # system prompt 当前不渲染
        assert "role" in system  # 保留原始模板
        assert "示例" in user

    def test_render_user_prompt_only(self):
        """测试仅渲染 User Prompt"""
        template = PromptTemplate(
            name="test",
            system_prompt="You are a {{ role }}.",
            user_prompt="Hello {{ name }}!",
            variables=["role", "name"]
        )
        engine = PromptEngine(template)
        user = engine.render_user_prompt({"name": "World"})
        assert user == "Hello World!"

    def test_few_shot_generation(self):
        """测试 Few-shot 生成"""
        template = PromptTemplate(
            name="test",
            system_prompt="Test",
            user_prompt="Hello!",
            variables=[]
        )
        engine = PromptEngine(template)
        examples = [
            {"input": "Hi", "output": "Hello"},
            {"input": "Bye", "output": "Goodbye"}
        ]
        result = engine.with_few_shot(examples)
        assert "输入：Hi" in result
        assert "输出：Hello" in result

    def test_create_template_static(self):
        """测试静态方法创建模板"""
        template = PromptEngine.create_template(
            name="static_test",
            system_prompt="System",
            user_prompt="User",
            variables=["var1"]
        )
        assert template.name == "static_test"
        assert template.variables == ["var1"]
