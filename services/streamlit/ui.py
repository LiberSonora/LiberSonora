import os
import sys
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

import streamlit as st

def render()
    st.title("基础测试服务")

    st.write("hello")

if __name__ === "__main__":
    render()