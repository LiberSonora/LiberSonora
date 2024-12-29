from sanic import Sanic, json, response
from sanic.worker.manager import WorkerManager
from functools import partial
import numpy as np
import os
import json as JSON
import tempfile
import zipfile
import logging
import re
import asyncio
from io import BytesIO
from datetime import datetime
from packages.audio import convert_to_wav, enhance_audio, speech_to_text
from packages.text import TextCorrector, TitleGenerator
from packages.translate import OpenAITranslator
from packages.openai import OpenAIHandler

class CustomJSONEncoder(JSON.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.float32):
            return format(float(obj), '.4f')
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, float):
            return format(obj, ".4f")
        return super().default(obj)

import multiprocessing
multiprocessing.set_start_method("spawn", force=True)
Sanic.START_METHOD_SET = True

WorkerManager.THRESHOLD = 400
app = Sanic("LiberSonora", dumps=partial(JSON.dumps, cls=CustomJSONEncoder))
app.config.REQUEST_TIMEOUT = 1000
app.config.REQUEST_MAX_SIZE = 1000000000

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
        audio_bytes = BytesIO(audio_file.body)
        wav_audio = await convert_to_wav(audio_bytes)
        
        # 背景音移除
        if config.get("remove_background", False):
            logger.info("正在进行背景音移除")
            wav_audio = await enhance_audio(wav_audio, model_name="enhance_model")
        
        # 语音转文字
        hotwords = config.get("subtitle", {}).get("hotwords", "")
        subtitles = await speech_to_text(wav_audio, hotwords=hotwords)
        text_lines = [s['text'] for s in subtitles]
        
        # 文本矫正
        if "correct" in config:
            logger.info("正在进行文本矫正")
            openai_config = config["correct"]["openai"]
            openai_handler = OpenAIHandler(
                model=openai_config["model"],
                use_ollama=openai_config["use_ollama"],
                openai_url=openai_config["openai_url"],
                openai_key=openai_config["openai_key"]
            )
            corrector = TextCorrector(openai_handler)
            common_errors = config["correct"].get("common_errors", [])
            text_lines = await corrector.fix_text(text_lines, common_errors)
        
        # 多语言翻译
        if "translate" in config:
            logger.info("正在进行多语言翻译")
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
            translated_lines = await translator.translate(from_lang, to_lang, text_lines)
            text_lines = [f"{orig}\n{trans}" for orig, trans in zip(text_lines, translated_lines)]
        
        # 生成SRT文件
        srt_content = ""
        for i, sub in enumerate(subtitles):
            start = sub['start']
            end = sub['end']
            text = text_lines[i]
            srt_content += f"{i+1}\n{start} --> {end}\n{text}\n\n"
        
        # 标题生成
        title = ""
        if config.get("title", {}).get("generate", False):
            logger.info("正在进行标题生成")
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
                config["title"].get("author", "")
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
                index=index+1,
                title=title,
                book_title=config["title"].get("book_title", ""),
                author=config["title"].get("author", ""),
                *groups
            )
        
        # 保存文件
        audio_path = os.path.join(temp_dir, f"{base_name}{ext}")  # 使用原始文件扩展名
        srt_path = os.path.join(temp_dir, f"{base_name}.srt")
        
        # 处理文件名冲突
        counter = 1
        while os.path.exists(audio_path):
            audio_path = os.path.join(temp_dir, f"{base_name}-{counter}{ext}")
            srt_path = os.path.join(temp_dir, f"{base_name}-{counter}.srt")
            counter += 1
        
        with open(audio_path, "wb") as f:
            f.write(audio_file.body)  # 保存原始音频文件
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        
        logger.info(f"第 {index + 1} 个音频处理完成，耗时 {(datetime.now() - start_time).total_seconds():.2f} 秒")
        return title, srt_content
        
    except Exception as e:
        logger.error(f"处理第 {index + 1} 个音频时发生错误: {str(e)}")
        raise

@app.get("/")
async def welcome(_):
    return json({
        "success": True,
        "message": "欢迎使用 LiberSonora AI 服务",
    })

@app.post("/handle")
async def handle_audio(request):
    """
    config 示例
    {
        "remove_background": true,
        "subtitle": {
            "hotwords": ""
        },
        "correct": {
            "openai": {
                "model": "xxx",
                "use_ollama": true,
                "openai_url": "xxx",
                "openai_key": "xxx"
            },
            "common_errors": [
                {
                    "from": "因改",
                    "to": "应该"
                }
            ]
        },
        "translate": {
            "openai": {
                "model": "xxx",
                "use_ollama": true,
                "openai_url": "xxx",
                "openai_key": "xxx"
            },
            "from": "zh-CN",
            "to": "en"
        },
        "title": {
            "openai": {
                "model": "xxx",
                "use_ollama": true,
                "openai_url": "xxx",
                "openai_key": "xxx"
            },
            "book_title": "",
            "author": "",
            "generate": true,
            "regex_origin": "(\\d*)",
            "rule": "{origin}_{index}_{title}_{0}"
        }
    }
    """
    if not request.files:
        return json({"error": "需要上传音频文件"}, status=400)
    
    try:
        config = JSON.loads(request.form.get("config", "{}"))
    except JSON.JSONDecodeError:
        return json({"error": "配置文件格式错误"}, status=400)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        tasks = []
        for index, audio_file in enumerate(request.files.getlist("files")):
            tasks.append(process_single_audio(index, audio_file, config, temp_dir))
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            return json({"error": f"处理音频时发生错误: {str(e)}"}, status=500)
        
        # 打包文件
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        return response.raw(
            zip_buffer.getvalue(),
            content_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=results.zip"}
        )

if __name__ == '__main__':
    cpu_count = int(os.getenv('WORKER_COUNT', '1'))
    print(f"working with {cpu_count} workers")
    app.run(host='0.0.0.0', port=8000, workers=cpu_count)