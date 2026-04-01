# Phase 2: Agent 架构设计文档

## 概述

本文档详细描述 4 个核心 Agent 的架构设计，包括职责边界、输入输出接口、Prompt 模板和数据处理逻辑。

---

## 1. 调研 Agent (ResearchAgent)

### 1.1 职责定义

**核心职责**：内容选题专家，负责分析主题、挖掘热点、拆解爆款逻辑。

**具体任务**：
- 分析过去 7 天的热搜趋势
- 挖掘目标用户的核心痛点
- 拆解前 3 名爆款内容的逻辑
- 输出 3 个病毒式传播潜力的选题切入点

### 1.2 输入接口

```python
class ResearchInput(BaseModel):
    topic: str                    # 内容主题（必填）
    target_audience: str          # 目标受众描述（必填）
    platform: str                 # 发布平台：wechat/xiaohongshu/blog（必填）
    brand_keywords: List[str]     # 品牌关键词（可选）
    competitor_analysis: str      # 竞品分析输入（可选）
    search_results: List[dict]    # 外部搜索结果（可选）
```

### 1.3 输出接口

```python
class ResearchOutput(BaseModel):
    trend_analysis: str                    # 热搜趋势分析（200 字内）
    pain_points: List[PainPoint]           # 用户痛点 TOP3
    viral_examples: List[ViralExample]     # 爆款案例拆解（3 个）
    angles: List[ContentAngle]             # 病毒式选题切入点（3 个）
    raw_data: dict                         # 原始数据（用于 trace）

class PainPoint(BaseModel):
    title: str              # 痛点标题
    description: str        # 详细描述
    emotion: str            # 情绪类型：焦虑/需求/渴望
    intensity: int          # 强度评分 1-5

class ViralExample(BaseModel):
    title: str              # 爆款标题
    platform: str           # 发布平台
    metrics: dict           # 数据指标（点赞/转发/评论）
    core_logic: str         # 核心逻辑（一句话）
    reusable_patterns: List[str]  # 可复用模式

class ContentAngle(BaseModel):
    headline: str           # 吸引人的标题
    target_audience: str    # 具体受众
    emotion_trigger: str    # 情绪触发：好奇/焦虑/共鸣/爽感
    core_value: str         # 核心价值
    viral_potential: str    # 预期爆点
    confidence_score: float # 置信度 0-1
```

### 1.4 Prompt 模板

```python
RESEARCH_AGENT_PROMPT = """
# 角色
你是内容选题专家，擅长利用搜索工具分析热点趋势、挖掘用户痛点、拆解爆款逻辑。

# 任务
针对用户给出的主题，分析过去 7 天的热搜趋势、用户痛点和前 3 名的爆款逻辑，
输出 3 个具有"病毒式传播"潜力的选题切入点。

# 输入信息
- 主题：{topic}
- 目标受众：{target_audience}
- 发布平台：{platform}
- 品牌关键词：{brand_keywords}

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

# 输出格式（JSON）
{{
    "trend_analysis": "200 字以内的趋势分析",
    "pain_points": [
        {{"title": "痛点 1", "description": "...", "emotion": "焦虑", "intensity": 5}}
    ],
    "viral_examples": [
        {{"title": "爆款标题", "platform": "小红书", "metrics": {{"likes": 10000}}, "core_logic": "...", "reusable_patterns": ["..."]}}
    ],
    "angles": [
        {{"headline": "标题", "target_audience": "...", "emotion_trigger": "好奇", "core_value": "...", "viral_potential": "...", "confidence_score": 0.9}}
    ]
}}
"""
```

### 1.5 处理流程

```
Input → Parse → [Trend Analysis] → [Pain Point Mining] → [Viral Example Analysis] → [Angle Generation] → Output
                 ↓                        ↓                        ↓                        ↓
            热搜关键词                痛点列表                 爆款模式                 切入点列表
```

---

## 2. 创作 Agent (CreatorAgent)

### 2.1 职责定义

**核心职责**：爆款文案写手，基于调研报告撰写高传播文案。

**具体任务**：
- 基于选定的选题切入点创作
- 使用强力钩子抓住注意力
- 注入情绪价值引发共鸣
- 生成符合平台调性的文案

### 2.2 输入接口

```python
class CreatorInput(BaseModel):
    research_report: ResearchOutput    # 调研报告（必填）
    selected_angle: ContentAngle       # 选定的切入点（必填）
    tone: str                          # 语气风格：formal/casual/passionate（必填）
    length: str                        # 文案长度：short/medium/long（必填）
    platform: str                      # 发布平台（必填）
    brand_guidelines: BrandGuidelines  # 品牌规范（可选）
```

### 2.3 输出接口

```python
class CreatorOutput(BaseModel):
    content_type: str                  # 文案类型
    headline: str                      # 标题（可选）
    body: str                          # 文案正文
    hook_type: str                     # 使用的钩子类型
    emotion_trigger: str               # 情绪触发点
    target_audience: str               # 目标受众
    image_suggestions: List[str]       # 配图建议
    metadata: dict                     # 元数据（字数/段落数等）
```

### 2.4 Prompt 模板

```python
CREATOR_AGENT_PROMPT = """
# 角色
你是爆款文案写手，擅长写出让人"一眼入魂"的高传播文案。
你的文字有感染力，懂得如何抓住读者注意力并引发行动。

# 任务
基于调研结果生成文案初稿，必须满足以下要求：

## 核心要求
1. **第一句话必须是强力钩子（Hook）** - 让读者无法划走
2. **多用短句** - 节奏明快，易于阅读
3. **加入情绪价值** - 让读者产生情感共鸣

## 钩子公式（选择最适合的一种）
- **反差型**: "你以为...其实..."
- **数字型**: "X 天/Y 个方法/Z 倍效果"
- **悬念型**: "我发现了...的秘密"
- **痛点型**: "你是不是也..."
- **权威型**: "XX 专家不会告诉你的..."
- **结果型**: "从...到...我只用了..."

## 写作风格
- 句子长度：80% 的句子不超过 15 字
- 段落结构：多分段，每段 1-3 句
- 语气：{tone}
- 情绪：根据内容注入（焦虑/希望/爽感/共鸣）

# 输入信息
## 选定的切入点
- 标题方向：{angle.headline}
- 目标人群：{angle.target_audience}
- 情绪触发：{angle.emotion_trigger}
- 核心价值：{angle.core_value}

## 用户痛点
{research.pain_points}

## 爆款参考
{research.viral_examples}

# 内容结构

### 开场 (Hook)
- 1-2 句话抓住注意力
- 制造好奇/痛点/反差

### 主体 (Value)
- 分点阐述核心价值
- 每点都有具体例子/数据
- 用"你"直接对话读者

### 收尾 (CTA)
- 总结核心观点
- 给出明确行动建议
- 或引发思考/讨论

# 输出格式（JSON）
{{
    "content_type": "社交媒体文案",
    "headline": "标题",
    "body": "文案正文",
    "hook_type": "反差型",
    "emotion_trigger": "好奇",
    "target_audience": "...",
    "image_suggestions": ["配图建议 1", "配图建议 2"]
}}
"""
```

### 2.5 处理流程

```
Research Report + Selected Angle → [Hook Selection] → [Outline Generation] → [Draft Writing] → [Style Adjustment] → Output
                                        ↓                    ↓                    ↓                    ↓
                                   钩子类型              文案大纲              初稿                风格调整
```

---

## 3. 审核 Agent (ReviewerAgent)

### 3.1 职责定义

**核心职责**：资深内容主编，10 年经验，眼光毒辣，给出具体修改建议。

**具体任务**：
- 6 维度评分审核文案
- 识别必须修改的问题
- 给出具体修改建议
- 做出审核结论

### 3.2 输入接口

```python
class ReviewerInput(BaseModel):
    draft: str                         # 文案初稿（必填）
    platform: str                      # 目标平台（必填）
    brand_guidelines: BrandGuidelines  # 品牌规范（可选）
    creator_metadata: dict             # 创作元数据（可选）
```

### 3.3 输出接口

```python
class ReviewerOutput(BaseModel):
    overall_score: int                 # 合格项数 /6
    dimension_scores: List[DimensionScore]  # 各维度得分
    highlights: List[str]              # 亮点列表
    must_fix_issues: List[Issue]       # 必须修改的问题
    suggested_improvements: List[str]  # 建议优化项
    risk_keywords: List[RiskKeyword]   # 敏感词/风险点
    conclusion: str                    # 审核结论：pass/modify/rewrite
    revision_priority: List[PriorityItem]  # 修改优先级

class DimensionScore(BaseModel):
    dimension: str          # 维度名称
    score: int              # 得分 1-5
    comment: str            # 一句话简评

class Issue(BaseModel):
    problem: str            # 问题描述
    location: str           # 位置
    suggestion: str         # 修改建议
    severity: str           # 严重程度：high/medium/low

class RiskKeyword(BaseModel):
    keyword: str            # 具体词句
    risk_type: str          # 风险类型：夸大/敏感/违规
    suggestion: str         # 替代建议
```

### 3.4 Prompt 模板

```python
REVIEWER_AGENT_PROMPT = """
# 角色
你是资深内容主编，有 10 年内容审核经验。
你的眼光毒辣，一眼就能看出文案的问题，并给出具体修改建议。

# 任务
审核文案初稿，从以下维度进行检查并给出修改建议：

## 审核维度

### 1. 钩子强度 (Hook Strength)
- 第一句话能否在 3 秒内抓住注意力？
- 是否制造了足够的好奇/痛点/反差？
- 评分：1-5 分

### 2. 情绪价值 (Emotional Value)
- 是否能引发读者情绪波动？
- 情绪类型是否匹配内容目标？
- 评分：1-5 分

### 3. 信息密度 (Information Density)
- 是否有足够干货/价值？
- 有没有废话和空洞表述？
- 评分：1-5 分

### 4. 可读性 (Readability)
- 句子是否简短有力？
- 段落划分是否合理？
- 评分：1-5 分

### 5. 平台适配 (Platform Fit)
- 是否符合目标平台的调性？
- 格式是否适合该平台用户习惯？
- 评分：1-5 分

### 6. 合规检查 (Compliance)
- 是否有夸大/虚假宣传风险？
- 是否涉及敏感话题？
- 是否违反平台规则？
- 评分：1-5 分

# 输入信息
- 文案类型：{content_type}
- 目标平台：{platform}
- 文案正文：{draft}

# 输出格式（JSON）
{{
    "overall_score": 5,
    "dimension_scores": [
        {{"dimension": "钩子强度", "score": 4, "comment": "第一句话有吸引力"}}
    ],
    "highlights": ["亮点 1", "亮点 2"],
    "must_fix_issues": [
        {{"problem": "问题描述", "location": "第 2 段", "suggestion": "修改建议", "severity": "high"}}
    ],
    "suggested_improvements": ["优化建议 1", "优化建议 2"],
    "risk_keywords": [
        {{"keyword": "具体词句", "risk_type": "夸大", "suggestion": "替代建议"}}
    ],
    "conclusion": "modify"  // pass/modify/rewrite
}}
"""
```

### 3.5 处理流程

```
Draft → [Hook Analysis] → [Emotion Analysis] → [Density Check] → [Readability Check] → [Platform Fit] → [Compliance Check] → Report
           ↓                   ↓                    ↓                  ↓                   ↓                  ↓
       钩子评分            情绪评分            密度评分           可读性评分          适配评分           合规评分
```

---

## 4. 优化 Agent (OptimizerAgent)

### 4.1 职责定义

**核心职责**：金牌文案编辑，在保留原文风格基础上进行润色提升。

**具体任务**：
- 根据审核意见优先级修复问题
- 强化文案优势（钩子、情绪）
- 精细打磨节奏和措辞

### 4.2 输入接口

```python
class OptimizerInput(BaseModel):
    original_draft: str                # 原文案（必填）
    review_report: ReviewerOutput      # 审核报告（必填）
    priority: str                      # 优化优先级：quick/standard/deep（必填）
    preserve_elements: List[str]       # 需要保留的元素（可选）
```

### 4.3 输出接口

```python
class OptimizerOutput(BaseModel):
    optimized_content: str             # 优化后文案
    changes: List[ChangeRecord]        # 修改记录
    summary: str                       # 优化总结
    self_score: SelfScore              # 自测评分

class ChangeRecord(BaseModel):
    location: str          # 修改位置
    original: str          # 原文
    revised: str           # 修改后
    reason: str            # 修改原因
    category: str          # 修改类别：fix/enhance/polish

class SelfScore(BaseModel):
    before: dict           # 优化前各维度得分
    after: dict            # 优化后各维度得分
    improvement: dict      # 提升幅度
```

### 4.4 Prompt 模板

```python
OPTIMIZER_AGENT_PROMPT = """
# 角色
你是金牌文案编辑，擅长在保留原文风格的基础上进行润色提升。
你的修改能让文案更精炼、更有力、更有感染力。

# 任务
根据审核意见对文案进行优化，在保持原有风格和核心信息的前提下提升质量。

## 优化原则

### 优先级 1: 修复问题
- 处理审核报告中"必须修改的问题"
- 解决合规风险
- 修复逻辑漏洞

### 优先级 2: 强化优势
- 让钩子更抓人
- 让情绪更强烈
- 让价值更明显

### 优先级 3: 精细打磨
- 删掉多余的字词
- 让句子更有节奏
- 让表达更精准

## 优化技巧

### 钩子优化
- 增加反差/悬念/冲突
- 用具体数字替代模糊表述
- 把痛点说得更扎心

### 情绪优化
- 加入更多感官细节
- 用对比制造情绪波动
- 适当暴露脆弱增加真诚

### 节奏优化
- 长短句搭配
- 关键信息单独成段
- 重要内容适当重复

### 信任优化
- 加入具体案例/数据
- 用"我"代替"你"增加真实感
- 承认局限性增加可信度

# 输入信息
- 原文案：{original_draft}
- 审核结论：{review_report.conclusion}
- 必须修改的问题：{review_report.must_fix_issues}
- 优化优先级：{priority}

# 输出格式（JSON）
{{
    "optimized_content": "优化后的完整文案",
    "changes": [
        {{"location": "第 1 段", "original": "原文", "revised": "新文案", "reason": "增强钩子", "category": "enhance"}}
    ],
    "summary": "共修改 X 处，主要改进...",
    "self_score": {{
        "before": {{"钩子强度": 3, "情绪价值": 4}},
        "after": {{"钩子强度": 5, "情绪价值": 5}},
        "improvement": {{"钩子强度": "+2", "情绪价值": "+1"}}
    }}
}}
"""
```

### 4.5 处理流程

```
Original Draft + Review Report → [Priority Sorting] → [Issue Fixing] → [Enhancement] → [Polishing] → [Self-Evaluation] → Output
                                      ↓                    ↓               ↓              ↓               ↓
                                 问题优先级           修复问题         强化优势        精细打磨        自测评分
```

---

## 5. 配图 Agent (ImageAgent)

### 5.1 职责定义

**核心职责**：视觉创意总监，为文案内容生成 Midjourney 提示词和排版建议。

**具体任务**：
- 分析文案内容和情绪基调
- 生成 3 组不同风格的 Midjourney 提示词
- 提供图文排版建议
- 输出配色方案和字体推荐

### 5.2 输入接口

```python
class ImageInput(BaseModel):
    content: str                       # 文案内容（必填）
    platform: str                      # 发布平台：wechat/xiaohongshu/blog（必填）
    emotion: str                       # 情绪基调：warm/cool/energetic/calm（必填）
    brand_colors: List[str]            # 品牌色（可选）
    product_images: List[str]          # 产品图链接（可选）
    style_preference: str              # 风格偏好：minimalist/vibrant/elegant（可选）
```

### 5.3 输出接口

```python
class ImageOutput(BaseModel):
    mj_prompts: List[MJPrompt]         # Midjourney 提示词（3 组）
    layout_suggestions: LayoutAdvice   # 排版建议
    color_palette: ColorPalette        # 配色方案
    font_recommendations: List[str]    # 字体推荐
    rationale: str                     # 设计理念说明

class MJPrompt(BaseModel):
    style: str             # 风格名称
    prompt_en: str         # 英文提示词（Midjourney 使用）
    prompt_cn: str         # 中文说明
    negative_prompt: str   # 负向提示词
    params: dict           # 参数设置（--ar, --v, --stylize 等）
    mood: str              # 传达的情绪
    use_case: str          # 适用场景

class LayoutAdvice(BaseModel):
    composition: str           # 构图方式：center/rule-of-thirds/diagonal
    text_position: str         # 文字位置：top/bottom/center/overlay
    image_text_ratio: str      # 图文字比例
    visual_hierarchy: List[str]  # 视觉层级（从上到下）
    whitespace_advice: str     # 留白建议
    platform_specific: dict    # 平台特定建议

class ColorPalette(BaseModel):
    primary: str           # 主色（HEX）
    secondary: str         # 辅色（HEX）
    accent: str            # 强调色（HEX）
    background: str        # 背景色（HEX）
    text: str              # 文字色（HEX）
    mood_description: str  # 色彩情绪说明
```

### 5.4 Prompt 模板

```python
IMAGE_AGENT_PROMPT = """
# 角色
你是视觉创意总监，有 8 年新媒体视觉设计经验。
你擅长为文案内容匹配视觉元素，懂得如何用图像增强文案感染力。

# 任务
为给定的文案内容生成 3 组 Midjourney 提示词和排版建议。

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

# 输入信息
- 文案内容：{content}
- 发布平台：{platform}
- 情绪基调：{emotion}
- 品牌色：{brand_colors}
- 风格偏好：{style_preference}

# Midjourney 参数说明
- --ar 16:9 : 横版（适合公众号头图）
- --ar 3:4  : 竖版（适合小红书封面）
- --ar 1:1  : 正方形（适合配图插图）
- --v 5.2   : 使用版本 5.2
- --stylize 250 : 艺术化程度（0-1000）

# 输出格式（JSON）
{{
    "mj_prompts": [
        {{
            "style": "极简风",
            "prompt_en": "minimalist product photography, clean background, soft lighting, professional --ar 3:4 --v 5.2",
            "prompt_cn": "极简产品摄影，干净背景，柔和光线，专业质感",
            "negative_prompt": "cluttered, noisy, oversaturated, amateur",
            "params": {{"--ar": "3:4", "--v": "5.2", "--stylize": 250}},
            "mood": "专业、高端",
            "use_case": "小红书封面"
        }}
    ],
    "layout_suggestions": {{
        "composition": "rule-of-thirds",
        "text_position": "bottom",
        "image_text_ratio": "70:30",
        "visual_hierarchy": ["主图", "标题", "副标题", "CTA"],
        "whitespace_advice": "顶部留白 20%，便于添加标题",
        "platform_specific": {{"xiaohongshu": "竖版 3:4，文字不超过画面 30%"}}
    }},
    "color_palette": {{
        "primary": "#1565C0",
        "secondary": "#42A5F5",
        "accent": "#FF7043",
        "background": "#F5F5F5",
        "text": "#212121",
        "mood_description": "蓝色系传递专业信任感，橙色强调行动"
    }},
    "font_recommendations": ["思源黑体 Medium", "苹方 Regular"],
    "rationale": "设计理念说明..."
}}
"""
```

### 5.5 Midjourney 提示词公式库

```python
MJ_PROMPT_FORMULAS = {
    "产品摄影": "{product} photography, {lighting} lighting, {background} background, {style} --ar {ar} --v 5.2",
    "场景图": "{scene} with {subject}, {mood} atmosphere, {style} style, {color_palette} --ar {ar}",
    "插画风": "{subject} illustration, {art_style}, {color_scheme}, {mood} --niji 5",
    "人物图": "{person_type} {action}, {setting}, {emotion} expression, {lighting} --ar {ar}",
    "抽象概念": "abstract representation of {concept}, {style}, {colors}, {mood} --ar {ar}"
}

# 风格关键词库
STYLE_KEYWORDS = {
    "极简": "minimalist, clean, simple, elegant",
    "活力": "vibrant, energetic, bold, dynamic",
    "温暖": "warm, cozy, soft, inviting",
    "专业": "professional, corporate, sleek, modern",
    "梦幻": "dreamy, ethereal, magical, soft focus",
    "复古": "vintage, retro, nostalgic, film grain"
}
```

### 5.6 处理流程

```
Content + Emotion → [Style Analysis] → [Prompt Generation] → [Layout Design] → [Color Selection] → Output
                         ↓                    ↓                    ↓                  ↓
                    风格定位            3 组 MJ 提示词         排版建议          配色方案
```

### 5.7 平台适配规则

```python
PLATFORM_SPECS = {
    "wechat": {
        "cover_ratio": "16:9",
        "inline_ratio": "3:4",
        "text_limit": "标题不超过 20 字",
        "style": "大气、专业"
    },
    "xiaohongshu": {
        "cover_ratio": "3:4",
        "inline_ratio": "1:1",
        "text_limit": "封面文字不超过 30%",
        "style": "清新、生活化"
    },
    "blog": {
        "cover_ratio": "16:9",
        "inline_ratio": "16:9",
        "text_limit": "灵活",
        "style": "与文章调性一致"
    }
}
```

---

## 6. Agent 间通信协议

### 5.1 数据传递格式

所有 Agent 间的数据传递采用统一的信封模式：

```python
class AgentEnvelope(BaseModel):
    """Agent 间传递的数据信封"""
    version: str                       # 协议版本
    source_agent: str                  # 源 Agent
    target_agent: str                  # 目标 Agent
    payload: dict                      # 实际数据
    metadata: dict                     # 元数据（timestamp, trace_id 等）
    context: dict                      # 上下文信息（累积传递）
```

### 5.2 上下文保持机制

```python
class WorkflowContext(BaseModel):
    """工作流上下文，在 Agent 间累积传递"""
    workflow_id: str                   # 工作流实例 ID
    user_input: dict                   # 用户原始输入
    agent_outputs: dict                # 各 Agent 输出（累积）
    decisions: dict                    # 用户决策记录
    constraints: dict                  # 约束条件

# 上下文传递链（含配图 Agent）
Context = UserInput
        → Context + ResearchOutput
        → Context + CreatorOutput
        → Context + ReviewerOutput
        → Context + OptimizerOutput
        → Context + ImageOutput  # 配图 Agent 最后执行
```

### 完整工作流

```
                    用户输入
                      │
                      ▼
        ┌─────────────────────────┐
        │     调研 Agent           │
        │   (Research Agent)      │
        └─────────────────────────┘
                      │
                      ▼ 调研报告
        ┌─────────────────────────┐
        │     创作 Agent           │
        │   (Creator Agent)       │
        └─────────────────────────┘
                      │
                      ▼ 文案初稿
         ┌────────────┴────────────┐
         │                         │
         ▼                         ▼
┌─────────────────┐      ┌─────────────────┐
│   审核 Agent     │      │                 │
│ (Reviewer Agent)│      │                 │
└─────────────────┘      │                 │
         │               │                 │
         ▼ 审核意见       │                 │
┌─────────────────┐      │                 │
│   优化 Agent     │      │                 │
│ (Optimizer Agent)│     │                 │
└─────────────────┘      │                 │
         │               │                 │
         ▼ 最终文案       │                 │
         └───────┬───────┘                 │
                 │                         │
                 ▼                         ▼
        ┌─────────────────────────┐
        │     配图 Agent           │
        │    (Image Agent)        │
        │  (并行执行，基于文案内容)  │
        └─────────────────────────┘
                      │
                      ▼ MJ 提示词 + 排版建议
                 ┌────────┐
                 │ 输出层 │
                 │ 最终包 │
                 └────────┘
```

### 5.3 接口规范

```python
class Agent(ABC):
    """Agent 基类"""

    @abstractmethod
    def process(self, envelope: AgentEnvelope) -> AgentEnvelope:
        """处理输入信封，返回输出信封"""
        pass

    @abstractmethod
    def validate_input(self, payload: dict) -> bool:
        """验证输入格式"""
        pass

    @abstractmethod
    def get_output_schema(self) -> dict:
        """返回输出 Schema"""
        pass
```

---

## 6. Prompt 模板系统

### 6.1 模板结构

```python
class PromptTemplate(BaseModel):
    """Prompt 模板基类"""
    name: str                          # 模板名称
    version: str                       # 版本
    system_prompt: str                 # System Prompt
    user_prompt: str                   # User Prompt 模板
    variables: List[str]               # 变量列表
    output_schema: dict                # 输出 JSON Schema
    examples: List[dict]               # Few-shot 示例
```

### 6.2 变量替换引擎

```python
class PromptEngine:
    """Prompt 引擎"""

    def __init__(self, template: PromptTemplate):
        self.template = template
        self.jinja_env = jinja2.Environment()

    def render(self, variables: dict) -> str:
        """渲染 Prompt"""
        template = self.jinja_env.from_string(self.template.user_prompt)
        return template.render(**variables)

    def with_few_shot(self, examples: List[dict]) -> str:
        """添加 Few-shot 示例"""
        pass
```

### 6.3 配置示例

```python
# config/agent_prompts.yaml
research_agent:
  model: "claude-sonnet-4-6"
  temperature: 0.7
  max_tokens: 2000
  system_prompt: "prompts/research_system.md"
  user_prompt: "prompts/research_user.md"

creator_agent:
  model: "claude-sonnet-4-6"
  temperature: 0.8
  max_tokens: 1500
  system_prompt: "prompts/creator_system.md"
  user_prompt: "prompts/creator_user.md"

reviewer_agent:
  model: "claude-sonnet-4-6"
  temperature: 0.3
  max_tokens: 1000
  system_prompt: "prompts/reviewer_system.md"
  user_prompt: "prompts/reviewer_user.md"

optimizer_agent:
  model: "claude-sonnet-4-6"
  temperature: 0.5
  max_tokens: 1500
  system_prompt: "prompts/optimizer_system.md"
  user_prompt: "prompts/optimizer_user.md"

image_agent:
  model: "claude-sonnet-4-6"
  temperature: 0.7
  max_tokens: 2000
  system_prompt: "prompts/image_system.md"
  user_prompt: "prompts/image_user.md"
```

---

## 7. 错误处理与重试

### 7.1 错误类型

```python
class AgentError(Exception):
    """Agent 错误基类"""
    pass

class ValidationError(AgentError):
    """输入/输出验证失败"""
    pass

class LLMError(AgentError):
    """LLM 调用失败"""
    pass

class TimeoutError(AgentError):
    """超时错误"""
    pass
```

### 7.2 重试策略

```python
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(LLMError)
)
async def call_llm_with_retry(prompt: str, config: dict):
    """带重试的 LLM 调用"""
    pass
```

---

## 验收标准

- [ ] 4 个 Agent 的职责和接口定义清晰
- [ ] 每个 Agent 有完整的 Prompt 模板
- [ ] 输入输出 Schema 定义完整
- [ ] Agent 间通信协议明确
- [ ] Prompt 模板系统可配置
- [ ] 错误处理机制完善
