# 定义模型常量
MINICPM3_MODEL = "yefx/minicpm3_4b:latest"
QWEN2_5_MODEL = "qwen2.5:7b-instruct-q4_K_M"

MODEL_CONFIGS = [
    {
        "model": MINICPM3_MODEL,
        "name": "minicpm3-4B-Q4_K_M",
        "comment": "本地运行的轻量模型，运行速度快，对中英文的处理较好",
    },
    {
        "model": QWEN2_5_MODEL,
        "name": "Qwen2.5-7B-Instruct-Q4_K_M",
        "comment": "强大的多语言模型，支持多种任务，性能优异，翻译效果更好一点",
    }
]
