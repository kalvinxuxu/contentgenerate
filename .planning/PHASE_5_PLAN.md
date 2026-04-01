# Phase 5 Plan - 测试与优化

## 目标
- 验证工作流功能完整性
- 优化生成质量
- 性能调优
- 确保代码质量

## 任务分解

### 5.1 单元测试编写
- [ ] ClaudeClient 测试 (`tests/test_claude_client.py`)
  - Token 计数验证
  - 成本计算验证
  - 错误处理测试
  - 重试机制测试
- [ ] Agent 测试 (`tests/test_agents.py`)
  - ResearchAgent 输入输出验证
  - CreatorAgent 生成质量验证
  - ReviewerAgent 评分逻辑验证
  - OptimizerAgent 优化效果验证
  - ImageAgent 提示词生成验证
- [ ] 工具函数测试 (`tests/test_utils.py`)
  - PromptEngine 渲染测试
  - JSON 解析测试
  - 配置加载测试

### 5.2 集成测试编写
- [ ] 工作流编排测试 (`tests/test_workflow.py`)
  - Agent 间数据传递验证
  - 上下文累积验证
  - 错误传播验证
- [ ] CLI 测试 (`tests/test_cli.py`)
  - 命令行参数解析
  - 输出格式化
  - 文件保存功能

### 5.3 端到端测试
- [ ] 完整工作流测试 (`tests/test_e2e.py`)
  - 小红书文案生成
  - 微信公众号文案生成
  - 博客文章生成
- [ ] 边界情况测试
  - 空输入处理
  - 超长输入处理
  - 特殊字符处理

### 5.4 Prompt 调优
- [ ] Research Agent Prompt 优化
  - 增加 Few-Shot 示例
  - 优化输出格式要求
- [ ] Creator Agent Prompt 优化
  - 钩子公式强化
  - 平台调性适配
- [ ] Reviewer Agent Prompt 优化
  - 6 维评估标准细化
  - 审核意见具体化
- [ ] Optimizer Agent Prompt 优化
  - 优化策略明确化
  - 保留原文风格指导

### 5.5 性能优化
- [ ] 响应时间优化
  - 并行调用可行性分析
  - 缓存机制（可选）
- [ ] Token 使用优化
  - Prompt 精简
  - 上下文压缩
- [ ] 成本优化
  - 模型选择建议
  - 重试次数限制

### 5.6 文档完善
- [ ] API 文档生成
- [ ] 开发指南编写
- [ ] 最佳实践文档

## 验收标准

- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 所有测试通过
- [ ] 端到端测试稳定运行
- [ ] Prompt 质量评分 ≥ 4.5/6
- [ ] 单次生成时间 < 2 分钟
- [ ] 文档齐全

## 负责人
Claude (AI Assistant)

## 时间估算
1 天

## 备注
- 使用 pytest 作为测试框架
- 使用 pytest-cov 进行覆盖率统计
- Mock API 调用以降低成本
