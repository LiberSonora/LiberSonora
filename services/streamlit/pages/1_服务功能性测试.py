import streamlit as st
from io import BytesIO
import time
import asyncio
from components.form import model_selection, get_text_correct_common_errors, select_translate_languages
from packages.openai import OpenAIHandler
from packages.llm import QWEN2_5_MODEL, MINICPM3_MODEL

async def render_text_correction():
    st.header("文本矫正")
    
    # 获取模型参数
    openai_handler = await model_selection(key_prefix="text_correction", default_model=MINICPM3_MODEL)

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
                st.success(f"文本矫正完成，耗时 {end_time - start_time:.2f} 秒")
                
            except Exception as e:
                st.error(f"文本矫正失败：{str(e)}")

async def render_translation():
    st.header("文本翻译")
    
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
                st.success(f"文本翻译完成，耗时 {end_time - start_time:.2f} 秒")
                
            except Exception as e:
                st.error(f"文本翻译失败：{str(e)}")

async def render_page():
    # 创建功能选项卡
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["文本矫正", "文本翻译", "章节取名", "背景音移除", "音频转字幕"])

    with tab1:
        await render_text_correction()

    with tab2:
        await render_translation()

    with tab3:
        st.header("章节取名")
        # 章节取名功能内容待添加

    with tab4:
        st.header("背景音移除")
        # 背景音移除功能内容待添加

    with tab5:
        st.header("音频转字幕")
        # 音频转字幕功能内容待添加
        audio_file = st.file_uploader("请选择音频文件", type=['wav'], key='audio')

def main():
    asyncio.run(render_page())

if __name__ == "__main__":
    main()