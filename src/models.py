"""
数据模型定义
包含所有 Agent 输入输出的 Pydantic 模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


# ============= 通用模型 =============

class Platform(str, Enum):
    """发布平台枚举"""
    WECHAT = "wechat"
    XIAOHONGSHU = "xiaohongshu"
    BLOG = "blog"


class ContentType(str, Enum):
    """文案类型枚举"""
    SOCIAL_MEDIA = "social_media"
    MARKETING = "marketing"
    PROFESSIONAL = "professional"


class Tone(str, Enum):
    """语气风格枚举"""
    FORMAL = "formal"
    CASUAL = "casual"
    PASSIONATE = "passionate"


class Length(str, Enum):
    """文案长度枚举"""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


# ============= 调研 Agent 模型 =============

class PainPoint(BaseModel):
    """用户痛点"""
    title: str = Field(..., description="痛点标题")
    description: str = Field(..., description="详细描述")
    emotion: str = Field(..., description="情绪类型：焦虑/需求/渴望")
    intensity: int = Field(..., ge=1, le=5, description="强度评分 1-5")


class ViralExample(BaseModel):
    """爆款案例"""
    title: str = Field(..., description="爆款标题")
    platform: str = Field(..., description="发布平台")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="数据指标")
    core_logic: str = Field(..., description="核心逻辑（一句话）")
    reusable_patterns: List[str] = Field(default_factory=list, description="可复用模式")


class ContentAngle(BaseModel):
    """选题切入点"""
    headline: str = Field(..., description="吸引人的标题")
    target_audience: str = Field(..., description="具体受众")
    emotion_trigger: str = Field(..., description="情绪触发")
    core_value: str = Field(..., description="核心价值")
    viral_potential: str = Field(..., description="预期爆点")
    confidence_score: float = Field(..., ge=0, le=1, description="置信度 0-1")


class ResearchInput(BaseModel):
    """调研 Agent 输入"""
    topic: str = Field(..., description="内容主题")
    target_audience: str = Field(..., description="目标受众描述")
    platform: Platform = Field(..., description="发布平台")
    brand_keywords: Optional[List[str]] = Field(default=None, description="品牌关键词")
    competitor_analysis: Optional[str] = Field(default=None, description="竞品分析")


class ResearchOutput(BaseModel):
    """调研 Agent 输出"""
    trend_analysis: str = Field(..., description="热搜趋势分析")
    pain_points: List[PainPoint] = Field(..., description="用户痛点 TOP3")
    viral_examples: List[ViralExample] = Field(..., description="爆款案例拆解")
    angles: List[ContentAngle] = Field(..., description="病毒式选题切入点")
    raw_data: Optional[Dict[str, Any]] = Field(default=None, description="原始数据")


# ============= 创作 Agent 模型 =============

class CreatorInput(BaseModel):
    """创作 Agent 输入"""
    research_report: ResearchOutput = Field(..., description="调研报告")
    selected_angle: ContentAngle = Field(..., description="选定的切入点")
    tone: Tone = Field(..., description="语气风格")
    length: Length = Field(..., description="文案长度")
    platform: Platform = Field(..., description="发布平台")
    brand_guidelines: Optional[Dict[str, Any]] = Field(default=None, description="品牌规范")


class CreatorOutput(BaseModel):
    """创作 Agent 输出"""
    content_type: str = Field(..., description="文案类型")
    headline: Optional[str] = Field(default=None, description="标题")
    body: str = Field(..., description="文案正文")
    hook_type: str = Field(..., description="使用的钩子类型")
    emotion_trigger: str = Field(..., description="情绪触发点")
    target_audience: str = Field(..., description="目标受众")
    image_suggestions: List[str] = Field(default_factory=list, description="配图建议")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


# ============= 审核 Agent 模型 =============

class DimensionScore(BaseModel):
    """维度评分"""
    dimension: str = Field(..., description="维度名称")
    score: int = Field(..., ge=1, le=5, description="得分 1-5")
    comment: str = Field(..., description="一句话简评")


class Issue(BaseModel):
    """问题"""
    problem: str = Field(..., description="问题描述")
    location: str = Field(..., description="位置")
    suggestion: str = Field(..., description="修改建议")
    severity: str = Field(..., description="严重程度")


class RiskKeyword(BaseModel):
    """风险词"""
    keyword: str = Field(..., description="具体词句")
    risk_type: str = Field(..., description="风险类型")
    suggestion: str = Field(..., description="替代建议")


class ReviewerInput(BaseModel):
    """审核 Agent 输入"""
    draft: str = Field(..., description="文案初稿")
    platform: Platform = Field(..., description="目标平台")
    brand_guidelines: Optional[Dict[str, Any]] = Field(default=None, description="品牌规范")


class ReviewerOutput(BaseModel):
    """审核 Agent 输出"""
    overall_score: int = Field(..., ge=0, le=6, description="合格项数")
    dimension_scores: List[DimensionScore] = Field(..., description="各维度得分")
    highlights: List[str] = Field(default_factory=list, description="亮点列表")
    must_fix_issues: List[Issue] = Field(default_factory=list, description="必须修改的问题")
    suggested_improvements: List[str] = Field(default_factory=list, description="建议优化项")
    risk_keywords: List[RiskKeyword] = Field(default_factory=list, description="敏感词/风险点")
    conclusion: str = Field(..., description="审核结论：pass/modify/rewrite")


# ============= 优化 Agent 模型 =============

class ChangeRecord(BaseModel):
    """修改记录"""
    location: str = Field(..., description="修改位置")
    original: str = Field(..., description="原文")
    revised: str = Field(..., description="修改后")
    reason: str = Field(..., description="修改原因")
    category: str = Field(..., description="修改类别")


class SelfScore(BaseModel):
    """自测评分"""
    before: Dict[str, int] = Field(..., description="优化前得分")
    after: Dict[str, int] = Field(..., description="优化后得分")
    improvement: Dict[str, str] = Field(..., description="提升幅度")


class OptimizerInput(BaseModel):
    """优化 Agent 输入"""
    original_draft: str = Field(..., description="原文案")
    review_report: ReviewerOutput = Field(..., description="审核报告")
    priority: str = Field(..., description="优化优先级")
    preserve_elements: Optional[List[str]] = Field(default=None, description="需要保留的元素")


class OptimizerOutput(BaseModel):
    """优化 Agent 输出"""
    optimized_content: str = Field(..., description="优化后文案")
    changes: List[ChangeRecord] = Field(..., description="修改记录")
    summary: str = Field(..., description="优化总结")
    self_score: SelfScore = Field(..., description="自测评分")


# ============= 配图 Agent 模型 =============

class MJPrompt(BaseModel):
    """Midjourney 提示词"""
    style: str = Field(..., description="风格名称")
    prompt_en: str = Field(..., description="英文提示词")
    prompt_cn: str = Field(..., description="中文说明")
    negative_prompt: str = Field(..., description="负向提示词")
    params: Dict[str, Any] = Field(..., description="参数设置")
    mood: str = Field(..., description="传达的情绪")
    use_case: str = Field(..., description="适用场景")


class LayoutAdvice(BaseModel):
    """排版建议"""
    composition: str = Field(..., description="构图方式")
    text_position: str = Field(..., description="文字位置")
    image_text_ratio: str = Field(..., description="图文字比例")
    visual_hierarchy: List[str] = Field(..., description="视觉层级")
    whitespace_advice: str = Field(..., description="留白建议")
    platform_specific: Dict[str, str] = Field(default_factory=dict, description="平台特定建议")


class ColorPalette(BaseModel):
    """配色方案"""
    primary: str = Field(..., description="主色 HEX")
    secondary: str = Field(..., description="辅色 HEX")
    accent: str = Field(..., description="强调色 HEX")
    background: str = Field(..., description="背景色 HEX")
    text: str = Field(..., description="文字色 HEX")
    mood_description: str = Field(..., description="色彩情绪说明")


class ImageInput(BaseModel):
    """配图 Agent 输入"""
    content: str = Field(..., description="文案内容")
    platform: Platform = Field(..., description="发布平台")
    emotion: str = Field(..., description="情绪基调")
    brand_colors: Optional[List[str]] = Field(default=None, description="品牌色")
    style_preference: Optional[str] = Field(default=None, description="风格偏好")


class ImageOutput(BaseModel):
    """配图 Agent 输出"""
    mj_prompts: List[MJPrompt] = Field(..., description="Midjourney 提示词")
    layout_suggestions: LayoutAdvice = Field(..., description="排版建议")
    color_palette: ColorPalette = Field(..., description="配色方案")
    font_recommendations: List[str] = Field(..., description="字体推荐")
    rationale: str = Field(..., description="设计理念说明")


# ============= 输出包裹模型 =============

class WorkflowOutput(BaseModel):
    """工作流最终输出"""
    research: ResearchOutput = Field(..., description="调研报告")
    draft: CreatorOutput = Field(..., description="文案初稿")
    review: ReviewerOutput = Field(..., description="审核报告")
    optimized: OptimizerOutput = Field(..., description="优化后文案")
    image: ImageOutput = Field(..., description="配图建议")
