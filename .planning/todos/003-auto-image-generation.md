---
id: 003
title: 配图自动生成（非仅 Prompt）
description: 配图直接生成图，不是仅仅生成 prompt
status: pending
created_at: 2026-03-31
tags: [feature, image-generation, ai]
---

## 需求描述

当前的配图功能只生成 Midjourney prompt，用户需要手动复制 prompt 到 Midjourney 生成图片。
需要实现自动图片生成，直接输出可用的配图。

## 实现方案

### 方案 A: 调用 AI 绘画 API
- DALL-E 3 API
- Stable Diffusion API
- Midjourney API（如果有）

### 方案 B: 本地部署
- Stable Diffusion WebUI
- ComfyUI

## 实现要点

- [ ] 选择并集成图片生成服务
- [ ] 修改 `ImageAgent` 直接返回图片
- [ ] 前端显示生成的图片
- [ ] 支持图片下载
- [ ] 支持重新生成

## 相关文件

- Agent: `src/agents/image.py` - `ImageAgent`
- 前端：`frontend/src/App.jsx` - 配图方案显示
- API: `backend/main.py` - `run_image_step`

## 备注

推荐优先集成 DALL-E 3 API：
- 简单易用
- 生成质量高
- 按量付费成本低
