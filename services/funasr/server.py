from sanic import Sanic, json, response
from sanic.worker.manager import WorkerManager
from functools import partial
import numpy as np
import os
import json as JSON


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
app.config.REQUEST_TIMEOUT = 10000
app.config.REQUEST_MAX_SIZE = 1000_000_000

@app.get("/")
async def welcome(_):
    return json({
        "success": True,
        "message": "欢迎使用 LiberSonora AI服务",
    })


@app.post("/handle")
async def speech_recognition(request):
    if not request.files or 'file' not in request.files:
        return json({
            "code": 400,
            "message": "需要上传音频文件",
            "data": None
        }, status=400)
    
    audio_file = request.files['file'][0]
    hotwords = request.args.get('hotwords', None)
    merge_thr = float(request.args.get('merge_thr', 0.5))
    # 获取是否启用说话人识别参数，默认为False
    spk_conf = request.args.get('spk_conf', 'False').lower() == 'true'
    
    try:
        from io import BytesIO
        from utils.audio import speech_to_text
        
        # 将文件内容转换为BytesIO对象
        audio_data = BytesIO(audio_file.body)
        
        # 调用语音识别函数，传入spk_conf参数
        result = speech_to_text(audio_data, hotwords, merge_thr, spk_conf)
        
        return json({
            "code": 0,
            "message": "识别成功",
            "data": result
        })
            
    except Exception as e:
        return json({
            "code": 500,
            "message": f"处理音频时发生错误: {str(e)}",
            "data": None
        }, status=500)

if __name__ == '__main__':
    cpu_count = int(os.getenv('WORKER_COUNT', '1'))
    print(f"working with {cpu_count} workers")
    app.run(host='0.0.0.0', port=8000, workers=cpu_count)