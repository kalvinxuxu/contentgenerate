"""
配图 Agent Prompt 模板
"""

SYSTEM_PROMPT = """
你是视觉创意总监，有 8 年新媒体视觉设计经验。
你擅长为文案内容匹配视觉元素，懂得如何用图像增强文案感染力。

请严格按照 JSON 格式输出，不要包含其他说明文字。
"""

USER_PROMPT = """
# 任务
为给定的文案内容生成 3 组 Midjourney 提示词和排版建议。

# 输入信息
- **文案内容**: {{ content }}
- **发布平台**: {{ platform }}
- **情绪基调**: {{ emotion }}
- **品牌色**: {{ brand_colors }}
- **风格偏好**: {{ style_preference }}

## 设计要求

### 1. Midjourney 提示词生成
- 每组提示词对应一种视觉风格
- 提示词必须包含：主体 + 场景 + 情绪 + 风格关键词
- 提供负向提示词避免 unwanted elements
- 设置合适的长宽比和参数

### 2. 排版建议
- 根据平台特性给出构图方案
- 说明文字与图像的位置关系
- 提供视觉层级指导

### 3. 配色方案
- 基于文案情绪选择主色调
- 提供 5 色配色板（主色、辅色、强调色、背景、文字）
- 考虑品牌色彩要求

# Midjourney 参数说明
- --ar 16:9 : 横版（适合公众号头图）
- --ar 3:4  : 竖版（适合小红书封面）
- --ar 1:1  : 正方形（适合配图插图）
- --v 5.2   : 使用版本 5.2
- --stylize 250 : 艺术化程度（0-1000）
- --niji 5  : 二次元风格

# 输出格式（JSON）
```json
{
    "mj_prompts": [
        {
            "style": "极简风",
            "prompt_en": "minimalist product photography, clean background, soft lighting, professional --ar 3:4 --v 5.2",
            "prompt_cn": "极简产品摄影，干净背景，柔和光线，专业质感",
            "negative_prompt": "cluttered, noisy, oversaturated, amateur",
            "params": {"--ar": "3:4", "--v": "5.2", "--stylize": 250},
            "mood": "专业、高端",
            "use_case": "小红书封面"
        }
    ],
    "layout_suggestions": {
        "composition": "rule-of-thirds",
        "text_position": "bottom",
        "image_text_ratio": "70:30",
        "visual_hierarchy": ["主图", "标题", "副标题", "CTA"],
        "whitespace_advice": "顶部留白 20%，便于添加标题",
        "platform_specific": {"xiaohongshu": "竖版 3:4，文字不超过画面 30%"}
    },
    "color_palette": {
        "primary": "#1565C0",
        "secondary": "#42A5F5",
        "accent": "#FF7043",
        "background": "#F5F5F5",
        "text": "#212121",
        "mood_description": "蓝色系传递专业信任感，橙色强调行动"
    },
    "font_recommendations": ["思源黑体 Medium", "苹方 Regular"],
    "rationale": "设计理念说明..."
}
```
"""

# Few-shot 示例
FEW_SHOT_EXAMPLES = [
    {
        "input": """
文案内容：
"28 岁存款为 0，我是如何做到月收入 5 万的？

说出来可能不信。
一年前的我，连房租都要刷信用卡。

现在的我，每个月稳定收入 5 位数。

不是凡尔赛，只是想告诉你：
选对赛道，真的比努力重要 100 倍。

这 3 个副业，普通人也能做：
1. 自媒体代运营 - 我靠它赚了第一桶金
2. AI 写作变现 - 现在每个月持续性收入 3 万 +
3. 知识付费分销 - 零成本起步，适合所有人

如果你想试试，可以从第一个开始。
不需要辞职，利用下班时间就能做。

今天就开始，别让犹豫耽误你。"

发布平台：xiaohongshu
情绪基调：hopeful
品牌色：["#1565C0", "#FF7043"]
风格偏好：minimalist
        """,
        "output": """
{
    "mj_prompts": [
        {
            "style": "极简摄影风",
            "prompt_en": "young asian woman working on laptop at minimalist desk, soft natural lighting, clean white background, hopeful expression, financial freedom concept, professional photography --ar 3:4 --v 5.2 --stylize 200",
            "prompt_cn": "年轻亚洲女性在极简书桌前使用笔记本电脑，柔和自然光，干净白色背景，充满希望的表情，财务自由概念，专业摄影",
            "negative_prompt": "cluttered, dark, stressful, oversaturated, messy",
            "params": {"--ar": "3:4", "--v": "5.2", "--stylize": 200},
            "mood": "希望、专业",
            "use_case": "小红书封面"
        },
        {
            "style": "扁平插画风",
            "prompt_en": "flat illustration of person growing from seed to tree, money leaves, financial growth journey, pastel colors, minimalist style, hopeful atmosphere --ar 3:4 --niji 5",
            "prompt_cn": "扁平插画，人物从种子成长为大树，金钱叶子，财务成长之旅，粉彩色系，极简风格，希望氛围",
            "negative_prompt": "realistic, 3d, dark, complex details",
            "params": {"--ar": "3:4", "--niji": "5", "--stylize": 150},
            "mood": "轻松、希望",
            "use_case": "小红书内页配图"
        },
        {
            "style": "对比拼贴风",
            "prompt_en": "split composition, left side empty wallet and bills, right side laptop and growing charts, transformation concept, clean modern design, blue and orange accent --ar 3:4 --v 5.2",
            "prompt_cn": "分割构图，左侧空钱包和账单，右侧笔记本电脑和增长图表，转变概念，干净现代设计，蓝色和橙色强调",
            "negative_prompt": "messy, too many elements, low quality",
            "params": {"--ar": "3:4", "--v": "5.2", "--stylize": 250},
            "mood": "反差、激励",
            "use_case": "小红书封面"
        }
    ],
    "layout_suggestions": {
        "composition": "rule-of-thirds",
        "text_position": "top",
        "image_text_ratio": "65:35",
        "visual_hierarchy": ["主标题（顶部）", "人物/主体（中下部）", "副标题/装饰（底部）"],
        "whitespace_advice": "顶部留白 30%，便于放置标题文字",
        "platform_specific": {
            "xiaohongshu": "竖版 3:4 比例，文字使用白色加黑色描边，确保可读性"
        }
    },
    "color_palette": {
        "primary": "#1565C0",
        "secondary": "#64B5F6",
        "accent": "#FF7043",
        "background": "#FAFAFA",
        "text": "#212121",
        "mood_description": "蓝色系传递专业与信任，橙色作为强调色激发行动欲，整体低饱和度营造冷静专业感"
    },
    "font_recommendations": ["思源黑体 Medium（标题）", "思源黑体 Regular（正文）", "OPPO Sans（数字强调）"],
    "rationale": "基于文案的'财务转变'主题，视觉上采用前后对比的手法。主图建议用人物工作状态传递希望感，配色使用品牌蓝 + 活力橙，符合小红书用户对'成长''副业'内容的视觉期待。"
}
        """
    }
]
