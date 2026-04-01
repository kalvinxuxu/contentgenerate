"""
调研 Agent Prompt 模板
支持产品图片分析
"""

SYSTEM_PROMPT = """
你是内容选题专家，擅长利用搜索工具分析热点趋势、挖掘用户痛点、拆解爆款逻辑。
你的分析将直接决定文案的传播潜力。

请严格按照 JSON 格式输出，不要包含其他说明文字。
"""

USER_PROMPT = """
# 任务
针对以下主题和产品，分析过去 7 天的热搜趋势、用户痛点和前 3 名的爆款逻辑，
输出 3 个具有"病毒式传播"潜力的选题切入点。

# 输入信息
- **主题**: {{ topic }}
- **目标受众**: {{ target_audience }}
- **发布平台**: {{ platform }}
- **品牌关键词**: {{ brand_keywords | default('无', true) }}
{% if product_image %}
- **产品图片**: 已上传，需要进行产品分析
{% endif %}

# 分析维度

## 1. 热搜趋势分析
- 检索过去 7 天内与主题相关的热门话题
- 识别热度上升最快的关键词
- 分析话题背后的社会情绪

## 2. 用户痛点挖掘
- 目标受众的核心焦虑/需求是什么
- 他们最想知道但还没得到解答的问题
- 哪些情绪点最容易引发共鸣

## 3. 爆款逻辑拆解
- 分析同类内容中点赞/转发最高的前 3 篇
- 提炼它们的共同特征（标题结构、情绪触发点、价值主张）
- 总结可复用的公式

{% if product_image %}
## 4. 产品分析（重要）
基于用户上传的产品图片，分析：
- 产品的质感、外观特点
- 可能的口味/功能特性
- 与市场上同类产品的差异化优势
- 可主打的宣传卖点（2-3 个）
{% endif %}

# 输出格式（JSON）
```json
{
    "trend_analysis": "200 字以内的趋势分析",
    "pain_points": [
        {
            "title": "痛点标题",
            "description": "详细描述",
            "emotion": "焦虑/需求/渴望",
            "intensity": 5
        }
    ],
    "viral_examples": [
        {
            "title": "爆款标题",
            "platform": "平台名称",
            "metrics": {"likes": 10000, "shares": 1000},
            "core_logics": "一句话总结核心逻辑",
            "reusable_patterns": ["模式 1", "模式 2"]
        }
    ],
    "angles": [
        {
            "headline": "吸引人的标题",
            "target_audience": "具体受众",
            "emotion_trigger": "好奇/焦虑/共鸣/爽感",
            "core_value": "用户能得到什么",
            "viral_potential": "为什么能火",
            "confidence_score": 0.9
        }
    ]{% if product_image %},{% endif %}
{% if product_image %}
    "product_analysis": {
        "description": "产品外观/质感描述",
        "features": ["特点 1", "特点 2"],
        "selling_points": [
            {
                "name": "卖点名称",
                "description": "详细描述",
                "differentiation": "与竞品的差异"
            }
        ]
    }
{% else %}
    "product_analysis": null
{% endif %}
}
```
```
"""

# Few-shot 示例
FEW_SHOT_EXAMPLES = [
    {
        "input": """
主题：AI 写作工具
目标受众：内容创作者、自媒体人
发布平台：小红书
品牌关键词：高效、智能、易用
        """,
        "output": """
{
    "trend_analysis": "过去 7 天，'AI 写作'相关话题热度上升 150%，关键词'ChatGPT 写作''AI 文案'搜索量激增。社会情绪呈现两极分化：一方面是对效率提升的期待，另一方面是对被替代的焦虑。",
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
        },
        {
            "title": "担心被 AI 取代",
            "description": "看到别人用 AI 写作，自己会不会被淘汰",
            "emotion": "焦虑",
            "intensity": 4
        }
    ],
    "viral_examples": [
        {
            "title": "我用 AI 写作，3 天涨粉 1 万",
            "platform": "小红书",
            "metrics": {"likes": 15000, "shares": 2000, "comments": 800},
            "core_logics": "结果展示 + 数据背书 + 方法分享",
            "reusable_patterns": ["数据化标题", "前后对比", "步骤拆解"]
        },
        {
            "title": "AI 写作 vs 人工写作，差距有多大？",
            "platform": "公众号",
            "metrics": {"likes": 10000, "shares": 1500, "comments": 500},
            "core_logics": "对比冲突 + 实测数据",
            "reusable_patterns": ["对比型标题", "实测展示", "客观评价"]
        },
        {
            "title": "30 天使用 AI 写作，我发现了这些坑",
            "platform": "知乎",
            "metrics": {"likes": 8000, "shares": 1000, "comments": 600},
            "core_logics": "经验分享 + 避坑指南",
            "reusable_patterns": ["时间跨度", "经验总结", "避坑清单"]
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
        },
        {
            "headline": "30 天 AI 写作实测：这 3 个坑千万别踩",
            "target_audience": "想尝试 AI 写作的人",
            "emotion_trigger": "焦虑 + 需求",
            "core_value": "避免踩坑，少走弯路",
            "viral_potential": "避坑内容天然有传播价值",
            "confidence_score": 0.85
        },
        {
            "headline": "AI 写作 vs 人工写作，差距比你想的大",
            "target_audience": "内容创作者",
            "emotion_trigger": "好奇 + 焦虑",
            "core_value": "了解 AI 写作真实水平",
            "viral_potential": "对比型内容容易引发讨论",
            "confidence_score": 0.8
        }
    ],
    "product_analysis": null
}
        """
    }
]
