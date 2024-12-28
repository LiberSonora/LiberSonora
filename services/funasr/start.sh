#!/bin/bash

# 需要安装额外的包
# export DEBIAN_FRONTEND="noninteractive"
# cp /etc/apt/sources.list /etc/apt/sources.list.backup && \
#     echo "deb http://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse" > /etc/apt/sources.list && \
#     echo "deb http://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse" >> /etc/apt/sources.list && \
#     echo "deb http://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse" >> /etc/apt/sources.list && \
#     echo "deb http://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse" >> /etc/apt/sources.list && \
#     echo "deb http://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse" >> /etc/apt/sources.list && \
#     apt update && \
#     apt install -y libgl1 && \
#     apt install -y libglib2.0-0

# 检查conda环境是否存在
if ! conda env list | grep -q "funasr"; then
    # 创建conda环境
    conda create -n funasr python=3.11 -y
    
    # 激活环境
    source activate funasr

    # 安装基础包
    pip install streamlit requests sanic -i https://pypi.tuna.tsinghua.edu.cn/simple/
    pip install torch torchaudio funasr pydub onnx onnxconverter-common -i https://pypi.tuna.tsinghua.edu.cn/simple/

else
    # 如果环境存在，直接激活
    source activate funasr
fi

# 运行主程序
python main.py

