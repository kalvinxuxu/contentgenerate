# 多 Agent 文案生成系统

基于 Anthropic Claude API 的多 Agent 协作文案生成工作流。支持 Anthropic Claude 和阿里云 DashScope 两种 LLM 后端。

## 架构设计

系统包含 5 个 Agent，按顺序协作完成文案生成：

```
用户输入 → 调研 Agent → 创作 Agent → 审核 Agent → 优化 Agent → 配图 Agent → 最终输出
```

### Agent 职责

| Agent | 职责 | 温度 |
|-------|------|------|
| **ResearchAgent** | 内容选题专家，分析热点趋势、用户痛点和爆款逻辑 | 0.7 |
| **CreatorAgent** | 爆款文案写手，基于调研报告撰写高传播文案 | 0.8 |
| **ReviewerAgent** | 资深内容主编，6 维评估体系给出修改建议 | 0.3 |
| **OptimizerAgent** | 金牌文案编辑，在保留原文风格基础上润色提升 | 0.5 |
| **ImageAgent** | 视觉创意总监，生成 Midjourney 提示词和排版建议 | 0.7 |

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 或者使用 editable 模式安装
pip install -e .
```

## 配置

### 1. 环境变量

在 `.env` 文件中配置 API 密钥：

```bash
# Anthropic Claude API（推荐）
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# 或者使用阿里云 DashScope（备选）
# DASHSCOPE_API_KEY=sk-xxxxx

# 可选：Minimax API（用于图片生成）
# MINIMAX_API_KEY=sk-xxxxx
```

获取 API Key：
- **Anthropic**: 访问 [Claude API Console](https://console.anthropic.com/)
- **阿里云**: 访问 [DashScope 控制台](https://dashscope.console.aliyun.com/)

### 2. 模型配置

编辑 `config/settings.yaml` 调整各 Agent 的模型参数：

```yaml
models:
  default: &default
    model: "claude-sonnet-4-6"
    temperature: 0.7
    max_tokens: 2048

  research:
    <<: *default
    temperature: 0.7
    max_tokens: 4096
```

### 3. LLM 后端选择

系统会自动根据环境变量选择合适的后端：
- 如果设置了 `ANTHROPIC_API_KEY`，使用 Anthropic Claude
- 如果设置了 `DASHSCOPE_API_KEY`，使用阿里云 DashScope

也可以显式指定：
```bash
# 强制使用 Anthropic
export LLM_PROVIDER=anthropic

# 强制使用 DashScope
export LLM_PROVIDER=dashscope
```

### 4. 配图功能配置（可选）

如需自动生成配图，配置 Minimax API Key：

```bash
# .env 文件中添加
MINIMAX_API_KEY=sk-api-xxxxx
```

获取 API Key：访问 [Minimax 开放平台](https://platform.minimaxi.com/)

**配图模式说明：**
- **文生图模式**：根据文案内容直接生成图片
- **图生图模式**：提供人物参考图，保持形象一致性（目前仅支持 character 类型）

**平台默认宽高比：**
| 平台 | 宽高比 |
|------|--------|
| 小红书 | 3:4 (竖版) |
| 微信公众号 | 16:9 (横版) |
| 博客 | 16:9 (横版) |

## 使用

### CLI 命令

```bash
# 运行完整工作流
python main.py generate \
  --topic "AI 写作" \
  --audience "自媒体创作者" \
  --platform xiaohongshu \
  --tone casual \
  --priority standard \
  --emotion hopeful \
  --style minimalist \
  --output result.json

# 仅运行调研
python main.py research \
  --topic "时间管理" \
  --audience "职场人士" \
  --platform xiaohongshu

# 审核文案文件
python main.py review draft.txt

# 查看当前配置
python main.py config
```

### Python API

```python
from src.workflow import WorkflowOrchestrator

# 初始化工作流
orchestrator = WorkflowOrchestrator()

# 运行完整流程
result = orchestrator.run(
    topic="AI 写作",
    target_audience="自媒体创作者",
    platform="xiaohongshu",
    tone="casual",
    priority="standard",
    emotion="hopeful",
    style_preference="minimalist"
)

# 获取最终文案
final_content = result["final_output"]["final_content"]

# 获取配图建议
mj_prompts = result["final_output"]["image"]["mj_prompts"]
```

## 输出格式

### 调研报告
```json
{
  "trend_analysis": "热搜趋势分析",
  "pain_points": [...],
  "viral_examples": [...],
  "angles": [...]
}
```

### 创作文案
```json
{
  "content_type": "社交媒体文案",
  "headline": "标题",
  "body": "文案正文",
  "hook_type": "结果型",
  "emotion_trigger": "好奇 + 爽感",
  "image_suggestions": [...]
}
```

### 审核结果
```json
{
  "overall_score": 4,
  "dimension_scores": [
    {"dimension": "钩子强度", "score": 5, "comment": "..."}
  ],
  "highlights": [...],
  "must_fix_issues": [...],
  "conclusion": "modify"
}
```

### 配图建议
```json
{
  "mj_prompts": [
    {
      "style": "极简风",
      "prompt_en": "minimalist product photography...",
      "params": {"--ar": "3:4", "--v": "5.2"}
    }
  ],
  "layout_suggestions": {...},
  "color_palette": {...}
}
```

## 项目结构

```
claude-content-agents/
├── src/
│   ├── agents/
│   │   ├── base.py           # Agent 抽象基类
│   │   ├── research.py       # 调研 Agent
│   │   ├── creator.py        # 创作 Agent
│   │   ├── reviewer.py       # 审核 Agent
│   │   ├── optimizer.py      # 优化 Agent
│   │   ├── image.py          # 配图 Agent
│   │   └── prompts/          # Prompt 模板
│   ├── workflow/
│   │   └── orchestrator.py   # 工作流编排器
│   ├── utils/
│   │   ├── llm_client.py     # LLM 客户端
│   │   ├── prompt_engine.py  # Prompt 引擎
│   │   └── config.py         # 配置加载
│   ├── cli.py                # CLI 入口
│   └── models.py             # Pydantic 数据模型
├── config/
│   └── settings.yaml         # 配置文件
├── requirements.txt
├── pyproject.toml
└── main.py                   # 主程序入口
```

## 核心特性

### 6 维审核体系
1. **钩子强度** - 第一句话能否在 3 秒内抓住注意力
2. **情绪价值** - 是否能引发读者情绪波动
3. **信息密度** - 是否有足够干货/价值
4. **可读性** - 句子是否简短有力
5. **平台适配** - 是否符合目标平台调性
6. **合规检查** - 是否有夸大/虚假宣传风险

### 钩子公式
- **反差型**: "你以为...其实..."
- **数字型**: "X 天/Y 个方法/Z 倍效果"
- **悬念型**: "我发现了...的秘密"
- **痛点型**: "你是不是也..."
- **权威型**: "XX 专家不会告诉你的..."
- **结果型**: "从...到...我只用了..."

## 开发

```bash
# 运行测试
pytest

# 开发模式安装
pip install -e ".[dev]"
```

## License

MIT
