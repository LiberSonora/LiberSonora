# 定义模型常量
MINICPM3_MODEL = "yefx/minicpm3_4b:latest"
QWEN2_5_MODEL = "qwen2.5:7b-instruct-q4_K_M"
QWEN2_5_14B_MODEL = "qwen2.5:14b-instruct-q4_K_M"

MODEL_CONFIGS = [
    {
        "model": MINICPM3_MODEL,
        "name": "minicpm3-4B-Q4_K_M",
        "comment": "本地运行的轻量模型，运行速度快，对中英文的处理较好",
    },
    {
        "model": QWEN2_5_MODEL,
        "name": "Qwen2.5-7B-Instruct-Q4_K_M",
        "comment": "强大的多语言模型，支持多种任务，性能优异，翻译、纠错效果都更好一点",
    },
    {
        "model": QWEN2_5_14B_MODEL,
        "name": "Qwen2.5-14B-Instruct-Q4_K_M",
        "comment": "更强大的多语言模型，支持多种任务，性能更优但速度较慢，翻译、纠错效果最好",
    }
]
