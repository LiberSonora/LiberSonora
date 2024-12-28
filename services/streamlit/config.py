import os

class Config:
    def __init__(self):
        self.clear_voice_url = os.getenv('CLEAR_VOICE_URL', 'http://clear-voice:8000')
        self.funasr_url = os.getenv('FUNASR_URL', 'http://funasr:8000')

# 创建配置实例
global_config = Config()
