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
from packages.audio import convert_to_wav, enhance_audio, speech_to_text, format_speech_results, remove_trailing_punctuation_list, generate_srt, generate_lrc
from packages.text import TextCorrector, TitleGenerator
from packages.translate import OpenAITranslator
from packages.openai import OpenAIHandler
from packages.process import process_single_audio

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
app.config.RESPONSE_TIMEOUT = 1000
app.config.REQUEST_MAX_SIZE = 1000000000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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