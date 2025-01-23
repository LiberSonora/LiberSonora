# 定义供应商常量
PROVIDER_OLLAMA = "ollama"
PROVIDER_DEEPSEEK = "deepseek"
PROVIDER_OPENAI = "openai"

# 定义供应商配置
PROVIDER_CONFIG = [
    {
        "provider": PROVIDER_OLLAMA,
        "name": "Ollama",
        "comment": "本地运行的轻量级大模型服务，支持多种开源模型，适合本地部署",
        "endpoint": "http://ollama:11434"
    },
    {
        "provider": PROVIDER_DEEPSEEK,
        "name": "DeepSeek",
        "comment": "深度求索提供的API服务，中文处理能力强，性能优异",
        "endpoint": "https://api.deepseek.com"
    },
    {
        "provider": PROVIDER_OPENAI,
        "name": "OpenAI",
        "comment": "全球领先的AI服务提供商，模型性能强大但需要网络连接",
        "endpoint": "https://api.openai.com"
    }
]

def getProvider(provider: str) -> dict:
    """根据供应商名称获取对应的配置信息
    
    参数:
        provider: 供应商名称，可选值为 PROVIDER_OLLAMA, PROVIDER_DEEPSEEK, PROVIDER_OPENAI
    
    返回:
        dict: 包含供应商配置信息的字典
    
    异常:
        ValueError: 当传入的供应商名称无效时抛出
    """
    for config in PROVIDER_CONFIG:
        if config['provider'] == provider:
            return config
    raise ValueError(f"Invalid provider: {provider}. Available providers are: {[p['provider'] for p in PROVIDER_CONFIG]}")



# 定义模型常量
MINICPM3_MODEL = "yefx/minicpm3_4b:latest"
QWEN2_5_MODEL = "qwen2.5:7b-instruct-q4_K_M"
QWEN2_5_14B_MODEL = "qwen2.5:14b-instruct-q4_K_M"

# 定义不同供应商的模型配置
OLLAMA_MODEL_CONFIG = [
    {
        "model": QWEN2_5_MODEL,
        "name": "Qwen2.5-7B-Instruct-Q4_K_M",
        "comment": "强大的多语言模型，支持多种任务，性能优异，翻译、纠错效果都更好一点",
    },
    {
        "model": QWEN2_5_14B_MODEL,
        "name": "Qwen2.5-14B-Instruct-Q4_K_M",
        "comment": "更强大的多语言模型，支持多种任务，性能更优但速度较慢，翻译、纠错效果最好",
    },
    {
        "model": MINICPM3_MODEL,
        "name": "minicpm3-4B-Q4_K_M",
        "comment": "本地运行的轻量模型，运行速度快，对中英文的处理较好",
    },
]

DEEPSEEK_MODEL_CONFIG = [
    {
        "model": "deepseek-chat",
        "name": "DeepSeek Chat",
        "comment": "深度求索的对话模型，适合中文场景",
    },
    {
        "model": "deepseek-r1",
        "name": "DeepSeek R1",
        "comment": "深度求索的 COT 推理模型，质量更好但更慢",
    }
]

OPENAI_MODEL_CONFIG = [
    {
        "model": "gpt-4o",
        "name": "GPT-4O",
        "comment": "OpenAI的最强模型，性能最好但成本较高",
    },
    {
        "model": "gpt-3.5-turbo",
        "name": "GPT-3.5 Turbo",
        "comment": "OpenAI的快速模型，性价比高",
    },
]

def getModelConfig(provider: str):
    """根据供应商获取对应的模型配置
    
    参数:
        provider: 供应商名称，可选值：ollama/deepseek/openai
    
    返回:
        list: 对应的模型配置列表
    
    异常:
        ValueError: 当传入不支持的供应商时抛出
    """
    if provider == PROVIDER_OLLAMA:
        return OLLAMA_MODEL_CONFIG
    elif provider == PROVIDER_DEEPSEEK:
        return DEEPSEEK_MODEL_CONFIG
    elif provider == PROVIDER_OPENAI:
        return OPENAI_MODEL_CONFIG
    else:
        raise ValueError(f"Unsupported provider: {provider}")
