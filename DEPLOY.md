# Fly.io + Vercel 部署指南

## 架构图

```
┌─────────────────┐     ┌─────────────────┐
│   Vercel (前端) │ ──→ │  Fly.io (后端)  │
│  React + Vite   │     │  FastAPI + AI   │
│  content-agent- │     │  content-agent- │
│  frontend       │     │  backend        │
└─────────────────┘     └─────────────────┘
```

---

## 第一部分：部署后端到 Fly.io

### 1. 登录 Fly.io

```bash
fly auth login
```

### 2. 更新 fly.toml 配置

已有配置文件，检查以下关键项：

```toml
app = "contentgenerate"  # 应用名称（全局唯一）
primary_region = "sin"   # 新加坡，离中国较近

[http_service]
  internal_port = 8002   # 你的 FastAPI 端口
```

### 3. 设置环境变量（密钥）

**重要：** 不要将 API 密钥提交到代码库，使用 Fly 的密钥管理：

```bash
# 设置 DashScope API 密钥
fly secrets set DASHSCOPE_API_KEY="sk-9465bd56013a4b1c9494e26b59237a77"

# 设置其他密钥
fly secrets set MINIMAX_API_KEY="sk-api-F9xAHFrM4pGuqhbt1cKr33y96JHC0DCdGoa9l5Tw0NA6T7Ykf540du4cTyaby6fZ-T76t824_THeETOeDNk_9WTCk9VePKalUKuhFXwyCY-PXfxyN3FPvt0"
```

### 4. 部署

在项目根目录运行：

```bash
fly deploy
```

### 5. 验证部署

```bash
# 查看状态
fly status

# 查看日志
fly logs

# 打开应用
fly open

# 健康检查
curl https://contentgenerate.fly.dev/health
```

### 6. 常见问题

**端口不匹配：**
- 确保 `fly.toml` 中 `internal_port = 8002`
- 确保 Dockerfile 中 `EXPOSE 8002`

**启动超时：**
```bash
fly deploy --health-check-only
```

**查看实例状态：**
```bash
fly status --app contentgenerate
fly ssh console --app contentgenerate  # 进入容器调试
```

---

## 第二部分：部署前端到 Vercel

### 1. 安装 Vercel CLI（可选）

```bash
npm i -g vercel
```

### 2. 配置前端 API 地址

已创建 `.env.production` 文件：

```
VITE_API_BASE=https://contentgenerate.fly.dev
```

**注意：** 将 URL 替换为你实际的 Fly.io 应用地址。

### 3. 通过 Vercel 官网部署

1. 访问 [vercel.com](https://vercel.com)
2. 登录（推荐用 GitHub）
3. 点击 "Add New Project"
4. 导入你的 GitHub 仓库
5. 配置：
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
6. 添加环境变量：
   - `VITE_API_BASE`: `https://contentgenerate.fly.dev`
7. 点击 "Deploy"

### 4. 使用 CLI 部署

```bash
cd frontend

# 首次部署
vercel --prod

# 后续部署
vercel
```

### 5. 绑定自定义域名（可选）

在 Vercel 项目设置中添加域名。

---

## 第三部分：本地测试

### 本地运行后端

```bash
cd backend
pip install -r requirements.txt
python main.py
# 访问 http://localhost:8002
```

### 本地运行前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

### 本地环境变量

创建 `frontend/.env.local`：

```
VITE_API_BASE=http://localhost:8002
```

---

## 第四部分：CI/CD 自动化

### GitHub Actions 自动部署

创建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}

  deploy-frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 20
      - run: npm ci
      - run: npm run build
      - uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

---

## 费用估算

### Fly.io 免费额度
- 每月 3 个 shared-cpu-1x 实例
- 512MB RAM
- 3GB 持久化存储

### Vercel 免费额度
- 无限部署
- 100GB 带宽/月
- 适合个人项目

---

## 故障排查

### 后端问题

```bash
# 查看实时日志
fly logs

# 重启实例
fly apps restart contentgenerate

# 查看机器状态
fly machines list

# SSH 进入容器
fly ssh console
```

### 前端问题

```bash
# 本地构建测试
cd frontend
npm run build
npx serve dist

# 检查 API 连接
curl https://contentgenerate.fly.dev/health
```

### CORS 错误

确保后端 `main.py` 中的 CORS 配置允许 Vercel 域名：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://your-app.vercel.app"
    ],
    # ...
)
```

---

## 检查清单

- [ ] Fly.io 账号已注册
- [ ] Vercel 账号已注册
- [ ] API 密钥已设置
- [ ] `fly.toml` 配置正确
- [ ] 前端 `.env.production` 配置正确
- [ ] 本地测试通过
- [ ] 部署成功
- [ ] 前后端连接正常
