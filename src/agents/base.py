"""
Agent 基类
定义所有 Agent 的抽象接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class AgentEnvelope(BaseModel):
    """
    Agent 间传递的数据信封
    采用信封模式封装数据，支持上下文累积传递
    """
    version: str = Field(default="1.0", description="协议版本")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="信封 ID")
    source_agent: Optional[str] = Field(default=None, description="源 Agent")
    target_agent: Optional[str] = Field(default=None, description="目标 Agent")
    payload: Dict[str, Any] = Field(default_factory=dict, description="实际数据")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")

    class Config:
        arbitrary_types_allowed = True

    def add_metadata(self, key: str, value: Any) -> "AgentEnvelope":
        """添加元数据"""
        self.metadata[key] = value
        return self

    def add_to_context(self, key: str, value: Any) -> "AgentEnvelope":
        """添加到上下文"""
        self.context[key] = value
        return self

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.context.get(key, default)


class WorkflowContext(BaseModel):
    """
    工作流上下文
    在 Agent 间累积传递，保持状态
    """
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_input: Dict[str, Any] = Field(default_factory=dict)
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    decisions: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def add_agent_output(self, agent_name: str, output: Any) -> "WorkflowContext":
        """添加 Agent 输出"""
        self.agent_outputs[agent_name] = output
        self.updated_at = datetime.now()
        return self

    def get_agent_output(self, agent_name: str) -> Optional[Any]:
        """获取 Agent 输出"""
        return self.agent_outputs.get(agent_name)

    def add_decision(self, key: str, value: Any) -> "WorkflowContext":
        """添加决策记录"""
        self.decisions[key] = value
        self.updated_at = datetime.now()
        return self


class Agent(ABC):
    """
    Agent 抽象基类
    所有 Agent 必须继承此类并实现抽象方法
    """

    name: str = "base_agent"
    description: str = "基础 Agent"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 Agent

        Args:
            config: 配置字典，包含 model、temperature 等参数
        """
        self.config = config or {}
        self._initialized = False

    @abstractmethod
    def process(self, envelope: AgentEnvelope) -> AgentEnvelope:
        """
        处理输入信封，返回输出信封

        Args:
            envelope: 输入信封

        Returns:
            输出信封
        """
        pass

    @abstractmethod
    def validate_input(self, payload: Dict[str, Any]) -> bool:
        """
        验证输入格式

        Args:
            payload: 输入数据

        Returns:
            是否有效
        """
        pass

    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """
        返回输入 Schema

        Returns:
            JSON Schema
        """
        pass

    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """
        返回输出 Schema

        Returns:
            JSON Schema
        """
        pass

    def initialize(self) -> bool:
        """
        初始化 Agent 资源

        Returns:
            是否成功初始化
        """
        self._initialized = True
        return True

    def cleanup(self) -> None:
        """清理资源"""
        self._initialized = False

    def _create_output_envelope(
        self,
        input_envelope: AgentEnvelope,
        payload: Dict[str, Any]
    ) -> AgentEnvelope:
        """
        创建输出信封

        Args:
            input_envelope: 输入信封
            payload: 输出数据

        Returns:
            输出信封
        """
        return AgentEnvelope(
            version=input_envelope.version,
            source_agent=self.name,
            target_agent=None,
            payload=payload,
            metadata={
                "parent_id": input_envelope.id,
                "timestamp": datetime.now().isoformat()
            },
            context=input_envelope.context.copy()
        )

    def _validate_payload(self, payload: Dict[str, Any], required_fields: list) -> tuple[bool, list]:
        """
        验证 payload 是否包含必需字段

        Args:
            payload: 输入数据
            required_fields: 必需字段列表

        Returns:
            (是否有效，缺失字段列表)
        """
        missing = [f for f in required_fields if f not in payload]
        return len(missing) == 0, missing
