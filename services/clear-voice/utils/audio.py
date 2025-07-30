import os
import tempfile
from io import BytesIO
import sys

from clearvoice import ClearVoice

def process_audio(audio_bytes: BytesIO, model: str) -> BytesIO:
    """
    处理音频文件并返回处理后的结果
    
    Args:
        audio_bytes: 输入的音频字节流
        model: 使用的模型名称
        
    Returns:
        BytesIO: 处理后的音频字节流
    """
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    input_path = None
    output_path = None
    
    try:
        # 创建临时输入文件
        input_path = os.path.join(temp_dir, "input.wav")
        with open(input_path, 'wb') as f:
            f.write(audio_bytes.getvalue())
            
        # 初始化 ClearVoice
        clear_voice = ClearVoice(
            task='speech_enhancement',
            model_names=[model]
        )
        
        # 处理音频
        output_wav = clear_voice(
            input_path=input_path,
            online_write=False
        )
        
        # 保存到临时输出文件
        output_path = os.path.join(temp_dir, "output.wav")
        clear_voice.write(output_wav, output_path=output_path)
        
        # 读取处理后的文件到BytesIO
        output_bytes = BytesIO()
        with open(output_path, 'rb') as f:
            output_bytes.write(f.read())
        output_bytes.seek(0)
        
        return output_bytes
        
    finally:
        # 清理临时文件
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
        os.rmdir(temp_dir)

