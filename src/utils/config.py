"""
配置加载工具
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径，默认使用 config/settings.yaml

    Returns:
        配置字典
    """
    if config_path is None:
        # 默认配置文件路径
        base_dir = Path(__file__).parent.parent.parent
        config_path = base_dir / "config" / "settings.yaml"

    if not os.path.exists(config_path):
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_model_config(
    agent_name: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    获取指定 Agent 的模型配置

    Args:
        agent_name: Agent 名称
        config: 配置字典，默认从文件加载

    Returns:
        模型配置字典
    """
    if config is None:
        config = load_config()

    models = config.get("models", {})
    default = models.get("default", {})

    # 获取特定 Agent 配置
    agent_config = models.get(agent_name, {})

    # 合并配置（Agent 特定配置覆盖默认配置）
    merged = {**default, **agent_config}

    # 从环境变量覆盖配置
    if os.getenv("DEFAULT_MODEL"):
        merged["model"] = os.getenv("DEFAULT_MODEL")
    if os.getenv("TEMPERATURE"):
        merged["temperature"] = float(os.getenv("TEMPERATURE"))
    if os.getenv("MAX_TOKENS"):
        merged["max_tokens"] = int(os.getenv("MAX_TOKENS"))

    return merged


def get_platform_config(
    platform: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    获取平台配置

    Args:
        platform: 平台名称
        config: 配置字典

    Returns:
        平台配置字典
    """
    if config is None:
        config = load_config()

    platforms = config.get("platforms", {})
    return platforms.get(platform, {})
