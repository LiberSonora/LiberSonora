# 使用Python 3.11作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     libgl1 \
#     libglib2.0-0 \
#     ffmpeg \
#     && rm -rf /var/lib/apt/lists/*

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app
ENV WORKER_COUNT=1

# 配置pip镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装Python依赖
RUN pip install --no-cache-dir streamlit requests sanic torch torchaudio funasr pydub onnx onnxconverter-common

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8501 8000

# 启动命令
CMD ["python", "main.py"] 