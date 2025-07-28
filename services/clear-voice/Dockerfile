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

# 安装 huggingface-hub 用于模型下载
RUN pip install --no-cache-dir huggingface-hub

# 克隆 ClearerVoice-Studio 代码仓库
RUN git clone https://cf.ghproxy.cc/https://github.com/modelscope/ClearerVoice-Studio.git studio && \
    cd studio && \
    git checkout 41cbe4d6f902af9e911d098fdf0f76bb2bd49c02 && \
    cd ..

# 安装 studio 的依赖
RUN pip install --no-cache-dir -r studio/requirements.txt

# 创建模型目录
RUN mkdir -p studio/clearvoice/checkpoints/MossFormer2_SE_48K \
    && mkdir -p studio/clearvoice/checkpoints/FRCRN_SE_16K \
    && mkdir -p studio/clearvoice/checkpoints/MossFormerGAN_SE_16K

# 下载所有模型到构建镜像中
RUN cd studio/clearvoice/checkpoints && \
    huggingface-cli download --resume-download alibabasglab/MossFormer2_SE_48K --local-dir MossFormer2_SE_48K && \
    huggingface-cli download --resume-download alibabasglab/FRCRN_SE_16K --local-dir FRCRN_SE_16K && \
    huggingface-cli download --resume-download alibabasglab/MossFormerGAN_SE_16K --local-dir MossFormerGAN_SE_16K && \
    cd ../../..

# 复制应用代码
COPY . .

# 设置启动脚本权限
RUN chmod +x docker-entrypoint.sh

# 暴露端口
EXPOSE 8501 8000

# 使用启动脚本
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "main.py"] 