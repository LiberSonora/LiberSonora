# Clear-Voice Docker 化说明

## 概述

clear-voice 服务已经完成了基于 Python 基础镜像的 Docker 化改造，不再依赖 conda 环境。

## 主要改动

### 1. 基础镜像
- **之前**: `condaforge/miniforge3:24.9.2-0`
- **现在**: `python:3.8-slim`

### 2. 依赖管理
- **之前**: 使用 `environment.yml` 和 conda 环境
- **现在**: 使用 `requirements.txt` 和 pip

### 3. 模型下载
- **之前**: 在 `start.sh` 中运行时下载
- **现在**: 在容器启动时通过 `docker-entrypoint.sh` 检查并下载

## 文件结构

```
services/clear-voice/
├── Dockerfile              # Docker 构建文件
├── requirements.txt        # Python 依赖
├── docker-entrypoint.sh   # 容器启动脚本
├── .dockerignore          # Docker 忽略文件
├── main.py               # 主程序
├── server.py             # API 服务
├── ui.py                 # Streamlit UI
├── utils/                # 工具模块
└── studio/               # ClearerVoice-Studio 代码
```

## 使用方法

### 1. 构建镜像
```bash
cd services/clear-voice
docker build -t clear-voice .
```

### 2. 使用 docker-compose
```bash
# 在项目根目录
docker-compose -f docker-compose.gpu.yml up clear-voice
```

### 3. 直接运行容器
```bash
docker run -d \
  --name clear-voice \
  --gpus all \
  -p 8502:8501 \
  -p 8503:8000 \
  -v /mnt/data:/mnt/data \
  -v ./services/clear-voice/.cache/:/root/.cache/ \
  clear-voice
```

## 服务访问

- **UI 界面**: http://localhost:8502
- **API 接口**: http://localhost:8503

## 环境变量

- `WORKER_COUNT`: 工作进程数量 (默认: 1)
- `HF_ENDPOINT`: HuggingFace 镜像地址 (默认: https://hf-mirror.com)

## 模型文件

模型文件会在容器首次启动时自动下载到以下目录：
- `studio/clearvoice/checkpoints/MossFormer2_SE_48K/`
- `studio/clearvoice/checkpoints/FRCRN_SE_16K/`
- `studio/clearvoice/checkpoints/MossFormerGAN_SE_16K/`

模型缓存会保存在 `./services/clear-voice/.cache/` 目录中。

## 注意事项

1. **首次启动**: 首次启动时需要下载模型文件，可能需要较长时间
2. **GPU 支持**: 需要 NVIDIA Docker 运行时支持
3. **内存要求**: 建议至少 8GB 内存
4. **存储空间**: 模型文件大约需要 2-3GB 存储空间

## 故障排除

### 1. 模型下载失败
检查网络连接和 HuggingFace 镜像地址：
```bash
docker logs clear-voice
```

### 2. GPU 不可用
确保安装了 NVIDIA Docker 运行时：
```bash
nvidia-docker run --rm nvidia/cuda:11.0-base nvidia-smi
```

### 3. 端口冲突
修改 docker-compose.gpu.yml 中的端口映射：
```yaml
ports:
  - 8504:8501 # 修改为其他端口
  - 8505:8000
``` 