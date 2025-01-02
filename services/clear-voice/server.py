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
app.config.REQUEST_TIMEOUT = 1000
app.config.REQUEST_MAX_SIZE = 1000_000_000

@app.get("/")
async def welcome(_):
    return json({
        "success": True,
        "message": "欢迎使用 LiberSonora AI 服务",
    })


@app.post("/handle")
async def enhance_audio(request):
    if not request.files or 'file' not in request.files:
        return json({"error": "需要上传音频文件"}, status=400)
    
    # 获取并验证model参数
    model = request.args.get('model', 'MossFormer2_SE_48K')
    if model not in ['MossFormer2_SE_48K', 'FRCRN_SE_16K', 'MossFormerGAN_SE_16K']:
        return json({"error": "无效的模型名称"}, status=400)
        
    audio_file = request.files['file'][0]
    
    try:
        from utils.audio import process_audio
        from io import BytesIO
        
        # 将文件内容转换为BytesIO对象
        audio_bytes = BytesIO(audio_file.body)
        
        # 使用process_audio处理音频
        output_bytes = process_audio(audio_bytes, model)
        
        # 返回处理后的音频
        return response.raw(
            output_bytes.getvalue(),
            content_type='audio/wav',
            headers={'Content-Disposition': 'attachment; filename=enhanced.wav'}
        )
        
    except Exception as e:
        return json({
            "error": f"处理音频时发生错误: {str(e)}"
        }, status=500)

if __name__ == '__main__':
    cpu_count = int(os.getenv('WORKER_COUNT', '1'))
    print(f"working with {cpu_count} workers")
    app.run(host='0.0.0.0', port=8000, workers=cpu_count)