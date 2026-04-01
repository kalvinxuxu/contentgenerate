"""
审核 Agent (ReviewerAgent)
负责内容质量审核，6 维评估体系
"""

import json
from typing import Dict, Any, Optional
from .base import Agent, AgentEnvelope
from .prompts.reviewer import SYSTEM_PROMPT, USER_PROMPT, FEW_SHOT_EXAMPLES
from src.utils.llm_client import create_llm_client, call_llm_sync, parse_json_response
from src.utils.prompt_engine import PromptEngine, PromptTemplate
from src.utils.config import get_model_config


class ReviewerAgent(Agent):
    """
    审核 Agent
    资深内容主编，10 年内容审核经验，6 维评估体系
    """

    name = "reviewer_agent"
    description = "资深内容主编，10 年内容审核经验，6 维评估体系"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化审核 Agent

        Args:
            config: 配置字典
        """
        # 获取默认配置
        default_config = get_model_config("reviewer")
        merged_config = {**default_config, **(config or {})}

        super().__init__(merged_config)

        # 初始化 LLM 客户端
        self.llm_client = None

        # 初始化 Prompt 引擎
        self.prompt_engine = PromptEngine(
            PromptTemplate(
                name="reviewer_agent",
                system_prompt=SYSTEM_PROMPT,
                user_prompt=USER_PROMPT,
                variables=["content_type", "platform", "draft"],
                examples=FEW_SHOT_EXAMPLES
            )
        )

    def initialize(self) -> bool:
        """初始化 LLM 客户端"""
        try:
            self.llm_client = create_llm_client(
                model=self.config.get("model", "qwen-plus"),
                temperature=self.config.get("temperature", 0.3),
                max_tokens=self.config.get("max_tokens", 2000)
            )
            self._initialized = True
            return True
        except Exception as e:
            print(f"初始化 ReviewerAgent 失败：{e}")
            return False

    def validate_input(self, payload: Dict[str, Any]) -> bool:
        """验证输入"""
        valid, missing = self._validate_payload(
            payload,
            required_fields=["content_type", "platform", "draft"]
        )
        if not valid:
            print(f"输入验证失败，缺失字段：{missing}")
            return False
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        """返回输入 Schema"""
        return {
            "type": "object",
            "properties": {
                "content_type": {"type": "string", "description": "文案类型"},
                "platform": {"type": "string", "description": "目标平台"},
                "draft": {"type": "string", "description": "文案正文"},
            },
            "required": ["content_type", "platform", "draft"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """返回输出 Schema"""
        return {
            "type": "object",
            "properties": {
                "overall_score": {"type": "integer"},
                "dimension_scores": {"type": "array"},
                "highlights": {"type": "array"},
                "must_fix_issues": {"type": "array"},
                "suggested_improvements": {"type": "array"},
                "risk_keywords": {"type": "array"},
                "conclusion": {"type": "string"}  # pass/modify/rewrite
            }
        }

    def process(self, envelope: AgentEnvelope) -> AgentEnvelope:
        """
        处理审核请求

        Args:
            envelope: 输入信封

        Returns:
            输出信封
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("ReviewerAgent 未初始化")

        # 验证输入
        if not self.validate_input(envelope.payload):
            raise ValueError("输入验证失败")

        # 提取输入参数
        content_type = envelope.payload.get("content_type", "社交媒体文案")
        platform = envelope.payload.get("platform", "小红书")
        draft = envelope.payload.get("draft", "")

        # 渲染 Prompt
        system_prompt, user_prompt = self.prompt_engine.render(
            {
                "content_type": content_type,
                "platform": platform,
                "draft": draft
            },
            include_examples=True
        )

        # 调用 LLM
        response = call_llm_sync(
            self.llm_client,
            system_prompt,
            user_prompt
        )

        # 解析 JSON 响应
        try:
            result = parse_json_response(response)
        except json.JSONDecodeError as e:
            retry_prompt = f"请将以下内容解析为 JSON 格式：\n\n{response}"
            response = call_llm_sync(self.llm_client, system_prompt, retry_prompt)
            result = parse_json_response(response)

        # 创建输出信封
        output_envelope = self._create_output_envelope(envelope, result)

        # 添加到上下文
        output_envelope.add_to_context("reviewer_output", result)

        return output_envelope
