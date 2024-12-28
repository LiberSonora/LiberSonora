import streamlit as st
import requests
from io import BytesIO
import time
import pandas as pd

st.title("音频转字幕服务")

# 上传音频文件
audio_file = st.file_uploader("请选择音频文件", type=['wav', 'mp3'], key='audio')

# 添加热词输入框
hotwords = st.text_input(
    "热词（可选）",
    help="多个热词请用空格分隔",
    value="家人们 感谢"
)

# 添加语音合并阈值输入
merge_thr = st.number_input(
    "语音合并阈值",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.1,
    help="用于合并相同说话人的语音片段，值越大合并越严格"
)

if audio_file is not None:
    # 显示音频播放器
    st.audio(audio_file)
    
    # 开始处理按钮
    if st.button('开始转写'):
        # 显示loading状态
        with st.spinner('正在处理...'):
            # 准备文件数据
            files = {
                'file': audio_file
            }
            
            try:
                # 记录开始时间
                start_time = time.time()
                
                # 调用API
                params = {
                    'merge_thr': merge_thr
                }
                if hotwords:
                    params['hotwords'] = hotwords
                    
                response = requests.post(
                    'http://127.0.0.1:8000/handle',
                    files=files,
                    params=params
                )
                
                # 计算执行时间
                execution_time = time.time() - start_time
                
                # 检查响应状态
                if response.status_code == 200:
                    result = response.json()
                    
                    if result['code'] == 0:
                        # 显示执行时间
                        st.info(f'执行时间: {execution_time:.2f} 秒')
                        
                        # 将结果转换为DataFrame并显示
                        df = pd.DataFrame(result['data'])
                        
                        # 格式化时间戳为秒
                        df['start'] = df['start'].apply(lambda x: f"{x:.2f}ms")
                        df['end'] = df['end'].apply(lambda x: f"{x:.2f}ms")
                        
                        # 重命名列
                        df.columns = ['文本内容', '开始时间', '结束时间', '说话人']
                        
                        # 显示表格
                        st.subheader("识别结果")
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.error(f'处理失败: {result["message"]}')
                else:
                    st.error(f'处理失败: HTTP {response.status_code}')
                    
            except Exception as e:
                st.error(f'发生错误: {str(e)}')
