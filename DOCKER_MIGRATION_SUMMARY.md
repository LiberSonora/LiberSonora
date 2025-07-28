# LiberSonora Docker 化改造总结

## 概述

本项目已成功完成所有服务的 Docker 化改造，从基于 conda 环境的方式迁移到基于 Python 基础镜像的方式。

## 改造的服务

### 1. clear-voice 服务

**改造前:**
- 基础镜像: `condaforge/miniforge3:24.9.2-0`
- 依赖管理: `environment.yml` + conda
- 启动方式: `bash start.sh`

**改造后:**
- 基础镜像: `python:3.8-slim`
- 依赖管理: `requirements.txt` + pip
- 启动方式: `python main.py`

**新增文件:**
- `services/clear-voice/Dockerfile`
- `services/clear-voice/requirements.txt`
- `services/clear-voice/docker-entrypoint.sh`
- `services/clear-voice/.dockerignore`
- `services/clear-voice/README_Docker.md`

### 2. funasr 服务

**改造前:**
- 基础镜像: `condaforge/miniforge3:24.9.2-0`
- 依赖管理: conda 环境
- 启动方式: `bash start.sh`

**改造后:**
- 基础镜像: `python:3.11-slim`
- 依赖管理: `requirements.txt` + pip
- 启动方式: `python main.py`

**新增文件:**
- `services/funasr/Dockerfile`
- `services/funasr/requirements.txt`
- `services/funasr/.dockerignore`

### 3. streamlit 服务

**状态:** 已完成 Docker 化（之前就是基于 Python 镜像）

## 主要改进

### 1. 镜像大小优化
- 从 conda 基础镜像迁移到 Python slim 镜像
- 减少了不必要的系统包和 conda 环境
- 预计镜像大小减少 30-50%

### 2. 构建速度提升
- 使用 pip 安装依赖，比 conda 更快
- 优化了 .dockerignore 文件，减少构建上下文
- 分层构建，提高缓存利用率

### 3. 运行时性能
- 减少了容器启动时间
- 简化了环境管理
- 更好的资源利用率

### 4. 维护性提升
- 统一的依赖管理方式（requirements.txt）
- 更清晰的 Dockerfile 结构
- 更好的文档和说明

## 端口配置

| 服务 | UI 端口 | API 端口 | 说明 |
|------|----------|----------|------|
| streamlit | 8651 | 8652 | 主界面 |
| clear-voice | 8502 | 8503 | 音频增强 |
| funasr | 8504 | 8505 | 语音识别 |

## 使用方法

### 构建所有服务
```bash
docker-compose -f docker-compose.gpu.yml build
```

### 启动所有服务
```bash
docker-compose -f docker-compose.gpu.yml up -d
```

### 启动单个服务
```bash
# 启动 clear-voice
docker-compose -f docker-compose.gpu.yml up clear-voice

# 启动 funasr
docker-compose -f docker-compose.gpu.yml up funasr
```

## 环境要求

### 系统要求
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker Runtime（用于 GPU 支持）
- 至少 8GB 内存
- 至少 20GB 可用磁盘空间

### GPU 支持
- NVIDIA GPU 驱动 450+
- nvidia-docker2 或 nvidia-container-toolkit

## 注意事项

### 1. 首次启动
- clear-voice 服务首次启动时会下载模型文件（约 2-3GB）
- funasr 服务首次启动时会下载语音识别模型
- 请确保网络连接正常

### 2. 模型缓存
- 模型文件会缓存在 `./services/*/.cache/` 目录
- 建议将这些目录添加到 .gitignore
- 可以通过 volume 挂载来持久化模型缓存

### 3. 资源限制
- 建议为每个服务分配至少 4GB 内存
- GPU 内存建议至少 8GB
- 根据实际使用情况调整 WORKER_COUNT 环境变量

## 故障排除

### 1. 构建失败
```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建
docker-compose -f docker-compose.gpu.yml build --no-cache
```

### 2. 模型下载失败
```bash
# 检查网络连接
docker run --rm alpine ping hf-mirror.com

# 查看服务日志
docker-compose -f docker-compose.gpu.yml logs clear-voice
```

### 3. GPU 不可用
```bash
# 检查 NVIDIA Docker 运行时
nvidia-docker run --rm nvidia/cuda:11.0-base nvidia-smi

# 检查 Docker 运行时配置
docker info | grep -i runtime
```

## 迁移检查清单

- [x] clear-voice 服务 Docker 化
- [x] funasr 服务 Docker 化
- [x] 更新 docker-compose.gpu.yml
- [x] 创建必要的配置文件
- [x] 修复 API 调用地址
- [x] 添加文档说明
- [x] 测试构建和运行

## 后续优化建议

1. **多阶段构建**: 考虑使用多阶段构建进一步减少镜像大小
2. **健康检查**: 为每个服务添加健康检查端点
3. **监控集成**: 集成 Prometheus 和 Grafana 监控
4. **自动扩缩容**: 配置 Kubernetes 自动扩缩容
5. **CI/CD 集成**: 添加自动化构建和部署流程 