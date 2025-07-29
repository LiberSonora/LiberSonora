# LiberSonora 变更日志

## 2024-12-19 更新

### 新增功能
1. **标题生成流程优化**
   - 新增"不做标题重命名"选项，默认选中
   - 选中后不渲染标题重命名相关的表单
   - 处理时不拷贝音频文件，只生成字幕文件
   - 提高处理效率，减少存储空间占用

### 技术改进
1. **Docker化部署**
   - 使用Python基础镜像替代conda环境
   - 创建Dockerfile简化部署流程
   - 更新docker-compose配置支持新的Dockerfile
   - 添加requirements.txt管理Python依赖

2. **默认模型配置**
   - 将默认大模型配置改为DeepSeek Chat
   - 优化中文处理能力
   - 提升标题生成和翻译质量

### 文件变更
- `services/streamlit/components/home.py`: 添加"不做标题重命名"选项
- `services/streamlit/packages/process.py`: 修改处理逻辑，支持跳过音频文件拷贝
- `services/streamlit/packages/llm.py`: 更新DeepSeek模型配置
- `services/streamlit/components/form.py`: 修改默认供应商为DeepSeek
- `services/streamlit/Dockerfile`: 新增Python基础镜像Dockerfile
- `services/streamlit/requirements.txt`: 新增Python依赖管理
- `services/streamlit/main.py`: 优化Docker环境下的启动逻辑
- `docker-compose.gpu.yml`: 更新使用新的Dockerfile

### 使用说明
1. **标题重命名功能**
   - 默认选中"不做标题重命名"
   - 如需标题重命名，请取消勾选该选项
   - 选中时只生成字幕文件，不拷贝音频文件

2. **Docker部署**
   ```bash
   docker-compose -f docker-compose.gpu.yml up --build
   ```

3. **默认模型**
   - 系统默认使用DeepSeek Chat模型
   - 如需使用其他模型，可在配置中手动选择 