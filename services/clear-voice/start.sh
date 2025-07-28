#!/bin/bash

# 简化的启动脚本，用于 Docker 容器外的直接运行

echo "ClearVoice 服务启动中..."

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo "错误：未找到 Python 解释器"
    exit 1
fi

# 检查必要的依赖
if [ ! -d "studio" ]; then
    echo "错误：studio 目录不存在，请确保已正确克隆 ClearerVoice-Studio"
    echo "运行：git clone https://cf.ghproxy.cc/https://github.com/modelscope/ClearerVoice-Studio.git studio"
    exit 1
fi

# 验证模型文件
if [ ! -d "studio/clearvoice/checkpoints" ]; then
    echo "错误：模型目录不存在，请确保已下载所需模型"
    exit 1
fi

echo "环境检查完成，启动服务..."

# 运行主程序
python main.py

