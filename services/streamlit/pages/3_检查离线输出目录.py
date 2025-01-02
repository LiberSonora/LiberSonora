import streamlit as st
import pandas as pd
import os
import asyncio
from components.form import model_selection, select_target_language
from packages.process import check_offline_task_output, get_audio_files, ai_rename_files
from components.home import display_audio_files
from packages.llm import QWEN2_5_MODEL, MINICPM3_MODEL

async def render_page():
    # 输入输出目录表单
    st.subheader("目录设置")
    input_dir = st.text_input("输入目录", value=st.session_state.get("input_audio_dir", "/mnt/data/"))

    # 显示输入目录音频文件
    input_audio_files = get_audio_files(input_dir)
    if input_audio_files:
        st.info(f"找到的音频文件：{len(input_audio_files)}")
        display_audio_files(input_audio_files)
    elif input_dir:
        st.warning(f"在目录 {input_dir} 中未找到任何音频文件")

    output_dir = st.text_input("输出目录", value=st.session_state.get("output_audio_dir", ""))

    # 显示输出目录音频文件并检查数量
    output_audio_files = get_audio_files(output_dir)
    if output_audio_files:
        st.info(f"输出目录中找到的音频文件：{len(output_audio_files)}")
        display_audio_files(output_audio_files)
        # 检查输入输出文件数量是否一致
        if input_audio_files:
            if len(input_audio_files) != len(output_audio_files):
                st.warning("""
                ⚠️ 文件数量不匹配警告

                输出目录文件数量：{}  
                输入目录文件数量：{}  

                可能原因：  
                • 离线任务未完成  
                • 执行过程中出现问题中断  
                • 输入输出目录指定不正确
                """.format(len(output_audio_files), len(input_audio_files)))
            else:
                st.success("输出目录文件数量与输入目录一致")
    elif output_dir:
        st.warning(f"在目录 {output_dir} 中未找到任何音频文件")

    # 标题重新生成表单
    with st.expander("标题重新生成设置", expanded=True):
        openai_config = await model_selection(key_prefix="regenerate_title", default_model=QWEN2_5_MODEL)
        col1, col2 = st.columns(2)
        with col1:
            book_title = st.text_input("书名（可选）", value="")
        with col2:
            author = st.text_input("作者（可选）", value="")
        
        # 新增选择目标语言
        lang = select_target_language()

    # 检查输出目录并显示结果
    if output_dir and os.path.exists(output_dir):
        results = check_offline_task_output(output_dir)
        
        # 将结果转换为DataFrame，只保留需要的列
        df = pd.DataFrame(results)[['relative_path', 'has_srt', 'has_lrc']]
        df['操作'] = False  # 添加操作列
        
        # 显示表格
        edited_df = st.data_editor(
            df,
            column_config={
                "relative_path": "相对路径",
                "has_srt": "SRT存在",
                "has_lrc": "LRC存在",
                "操作": st.column_config.CheckboxColumn(
                    "重命名",
                    help="选择要重命名的文件",
                    default=False,
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # 处理重命名操作
        for index, row in edited_df.iterrows():
            if row['操作']:
                with st.form(key=f"rename_form_{index}"):
                    # 渲染音频播放器
                    st.audio(results[index]['audio_path'], format='audio/wav')
                    
                    new_name = st.text_input("新文件名", value=os.path.splitext(os.path.basename(results[index]['audio_path']))[0])
                    col1, col2 = st.columns([4, 1])
                    with col2:
                        if st.form_submit_button("应用"):
                            # 获取文件扩展名
                            ext = os.path.splitext(results[index]['audio_path'])[1]
                            new_audio_path = os.path.join(os.path.dirname(results[index]['audio_path']), new_name + ext)
                            new_srt_path = os.path.join(os.path.dirname(results[index]['srt_path']), new_name + ".srt")
                            new_lrc_path = os.path.join(os.path.dirname(results[index]['lrc_path']), new_name + ".lrc")
                            
                            # 重命名文件
                            try:
                                os.rename(results[index]['audio_path'], new_audio_path)
                                if os.path.exists(results[index]['srt_path']):
                                    os.rename(results[index]['srt_path'], new_srt_path)
                                if os.path.exists(results[index]['lrc_path']):
                                    os.rename(results[index]['lrc_path'], new_lrc_path)
                                st.rerun()
                            except Exception as e:
                                st.error(f"重命名失败: {str(e)}")
                    with col1:
                        if st.form_submit_button("AI生成"):
                            try:
                                # 调用AI生成标题
                                title = await ai_rename_files(
                                    openai_config.get_config(),
                                    book_title,
                                    author,
                                    lang,
                                    results[index]['audio_path'],
                                    results[index]['lrc_path'],
                                    results[index]['srt_path']
                                )
                                st.success(f"AI 建议标题：\n{title}")
                            except Exception as e:
                                st.error(f"AI生成标题失败: {str(e)}")

def main():
    asyncio.run(render_page())

if __name__ == "__main__":
    main()