#!/bin/bash

# 设置错误时退出
set -e

echo "清晰语音服务启动中..."

# 验证关键文件是否存在
if [ ! -d "studio" ]; then
    echo "错误：studio 目录不存在"
    exit 1
fi

if [ ! -d "studio/clearvoice/checkpoints" ]; then
    echo "错误：模型目录不存在"
    exit 1
fi

echo "环境检查完成，启动服务..."

# 执行原始命令
exec "$@" 