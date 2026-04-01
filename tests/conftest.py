"""
测试配置文件
"""
import os
import pytest
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def root_dir():
    """项目根目录"""
    return ROOT_DIR


@pytest.fixture(scope="session")
def tests_dir():
    """测试目录"""
    return ROOT_DIR / "tests"


@pytest.fixture
def sample_topic():
    """示例主题"""
    return {
        "topic": "AI 写作工具",
        "target_audience": "自媒体创作者",
        "platform": "xiaohongshu",
        "tone": "casual",
        "priority": "standard",
        "emotion": "hopeful",
        "style_preference": "minimalist",
        "brand_keywords": ["AI", "效率", "创作"]
    }


@pytest.fixture
def sample_research_output():
    """示例调研报告"""
    return {
        "trend_analysis": "AI 写作工具在自媒体领域越来越受欢迎，能够帮助创作者提高效率。",
        "pain_points": [
            {
                "title": "写作效率低",
                "description": "很多创作者花费大量时间在素材收集和初稿撰写上"
            },
            {
                "title": "缺乏灵感",
                "description": "面对空白文档不知如何开始"
            }
        ],
        "viral_examples": [
            {
                "title": "《我用 AI 写作，1 天产出 100 篇爆款》",
                "analysis": "数字对比 + 结果展示"
            }
        ],
        "angles": [
            {
                "headline": "我用 AI 写作，1 天产出 100 篇爆款",
                "hook_type": "数字型",
                "confidence_score": 0.9
            },
            {
                "headline": "自媒体人必看！AI 写作工具让效率翻倍",
                "hook_type": "痛点型",
                "confidence_score": 0.85
            }
        ]
    }


@pytest.fixture
def sample_draft():
    """示例文案初稿"""
    return """🔥 我用 AI 写作，1 天产出 100 篇爆款！

姐妹们，今天一定要分享这个神仙工具！
作为一个自媒体人，每天都在为写稿发愁😭

直到我发现了 AI 写作...

💡 3 个核心功能：
1️⃣ 自动收集素材
2️⃣ 智能生成初稿
3️⃣ 一键优化润色

现在每天 2 小时搞定一整天的工作量！
"""


@pytest.fixture
def sample_review():
    """示例审核结果"""
    return {
        "overall_score": 4,
        "dimension_scores": [
            {"dimension": "钩子强度", "score": 5, "comment": "标题使用数字型钩子，吸引力强"},
            {"dimension": "情绪价值", "score": 4, "comment": "有共鸣感，但可以更强烈"},
            {"dimension": "信息密度", "score": 4, "comment": "有干货，但细节不够"},
            {"dimension": "可读性", "score": 5, "comment": "句子简短有力"},
            {"dimension": "平台适配", "score": 4, "comment": "符合小红书调性"},
            {"dimension": "合规检查", "score": 5, "comment": "无夸大宣传"}
        ],
        "highlights": [
            "标题使用数字对比，吸引眼球",
            "使用 emoji 增强可读性",
            "结构清晰，有行动号召"
        ],
        "must_fix_issues": [
            {
                "location": "正文第 2 段",
                "problem": "缺乏具体使用场景",
                "suggestion": "增加 1-2 个具体使用案例"
            }
        ],
        "suggested_improvements": [
            "增加数据支撑",
            "添加用户评价"
        ],
        "conclusion": "modify"
    }


@pytest.fixture(autouse=True)
def setup_env():
    """设置测试环境变量"""
    # 设置测试用 API Key（不会实际调用）
    os.environ["DASHSCOPE_API_KEY"] = "test-api-key-for-testing"
    os.environ["ANTHROPIC_API_KEY"] = "test-api-key-for-testing"
    yield
    # 清理环境变量
    if "DASHSCOPE_API_KEY" in os.environ:
        del os.environ["DASHSCOPE_API_KEY"]
    if "ANTHROPIC_API_KEY" in os.environ:
        del os.environ["ANTHROPIC_API_KEY"]
