---
phase: quick
plan: 002
type: execute
tags: [conversation, multi-turn, version-control]
tech_stack:
  added: []
  patterns:
    - 版本历史存储模式
    - 对话轮次追踪
key_files:
  created:
    - backend/conversation_history.py
  modified:
    - backend/main.py
    - frontend/src/App.jsx
decisions:
  - 每个任务独立存储对话历史文件
  - 版本号从 0 开始自动递增
  - 支持恢复到任意历史版本
metrics:
  duration: ~45min
  completed: 2026-03-31
---

# Quick Task 002: 多轮对话文案优化功能

## 一句话总结

实现多轮对话版本追踪功能，用户可以查看历史版本、对比修改意见、恢复到任意版本。

## 完成的工作

### 1. 创建对话历史模块 (`backend/conversation_history.py`)

新建 `ConversationHistory` 类提供以下功能：
- `add_turn(task_id, user_feedback, new_result, version_index)` - 添加一轮对话记录
- `get_history(task_id)` - 获取完整对话历史
- `get_version(task_id, version_index)` - 获取指定版本文案
- `get_current_version(task_id)` - 获取当前版本文案
- `set_current_version(task_id, version_index)` - 恢复到指定版本
- `list_versions(task_id)` - 列出所有版本摘要

存储结构：
- 每个任务独立存储为 `results/conversations/{task_id}.json`
- 每个版本包含：版本号、创建时间、用户修改意见、完整结果数据

### 2. 添加对话历史 API 接口 (`backend/main.py`)

新增 5 个 API 接口：
- `GET /api/conversations/{task_id}` - 获取完整对话历史
- `GET /api/conversations/{task_id}/versions` - 列出所有版本
- `GET /api/conversations/{task_id}/version/{version_index}` - 获取指定版本
- `POST /api/conversations/{task_id}/restore?version_index=N` - 恢复到指定版本

修改 `run_current_step_with_modification` 函数：
- 每次根据修改意见重新生成后，自动保存到对话历史
- 记录用户修改意见和新的生成结果

### 3. 前端版本历史 UI (`frontend/src/App.jsx`)

新增状态：
- `showVersionHistory` - 是否显示版本历史面板
- `versionHistory` - 版本历史列表
- `currentVersionIndex` - 当前版本索引

新增功能：
- `loadVersionHistory(taskId)` - 加载版本历史
- `getVersion(taskId, versionIndex)` - 获取指定版本
- `restoreVersion(taskId, versionIndex)` - 恢复到指定版本
- `handleShowVersionHistory()` - 显示版本历史

UI 改进：
- 在结果区新增"版本历史"标签页
- 显示所有版本号、创建时间、修改意见预览
- 当前版本高亮显示
- 支持一键恢复到历史版本

## 版本历史数据结构

```json
{
  "task_id": "xxx",
  "created_at": "2026-03-31T...",
  "versions": [
    {
      "version": 0,
      "created_at": "...",
      "user_feedback": "初始版本",
      "result": { ... }
    },
    {
      "version": 1,
      "created_at": "...",
      "user_feedback": "语气再活泼一些",
      "result": { ... }
    }
  ],
  "current_version": 1
}
```

## Deviations from Plan

None - 计划按预期执行完成。

## Self-Check: PASSED

- [x] `backend/conversation_history.py` 已创建
- [x] `backend/main.py` API 接口已添加
- [x] `frontend/src/App.jsx` 版本历史 UI 已实现
- [x] `STATE.md` 已更新

## Next Steps

执行 Quick Task 003: 配图自动生成（DALL-E 3 集成）
