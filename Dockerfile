FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装uv（Python包管理器）
RUN pip install uv

# 复制项目文件
COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/prompts/ ./prompts/
COPY backend/main.py ./

# 安装Python依赖
RUN uv sync --frozen

# 创建uploads目录
RUN mkdir -p uploads

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONPATH=/app
ENV PORT=8000

# 启动应用
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 