import streamlit as st
import requests
from io import BytesIO
import time

st.title("音频增强服务")

# 上传音频文件
audio_file = st.file_uploader("请选择音频文件", type=['wav'], key='audio')

# 选择模型
model = st.selectbox(
    "请选择模型",
    ('MossFormer2_SE_48K', 'FRCRN_SE_16K', 'MossFormerGAN_SE_16K')
)

# 如果上传了音频文件
if audio_file is not None:
    st.subheader("原始音频")
    st.audio(audio_file)
    
    # 增强按钮
    if st.button('开始音频增强'):
        # 显示loading状态
        with st.spinner('正在进行...'):
            # 准备文件数据
            files = {
                'file': audio_file
            }
            
            # 准备参数
            params = {
                'model': model
            }
            
            try:
                # 记录开始时间
                start_time = time.time()
                
                # 调用音频增强API
                response = requests.post('http://127.0.0.1:8000/handle', 
                                      files=files,
                                      params=params)
                
                # 计算执行时间
                execution_time = time.time() - start_time
                
                # 检查响应状态
                if response.status_code == 200:
                    # 将响应内容转换为音频并显示
                    enhanced_audio = BytesIO(response.content)
                    st.info(f'执行时间: {execution_time:.2f} 秒')
                    st.subheader("增强后的音频")
                    st.audio(enhanced_audio)
                else:
                    st.error(f'音频增强失败: HTTP {response.status_code}')
                    
            except Exception as e:
                st.error(f'发生错误: {str(e)}')
