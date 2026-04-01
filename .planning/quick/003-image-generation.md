---
id: 003
title: 配图自动生成（DALL-E 3 集成）
status: pending
created_at: 2026-03-31
tags: [quick, feature, image-generation]
---

## 目标

集成 DALL-E 3 API，直接生成配图而不是仅生成 prompt。

## 任务

### Task 1: DALL-E 3 客户端封装

**文件**: `src/utils/dalle_client.py`

**行动**:
- 创建 DALL-E 3 客户端类
- 配置 API KEY 从环境变量 `OPENAI_API_KEY` 读取
- 实现 `generate_image(prompt, size="1024x1024")` 方法
- 实现 `save_image(image_url, save_path)` 方法
- 添加错误处理和重试机制
- 添加 rate limiting 避免 API 限制

**验证**: `python -c "from src.utils.dalle_client import DALLEClient; print('OK')"`

**完成**: 客户端可正常初始化，API 调用方法完整

### Task 2: 修改 ImageAgent 生成图片

**文件**: `src/agents/image.py`

**行动**:
- 导入 DALL-E 3 客户端
- 修改 `process()` 方法调用 DALL-E 3 API
- 保存生成的图片到 `uploads/generated/` 目录
- 返回图片路径和 base64 编码给前端
- 保留 prompt 生成作为元数据

**验证**: ImageAgent 处理请求后返回包含图片路径的结果

**完成**: 配图 agent 直接生成图片文件

### Task 3: 前端显示生成的图片

**文件**: `frontend/src/App.jsx`

**行动**:
- 在配图标签页显示生成的图片
- 添加图片下载按钮
- 添加"重新生成"按钮
- 显示图片生成时间等信息
- 如果没有图片则显示 prompt 方案

**验证**: 前端可显示生成的图片，下载功能正常

**完成**: 用户可以看到和下载生成的配图
