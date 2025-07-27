#!/bin/bash

# 需要安装额外的包
export DEBIAN_FRONTEND="noninteractive"
# 检查是否已安装gcc和g++
if ! command -v gcc &> /dev/null || ! command -v g++ &> /dev/null; then
    # 如果未安装，则执行安装
    cp /etc/apt/sources.list /etc/apt/sources.list.backup && \
    echo "deb http://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse" >> /etc/apt/sources.list && \
    apt update && \
    apt install -y gcc g++
fi

# 如果代码仓库不存在，克隆指定版本
if [ ! -d "studio" ]; then
    git clone https://github.com/modelscope/ClearerVoice-Studio.git studio
    cd studio/
    git checkout 41cbe4d6f902af9e911d098fdf0f76bb2bd49c02
    cd ..
fi
# 检查conda环境是否存在
if ! conda env list | grep -q "clear-voice"; then
    # 配置conda镜像源
    # conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
    # conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
    # conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
    # conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/msys2/
    # conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/bioconda/
    # conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/menpo/
    # conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/pytorch/
    # conda config --set show_channel_urls yes

    # 配置pip镜像源
    # pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

    # 创建 Python 3.8 环境
    conda create -n clear-voice python=3.8 -y

    # 激活环境
    source activate clear-voice

    # 安装依赖包
    pip install -r studio/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

    pip install streamlit requests sanic huggingface-hub -i https://pypi.tuna.tsinghua.edu.cn/simple/
else
    # 如果环境存在，直接激活
    source activate clear-voice
fi


# 设置huggingface镜像
export HF_ENDPOINT=https://hf-mirror.com

# 创建模型目录
mkdir -p studio/clearvoice/checkpoints/MossFormer2_SE_48K
mkdir -p studio/clearvoice/checkpoints/FRCRN_SE_16K 
mkdir -p studio/clearvoice/checkpoints/MossFormerGAN_SE_16K

# 下载模型
cd studio/clearvoice/checkpoints

# 下载 MossFormer2_SE_48K
huggingface-cli download --resume-download alibabasglab/MossFormer2_SE_48K --local-dir MossFormer2_SE_48K

# 下载 FRCRN_SE_16K
huggingface-cli download --resume-download alibabasglab/FRCRN_SE_16K --local-dir FRCRN_SE_16K

# 下载 MossFormerGAN_SE_16K  
huggingface-cli download --resume-download alibabasglab/MossFormerGAN_SE_16K --local-dir MossFormerGAN_SE_16K

# 返回原目录
cd ../../..


# 运行主程序
python main.py

