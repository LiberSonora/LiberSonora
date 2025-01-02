import os
import sys
import asyncio
import streamlit as st
import streamlit_antd_components as sac
import json
from io import BytesIO
import re
import time
import requests
from components.home import step_upload_audio,step_remove_background,step_subtitle_config,step_translate_config,step_correct_config,step_title_config, step_preview_config

async def render_page():
    st.title("有声书批量字幕识别及命名")

    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'config' not in st.session_state:
        st.session_state.config = {}
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

    step_items = [
        sac.StepsItem(title="上传音频", description="批量上传音频文件", disabled=True),
        sac.StepsItem(title="背景音移除", description="选择是否移除背景音乐", disabled=True),
        sac.StepsItem(title="字幕识别", description="配置字幕识别参数", disabled=True),
        sac.StepsItem(title="多语字幕", description="配置多语言翻译", disabled=True),
        sac.StepsItem(title="文本纠错", description="配置文本纠错功能", disabled=True),
        sac.StepsItem(title="标题生成", description="配置标题生成规则", disabled=True),
        sac.StepsItem(title="预览配置", description="确认配置并处理音频", disabled=True)
    ]

    current_step = sac.steps(
        items=step_items,
        index=st.session_state.current_step,
        return_index=True,
        format_func='title',
        variant='default',
        placement='horizontal',
        direction='vertical'
    )

    step_functions = [
        step_upload_audio,
        step_remove_background,
        step_subtitle_config,
        step_translate_config,
        step_correct_config,
        step_title_config,
        step_preview_config
    ]

    st.warning("""
    请注意：
    1. 步骤必须按顺序进行，不能跳跃
    2. 每次重新进入某个步骤时，配置都会恢复默认值
    3. 最终以任务执行前的预览配置为准
    """)

    await step_functions[current_step]()

    # 根据当前步骤决定显示哪些按钮
    if current_step > 0 and current_step < len(step_items) - 1:
        # 中间步骤显示上下步按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("上一步"):
                st.session_state.current_step -= 1
                st.rerun()
        with col2:
            if st.button("下一步"):
                st.session_state.current_step += 1
                st.rerun()
    elif current_step == 0:
        # 第一步只显示下一步按钮
        if st.button("下一步"):
            st.session_state.current_step += 1
            st.rerun()
    else:
        # 最后一步只显示上一步按钮
        if st.button("上一步"):
            st.session_state.current_step -= 1
            st.rerun()

def main():
    asyncio.run(render_page())

if __name__ == "__main__":
    main()
