#!/bin/bash

# 设置错误时退出
set -e

# 检查模型是否已下载
check_and_download_models() {
    echo "检查模型文件..."
    
    # 检查 MossFormer2_SE_48K 模型
    if [ ! -d "studio/clearvoice/checkpoints/MossFormer2_SE_48K" ] || [ -z "$(ls -A studio/clearvoice/checkpoints/MossFormer2_SE_48K 2>/dev/null)" ]; then
        echo "下载 MossFormer2_SE_48K 模型..."
        cd studio/clearvoice/checkpoints
        huggingface-cli download --resume-download alibabasglab/MossFormer2_SE_48K --local-dir MossFormer2_SE_48K
        cd ../../..
    else
        echo "MossFormer2_SE_48K 模型已存在"
    fi
    
    # 检查 FRCRN_SE_16K 模型
    if [ ! -d "studio/clearvoice/checkpoints/FRCRN_SE_16K" ] || [ -z "$(ls -A studio/clearvoice/checkpoints/FRCRN_SE_16K 2>/dev/null)" ]; then
        echo "下载 FRCRN_SE_16K 模型..."
        cd studio/clearvoice/checkpoints
        huggingface-cli download --resume-download alibabasglab/FRCRN_SE_16K --local-dir FRCRN_SE_16K
        cd ../../..
    else
        echo "FRCRN_SE_16K 模型已存在"
    fi
    
    # 检查 MossFormerGAN_SE_16K 模型
    if [ ! -d "studio/clearvoice/checkpoints/MossFormerGAN_SE_16K" ] || [ -z "$(ls -A studio/clearvoice/checkpoints/MossFormerGAN_SE_16K 2>/dev/null)" ]; then
        echo "下载 MossFormerGAN_SE_16K 模型..."
        cd studio/clearvoice/checkpoints
        huggingface-cli download --resume-download alibabasglab/MossFormerGAN_SE_16K --local-dir MossFormerGAN_SE_16K
        cd ../../..
    else
        echo "MossFormerGAN_SE_16K 模型已存在"
    fi
}

# 下载模型
check_and_download_models

echo "所有模型检查完成，启动服务..."

# 执行原始命令
exec "$@" 