---
id: 001
title: 生成结果本地存储与回溯功能增强
status: pending
created_at: 2026-03-31
tags: [quick, feature, storage]
---

## 目标

增强现有结果存储功能，支持历史记录查询和结果调用。

## 任务

### Task 1: 创建结果索引文件

**文件**: `backend/results_index.py`

**行动**:
- 创建 ResultsIndex 类，管理 results/目录下的 JSON 文件索引
- 实现 `add_result(task_id, data)` 方法 - 添加新结果
- 实现 `list_results(limit=20)` 方法 - 列出最近结果
- 实现 `get_result(task_id)` 方法 - 获取单个结果
- 实现 `search_results(keyword)` 方法 - 按关键词搜索
- 实现 `delete_result(task_id)` 方法 - 删除结果

**验证**: `python -c "from backend.results_index import ResultsIndex; idx = ResultsIndex(); print('OK')"`

**完成**: 索引类可正常初始化，方法定义完整

### Task 2: 后端 API 接口

**文件**: `backend/main.py`

**行动**:
- 添加 `GET /api/results` 接口 - 获取历史列表
- 添加 `GET /api/results/{task_id}` 接口 - 获取单个结果
- 添加 `GET /api/results/search?q=keyword` 接口 - 搜索结果
- 添加 `DELETE /api/results/{task_id}` 接口 - 删除结果
- 修改现有 `save_task_result` 调用索引类

**验证**: `curl http://localhost:8002/api/results` 返回 JSON 列表

**完成**: 所有 API 接口可正常访问
