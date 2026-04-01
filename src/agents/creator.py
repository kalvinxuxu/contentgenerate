"""
创作 Agent (CreatorAgent)
基于调研报告撰写高传播文案
"""

import json
from typing import Dict, Any, Optional
from .base import Agent, AgentEnvelope
from .prompts.creator import SYSTEM_PROMPT, USER_PROMPT, FEW_SHOT_EXAMPLES
from src.utils.llm_client import create_llm_client, call_llm_sync, parse_json_response
from src.utils.prompt_engine import PromptEngine, PromptTemplate
from src.utils.config import get_model_config


class CreatorAgent(Agent):
    """
    创作 Agent
    爆款文案写手，基于调研报告撰写高传播文案
    """

    name = "creator_agent"
    description = "爆款文案写手，基于调研报告撰写高传播文案"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化创作 Agent

        Args:
            config: 配置字典
        """
        # 获取默认配置
        default_config = get_model_config("creator")
        merged_config = {**default_config, **(config or {})}

        super().__init__(merged_config)

        # 初始化 LLM 客户端
        self.llm_client = None

        # 初始化 Prompt 引擎
        self.prompt_engine = PromptEngine(
            PromptTemplate(
                name="creator_agent",
                system_prompt=SYSTEM_PROMPT,
                user_prompt=USER_PROMPT,
                variables=["angle", "pain_points", "viral_examples", "tone"],
                examples=FEW_SHOT_EXAMPLES
            )
        )

    def initialize(self) -> bool:
        """初始化 LLM 客户端"""
        try:
            self.llm_client = create_llm_client(
                model=self.config.get("model", "qwen-plus"),
                temperature=self.config.get("temperature", 0.8),
                max_tokens=self.config.get("max_tokens", 1500)
            )
            self._initialized = True
            return True
        except Exception as e:
            print(f"初始化 CreatorAgent 失败：{e}")
            return False

    def validate_input(self, payload: Dict[str, Any]) -> bool:
        """验证输入"""
        valid, missing = self._validate_payload(
            payload,
            required_fields=["research_report", "selected_angle", "tone"]
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
                "research_report": {"type": "object", "description": "调研报告"},
                "selected_angle": {"type": "object", "description": "选定的切入点"},
                "tone": {"type": "string", "description": "语气风格"},
                "length": {"type": "string", "description": "文案长度"},
                "platform": {"type": "string", "description": "发布平台"},
            },
            "required": ["research_report", "selected_angle", "tone"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """返回输出 Schema"""
        return {
            "type": "object",
            "properties": {
                "content_type": {"type": "string"},
                "headline": {"type": "string"},
                "body": {"type": "string"},
                "hook_type": {"type": "string"},
                "emotion_trigger": {"type": "string"},
                "image_suggestions": {"type": "array"},
                "metadata": {"type": "object"}
            }
        }

    def process(self, envelope: AgentEnvelope) -> AgentEnvelope:
        """
        处理创作请求

        Args:
            envelope: 输入信封

        Returns:
            输出信封
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("CreatorAgent 未初始化")

        # 验证输入
        if not self.validate_input(envelope.payload):
            raise ValueError("输入验证失败")

        # 提取输入参数
        research_report = envelope.payload.get("research_report", {})
        selected_angle = envelope.payload.get("selected_angle", {})
        tone = envelope.payload.get("tone", "casual")

        # 准备模板变量
        variables = {
            "angle": selected_angle,
            "pain_points": research_report.get("pain_points", []),
            "viral_examples": research_report.get("viral_examples", []),
            "tone": tone
        }

        # 渲染 Prompt
        system_prompt, user_prompt = self.prompt_engine.render(
            variables,
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
        output_envelope.add_to_context("creator_output", result)

        return output_envelope
