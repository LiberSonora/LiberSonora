import streamlit as st
from io import BytesIO
import time

st.title("基础测试服务")

# 上传音频文件
audio_file = st.file_uploader("请选择音频文件", type=['wav'], key='audio')
