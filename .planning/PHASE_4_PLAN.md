# Phase 4 Plan - Claude API 集成

## 目标
- 集成 Anthropic Claude API
- 配置模型参数
- 实现 token 管理和成本追踪
- 实现完善的错误处理和重试机制

## 任务分解

### 4.1 Anthropic SDK 集成
- [ ] 安装 `anthropic` 和 `@anthropic-ai/sdk`
- [ ] 创建 `ClaudeClient` 类封装
- [ ] 支持同步和异步调用
- [ ] 实现流式输出支持

### 4.2 API 认证管理
- [ ] 配置 `ANTHROPIC_API_KEY` 环境变量
- [ ] 创建 `.env.example` 模板文件
- [ ] 实现多 Key 轮询（可选）

### 4.3 模型参数配置
- [ ] 支持 Claude 4.5/4.6 模型系列
- [ ] 配置 temperature、max_tokens、top_p 等参数
- [ ] 为不同 Agent 配置最优参数

### 4.4 Token 管理与成本追踪
- [ ] 实现 token 计数功能
- [ ] 记录每次调用的输入/输出 token 数
- [ ] 计算 API 成本
- [ ] 实现 token 使用日志

### 4.5 错误处理和重试机制
- [ ] 处理 API 限流（429）
- [ ] 处理超时（5xx）
- [ ] 实现指数退避重试
- [ ] 实现请求日志记录

### 4.6 Agent 迁移
- [ ] 迁移 Research Agent 到 ClaudeClient
- [ ] 迁移 Creator Agent 到 ClaudeClient
- [ ] 迁移 Reviewer Agent 到 ClaudeClient
- [ ] 迁移 Optimizer Agent 到 ClaudeClient
- [ ] 迁移 Image Agent 到 ClaudeClient

### 4.7 测试与验证
- [ ] 单元测试 ClaudeClient
- [ ] 端到端测试完整工作流
- [ ] 验证错误处理
- [ ] 验证 token 计数准确性

## 验收标准

- [ ] 所有 Agent 都使用 Claude API
- [ ] Token 计数和成本追踪功能正常
- [ ] 错误处理和重试机制完善
- [ ] 工作流可稳定运行
- [ ] 文档齐全（README、配置说明）

## 负责人
Claude (AI Assistant)

## 时间估算
1 天

## 备注
- 当前代码使用阿里云百炼云（OpenAI 兼容接口）
- Phase 4 将迁移到原生 Anthropic SDK
- 保持代码向后兼容，支持多 LLM 后端
