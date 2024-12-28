#!/bin/bash
# 需要安装额外的包
export DEBIAN_FRONTEND="noninteractive"
# 检查是否已安装ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    # 如果未安装，则执行安装
    cp /etc/apt/sources.list /etc/apt/sources.list.backup && \
    echo "deb http://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse" >> /etc/apt/sources.list && \
    apt update && \
    apt install -y ffmpeg
fi

# 检查conda环境是否存在
if ! conda env list | grep -q "LiberSonora"; then
    # 创建conda环境
    conda create -n LiberSonora python=3.11 -y
    
    # 激活环境
    source activate LiberSonora

    # 安装基础包
    pip install streamlit sanic ffmpeg aiohttp st-diff-viewer streamlit-antd-components -i https://pypi.tuna.tsinghua.edu.cn/simple/
else
    # 如果环境存在，直接激活
    source activate LiberSonora
fi

# 运行主程序
streamlit run main.py

