"""
调研 Agent (ResearchAgent)
负责分析主题、挖掘热点、拆解爆款逻辑
"""

import json
from typing import Dict, Any, Optional
from .base import Agent, AgentEnvelope
from .prompts.research import SYSTEM_PROMPT, USER_PROMPT, FEW_SHOT_EXAMPLES
from src.utils.llm_client import create_llm_client, call_llm_sync, parse_json_response
from src.utils.prompt_engine import PromptEngine, PromptTemplate
from src.utils.config import get_model_config


class ResearchAgent(Agent):
    """
    调研 Agent
    内容选题专家，分析热点趋势、用户痛点和爆款逻辑
    """

    name = "research_agent"
    description = "内容选题专家，分析热点趋势、用户痛点和爆款逻辑"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化调研 Agent

        Args:
            config: 配置字典
        """
        # 获取默认配置
        default_config = get_model_config("research")
        merged_config = {**default_config, **(config or {})}

        super().__init__(merged_config)

        # 初始化 LLM 客户端
        self.llm_client = None

        # 初始化 Prompt 引擎
        self.prompt_engine = PromptEngine(
            PromptTemplate(
                name="research_agent",
                system_prompt=SYSTEM_PROMPT,
                user_prompt=USER_PROMPT,
                variables=["topic", "target_audience", "platform", "brand_keywords"],
                examples=FEW_SHOT_EXAMPLES
            )
        )

    def initialize(self) -> bool:
        """初始化 LLM 客户端"""
        try:
            self.llm_client = create_llm_client(
                model=self.config.get("model", "qwen-plus"),
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens", 2000)
            )
            self._initialized = True
            return True
        except Exception as e:
            print(f"初始化 ResearchAgent 失败：{e}")
            return False

    def validate_input(self, payload: Dict[str, Any]) -> bool:
        """验证输入"""
        valid, missing = self._validate_payload(
            payload,
            required_fields=["topic", "target_audience", "platform"]
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
                "topic": {"type": "string", "description": "内容主题"},
                "target_audience": {"type": "string", "description": "目标受众"},
                "platform": {"type": "string", "description": "发布平台"},
                "brand_keywords": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["topic", "target_audience", "platform"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """返回输出 Schema"""
        return {
            "type": "object",
            "properties": {
                "trend_analysis": {"type": "string"},
                "pain_points": {"type": "array"},
                "viral_examples": {"type": "array"},
                "angles": {"type": "array"}
            }
        }

    def process(self, envelope: AgentEnvelope) -> AgentEnvelope:
        """
        处理调研请求

        Args:
            envelope: 输入信封

        Returns:
            输出信封
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("ResearchAgent 未初始化")

        # 验证输入
        if not self.validate_input(envelope.payload):
            raise ValueError("输入验证失败")

        # 提取输入参数
        topic = envelope.payload.get("topic")
        target_audience = envelope.payload.get("target_audience")
        platform = envelope.payload.get("platform")
        brand_keywords = envelope.payload.get("brand_keywords", [])

        # 渲染 Prompt
        system_prompt, user_prompt = self.prompt_engine.render(
            {
                "topic": topic,
                "target_audience": target_audience,
                "platform": platform,
                "brand_keywords": brand_keywords if brand_keywords else "无"
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
            # 如果解析失败，尝试让模型重新输出
            retry_prompt = f"请将以下内容解析为 JSON 格式：\n\n{response}"
            response = call_llm_sync(self.llm_client, system_prompt, retry_prompt)
            result = parse_json_response(response)

        # 创建输出信封
        output_envelope = self._create_output_envelope(envelope, result)

        # 添加到上下文
        output_envelope.add_to_context("research_output", result)

        return output_envelope
