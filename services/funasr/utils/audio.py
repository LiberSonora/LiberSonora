from funasr import AutoModel
import torch
import tempfile
import os
from io import BytesIO

# 初始化模型
model_config = {
    # 主模型是语音识别检测
    "model": "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
    # vad 是语音检测，有效语音的起止时间
    "vad_model": "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
    # punc 是加标点的
    "punc_model": "iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
    "disable_log": True,
    "disable_pbar": True,
    "disable_update": True
}

# 如果 CUDA 可用，添加说话人检测模型
if torch.cuda.is_available():
    model_config["spk_model"] = "iic/speech_campplus_sv_zh-cn_16k-common"

model = AutoModel(**model_config)

def speech_to_text(audio_file: BytesIO, hotwords: str = None, merge_thr: float = 0.5) -> list:
    """
    将语音文件转换为文字，返回带时间戳的文本列表
    
    Args:
        audio_file: 音频文件的二进制数据流
        hotwords: 热词，用空格分隔的字符串
        merge_thr: 说话人聚类的阈值，默认0.5
        
    Returns:
        list: 包含 [start_time, end_time, text] 的列表
    """
    
    # 创建临时文件保存音频数据
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
        temp_audio.write(audio_file.getvalue())
        temp_path = temp_audio.name
    
    try:
        # 生成识别结果
        res = model.generate(
            input=temp_path,
            sentence_timestamp=True,
            hotword=hotwords,
            spk_kwargs={"cb_kwargs": {"merge_thr": merge_thr}}
        )

        # 直接提取句子信息并格式化为JSON结果
        return [{
            "text": sentence["text"],
            "start": sentence["start"], 
            "end": sentence["end"],
            "spk": sentence.get("spk", 0)
        } for sentence in res[0]["sentence_info"]]
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)