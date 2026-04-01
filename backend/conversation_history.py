"""
对话历史管理模块

提供多轮对话版本追踪和恢复功能
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime


class ConversationHistory:
    """对话历史管理类"""

    def __init__(self, history_dir: str = None):
        """初始化对话历史

        Args:
            history_dir: 历史存储目录，默认为项目根目录的 results/conversations/
        """
        if history_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            history_dir = os.path.join(base_dir, "results", "conversations")

        self.history_dir = history_dir
        os.makedirs(history_dir, exist_ok=True)

    def _get_file_path(self, task_id: str) -> str:
        """获取任务历史文件路径"""
        return os.path.join(self.history_dir, f"{task_id}.json")

    def add_turn(self, task_id: str, user_feedback: str, new_result: dict, version_index: int = None):
        """添加一轮对话记录

        Args:
            task_id: 任务 ID
            user_feedback: 用户修改意见
            new_result: 新的生成结果
            version_index: 版本号（可选，默认自动分配）

        Returns:
            版本号
        """
        filepath = self._get_file_path(task_id)

        # 加载现有历史
        history = self._load_history(filepath)

        # 确定版本号
        if version_index is None:
            version_index = len(history.get("versions", []))

        # 创建版本记录
        version = {
            "version": version_index,
            "created_at": datetime.now().isoformat(),
            "user_feedback": user_feedback,
            "result": new_result
        }

        # 添加版本
        if "versions" not in history:
            history["versions"] = []

        history["versions"].append(version)
        history["current_version"] = version_index
        history["updated_at"] = datetime.now().isoformat()

        # 保存
        self._save_history(filepath, history)
        return version_index

    def _load_history(self, filepath: str) -> dict:
        """加载历史记录"""
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass

        return {
            "task_id": os.path.basename(filepath).replace(".json", ""),
            "created_at": datetime.now().isoformat(),
            "versions": []
        }

    def _save_history(self, filepath: str, history: dict):
        """保存历史记录"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def get_history(self, task_id: str) -> Optional[dict]:
        """获取完整对话历史

        Args:
            task_id: 任务 ID

        Returns:
            完整历史记录，不存在则返回 None
        """
        filepath = self._get_file_path(task_id)
        if not os.path.exists(filepath):
            return None

        return self._load_history(filepath)

    def get_version(self, task_id: str, version_index: int) -> Optional[dict]:
        """获取指定版本文案

        Args:
            task_id: 任务 ID
            version_index: 版本号

        Returns:
            版本文案，不存在则返回 None
        """
        history = self.get_history(task_id)
        if history is None:
            return None

        versions = history.get("versions", [])
        if version_index < 0 or version_index >= len(versions):
            return None

        return versions[version_index]

    def get_current_version(self, task_id: str) -> Optional[dict]:
        """获取当前版本文案"""
        history = self.get_history(task_id)
        if history is None:
            return None

        current_index = history.get("current_version")
        if current_index is None:
            return None

        return self.get_version(task_id, current_index)

    def set_current_version(self, task_id: str, version_index: int) -> bool:
        """设置当前版本（恢复到某个版本）

        Args:
            task_id: 任务 ID
            version_index: 版本号

        Returns:
            是否成功
        """
        filepath = self._get_file_path(task_id)
        if not os.path.exists(filepath):
            return False

        history = self._load_history(filepath)
        versions = history.get("versions", [])

        if version_index < 0 or version_index >= len(versions):
            return False

        history["current_version"] = version_index
        history["updated_at"] = datetime.now().isoformat()

        self._save_history(filepath, history)
        return True

    def list_versions(self, task_id: str) -> List[dict]:
        """列出所有版本摘要

        Args:
            task_id: 任务 ID

        Returns:
            版本摘要列表
        """
        history = self.get_history(task_id)
        if history is None:
            return []

        versions = history.get("versions", [])
        return [
            {
                "version": v.get("version"),
                "created_at": v.get("created_at"),
                "feedback_preview": (v.get("user_feedback", "")[:50] + "...") if v.get("user_feedback") else "初始版本"
            }
            for v in versions
        ]


# 全局单例
_history_instance: Optional[ConversationHistory] = None


def get_conversation_history() -> ConversationHistory:
    """获取 ConversationHistory 单例"""
    global _history_instance
    if _history_instance is None:
        _history_instance = ConversationHistory()
    return _history_instance
