---
id: 002
title: 多轮对话文案优化功能
status: pending
created_at: 2026-03-31
tags: [quick, feature, conversation]
---

## 目标

支持多轮对话式文案修改，让用户可以通过多轮反馈迭代直到文案符合要求。

## 任务

### Task 1: 对话历史存储

**文件**: `backend/main.py`, `backend/conversation_history.py`

**行动**:
- 创建 ConversationHistory 类管理对话历史
- 实现 `add_turn(task_id, user_feedback, new_result)` 方法
- 实现 `get_history(task_id)` 方法获取完整对话历史
- 实现 `get_version(task_id, version_index)` 获取指定版本文案
- 在 `workflow_states` 中添加 `conversation_history` 字段
- 每次修改意见提交后保存对话记录

**验证**: `python -c "from backend.conversation_history import ConversationHistory; ch = ConversationHistory(); print('OK')"`

**完成**: 对话历史类正常工作，版本可追溯

### Task 2: 前端多轮对话 UI

**文件**: `frontend/src/App.jsx`

**行动**:
- 在结果区添加"版本历史"标签页
- 显示所有版本文案的列表
- 支持点击切换查看不同版本
- 支持"恢复到这个版本"按钮
- 显示每次修改的用户反馈

**验证**: 前端可显示版本文历史，点击可切换

**完成**: 用户可以查看和恢复历史版本
