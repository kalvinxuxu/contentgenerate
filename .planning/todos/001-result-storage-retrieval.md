---
id: 001
title: 生成结果本地存储与回溯功能
description: 实现的文案生成结果应该能够回溯，储存在本地，可以调用
status: pending
created_at: 2026-03-31
tags: [feature, storage, retrieval]
---

## 需求描述

生成的文案结果应该能够：
1. 储存到本地（JSON 文件或其他格式）
2. 支持历史记录回溯
3. 可以调用之前生成的结果

## 实现要点

- [ ] 设计本地存储结构（JSON/SQLite）
- [ ] 实现结果保存功能
- [ ] 实现历史记录查询
- [ ] 实现结果调用/加载功能
- [ ] 前端历史记录面板优化

## 相关文件

- 后端：`backend/main.py` - 结果保存逻辑
- 前端：`frontend/src/App.jsx` - 历史记录显示
- 存储目录：`results/`

## 备注

当前已有基础的 JSON 结果保存到 `results/` 目录，但需要增强：
- 索引管理
- 搜索/筛选功能
- 版本管理（同一主题的多次生成）
