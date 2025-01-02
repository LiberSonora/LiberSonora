import streamlit as st
from io import BytesIO
import time
import asyncio
from components.form import model_selection, get_text_correct_common_errors, select_translate_languages, select_target_language
from packages.openai import OpenAIHandler
from packages.llm import QWEN2_5_MODEL, MINICPM3_MODEL

async def render_text_correction():
    st.header("语音识别文本矫正")
    st.warning("试过 pycorrect 和大模型矫正，效果挺一般还费时间，只作为实验特性推出")
    
    # 获取模型参数
    openai_handler = await model_selection(key_prefix="text_correction", default_model=QWEN2_5_MODEL)

    # 初始化TextCorrector
    from packages.text import TextCorrector
    corrector = TextCorrector(openai_handler)
    
    # 录入错误
    common_errors_list = get_text_correct_common_errors()
    
    # 输入框默认测试数据
    default_text = """贾知府：李大人，我门这次去京城，可要好好准备。
李大人：以经安排妥当了，不过因该再检查一遍。
贾知府：说得对，到低是大事，不能马虎。
李大人：在见了，贾知府，我这就去安排。
贾知府：他门那边怎么说？
李大人：都说准备好了，就等我们出发了。
贾知府：那好，我们明天一早就动身。
李大人：好的，我这就去通知他门。"""
    
    # 文本输入框
    input_text = st.text_area("请输入需要矫正的文本", value=default_text, height=200)
    
    if st.button("开始矫正"):
        with st.spinner("正在矫正文本..."):
            try:
                # 调用矫正功能，传入常见错误列表
                start_time = time.time()
                corrected_text = await corrector.fix_text(input_text.split("\n"), common_errors_list)
                end_time = time.time()
                
                # 展示矫正前后对比
                from st_diff_viewer import diff_viewer
                diff_viewer(input_text, "\n".join(corrected_text), split_view=True)
                
                # 显示矫正耗时
                st.success(f"语音识别文本矫正完成，耗时 {end_time - start_time:.2f} 秒")
                
            except Exception as e:
                st.error(f"语音识别文本矫正失败：{str(e)}")

async def render_translation():
    st.header("多语言翻译")
    
    # 获取模型参数
    openai_handler = await model_selection(key_prefix="translate", default_model=QWEN2_5_MODEL)

    # 初始化OpenAITranslator
    from packages.translate import OpenAITranslator
    translator = OpenAITranslator(openai_handler)
    
    # 输入框默认测试数据
    default_text = """贾知府：李大人，我们这次去京城，可要好好准备。
李大人：已经安排妥当了，不过应该再检查一遍。
贾知府：说得对，到底是大事，不能马虎。
李大人：再见了，贾知府，我这就去安排。
贾知府：他们那边怎么说？
李大人：都说准备好了，就等我们出发了。
贾知府：那好，我们明天一早就动身。
李大人：好的，我这就去通知他们。"""
    
    # 文本输入框
    input_text = st.text_area("请输入需要翻译的文本", value=default_text, height=200)
    
    # 选择源语言和目标语言
    from_lang, to_lang = select_translate_languages()
    
    if st.button("开始翻译"):
        with st.spinner("正在翻译文本..."):
            try:
                # 调用翻译功能
                start_time = time.time()
                translated_text = await translator.translate(from_lang, to_lang, input_text.split("\n"))
                end_time = time.time()
                
                # 展示翻译结果
                st.text_area("翻译结果", value="\n".join(translated_text), height=200)
                
                # 显示翻译耗时
                st.success(f"多语言翻译完成，耗时 {end_time - start_time:.2f} 秒")
                
            except Exception as e:
                st.error(f"多语言翻译失败：{str(e)}")
async def render_title_generation():
    st.header("识别小节取名")
    
    # 获取模型参数
    openai_handler = await model_selection(key_prefix="title", default_model=QWEN2_5_MODEL)

    # 初始化TitleGenerator
    from packages.text import TitleGenerator
    
    # 输入框默认测试数据
    default_text = """贾知府：李大人，我们这次去京城，可要好好准备。
李大人：已经安排妥当了，不过应该再检查一遍。
贾知府：说得对，到底是大事，不能马虎。
李大人：再见了，贾知府，我这就去安排。
贾知府：他们那边怎么说？
李大人：都说准备好了，就等我们出发了。
贾知府：那好，我们明天一早就动身。
李大人：好的，我这就去通知他们。"""
    
    # 文本输入框
    input_text = st.text_area("请输入文本内容", value=default_text, height=200)
    
    # 可选输入项
    col1, col2 = st.columns(2)
    with col1:
        book_title = st.text_input("书名（可选）", value="")
    with col2:
        author = st.text_input("作者（可选）", value="")
    
    # 选择目标语言
    lang = select_target_language()
    
    if st.button("生成章节标题"):
        with st.spinner("正在生成章节标题..."):
            try:
                # 调用标题生成功能
                start_time = time.time()
                title_generator = TitleGenerator(openai_handler, book_title, author, lang)
                generated_title = await title_generator.generate_title(input_text)
                end_time = time.time()
                
                # 展示生成结果
                st.text_area("生成的章节标题", value=generated_title, height=100)
                
                # 显示生成耗时
                st.success(f"章节标题生成完成，耗时 {end_time - start_time:.2f} 秒")
                
            except Exception as e:
                st.error(f"章节标题生成失败：{str(e)}")
async def render_background_removal():
    st.header("背景音移除")
    
    # 文件上传器
    audio_file = st.file_uploader("请选择音频文件", type=['mp3', 'wav', 'pcm'], key='background_removal')
    
    if audio_file is not None:
        if st.button("开始处理音频"):
            with st.spinner("正在处理音频..."):
                try:
                    start_time = time.time()
                    
                    # 读取音频文件
                    audio_bytes = audio_file.getvalue()
                    
                    # 调用音频处理函数
                    from packages.audio import convert_to_wav, enhance_audio
                    wav_audio = await convert_to_wav(audio_bytes)
                    enhanced_audio = await enhance_audio(wav_audio, model_name="enhance_model")
                    
                    end_time = time.time()
                    
                    # 展示处理结果
                    st.audio(enhanced_audio, format='audio/wav')
                    st.success(f"背景音移除完成，耗时 {end_time - start_time:.2f} 秒")
                    
                except Exception as e:
                    st.error(f"背景音移除失败：{str(e)}")

async def render_audio_to_subtitle():
    st.header("音频转字幕")
    
    # 文件上传器
    audio_file = st.file_uploader("请选择音频文件", type=['mp3', 'wav', 'pcm'], key='audio_to_subtitle')
    
    if audio_file is not None:
        # 添加 hotwords 输入
        hotwords = st.text_input("请输入热词（可选，增加识别准确率，多个词用空格分隔）", value="")
        
        if st.button("开始转换音频"):
            with st.spinner("正在转换音频为字幕..."):
                try:
                    start_time = time.time()
                    
                    # 读取音频文件
                    audio_bytes = audio_file.getvalue()
                    
                    # 调用音频处理函数
                    from packages.audio import convert_to_wav, speech_to_text, format_speech_results
                    # wav_audio = await convert_to_wav(audio_bytes)
                    subtitles = await speech_to_text(audio_bytes, hotwords=hotwords)
                    # st.json(subtitles)
                    subtitles = format_speech_results(subtitles)
                    
                    end_time = time.time()
                    
                    # 展示处理结果
                    import pandas as pd
                    df = pd.DataFrame(subtitles)
                    st.dataframe(df)
                    st.success(f"音频转字幕完成，耗时 {end_time - start_time:.2f} 秒")
                    
                except Exception as e:
                    st.error(f"音频转字幕失败：{str(e)}")

async def render_page():
    # 创建功能选项卡
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["语音识别文本矫正", "多语言翻译", "识别小节取名", "背景音移除", "音频转字幕"])

    with tab1:
        await render_text_correction()

    with tab2:
        await render_translation()

    with tab3:
        await render_title_generation()

    with tab4:
        await render_background_removal()

    with tab5:
        await render_audio_to_subtitle()

def main():
    asyncio.run(render_page())

if __name__ == "__main__":
    main()