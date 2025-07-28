FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 设置镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 更新 pip
RUN pip install --upgrade pip

# 安装基础包和 ClearVoice
RUN pip install streamlit requests sanic huggingface_hub torch torchaudio

	# 安装 ClearVoice（避免复杂的源码编译）
RUN pip install clearvoice

# 设置环境变量
ENV HF_ENDPOINT=https://hf-mirror.com

# 复制应用代码
COPY . /app/

# 创建模型目录
RUN mkdir -p clearvoice/checkpoints


# # 创建模型目录
# RUN mkdir -p studio/clearvoice/checkpoints/MossFormer2_SE_48K && \
#     mkdir -p studio/clearvoice/checkpoints/FRCRN_SE_16K && \
#     mkdir -p studio/clearvoice/checkpoints/MossFormerGAN_SE_16K
# # 下载模型
# RUN cd studio/clearvoice/checkpoints && \
#     huggingface-cli download --resume-download alibabasglab/MossFormer2_SE_48K --local-dir MossFormer2_SE_48K && \
#     huggingface-cli download --resume-download alibabasglab/FRCRN_SE_16K --local-dir FRCRN_SE_16K && \
#     huggingface-cli download --resume-download alibabasglab/MossFormerGAN_SE_16K --local-dir MossFormerGAN_SE_16K && \
#     cd ../../..

# 创建模型预下载脚本
RUN echo '#!/usr/bin/env python3\n\
import os\n\
from clearvoice import ClearVoice\n\
\n\
# 设置模型下载目录\n\
os.makedirs("./clearvoice/checkpoints", exist_ok=True)\n\
\n\
models = ["MossFormer2_SE_48K", "FRCRN_SE_16K", "MossFormerGAN_SE_16K"]\n\
\n\
for model in models:\n\
    print(f"开始下载 {model} 模型...")\n\
    try:\n\
        cv = ClearVoice(task="speech_enhancement", model_names=[model])\n\
        print(f"{model} 模型下载完成")\n\
    except Exception as e:\n\
        print(f"{model} 下载失败: {e}")\n\
\n\
print("所有模型预下载完成")\n\
' > /tmp/download_models.py

# 预下载模型到构建阶段，避免运行时下载
RUN python /tmp/download_models.py && rm /tmp/download_models.py

# 设置启动命令
CMD ["python", "main.py"] 