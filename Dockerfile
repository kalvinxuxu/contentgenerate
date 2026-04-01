# 使用 Python 3.10 精简版镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（如果需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt .
COPY requirements.txt ./requirements-root.txt

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-root.txt && \
    pip install python-dotenv

# 复制后端代码
COPY backend/ ./backend/
COPY src/ ./src/
COPY config/ ./config/

# 创建 uploads 和 results 目录
RUN mkdir -p /app/uploads /app/results

# 暴露端口
EXPOSE 8002

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# 启动命令
CMD ["python", "backend/main.py"]
