"""
测试创作 Agent 的输入数据流
"""

import json
from src.agents.prompts.creator import SYSTEM_PROMPT, USER_PROMPT
from src.utils.prompt_engine import PromptEngine, PromptTemplate

# 模拟调研 Agent 的输出
research_report = {
    "trend_analysis": "过去 7 天，'AI 写作'相关话题热度上升 150%",
    "pain_points": [
        {
            "title": "写作效率低，熬夜赶稿成常态",
            "description": "每天花费 3-4 小时写一篇文案，还要反复修改",
            "emotion": "焦虑",
            "intensity": 5
        },
        {
            "title": "不知道写什么，选题困难",
            "description": "面对空白文档发呆，没有灵感和方向",
            "emotion": "需求",
            "intensity": 4
        }
    ],
    "viral_examples": [
        {
            "title": "我用 AI 写作，3 天涨粉 1 万",
            "platform": "小红书",
            "metrics": {"likes": 15000, "shares": 2000},
            "core_logics": "结果展示 + 数据背书 + 方法分享",
            "reusable_patterns": ["数据化标题", "前后对比", "步骤拆解"]
        }
    ],
    "angles": [
        {
            "headline": "我用 AI 写作，3 天涨粉 1 万，方法公开",
            "target_audience": "0-1 岁自媒体新人",
            "emotion_trigger": "好奇 + 爽感",
            "core_value": "学到 AI 写作涨粉方法",
            "viral_potential": "数据吸引眼球 + 方法可复制",
            "confidence_score": 0.9
        }
    ]
}

# 模拟 selected_angle
selected_angle = research_report["angles"][0]

# 准备变量
variables = {
    "angle": selected_angle,
    "pain_points": research_report["pain_points"],
    "viral_examples": research_report["viral_examples"],
    "tone": "casual"
}

print("=" * 60)
print("测试创作 Agent Prompt 渲染")
print("=" * 60)

# 初始化 Prompt 引擎
prompt_engine = PromptEngine(
    PromptTemplate(
        name="creator_agent",
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT,
        variables=["angle", "pain_points", "viral_examples", "tone"],
        examples=[]
    )
)

# 渲染 Prompt
system_prompt, user_prompt = prompt_engine.render(variables, include_examples=False)

print("\n[System Prompt]")
print(system_prompt)

print("\n[User Prompt]")
print(user_prompt)

print("\n" + "=" * 60)
print("变量检查")
print("=" * 60)
print(f"angle.headline: {selected_angle.get('headline')}")
print(f"angle.target_audience: {selected_angle.get('target_audience')}")
print(f"angle.emotion_trigger: {selected_angle.get('emotion_trigger')}")
print(f"angle.core_value: {selected_angle.get('core_value')}")
print(f"pain_points 数量：{len(research_report['pain_points'])}")
print(f"viral_examples 数量：{len(research_report['viral_examples'])}")
