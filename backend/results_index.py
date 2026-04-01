"""
结果索引管理模块

提供结果存储、查询、搜索功能
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime


class ResultsIndex:
    """结果索引管理类"""

    def __init__(self, results_dir: str = None):
        """初始化结果索引

        Args:
            results_dir: 结果存储目录，默认为项目根目录的 results/
        """
        if results_dir is None:
            # 默认使用项目根目录的 results/
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            results_dir = os.path.join(base_dir, "results")

        self.results_dir = results_dir
        self.index_file = os.path.join(results_dir, "_index.json")

        # 确保目录存在
        os.makedirs(results_dir, exist_ok=True)

        # 加载或创建索引
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        """加载索引文件"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass

        # 初始化新索引
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "entries": []
        }

    def _save_index(self):
        """保存索引文件"""
        self.index["updated_at"] = datetime.now().isoformat()
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)

    def add_result(self, task_id: str, data: dict) -> str:
        """添加或更新结果

        Args:
            task_id: 任务 ID
            data: 完整的结果数据（包含 task_id, created_at, config, step_results, final_output）

        Returns:
            保存的文件路径
        """
        # 保存到 JSON 文件
        filepath = os.path.join(self.results_dir, f"{task_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 更新索引
        entry = {
            "task_id": task_id,
            "filename": f"{task_id}.json",
            "created_at": data.get("created_at", datetime.now().isoformat()),
            "topic": data.get("config", {}).get("topic", "未命名"),
            "platform": data.get("config", {}).get("platform", "unknown"),
            "final_content_preview": self._get_content_preview(data.get("final_output", {})),
            "filepath": filepath
        }

        # 检查是否已存在
        existing_idx = next((i for i, e in enumerate(self.index["entries"]) if e["task_id"] == task_id), None)
        if existing_idx is not None:
            # 更新现有条目
            self.index["entries"][existing_idx] = entry
        else:
            # 添加新条目
            self.index["entries"].append(entry)

        # 按时间倒序排序（最新的在前）
        self.index["entries"].sort(key=lambda x: x["created_at"], reverse=True)

        self._save_index()
        return filepath

    def _get_content_preview(self, final_output: dict, max_length: int = 100) -> str:
        """获取内容预览"""
        content = final_output.get("final_content", "")
        if not content:
            # 尝试从审核结果获取
            content = final_output.get("reviewer", {}).get("conclusion", "")
        if len(content) > max_length:
            return content[:max_length] + "..."
        return content

    def list_results(self, limit: int = 20) -> List[Dict]:
        """列出最近的结果

        Args:
            limit: 最多返回的条目数

        Returns:
            结果列表
        """
        return self.index["entries"][:limit]

    def get_result(self, task_id: str) -> Optional[Dict]:
        """获取单个结果

        Args:
            task_id: 任务 ID

        Returns:
            完整的结果数据，如果不存在则返回 None
        """
        filepath = os.path.join(self.results_dir, f"{task_id}.json")
        if not os.path.exists(filepath):
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def search_results(self, keyword: str) -> List[Dict]:
        """搜索结果

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的结果列表
        """
        keyword_lower = keyword.lower()
        matches = []

        for entry in self.index["entries"]:
            # 搜索主题
            if keyword_lower in entry.get("topic", "").lower():
                matches.append(entry)
                continue

            # 搜索完整内容
            result = self.get_result(entry["task_id"])
            if result:
                content = result.get("final_output", {}).get("final_content", "")
                if keyword_lower in content.lower():
                    matches.append(entry)
                    continue

                config = result.get("config", {})
                config_str = json.dumps(config, ensure_ascii=False).lower()
                if keyword_lower in config_str:
                    matches.append(entry)

        return matches

    def delete_result(self, task_id: str) -> bool:
        """删除结果

        Args:
            task_id: 任务 ID

        Returns:
            是否删除成功
        """
        filepath = os.path.join(self.results_dir, f"{task_id}.json")

        # 删除文件
        if os.path.exists(filepath):
            os.remove(filepath)

        # 从索引中移除
        self.index["entries"] = [e for e in self.index["entries"] if e["task_id"] != task_id]
        self._save_index()

        return True

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_count": len(self.index["entries"]),
            "storage_dir": self.results_dir,
            "index_file": self.index_file
        }


# 全局单例
_index_instance: Optional[ResultsIndex] = None


def get_results_index() -> ResultsIndex:
    """获取 ResultsIndex 单例"""
    global _index_instance
    if _index_instance is None:
        _index_instance = ResultsIndex()
    return _index_instance
