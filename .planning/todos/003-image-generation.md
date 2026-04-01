# Quick Task 003: 配图自动生成（Minimax API 集成）

## 目标
完善配图自动生成功能，使用 Minimax API 实际生成图片，而非仅生成 Midjourney 提示词。

## 当前状态分析

### 已有功能 ✅
- `MinimaxImageClient` 类已实现 (`src/utils/minimax_client.py`)
  - 文生图功能 (`generate_text_to_image`)
  - 图生图功能 (`generate_image_with_subject_reference`)
  - 图片保存功能 (`save_image`, `generate_and_save`)
- `ImageAgent` 已集成 Minimax 客户端 (`src/agents/image.py`)
  - 支持 `generate_image` 参数控制是否生成实际图片
  - 支持 `reference_image_path` 参数进行主体参考
- Minimax API Key 已配置

### 待完善功能 🔧
- [ ] 测试 Minimax 文生图功能
- [ ] 测试 Minimax 图生图功能（主体参考）
- [ ] 添加图片生成进度提示
- [ ] 添加图片生成失败降级处理
- [ ] 生成多张备选图片
- [ ] 优化图片参数（宽高比、风格等）

## 任务分解

### 1. 测试 Minimax API 连接
- [ ] 验证 API Key 有效性
- [ ] 测试文生图基础功能
- [ ] 验证图片下载和保存

### 2. 增强 ImageAgent 功能
- [ ] 支持生成多张备选图片（1-4 张）
- [ ] 优化宽高比配置（根据平台自动选择）
- [ ] 添加图片生成状态输出
- [ ] 添加失败重试机制

### 3. 配置优化
- [ ] 添加 Minimax 模型配置到 `config/settings.yaml`
- [ ] 添加图片生成参数配置
- [ ] 更新 `.env.example`

### 4. 测试与文档
- [ ] 编写 Minimax 客户端测试
- [ ] 更新 README 说明配图功能
- [ ] 记录使用示例

## 验收标准
- [ ] Minimax API 可正常生成图片
- [ ] 图片保存到 `uploads/generated/` 目录
- [ ] 支持文生图和图生图两种模式
- [ ] 生成结果包含图片路径和元数据
- [ ] 错误处理完善

## 时间估算
2-3 小时

## 备注
Minimax API 目前仅支持 `character` 类型的主体参考，适用于人物形象一致性保持。
