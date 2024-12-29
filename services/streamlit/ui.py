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
from components.form import model_selection, select_translate_languages, get_text_correct_common_errors
from packages.llm import QWEN2_5_MODEL, MINICPM3_MODEL

async def step_upload_audio():
    st.subheader("上传音频文件")
    uploaded_files = st.file_uploader("请选择音频文件", type=['mp3', 'wav', 'pcm'],
                                    accept_multiple_files=True)
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
    if st.session_state.uploaded_files:
        # 展示已上传文件信息
        st.info(f"已成功上传 {len(uploaded_files)} 个文件（重新进入步骤会清空）：")
        for i, file in enumerate(uploaded_files, 1):
            st.write(f"{i}. {file.name} ({round(file.size/1024/1024, 2)} MB)")

async def step_remove_background():
    st.subheader("背景音移除配置")
    remove_background = st.checkbox("移除背景音乐", value=False,
                                  help="选择后会增加处理时间，但可以提高语音识别质量，如果你的音频不带背景音或背景音很轻微，请勿选择")
    st.session_state.config['remove_background'] = remove_background

async def step_subtitle_config():
    st.subheader("字幕识别配置")
    hotwords = st.text_input("请输入热词（可选，多个词用空格分隔）", value="",
                           help="输入特定词汇可以提高识别准确率")
    st.session_state.config['subtitle'] = {'hotwords': hotwords}

async def step_translate_config():
    st.subheader("多语言字幕生成")
    enable_translate = st.checkbox("启用多语言字幕翻译", value=False)
    if enable_translate:
        from_lang, to_lang = select_translate_languages()
        openai_config = await model_selection(key_prefix="main_translate", default_model=QWEN2_5_MODEL)
        st.session_state.config['translate'] = {
            'from': from_lang,
            'to': to_lang,
            'openai': openai_config.get_config()
        }
    else:
        st.session_state.config['translate'] = None

async def step_correct_config():
    st.subheader("文本纠错配置")
    st.warning("这是实验性功能，可能会带来误判，请谨慎使用")
    enable_correct = st.checkbox("启用文本纠错", value=False)
    if enable_correct:
        openai_config = await model_selection(key_prefix="main_correct", default_model=QWEN2_5_MODEL)
        common_errors = get_text_correct_common_errors()
        st.session_state.config['correct'] = {
            'openai': openai_config.get_config(),
            'common_errors': common_errors
        }
    else:
        st.session_state.config['correct'] = None

async def step_title_config():
    st.subheader("文件名配置")
    generate_title = st.checkbox("自动总结标题", value=True, help="如果开启，则会利用大模型从识别的文本中进行总结")
    openai_config = None
    if generate_title:
        openai_config = await model_selection(key_prefix="main_title", default_model=QWEN2_5_MODEL)
    col1, col2 = st.columns(2)
    with col1:
        book_title = st.text_input("书名（可选）", value="")
    with col2:
        author = st.text_input("作者（可选）", value="")
    
    regex_origin = st.text_input("文件名正则表达式", value="(\\d+)",
                                help="用于从原始文件名中提取数据")
    rule = st.text_input("文件名生成规则", value="{index}_{title}")
    with st.expander("文件名生成规则说明"):
        st.write('''
            - origin: 原始文件名
            - index: 文件序号
            - title: 生成的标题
            - book_title: 书名
            - author: 作者
            - 0,1,2...: 从正则表达式中提取的匹配组
            示例：{origin}\_{index}\_{title}\_{book_title}\_{author}\_{0}
        ''')
    
    if 'uploaded_files' in st.session_state:
        sample_data = []
        for i, file in enumerate(st.session_state.uploaded_files):
            base_name = os.path.splitext(file.name)[0]
            new_name = rule.format(
                origin=base_name,
                index=i+1,
                title="待生成",
                book_title=book_title,
                author=author,
                *re.search(regex_origin, base_name).groups() if re.search(regex_origin, base_name) else []
            )
            sample_data.append({
                "原始文件名": file.name,
                "新文件名": new_name + os.path.splitext(file.name)[1]
            })
        st.dataframe(sample_data)
    
    st.session_state.config['title'] = {
        'generate': generate_title,
        'book_title': book_title,
        'author': author,
        'regex_origin': regex_origin,
        'rule': rule,
        'openai': openai_config.get_config() if openai_config != None else None
    }

async def step_preview_config():
    st.subheader("配置预览")
    st.json(st.session_state.config)
    if st.session_state.uploaded_files:
        # 展示已上传文件信息
        st.info(f"待处理的 {len(st.session_state.uploaded_files)} 个文件：")
        for i, file in enumerate(st.session_state.uploaded_files, 1):
            st.write(f"{i}. {file.name} ({round(file.size/1024/1024, 2)} MB)")
    
    if st.button("开始处理音频"):
        if 'uploaded_files' not in st.session_state or not st.session_state.uploaded_files:
            st.error("请先上传音频文件")
        else:
            try:
                start_time = time.time()
                files = [("files", file) for file in st.session_state.uploaded_files]
                response = requests.post(
                    "http://127.0.0.1:8000/handle",
                    files=files,
                    data={"config": json.dumps(st.session_state.config)}
                )
                
                if response.status_code == 200:
                    end_time = time.time()
                    processing_time = end_time - start_time
                    st.balloons()
                    st.success(f"音频处理成功！耗时 {processing_time:.2f} 秒")
                    st.download_button(
                        label="下载处理结果",
                        data=BytesIO(response.content),
                        file_name="results.zip",
                        mime="application/zip"
                    )
                else:
                    st.error(f"处理失败：{response.json().get('error', '未知错误')}")
            except Exception as e:
                st.error(f"请求失败：{str(e)}")

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
