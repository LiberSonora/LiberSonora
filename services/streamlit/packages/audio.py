import aiohttp
import asyncio
from config import global_config
from typing import Optional
import tempfile
import subprocess
import os

def _ms_to_srt_time(ms: int) -> str:
    """
    将毫秒转换为SRT时间格式 (HH:MM:SS,mmm)
    
    Args:
        ms: 毫秒数
        
    Returns:
        str: SRT格式的时间字符串
    """
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    milliseconds = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def _ms_to_lrc_time(ms: int) -> str:
    """
    将毫秒转换为LRC时间格式 [MM:SS.xx]
    
    Args:
        ms: 毫秒数
        
    Returns:
        str: LRC格式的时间字符串
    """
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    hundredths = (ms % 1000) // 10
    return f"[{minutes:02d}:{seconds:02d}.{hundredths:02d}]"

def generate_srt(subtitles: list) -> str:
    """
    根据字幕信息生成SRT格式文本
    
    Args:
        subtitles: 字幕列表，每个元素包含 start, end, text
        
    Returns:
        str: SRT格式的字符串
    """
    srt_content = ""
    for i, sub in enumerate(subtitles):
        start_time = _ms_to_srt_time(sub['start'])
        end_time = _ms_to_srt_time(sub['end'])
        # 处理多行文本
        text = sub['text']
        srt_content += f"{i+1}\n{start_time} --> {end_time}\n{text}\n\n"
    return srt_content

def generate_lrc(subtitles: list) -> str:
    """
    根据字幕信息生成LRC格式文本
    
    Args:
        subtitles: 字幕列表，每个元素包含 start, end, text
        
    Returns:
        str: LRC格式的字符串
    """
    lrc_content = ""
    for sub in subtitles:
        timestamp = _ms_to_lrc_time(sub['start'])
        # 处理多行文本，每行都加上相同的时间戳
        for line in reversed(sub['text'].split('\n')):
            if line.strip():  # 忽略空行
                lrc_content += f"{timestamp}{line}\n"
    return lrc_content



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

async def speech_to_text(audio_bytes: bytes, hotwords: Optional[str] = None, spk_conf: bool = False) -> list:
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
    
    data = {
        "spk_conf": "True" if spk_conf  else "False"
    }
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
            
        # 提取并检查数据
        data = result.get('data', [])
        if not data:
            raise Exception("语音识别结果为空")
        return data
    except Exception as e:
        raise Exception(f"语音识别失败: {str(e)}")

def remove_trailing_punctuation(text: str) -> str:
    """去除字符串末尾的标点符号"""
    punc = '。，、；：！？,.?!;:'
    return text.rstrip(punc)
def remove_trailing_punctuation_list(text_list: list) -> list:
    """去除列表中每个字符串末尾的标点符号
    
    Args:
        text_list: 字符串列表
        
    Returns:
        list: 去除末尾标点后的字符串列表
    """
    return [remove_trailing_punctuation(text) for text in text_list]


def format_speech_results(results: list, text_min_len: int = 5) -> list:
    """
    格式化语音识别结果，确保每句话长度不小于指定值
    
    Args:
        results: 原始识别结果列表，每个元素包含 text, start, end, spk
        text_min_len: 最小文本长度，默认5
        
    Returns:
        list: 格式化后的结果列表
        
    Raises:
        Exception: 当输入结果格式不正确时抛出异常
    """
    
    if not results:
        return []
    
    formatted_results = []
    current_result = None
    
    for item in results:
        # 检查输入格式
        if not all(key in item for key in ['text', 'start', 'end', 'spk']):
            raise Exception("Invalid result format")
            
        text = item['text']
        
        # 如果是第一句或者说话人不同，直接添加
        if current_result is None or current_result['spk'] != item['spk']:
            if current_result is not None:
                # 去除当前结果的句末标点
                current_result['text'] = remove_trailing_punctuation(current_result['text'])
                formatted_results.append(current_result)
            current_result = {
                'text': text,
                'start': item['start'],
                'end': item['end'],
                'spk': item['spk']
            }
        else:
            # 合并文本和时间
            current_result['text'] += f" {text}"
            current_result['end'] = item['end']
            
        # 如果当前结果达到最小长度，添加到最终结果
        if len(current_result['text']) >= text_min_len:
            # 去除当前结果的句末标点
            current_result['text'] = remove_trailing_punctuation(current_result['text'])
            formatted_results.append(current_result)
            current_result = None
    
    # 添加最后一个未处理的结果
    if current_result is not None:
        # 去除当前结果的句末标点
        current_result['text'] = remove_trailing_punctuation(current_result['text'])
        formatted_results.append(current_result)
        
    return formatted_results


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

