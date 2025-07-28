![LiberSonora Logo](./assets/logo.jpg)


LiberSonora，寓意“自由的声音”，是一个 AI 赋能的、强大的、开源有声书工具集，包含智能字幕提取、AI标题生成、多语言翻译等功能，支持 GPU 加速、批量离线处理

> 使用 Deepseek + Cursor 开发 ❤

## 🌟 项目亮点

📚 **开源自由**
- 采用 MIT 许可证，真正的开源免费
- 音频处理与大模型推理全程本地离线运行
- 自主可控，数据安全有保障

🚀 **便捷部署**
- 项目容器化，开发与部署便利
- 支持 API，轻松集成到个人工作流

🧩 **模块化设计**
- 各功能模块独立
- 可单独启动特定服务（如音频增强、字幕识别等）

🔧 **灵活定制**
- 支持自定义大模型，针对特定任务提升效果
- 配置灵活多样，满足不同需求

💡 **创新功能**
- 持续更新，引入最新AI技术
- 提供独特的音频处理与文本生成能力

# 🚀 LiberSonora 发展规划

项目的愿景是打造一个全方位的有声书生态系统，目前仅实现智能字幕提取、标题生成与多语言支持，后续会逐步实现更多功能：

## 🎯 第一期：智能字幕提取、标题生成与多语言支持（已完成）

🎯 解决的核心问题：
- 📁 智能重命名：摆脱"第001集_xxxx.mp3"、"Chapter_001.mp3"等无意义命名，轻松找到感兴趣的内容
- 📄 自动字幕生成：为无字幕音频添加精准字幕，实现文字内容快速定位
- 🗣️ 多语言学习辅助：借助大模型翻译，提供多语言字幕，助力语言学习

✨ 功能：
- 🎙️ 有声书音频字幕提取
- 🏷️ AI 智能命名工具
- 🌐 AI 驱动的多语言翻译
- 🇬🇧 英语有声书全面支持
- 🧠 子任务维度灵活的大模型配置
- 🏠 项目官网搭建

> 💖 如果您喜欢这个项目，欢迎赞助支持我们的开发！
> ![赞助二维码](./assets/rewardcode.png)


## 功能列表

- [x] 有声音频批量处理
- [x] 移除背景音
- [x] 本地大模型进行字幕矫正
- [x] 本地大模型生成双语字幕
- [x] 本地大模型生成标题生成
- [x] 自动标点移除
- [x] 支持灵活的批量重命名
- [x] API 支持
- [x] 超过 3h 的音频转换支持
- [ ] 提供云服务
- [ ] 国际化接轨，实现英文界面和英文 README
- [ ] CPU 可运行（低优先级，可能不做，由于 clear-voice 和 funasr 项目依赖原因，现在只能用带 nvidia GPU 的环境运行）

### 字幕转换和重命名结果示例下载

> 有声书资源均来自互联网，仅供效果参考和学习，若有侵犯著作权利请联系我删除

> 若想转换你正在听的有声书，但又不想搭建环境，可以到 [📚有声书转换体验区](https://github.com/LiberSonora/LiberSonora/discussions/1) 留言

| 书名 | 下载链接 | 提取码 | 备注 |
|------|----------|--------|------|
| 《资本论.马克思》 | https://pan.quark.cn/s/7d2e048b0747 | uhjP | 经典政治经济学著作，中文 |
| 《苦难辉煌.金一南》 | https://pan.quark.cn/s/b37fd2be9d50 | Mhud | 现代历史题材作品，中文 |
| 《毛泽东选集》 | https://pan.quark.cn/s/db5d332ca110 | 1Vvr | 中文 |
| 《Alice's Adventures in Wonderland.Lewis Carroll》 | https://pan.quark.cn/s/2699b5b63abc | FNx8 | 爱丽丝梦游仙境，源语言英语+标题英语+字幕自动翻译中文 |
| 《Romeo and Juliet.William Shakespeare》 | https://pan.quark.cn/s/27cb7de6f7ce | pjJ9 | 罗密欧与朱丽叶，源语言英语+标题英语+字幕自动翻译中文 |

## 开源项目

| 项目名称 | 项目地址 | 用途 |
|----------|----------|------|
| ClearerVoice-Studio | https://github.com/modelscope/ClearerVoice-Studio | 移除背景音 |
| FFmpeg | https://github.com/FFmpeg/FFmpeg | 音频转码 |
| FunASR | https://github.com/modelscope/FunASR | 字幕提取 |
| Ollama | https://github.com/ollama/ollama | 大模型推理 |
| Qwen2.5 | https://github.com/QwenLM/Qwen2.5 | 大模型推理 |
| MiniCPM | https://github.com/OpenBMB/MiniCPM | 大模型推理 |
| Sanic | https://github.com/sanic-org/sanic | 对外暴露 API 接口 |
| Streamlit | https://github.com/streamlit/streamlit | 页面交互 |
| StreamlitAntdComponents | https://github.com/nicedouble/StreamlitAntdComponents | 页面交互，实现步骤条 |


## 问题反馈

如果您在使用过程中遇到任何问题或有改进建议，欢迎通过以下方式反馈：

1. 在 GitHub 上提交 Issue：
   - 访问我们的 [GitHub Issues 页面](https://github.com/LiberSonora/LiberSonora/issues)
   - 点击 "New Issue" 按钮
   - 选择适当的 issue 模板（如果有）
   - 详细描述您遇到的问题或建议

我们会认真查看每一个 issue，并尽快回复。

## 开源许可

本项目采用 [MIT 许可证](https://opensource.org/licenses/MIT)。

您可以在项目根目录的 `LICENSE` 文件中查看完整的许可证文本。
