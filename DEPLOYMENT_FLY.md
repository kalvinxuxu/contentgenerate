# Fly.io 部署指南

## 前提条件

1. 安装 Fly.io CLI:
   ```bash
   # macOS
   brew install flyctl

   # Windows (WSL)
   curl -L https://fly.io/install.sh | sh

   # 或直接下载：https://fly.io/docs/getting-started/installing-flyctl/
   ```

2. 登录 Fly.io:
   ```bash
   fly auth login
   ```

## 部署步骤

### 1. 初始化应用（如果还没有 fly.toml）

```bash
fly launch --no-deploy
```

- 应用名称：输入你想要的名称（全球唯一）
- 区域：选择 `sin` (新加坡) 或 `hkg` (香港) 以获得更低延迟
- 不需要立即部署，选 No

### 2. 配置环境变量（重要！）

```bash
# 设置 Anthropic API Key
fly secrets set ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 可选：设置 Minimax API Key（用于图片生成）
fly secrets set MINIMAX_API_KEY=sk-xxxxx

# 可选：设置 Dashscope API Key（阿里云百炼云）
fly secrets set DASHSCOPE_API_KEY=sk-xxxxx
```

### 3. 部署应用

```bash
fly deploy
```

### 4. 查看部署状态

```bash
fly status
fly logs
```

### 5. 打开应用

```bash
fly open
```

## 前端配置

部署后端成功后，在前端项目中配置 API 地址：

1. 获取后端 URL:
   ```bash
   fly status --app contentgenerate
   # 输出类似：https://contentgenerate.fly.dev
   ```

2. 在 Vercel 前端项目中设置环境变量：
   ```
   VITE_API_BASE=https://contentgenerate.fly.dev
   VITE_WS_BASE=wss://contentgenerate.fly.dev
   ```

## 常用命令

```bash
# 查看日志
fly logs

# 查看应用信息
fly status

# 重启应用
fly restart

# 扩容（增加实例）
fly scale count 2

# 升级配置
fly scale vm shared-cpu-2x --memory 1024

# 查看环境变量
fly secrets list

# 删除环境变量
fly secrets unset KEY_NAME
```

## 故障排查

### 应用启动失败
```bash
# 查看日志
fly logs

# 进入机器 shell 调试
fly ssh console
```

### API 调用失败
- 检查 API Key 是否正确设置
- 检查网络连接
- 查看 `/health` 端点是否正常

## 成本估算

Fly.io 免费额度：
- 3 台共享 CPU 虚拟机（256MB 内存）
- 每月 160GB 出站流量

本应用配置（512MB）：
- 约 $5-10/月（取决于使用量）
- 可设置 `auto_stop_machines = true` 节省成本

## 升级配置

如果并发量增加，可以升级：

```bash
# 增加内存
fly scale vm shared-cpu-2x --memory 1024

# 增加实例数
fly scale count 2
```
