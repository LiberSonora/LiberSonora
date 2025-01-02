import streamlit as st
from typing import List
import pandas as pd
from packages.llm import MODEL_CONFIGS
from packages.ollama import OllamaHandler
from packages.openai import OpenAIHandler
import asyncio

@st.dialog("配置大模型参数")
def config_dialog(key_prefix, config_key):
    # 使用ollama勾选框
    use_ollama = st.checkbox(
        "使用Ollama", 
        value=st.session_state[config_key]['use_ollama'], 
        help="勾选此选项将尝试自动通过 ollama API 拉取所需的大模型",
        key=f'{key_prefix}_use_ollama'
    )
    st.session_state[config_key]['use_ollama'] = use_ollama

    # API地址输入
    openai_url = st.text_input(
        "API地址", 
        help="http://ollama:11434 是本机 ollama docker 地址，可替换为 deepseek/openai 等地址连接外部 API",
        value=st.session_state[config_key]['openai_url'],
        key=f'{key_prefix}_openai_url'
    )
    st.session_state[config_key]['openai_url'] = openai_url
    
    # API密钥输入
    openai_key = st.text_input(
        "API密钥", 
        value=st.session_state[config_key]['openai_key'],
        type="password",
        key=f'{key_prefix}_openai_key'
    )
    st.session_state[config_key]['openai_key'] = openai_key
    
    # 自定义模型勾选框
    custom_model = st.checkbox(
        "自定义模型名称",
        key=f'{key_prefix}_custom_model',
        help="可替换为更大的 ollama 模型或 deepseek 等提升质量，连接外部模型时需要先修改 API 地址"
    )
    
    if custom_model:
        # 自定义模型输入框
        model = st.text_input(
            "请输入模型名称", 
            value=st.session_state[config_key]['model'],
            key=f'{key_prefix}_custom_model_input'
        )
    else:
        # 模型选择单选，显示name，返回model
        model_options = [(config['name'], config["model"], config['comment']) for config in MODEL_CONFIGS]
        selected = st.radio(
            "请选择模型",
            options=[option[0] for option in model_options],
            index=next(i for i, option in enumerate(model_options) if option[1] == st.session_state[config_key]['model']),
            key=f'{key_prefix}_model_radio',
            captions=[option[2] for option in model_options]
        )
        model = next(option[1] for option in model_options if option[0] == selected)
    
    st.session_state[config_key]['model'] = model

    if st.button("保存并生效", key=f"{key_prefix}_save_config_button"):
        st.rerun()
    return st.session_state[config_key]

async def model_selection(key_prefix: str = "default", default_model: str = None):
    """大模型选择组件
    
    参数:
        key_prefix: 用于拼接st组件key的前缀，默认为"default"
        default_model: 默认模型名称，如果未提供则使用MODEL_CONFIGS中的第一个模型
    
    返回:
        model: 选择的模型名称
        use_ollama: 是否使用ollama
        openai_url: API基础地址
        openai_key: API密钥
    """
    # 初始化session_state中的配置项，按key_prefix区分
    config_key = f'llm_config_{key_prefix}'
    if config_key not in st.session_state:
        st.session_state[config_key] = {
            'model': default_model or MODEL_CONFIGS[0]['model'],
            'use_ollama': True,
            'openai_url': "http://ollama:11434",
            'openai_key': ""
        }
    # 显示当前配置
    with st.container(border=True):
        st.write(f"选择的模型名称：{st.session_state[config_key]['model']}")
        st.write(f"是否使用ollama：{'是' if st.session_state[config_key]['use_ollama'] else '否'}")
        st.write(f"API基础地址：{st.session_state[config_key]['openai_url']}")
        st.write(f"API密钥：{'*' * len(st.session_state[config_key]['openai_key']) if st.session_state[config_key]['openai_key'] else '未设置'}")
        if st.button("配置大模型参数", key=f"{key_prefix}_config_button"):
            config_dialog(key_prefix, config_key)

        if st.session_state[config_key]['use_ollama']:
            model = st.session_state[config_key]['model']
            ollama_handler = OllamaHandler(base_url=st.session_state[config_key]['openai_url'])
            with st.spinner(f"正在检查或拉取模型 {model}，这可能需要一些时间..."):
                try:
                    await ollama_handler.check_and_pull_model(model)
                    st.success(f"模型 {model} 已成功拉取或已存在")
                except Exception as e:
                    st.error(f"模型拉取失败: {str(e)}")

    # 初始化OpenAIHandler
    openai_handler = OpenAIHandler(
        model=st.session_state[config_key]['model'],
        openai_url=st.session_state[config_key]['openai_url'],
        openai_key=st.session_state[config_key]['openai_key'],
        use_ollama=st.session_state[config_key]['use_ollama']
    )
    return openai_handler

def get_text_correct_common_errors(key_prefix: str = "default") -> List[dict]:
    """获取并编辑常见错误列表
    
    参数:
        key_prefix: 用于拼接st组件key的前缀，默认为"default"
    
    返回:
        List[dict]: 包含常见错误映射的字典列表
    """
    # 初始化常见错误表格
    common_errors = [
        {"from": "我门", "to": "我们"},
        {"from": "在见", "to": "再见"},
        {"from": "以经", "to": "已经"},
        {"from": "他门", "to": "他们"},
        {"from": "因该", "to": "应该"},
        {"from": "到低", "to": "到底"}
    ]
    
    # 创建可编辑的错误表格
    df = pd.DataFrame(common_errors)
    st.write("请编辑或添加需要纠正的常见错误：")
    edited_df = st.data_editor(df, num_rows="dynamic", key=f"{key_prefix}_error_editor")
    
    # 将DataFrame转换为字典列表
    common_errors_list = edited_df.to_dict('records')
    
    return common_errors_list

def select_translate_languages(key_prefix: str = "default") -> tuple[str, str]:
    """选择翻译的源语言和目标语言
    
    参数:
        key_prefix: 用于拼接st组件key的前缀，默认为"default"
    
    返回:
        tuple[str, str]: (源语言代码, 目标语言代码)
    """
    # 导入语言列表
    from packages.translate import from_languages, to_languages
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    with col1:
        # 选择源语言
        from_lang = st.selectbox(
            "选择源语言",
            options=[lang["code"] for lang in from_languages],
            format_func=lambda code: next((lang["name"] for lang in from_languages if lang["code"] == code), code),
            key=f"{key_prefix}_from_lang"
        )
    
    with col2:
        # 选择目标语言
        to_lang = st.selectbox(
            "选择目标语言", 
            options=[lang["code"] for lang in to_languages],
            format_func=lambda code: next((lang["name"] for lang in to_languages if lang["code"] == code), code),
            key=f"{key_prefix}_to_lang"
        )
    
    return from_lang, to_lang


def select_target_language(key_prefix: str = "default", label: str = "选择语言") -> str:
    """选择目标语言
    
    参数:
        key_prefix: 用于拼接st组件key的前缀，默认为"default"
        label: 选择框的标签文本，默认为"选择语言"
    
    返回:
        str: 目标语言代码
    """
    # 导入目标语言列表
    from packages.translate import from_languages
    
    # 选择目标语言
    to_lang = st.selectbox(
        label, 
        options=[lang["code"] for lang in from_languages],
        format_func=lambda code: next((lang["name"] for lang in from_languages if lang["code"] == code), code),
        key=f"{key_prefix}_target_lang"
    )
    
    return to_lang
