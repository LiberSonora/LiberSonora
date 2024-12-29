import aiohttp
import asyncio
from config import global_config
from typing import Optional
import tempfile
import subprocess
import os

async def convert_to_wav(audio_bytes: bytes) -> bytes:
    """
    将输入音频转换为 WAV 格式
    
    Args:
        audio_bytes: 输入音频字节流
        
    Returns:
        bytes: 转换后的 WAV 音频字节流
        
    Raises:
        Exception: 当转换失败时抛出异常
    """
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            with tempfile.NamedTemporaryFile(delete=False) as temp_input:
                # 写入输入音频
                temp_input.write(audio_bytes)
                temp_input.flush()
                
                # 构建 ffmpeg 命令
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-y',  # 覆盖输出文件
                    '-i', temp_input.name,  # 输入文件
                    '-vn',  # 不处理视频
                    '-acodec', 'pcm_s16le',  # PCM 编码
                    '-ar', '48000',  # 采样率
                    '-ac', '1',  # 单声道
                    temp_wav.name  # 输出文件
                ]
                
                # 执行转换
                subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # 读取转换后的音频
                temp_wav.seek(0)
                wav_bytes = temp_wav.read()
                
        # 删除临时文件
        os.unlink(temp_input.name)
        os.unlink(temp_wav.name)
        
        return wav_bytes
    
    except subprocess.CalledProcessError as e:
        raise Exception(f"音频转换失败: {e.stderr.decode('utf-8')}")
    except Exception as e:
        raise Exception(f"音频转换发生错误: {str(e)}")


async def convert_to_mp3(audio_bytes: bytes) -> bytes:
    """将输入音频转换为 MP3 格式
    
    Args:
        audio_bytes: 输入音频字节流
        
    Returns:
        bytes: 转换后的 MP3 音频字节流
        
    Raises:
        Exception: 当转换失败时抛出异常
    """
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_mp3:
            with tempfile.NamedTemporaryFile(delete=False) as temp_input:
                # 写入输入音频
                temp_input.write(audio_bytes)
                temp_input.flush()
                
                # 构建 ffmpeg 命令
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-y',  # 覆盖输出文件
                    '-i', temp_input.name,  # 输入文件
                    '-vn',  # 不处理视频
                    '-acodec', 'libmp3lame',  # MP3 编码
                    '-b:a', '192k',  # 比特率
                    '-ar', '48000',  # 采样率
                    '-ac', '1',  # 单声道
                    temp_mp3.name  # 输出文件
                ]
                
                # 执行转换
                subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # 读取转换后的音频
                temp_mp3.seek(0)
                mp3_bytes = temp_mp3.read()
                
        # 删除临时文件
        os.unlink(temp_input.name)
        os.unlink(temp_mp3.name)
        
        return mp3_bytes
    
    except subprocess.CalledProcessError as e:
        raise Exception(f"音频转换失败: {e.stderr.decode('utf-8')}")
    except Exception as e:
        raise Exception(f"音频转换发生错误: {str(e)}")


async def _request_with_retry(url: str, data: dict, files: dict, retries: int = 3) -> dict:
    """
    带重试功能的请求函数
    
    Args:
        url: 请求URL
        data: 表单数据
        files: 文件数据
        retries: 重试次数
        
    Returns:
        dict: 响应结果
        
    Raises:
        Exception: 当请求失败时抛出异常
    """
    for i in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                form_data = aiohttp.FormData()
                for key, value in data.items():
                    form_data.add_field(key, value)
                form_data.add_field('file', files['file'], filename='audio.wav')
                
                async with session.post(url, data=form_data, timeout=360) as response:
                    if response.status != 200:
                        raise Exception(f"请求失败，状态码: {response.status}")
                    return await response.json()
        except Exception as e:
            if i == retries - 1:
                raise Exception(f"请求失败，重试次数已达上限: {str(e)}")
            await asyncio.sleep(1 * (i + 1))  # 指数退避

async def speech_to_text(audio_bytes: bytes, hotwords: Optional[str] = None) -> list:
    """
    将语音文件转换为文字，返回带时间戳的文本列表
    
    Args:
        audio_bytes: 音频文件字节流
        hotwords: 热词，用空格分隔的字符串
        
    Returns:
        list: 包含 [start_time, end_time, text] 的列表
        
    Raises:
        Exception: 当服务器返回错误或响应格式不正确时抛出异常
    """
    url = global_config.funasr_url + "/handle"
    
    data = {}
    if hotwords:
        data['hotwords'] = hotwords
        
    files = {
        'file': audio_bytes
    }
    
    try:
        result = await _request_with_retry(url, data, files)
        
        # 检查响应状态
        if result.get('code') != 0:
            raise Exception(f"语音识别失败: {result.get('message')}")
            
        # 提取并返回数据
        return result.get('data', [])
    except Exception as e:
        raise Exception(f"语音识别失败: {str(e)}")

async def enhance_audio(audio_bytes: bytes, model_name: str) -> bytes:
    """
    使用指定模型增强音频文件
    
    Args:
        audio_bytes: 音频文件字节流
        model_name: 模型名称，如 'MossFormer2_SE_48K', 'FRCRN_SE_16K', 'MossFormerGAN_SE_16K'
        
    Returns:
        bytes: 增强后的音频文件流
        
    Raises:
        Exception: 当服务器返回非200状态码时抛出异常
    """
    url = global_config.clear_voice_url + "/handle"

    data = {
        'model': model_name
    }
    files = {
        'file': audio_bytes
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            form_data.add_field('model', model_name)
            form_data.add_field('file', audio_bytes, filename='audio.wav')
            
            async with session.post(url, data=form_data, timeout=360) as response:
                if response.status != 200:
                    raise Exception(f"增强音频失败: {await response.text()}")
                return await response.read()
    except Exception as e:
        raise Exception(f"增强音频失败: {str(e)}")
