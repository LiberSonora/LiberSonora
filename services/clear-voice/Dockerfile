# 使用Python 3.8作为基础镜像（与原始环境保持一致）
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV HF_ENDPOINT=https://hf-mirror.com
ENV PYTHONPATH=/app
ENV WORKER_COUNT=1

# 配置pip镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 复制requirements文件（从environment.yml转换而来）
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建模型目录
RUN mkdir -p studio/clearvoice/checkpoints/MossFormer2_SE_48K \
    && mkdir -p studio/clearvoice/checkpoints/FRCRN_SE_16K \
    && mkdir -p studio/clearvoice/checkpoints/MossFormerGAN_SE_16K

# 设置启动脚本权限
RUN chmod +x docker-entrypoint.sh

# 暴露端口
EXPOSE 8501 8000

# 使用启动脚本
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "main.py"] 