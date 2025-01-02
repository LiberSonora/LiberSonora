from functools import partial
import numpy as np
import os
import json
import tempfile
import logging
import re
import asyncio
from io import BytesIO
from datetime import datetime
from packages.audio import convert_to_wav, enhance_audio, speech_to_text, format_speech_results, remove_trailing_punctuation_list, generate_srt, generate_lrc
from packages.text import TextCorrector, TitleGenerator
from packages.translate import OpenAITranslator
from packages.openai import OpenAIHandler
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_single_audio(index, audio_file, config, temp_dir):
    start_time = datetime.now()
    logger.info(f"开始处理第 {index + 1} 个音频文件")
    
    try:
        # 获取文件名和扩展名
        filename = audio_file.name
        base_name, ext = os.path.splitext(filename)
        
        # 转换音频格式
        convert_start = datetime.now()
        logger.info(f"音频格式转换完成，耗时 {(datetime.now() - convert_start).total_seconds():.2f} 秒")
        
        # 背景音移除
        if config.get("remove_background", False):
            logger.info("正在进行背景音移除")
            wav_audio = await convert_to_wav(audio_file.body)
            enhance_start = datetime.now()
            wav_audio = await enhance_audio(wav_audio, model_name="enhance_model")
            logger.info(f"背景音移除完成，耗时 {(datetime.now() - enhance_start).total_seconds():.2f} 秒")
        
        # 语音转文字
        stt_start = datetime.now()
        hotwords = config.get("subtitle", {}).get("hotwords", "")
        subtitles = format_speech_results(await speech_to_text(audio_file.body, hotwords=hotwords))
        text_lines = [s['text'] for s in subtitles]
        logger.info(f"语音转文字完成，耗时 {(datetime.now() - stt_start).total_seconds():.2f} 秒")
        
        # 文本矫正
        if "correct" in config and config["correct"]:
            logger.info("正在进行文本矫正")
            correct_start = datetime.now()
            openai_config = config["correct"]["openai"]
            openai_handler = OpenAIHandler(
                model=openai_config["model"],
                use_ollama=openai_config["use_ollama"],
                openai_url=openai_config["openai_url"],
                openai_key=openai_config["openai_key"]
            )
            corrector = TextCorrector(openai_handler)
            common_errors = config["correct"].get("common_errors", [])
            text_lines = remove_trailing_punctuation_list(await corrector.fix_text(text_lines, common_errors))
            logger.info(f"文本矫正完成，耗时 {(datetime.now() - correct_start).total_seconds():.2f} 秒")
        
        # 标题生成
        title = "未生成"
        if config.get("title", {}).get("generate", False):
            logger.info("正在进行标题生成")
            title_start = datetime.now()
            openai_config = config["title"]["openai"]
            openai_handler = OpenAIHandler(
                model=openai_config["model"],
                use_ollama=openai_config["use_ollama"],
                openai_url=openai_config["openai_url"],
                openai_key=openai_config["openai_key"]
            )
            title_generator = TitleGenerator(
                openai_handler,
                config["title"].get("book_title", ""),
                config["title"].get("author", ""),
                config["title"].get("lang", "")
            )
            title = await title_generator.generate_title("\n".join(text_lines))
            
            # 应用标题生成规则
            regex_origin = config["title"].get("regex_origin", "(\\d*)")
            match = re.search(regex_origin, base_name)
            groups = match.groups() if match else []
            # {origin}_{index}_{title}_{book_title}_{author}_{0/1/2/...}，中 origin 表示原始音频名称，index 是索引+1，title 是新生成的 title（如果不需要生成标题则为空），book_title 是书名，author 是作者，{0/1/2/...} 是 regex_origin 中提取的数据，regex_origin 是从原始文件名中提取数据的正则表达式
            rule = config["title"].get("rule", "{origin}")
            base_name = rule.format(
                origin=base_name,
                index=str(index+1).zfill(3),
                title=title,
                book_title=config["title"].get("book_title", ""),
                author=config["title"].get("author", ""),
                *groups
            )
            logger.info(f"标题生成完成，耗时 {(datetime.now() - title_start).total_seconds():.2f} 秒")
        
        # 多语言翻译
        if "translate" in config and config['translate']:
            logger.info("正在进行多语言翻译")
            translate_start = datetime.now()
            openai_config = config["translate"]["openai"]
            openai_handler = OpenAIHandler(
                model=openai_config["model"],
                use_ollama=openai_config["use_ollama"],
                openai_url=openai_config["openai_url"],
                openai_key=openai_config["openai_key"]
            )
            translator = OpenAITranslator(openai_handler)
            from_lang = config["translate"]["from"]
            to_lang = config["translate"]["to"]
            translated_lines = remove_trailing_punctuation_list(await translator.translate(from_lang, to_lang, text_lines))
            text_lines = [f"{orig}\n{trans}" for orig, trans in zip(text_lines, translated_lines)]
            logger.info(f"多语言翻译完成，耗时 {(datetime.now() - translate_start).total_seconds():.2f} 秒")
        
        # 生成SRT和LRC文件
        srt_start = datetime.now()
        # 将处理后的文本更新到字幕信息中
        for i, sub in enumerate(subtitles):
            sub['text'] = text_lines[i]
        # 生成SRT内容
        srt_content = generate_srt(subtitles)
        # 生成LRC内容
        lrc_content = generate_lrc(subtitles)
        logger.info(f"字幕文件生成完成，耗时 {(datetime.now() - srt_start).total_seconds():.2f} 秒")

        # 保存文件
        save_start = datetime.now()
        audio_path = os.path.join(temp_dir, f"{base_name}{ext}")  # 使用原始文件扩展名
        srt_path = os.path.join(temp_dir, f"{base_name}.srt")
        lrc_path = os.path.join(temp_dir, f"{base_name}.lrc")
        
        # 处理文件名冲突
        counter = 1
        while os.path.exists(audio_path):
            audio_path = os.path.join(temp_dir, f"{base_name}-{counter}{ext}")
            srt_path = os.path.join(temp_dir, f"{base_name}-{counter}.srt")
            lrc_path = os.path.join(temp_dir, f"{base_name}-{counter}.lrc")
            counter += 1
        
        with open(audio_path, "wb") as f:
            f.write(audio_file.body)  # 保存原始音频文件
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        with open(lrc_path, "w", encoding="utf-8") as f:
            f.write(lrc_content)
        logger.info(f"文件保存完成，耗时 {(datetime.now() - save_start).total_seconds():.2f} 秒")
        
        logger.info(f"第 {index + 1} 个音频处理完成，总耗时 {(datetime.now() - start_time).total_seconds():.2f} 秒")
        return audio_path
        
    except Exception as e:
        import traceback
        logger.error(f"处理第 {index + 1} 个音频时发生错误: {str(e)}")
        logger.error(f"错误堆栈信息: {traceback.format_exc()}")
        raise e

async def process_audio_batch_backround(input_dir: str, output_dir: str, config: dict, audio_files: list):
    """异步批量处理音频文件
    
    参数:
        input_dir: 输入目录路径
        output_dir: 输出目录路径
        config: 配置字典
        audio_files: 需要处理的音频文件列表
    """
    try:
        # 生成唯一ID
        config_id = str(uuid.uuid4())
        
        # 创建临时配置文件路径
        config_path = f"/tmp/config_{config_id}.json"
        files_path = f"/tmp/files_{config_id}.json"
        
        # 将配置写入临时文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 将音频文件列表写入临时文件
        with open(files_path, 'w', encoding='utf-8') as f:
            json.dump(audio_files, f, ensure_ascii=False, indent=2)
        
        # 构造nohup命令
        command = f"nohup python3 scripts/convert.py --config=\"{config_path}\" --input-dir=\"{input_dir}\" --output-dir=\"{output_dir}\" --audio-files=\"{files_path}\" > /dev/null 2>&1 &"

        logger.info(f"运行命令：{command}")
        
        # 执行命令
        import subprocess
        process = subprocess.Popen(command, shell=True)
        
        # 等待进程启动
        await asyncio.sleep(1)
        
        # 检查进程是否在运行
        if process.poll() is None:
            logger.info(f"成功启动后台处理进程，PID: {process.pid}")
            logger.info(f"配置文件已保存至: {config_path}")
            logger.info(f"音频文件列表已保存至: {files_path}")
            return True
        else:
            logger.error("后台处理进程启动失败")
            return False
            
    except Exception as e:
        logger.error(f"启动后台处理进程时发生错误: {str(e)}")
        raise e

def check_offline_task_output(output_dir: str) -> list:
    """检查离线输出目录中的音频文件及其字幕文件
    
    参数:
        output_dir: 输出目录路径
        
    返回:
        包含音频文件信息的列表，每个元素为字典，包含：
        - audio_path: 音频文件绝对路径
        - srt_path: srt字幕文件绝对路径
        - lrc_path: lrc字幕文件绝对路径  
        - relative_path: 音频文件相对路径
        - has_srt: srt文件是否存在
        - has_lrc: lrc文件是否存在
    """
    import os
    from glob import glob
    
    # 支持的音频文件扩展名
    audio_extensions = ['mp3', 'wav', 'pem']
    
    # 查找所有音频文件
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(glob(os.path.join(output_dir, '**', f'*.{ext}'), recursive=True))
    
    result = []
    for audio_path in audio_files:
        # 获取相对路径
        relative_path = os.path.relpath(audio_path, output_dir)
        
        # 获取文件名（不含扩展名）
        base_name = os.path.splitext(audio_path)[0]
        
        # 检查字幕文件
        srt_path = f"{base_name}.srt"
        lrc_path = f"{base_name}.lrc"
        
        result.append({
            'audio_path': audio_path,
            'srt_path': srt_path,
            'lrc_path': lrc_path,
            'relative_path': relative_path,
            'has_srt': os.path.exists(srt_path),
            'has_lrc': os.path.exists(lrc_path)
        })
    
    # 按照relative_path进行排序
    result.sort(key=lambda x: x['relative_path'])
    
    return result

async def ai_rename_files(openai_config, book_title, author, lang, audio_path, lrc_path, srt_path):
    """使用AI对已生成的文件进行重命名
    
    参数:
        openai_config: OpenAI配置
        book_title: 书名
        author: 作者
        lang: 语言
        audio_path: 音频文件路径
        lrc_path: lrc字幕文件路径
        srt_path: srt字幕文件路径
        
    返回:
        新生成的标题
    """
    try:
        # 读取lrc文件内容并移除字幕格式
        if os.path.exists(lrc_path):
            with open(lrc_path, 'r', encoding='utf-8') as f:
                lrc_content = f.read()
                # 移除时间戳，保留文本内容
                text_lines = [line.split(']')[-1].strip() for line in lrc_content.split('\n') if line.strip()]
        else:
            raise FileNotFoundError("LRC file not found")

        # print("text_lines", text_lines)

        # 初始化OpenAI处理器
        openai_handler = OpenAIHandler(
            model=openai_config["model"],
            use_ollama=openai_config["use_ollama"],
            openai_url=openai_config["openai_url"],
            openai_key=openai_config["openai_key"]
        )

        # 创建标题生成器并生成标题
        title_generator = TitleGenerator(
            openai_handler,
            book_title,
            author,
            lang
        )
        title = await title_generator.generate_title("\n".join(text_lines))
        
        return title

    except Exception as e:
        raise Exception(f"AI rename failed: {str(e)}")



def get_audio_files(directory):
    """获取目录中的所有音频文件"""
    audio_files = []
    if directory and os.path.exists(directory):
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.mp3', '.wav', '.pcm')):
                    file_path = os.path.join(root, file)
                    audio_files.append(file_path)
        # 按文件名正序排序
        audio_files.sort(key=lambda x: os.path.basename(x).lower())
    return audio_files