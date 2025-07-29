import os
import sys
import asyncio
import streamlit as st
import streamlit_antd_components as sac
import json
from io import BytesIO
import pandas as pd
import re
import time
import requests
from components.form import model_selection, select_translate_languages, get_text_correct_common_errors, select_target_language
from packages.process import process_single_audio, process_audio_batch_backround
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

def display_audio_files(audio_files):
    """用DataFrame展示找到的音频文件"""
    import pandas as pd
    # 准备数据
    data = []
    for file_path in audio_files:
        file_size = os.path.getsize(file_path) / 1024 / 1024  # 转换为MB
        data.append({
            '文件路径': file_path,
            '文件大小(MB)': round(file_size, 2)
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    # 显示表格
    st.dataframe(df, use_container_width=True)

def choose_audio_files(audio_files):
    """用DataFrame展示音频文件并支持多选
    
    参数:
        audio_files: 音频文件路径列表
        
    返回:
        checked_audio_files: 用户选择的文件路径列表
    """
    # 准备数据
    data = []
    for file_path in audio_files:
        file_size = os.path.getsize(file_path) / 1024 / 1024  # 转换为MB
        data.append({
            '文件路径': file_path,
            '文件大小(MB)': round(file_size, 2)
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 显示可多选的表格
    event = st.dataframe(
        df,
        use_container_width=True,
        on_select="rerun",
        selection_mode=["multi-row"]
    )
    
    # 获取用户选择的行
    selected_rows = event.selection.rows if event.selection else []
    
    # 根据选择的行索引获取对应的文件路径
    checked_audio_files = [audio_files[i] for i in selected_rows]
    
    return checked_audio_files



async def step_choose_audio_dir():
    st.subheader("选择音频目录")
    # 输入服务器目录路径
    audio_dir = st.text_input("请输入服务器上的音频目录路径", value="/mnt/data",
                            help="请确保该目录存在且包含音频文件")
    
    if audio_dir and os.path.exists(audio_dir):
        # 将选择的目录存入session_state
        st.session_state.input_audio_dir = audio_dir
        
        # 扫描目录中的音频文件
        audio_files = []
        for root, dirs, files in os.walk(audio_dir):
            for file in files:
                if file.lower().endswith(('.mp3', '.wav', '.pcm')):
                    file_path = os.path.join(root, file)
                    audio_files.append(file_path)
        
        if audio_files:
            # 按文件名正序排序
            audio_files.sort(key=lambda x: os.path.basename(x).lower())
            # 将文件路径存入session_state
            st.session_state.uploaded_file_paths = audio_files
            # 展示找到的文件列表
            st.info(f"找到的音频文件：{len(st.session_state.uploaded_file_paths)}，在预览配置时可选择部分进行转换")
            display_audio_files(st.session_state.uploaded_file_paths)
        else:
            st.warning(f"在目录 {audio_dir} 中未找到任何音频文件")
    elif audio_dir:
        st.error(f"目录 {audio_dir} 不存在，请检查路径是否正确")


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
        openai_config = await model_selection(key_prefix="main_translate")
        st.session_state.config['translate'] = {
            'from': from_lang,
            'to': to_lang,
            'openai': openai_config.get_config()
        }
    else:
        st.session_state.config['translate'] = None

async def step_correct_config():
    st.subheader("文本纠错配置")
    st.warning("这是实验性功能，可能会带来误修正、歌词错位等问题，请谨慎使用")
    enable_correct = st.checkbox("启用文本纠错", value=False)
    if enable_correct:
        openai_config = await model_selection(key_prefix="main_correct")
        common_errors = get_text_correct_common_errors()
        st.session_state.config['correct'] = {
            'openai': openai_config.get_config(),
            'common_errors': common_errors
        }
    else:
        st.session_state.config['correct'] = None

async def step_title_config():
    st.subheader("文件名配置")
    
    # 增加"不做标题重命名"选项，默认选中
    skip_title_rename = st.checkbox("不做标题重命名", value=True, help="选中后不进行标题重命名，只生成字幕文件")
    
    generate_title = st.checkbox("自动总结标题", value=False, help="如果开启，则会利用大模型从识别的文本中进行总结", disabled=skip_title_rename)
    openai_config = None
    lang="zh-CN"
    
    # 只有在不跳过标题重命名且开启标题生成时才显示相关配置
    if not skip_title_rename and generate_title:
        openai_config = await model_selection(key_prefix="main_title")
        # 新增选择目标语言
        lang = select_target_language(label="标题生成语言")
    
    col1, col2 = st.columns(2)
    with col1:
        book_title = st.text_input("书名（可选）", value="", disabled=skip_title_rename)
    with col2:
        author = st.text_input("作者（可选）", value="", disabled=skip_title_rename)
    
    
    regex_origin = st.text_input("文件名正则表达式", value="(\\d+)",
                                help="用于从原始文件名中提取数据", disabled=skip_title_rename)
    rule = st.text_input("文件名生成规则", value="{0}_{title}", disabled=skip_title_rename)
    
    if not skip_title_rename:
        with st.expander("文件名生成规则说明", expanded=True):
            st.write('''
                - origin: 原始文件名
                - index: 文件序号（请注意可能导致乱序）
                - title: 生成的标题
                - book_title: 书名
                - author: 作者
                - 0,1,2...: 从正则表达式中提取的匹配组
                示例：{origin}\_{index}\_{title}\_{book_title}\_{author}\_{0}
            ''')
    
    # 兼容 uploaded_files 和 uploaded_file_paths
    files = []
    if 'uploaded_file_paths' in st.session_state:
        files = [(os.path.basename(path), path) for path in st.session_state.uploaded_file_paths]
    elif 'uploaded_files' in st.session_state:
        files = [(os.path.basename(file.name), file) for file in st.session_state.uploaded_files]
    
    if files and not skip_title_rename:
        sample_data = []
        for i, (file_name, file) in enumerate(files):
            base_name = os.path.splitext(file_name)[0]
            new_name = rule.format(
                origin=base_name,
                index=str(i+1).zfill(3),
                title="AI生成" if generate_title else "空字符",
                book_title=book_title,
                author=author,
                *re.search(regex_origin, base_name).groups() if re.search(regex_origin, base_name) else []
            )
            sample_data.append({
                "原始文件名": file_name,
                "新文件名": new_name + os.path.splitext(file_name)[1]
            })
        st.dataframe(sample_data)
    
    st.session_state.config['title'] = {
        'skip_rename': skip_title_rename,
        'generate': generate_title,
        'book_title': book_title,
        'author': author,
        'lang': lang,
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
                with st.spinner("音频处理中，请稍候..."):
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

def check_output_dir(directory):
    """检查输出目录状态并提示用户"""
    if os.path.exists(directory):
        files = os.listdir(directory)
        if files:
            st.warning(f"警告：输出目录 '{directory}' 非空，包含 {len(files)} 个文件")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("删除目录内容", key="delete_dir_contents"):
                    for file in files:
                        os.remove(os.path.join(directory, file))
                    st.success("目录内容已删除")
                    st.rerun()
            with col2:
                if st.button("更换目录", key="change_output_dir"):
                    st.session_state.output_dir = ""
                    st.rerun()
            return True
    return False
async def step_local_fileoutput():
    st.subheader("配置预览")
    st.json(st.session_state.config)
    
    # 获取输出目录
    output_dir = st.text_input("请输入输出目录路径", 
                             value=os.path.dirname(st.session_state.uploaded_file_paths[0]) + "-output/")
    if output_dir:
        check_output_dir(output_dir)
        st.session_state.output_audio_dir = output_dir

    st.info(f"找到的音频文件：{len(st.session_state.uploaded_file_paths)}")
    checked_audio_files = choose_audio_files(st.session_state.uploaded_file_paths)
    if not checked_audio_files:  # 如果用户没有选择任何文件
        checked_audio_files = st.session_state.uploaded_file_paths  # 自动选择所有文件
        st.info("未选择特定文件，默认将处理所有音频文件")
    else:
        display_audio_files(checked_audio_files)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("开始处理音频"):
            if 'uploaded_file_paths' not in st.session_state or not st.session_state.uploaded_file_paths:
                st.error("请先选择音频文件")
            else:
                try:
                    # 创建输出目录（如果不存在）
                    os.makedirs(output_dir, exist_ok=True)
                    
                    with st.spinner("音频处理中，请稍候..."):
                        start_time = time.time()
                        
                        success_count = 0
                        # 顺序处理每个文件
                        for index, file_path in enumerate(checked_audio_files):
                            try:
                                with open(file_path, 'rb') as f:
                                    file_obj = type('StreamlitUploadedFile', (), {
                                        'name': os.path.basename(file_path),
                                        'body': f.read()
                                    })()
                                    
                                    # 获取文件相对于input_dir的相对路径
                                    relative_path = os.path.relpath(file_path, st.session_state.input_audio_dir)
                                    # 去掉文件名，只保留目录结构
                                    relative_dir = os.path.dirname(relative_path)
                                    # 在output_dir中创建对应的目录结构
                                    output_subdir = os.path.join(output_dir, relative_dir)
                                    os.makedirs(output_subdir, exist_ok=True)
                                    
                                    # 顺序处理单个音频文件
                                    audio_path = await process_single_audio(
                                        index=index,
                                        audio_file=file_obj,
                                        config=st.session_state.config,
                                        temp_dir=output_subdir
                                    )
                                    
                                    if audio_path:
                                        success_count += 1
                            except Exception as e:
                                st.error(f"处理文件 {os.path.basename(file_path)} 时出错：{str(e)}")
                                raise e
                        
                        end_time = time.time()
                        processing_time = end_time - start_time
                        st.balloons()
                        st.success(f"音频处理完成！成功处理 {success_count}/{len(st.session_state.uploaded_file_paths)} 个文件，总耗时 {processing_time:.2f} 秒")
                        st.info(f"处理结果已保存到：{output_dir}")
                        
                except Exception as e:
                    st.error(f"处理过程中发生错误：{str(e)}")

    with col2:
        if st.button("异步处理音频", help="在服务器后台异步处理音频文件，可以关闭页面。如需停止处理请停止容器。"):
            if 'uploaded_file_paths' not in st.session_state or not st.session_state.uploaded_file_paths:
                st.error("请先选择音频文件")
            else:
                try:
                    # 创建输出目录（如果不存在）
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # 启动异步处理
                    await process_audio_batch_backround(
                        input_dir=st.session_state.input_audio_dir,
                        output_dir=output_dir,
                        config=st.session_state.config,
                        audio_files=checked_audio_files
                    )
                    
                    st.success("已启动异步处理！")
                    st.info(f"""
                    请注意：
                    1. 处理结果将保存到：{output_dir}
                    2. 您可以关闭页面，处理会在后台继续进行
                    3. 处理完成后，输出目录中的音频文件数量应该与输入文件数量一致
                    4. 如需完全停止处理，请停止容器
                    5. 执行时间请根据设备在同样配置下的单个音频处理时间相乘推断
                    """)
                    
                except Exception as e:
                    st.error(f"启动异步处理时发生错误：{str(e)}")
