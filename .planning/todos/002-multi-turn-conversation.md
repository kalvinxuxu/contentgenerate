---
id: 002
title: 多轮对话文案优化功能
description: 支持多轮对话，达到符合用户要求的文案
status: pending
created_at: 2026-03-31
tags: [feature, conversation, iteration]
---

## 需求描述

支持多轮对话式文案修改，让用户可以通过多轮反馈迭代，直到文案完全符合要求。

## 实现要点

- [ ] 保存对话历史上下文
- [ ] 支持基于上下文的修改请求
- [ ] 实现文案版本管理
- [ ] 用户可以选择恢复到任意版本
- [ ] 记录每次修改的用户反馈

## 交互流程

1. 用户查看生成的文案
2. 提出修改意见（如"语气再活泼一些"）
3. 系统根据反馈重新生成
4. 用户继续提出修改意见
5. 循环直到满意

## 相关文件

- 后端：`backend/main.py` - `/api/task/{task_id}/confirm` 接口
- 前端：`frontend/src/App.jsx` - 修改意见输入框
- Agent：`src/agents/creator.py`, `src/agents/optimizer.py`

## 备注

当前已有基础的修改意见提交功能，但需要增强：
- 多轮对话上下文管理
- 版本对比功能
- 一键恢复历史版本
