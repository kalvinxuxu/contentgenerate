"""
工作流编排器
负责串联所有 Agent，实现完整的文案生成流程
"""

import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.agents.base import Agent, AgentEnvelope
from src.agents.research import ResearchAgent
from src.agents.creator import CreatorAgent
from src.agents.reviewer import ReviewerAgent
from src.agents.optimizer import OptimizerAgent
from src.agents.image import ImageAgent
from src.utils.config import get_model_config


class WorkflowContext:
    """
    工作流上下文
    在 Agent 间累积传递状态
    """

    def __init__(self, workflow_id: str, user_input: Dict[str, Any]):
        self.workflow_id = workflow_id
        self.user_input = user_input
        self.agent_outputs: Dict[str, Any] = {}
        self.decisions: Dict[str, Any] = {}
        self.constraints: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_agent_output(self, agent_name: str, output: Any):
        """添加 Agent 输出"""
        self.agent_outputs[agent_name] = output
        self.updated_at = datetime.now()

    def add_decision(self, decision_key: str, decision: Any):
        """添加用户决策"""
        self.decisions[decision_key] = decision
        self.updated_at = datetime.now()

    def get_full_context(self) -> Dict[str, Any]:
        """获取完整上下文"""
        return {
            "workflow_id": self.workflow_id,
            "user_input": self.user_input,
            "agent_outputs": self.agent_outputs,
            "decisions": self.decisions,
            "constraints": self.constraints
        }


class WorkflowOrchestrator:
    """
    工作流编排器
    负责按顺序调用各 Agent，处理异常和重试
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化工作流编排器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self._initialized = False

        # 初始化各 Agent
        self.research_agent = None
        self.creator_agent = None
        self.reviewer_agent = None
        self.optimizer_agent = None
        self.image_agent = None

    def initialize(self) -> bool:
        """初始化所有 Agent"""
        try:
            # 获取各 Agent 配置
            research_config = get_model_config("research")
            creator_config = get_model_config("creator")
            reviewer_config = get_model_config("reviewer")
            optimizer_config = get_model_config("optimizer")
            image_config = get_model_config("image")

            # 初始化 Agent
            self.research_agent = ResearchAgent(research_config)
            self.creator_agent = CreatorAgent(creator_config)
            self.reviewer_agent = ReviewerAgent(reviewer_config)
            self.optimizer_agent = OptimizerAgent(optimizer_config)
            self.image_agent = ImageAgent(image_config)

            # 初始化各 Agent
            self.research_agent.initialize()
            self.creator_agent.initialize()
            self.reviewer_agent.initialize()
            self.optimizer_agent.initialize()
            self.image_agent.initialize()

            self._initialized = True
            return True
        except Exception as e:
            print(f"初始化工作流编排器失败：{e}")
            return False

    def _create_envelope(
        self,
        source_agent: str,
        target_agent: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AgentEnvelope:
        """创建 Agent 信封"""
        return AgentEnvelope(
            version="1.0",
            source_agent=source_agent,
            target_agent=target_agent,
            payload=payload,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "trace_id": str(uuid.uuid4())
            },
            context=context or {}
        )

    def run(
        self,
        topic: str,
        target_audience: str,
        platform: str,
        tone: str = "casual",
        priority: str = "standard",
        brand_keywords: Optional[List[str]] = None,
        style_preference: str = "minimalist",
        emotion: str = "hopeful"
    ) -> Dict[str, Any]:
        """
        运行完整工作流

        Args:
            topic: 内容主题
            target_audience: 目标受众
            platform: 发布平台
            tone: 语气风格 (casual/formal/passionate)
            priority: 优化优先级 (quick/standard/deep)
            brand_keywords: 品牌关键词
            style_preference: 视觉风格偏好
            emotion: 情绪基调

        Returns:
            完整输出，包含所有 Agent 的结果
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("工作流编排器未初始化")

        # 创建上下文
        workflow_id = str(uuid.uuid4())
        user_input = {
            "topic": topic,
            "target_audience": target_audience,
            "platform": platform,
            "tone": tone,
            "priority": priority,
            "brand_keywords": brand_keywords or [],
            "style_preference": style_preference,
            "emotion": emotion
        }
        context = WorkflowContext(workflow_id, user_input)

        results = {
            "workflow_id": workflow_id,
            "status": "running",
            "steps": []
        }

        try:
            # Step 1: 调研 Agent
            print(f"[{workflow_id[:8]}] 执行调研 Agent...")
            research_result = self._run_research(
                topic=topic,
                target_audience=target_audience,
                platform=platform,
                brand_keywords=brand_keywords or []
            )
            context.add_agent_output("research", research_result)
            results["steps"].append({"name": "research", "status": "completed"})
            print(f"[{workflow_id[:8]}] 调研完成")

            # Step 2: 创作 Agent
            print(f"[{workflow_id[:8]}] 执行创作 Agent...")
            creator_result = self._run_creator(
                research_report=research_result,
                tone=tone
            )
            context.add_agent_output("creator", creator_result)
            results["steps"].append({"name": "creator", "status": "completed"})
            print(f"[{workflow_id[:8]}] 创作完成")

            # Step 3: 审核 Agent
            print(f"[{workflow_id[:8]}] 执行审核 Agent...")
            reviewer_result = self._run_reviewer(
                content_type=creator_result.get("content_type", "社交媒体文案"),
                platform=platform,
                draft=creator_result.get("body", "")
            )
            context.add_agent_output("reviewer", reviewer_result)
            results["steps"].append({"name": "reviewer", "status": "completed"})
            print(f"[{workflow_id[:8]}] 审核完成")

            # Step 4: 优化 Agent（根据审核结论决定是否执行）
            conclusion = reviewer_result.get("conclusion", "pass")
            if conclusion in ["modify", "rewrite"]:
                print(f"[{workflow_id[:8]}] 执行优化 Agent...")
                optimizer_result = self._run_optimizer(
                    original_draft=creator_result.get("body", ""),
                    review_report=reviewer_result,
                    priority=priority
                )
                context.add_agent_output("optimizer", optimizer_result)
                results["steps"].append({"name": "optimizer", "status": "completed"})
                print(f"[{workflow_id[:8]}] 优化完成")
            else:
                print(f"[{workflow_id[:8]}] 审核通过，跳过优化")
                optimizer_result = None
                results["steps"].append({"name": "optimizer", "status": "skipped"})

            # Step 5: 配图 Agent
            print(f"[{workflow_id[:8]}] 执行配图 Agent...")
            # 确定最终文案
            final_content = optimizer_result.get("optimized_content", creator_result.get("body", "")) if optimizer_result else creator_result.get("body", "")
            image_result = self._run_image(
                content=final_content,
                platform=platform,
                emotion=emotion,
                style_preference=style_preference
            )
            context.add_agent_output("image", image_result)
            results["steps"].append({"name": "image", "status": "completed"})
            print(f"[{workflow_id[:8]}] 配图完成")

            # 整合最终结果
            results["status"] = "completed"
            results["final_output"] = {
                "research": research_result,
                "creator": creator_result,
                "reviewer": reviewer_result,
                "optimizer": optimizer_result,
                "image": image_result,
                "final_content": final_content
            }
            results["context"] = context.get_full_context()

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            print(f"[{workflow_id[:8]}] 工作流执行失败：{e}")
            raise

        return results

    def _run_research(
        self,
        topic: str,
        target_audience: str,
        platform: str,
        brand_keywords: List[str]
    ) -> Dict[str, Any]:
        """运行调研 Agent"""
        envelope = self._create_envelope(
            source_agent="user",
            target_agent="research_agent",
            payload={
                "topic": topic,
                "target_audience": target_audience,
                "platform": platform,
                "brand_keywords": brand_keywords
            }
        )
        output = self.research_agent.process(envelope)
        return output.payload

    def _run_creator(
        self,
        research_report: Dict[str, Any],
        tone: str
    ) -> Dict[str, Any]:
        """运行创作 Agent"""
        # 从调研报告中选择一个切入点（这里默认选第一个，实际可由用户选择）
        angles = research_report.get("angles", [])
        selected_angle = angles[0] if angles else {}

        envelope = self._create_envelope(
            source_agent="research_agent",
            target_agent="creator_agent",
            payload={
                "research_report": research_report,
                "selected_angle": selected_angle,
                "tone": tone
            },
            context={"research_output": research_report}
        )
        output = self.creator_agent.process(envelope)
        return output.payload

    def _run_reviewer(
        self,
        content_type: str,
        platform: str,
        draft: str
    ) -> Dict[str, Any]:
        """运行审核 Agent"""
        envelope = self._create_envelope(
            source_agent="creator_agent",
            target_agent="reviewer_agent",
            payload={
                "content_type": content_type,
                "platform": platform,
                "draft": draft
            }
        )
        output = self.reviewer_agent.process(envelope)
        return output.payload

    def _run_optimizer(
        self,
        original_draft: str,
        review_report: Dict[str, Any],
        priority: str
    ) -> Dict[str, Any]:
        """运行优化 Agent"""
        envelope = self._create_envelope(
            source_agent="reviewer_agent",
            target_agent="optimizer_agent",
            payload={
                "original_draft": original_draft,
                "review_report": review_report,
                "priority": priority
            }
        )
        output = self.optimizer_agent.process(envelope)
        return output.payload

    def _run_image(
        self,
        content: str,
        platform: str,
        emotion: str,
        style_preference: str
    ) -> Dict[str, Any]:
        """运行配图 Agent"""
        envelope = self._create_envelope(
            source_agent="optimizer_agent",
            target_agent="image_agent",
            payload={
                "content": content,
                "platform": platform,
                "emotion": emotion,
                "style_preference": style_preference
            }
        )
        output = self.image_agent.process(envelope)
        return output.payload
