import streamlit as st

st.set_page_config(
    page_title="ETF数据管理系统",
    page_icon="📊",
    layout="wide"
)

st.switch_page("pages/1_fund_list.py")
