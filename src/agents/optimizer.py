"""
优化 Agent (OptimizerAgent)
根据审核意见优化文案
"""

import json
from typing import Dict, Any, Optional
from .base import Agent, AgentEnvelope
from .prompts.optimizer import SYSTEM_PROMPT, USER_PROMPT, FEW_SHOT_EXAMPLES
from src.utils.llm_client import create_llm_client, call_llm_sync, parse_json_response
from src.utils.prompt_engine import PromptEngine, PromptTemplate
from src.utils.config import get_model_config


class OptimizerAgent(Agent):
    """
    优化 Agent
    金牌文案编辑，在保留原文风格基础上进行润色提升
    """

    name = "optimizer_agent"
    description = "金牌文案编辑，在保留原文风格基础上进行润色提升"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化优化 Agent

        Args:
            config: 配置字典
        """
        # 获取默认配置
        default_config = get_model_config("optimizer")
        merged_config = {**default_config, **(config or {})}

        super().__init__(merged_config)

        # 初始化 LLM 客户端
        self.llm_client = None

        # 初始化 Prompt 引擎
        self.prompt_engine = PromptEngine(
            PromptTemplate(
                name="optimizer_agent",
                system_prompt=SYSTEM_PROMPT,
                user_prompt=USER_PROMPT,
                variables=["original_draft", "review_conclusion", "must_fix_issues", "priority"],
                examples=FEW_SHOT_EXAMPLES
            )
        )

    def initialize(self) -> bool:
        """初始化 LLM 客户端"""
        try:
            self.llm_client = create_llm_client(
                model=self.config.get("model", "qwen-plus"),
                temperature=self.config.get("temperature", 0.5),
                max_tokens=self.config.get("max_tokens", 2000)
            )
            self._initialized = True
            return True
        except Exception as e:
            print(f"初始化 OptimizerAgent 失败：{e}")
            return False

    def validate_input(self, payload: Dict[str, Any]) -> bool:
        """验证输入"""
        valid, missing = self._validate_payload(
            payload,
            required_fields=["original_draft", "review_report", "priority"]
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
                "original_draft": {"type": "string", "description": "原文案"},
                "review_report": {"type": "object", "description": "审核报告"},
                "priority": {"type": "string", "description": "优化优先级：quick/standard/deep"},
            },
            "required": ["original_draft", "review_report", "priority"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """返回输出 Schema"""
        return {
            "type": "object",
            "properties": {
                "optimized_content": {"type": "string"},
                "changes": {"type": "array"},
                "summary": {"type": "string"},
                "self_score": {"type": "object"}
            }
        }

    def process(self, envelope: AgentEnvelope) -> AgentEnvelope:
        """
        处理优化请求

        Args:
            envelope: 输入信封

        Returns:
            输出信封
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("OptimizerAgent 未初始化")

        # 验证输入
        if not self.validate_input(envelope.payload):
            raise ValueError("输入验证失败")

        # 提取输入参数
        original_draft = envelope.payload.get("original_draft", "")
        review_report = envelope.payload.get("review_report", {})
        priority = envelope.payload.get("priority", "standard")

        # 从审核报告中提取必要信息
        review_conclusion = review_report.get("conclusion", "modify")
        must_fix_issues = review_report.get("must_fix_issues", [])

        # 渲染 Prompt
        system_prompt, user_prompt = self.prompt_engine.render(
            {
                "original_draft": original_draft,
                "review_conclusion": review_conclusion,
                "must_fix_issues": must_fix_issues,
                "priority": priority
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
        output_envelope.add_to_context("optimizer_output", result)

        return output_envelope
