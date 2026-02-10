"""
Fund List Page - Main page for browsing and searching funds

This page displays a paginated list of funds with search and filter capabilities.
Users can filter by fund type, market, and search by code/name/manager.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
from utils.data_loader import (
    get_fund_count,
    get_latest_update,
    load_fund_list,
    search_funds,
    get_database
)
from components.fund_card import render_fund_card
from components.search_bar import render_search_bar


# Page configuration
st.set_page_config(
    page_title="基金列表 - ETF数据管理系统",
    page_icon="📊",
    layout="wide"
)

# Page title
st.title("📊 基金列表")

try:
    # Initialize session state for pagination
    if "page" not in st.session_state:
        st.session_state.page = 1

    # Metrics row - Display key statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        total_funds = get_fund_count()
        st.metric("ETF总数", f"{total_funds:,}")

    with col2:
        latest_date = get_latest_update()
        if latest_date:
            date_str = latest_date.strftime("%Y-%m-%d")
        else:
            date_str = "无数据"
        st.metric("最新数据日期", date_str)

    with col3:
        # Check database status
        try:
            db = get_database()
            db_status = "正常"
        except Exception:
            db_status = "异常"
        st.metric("数据库状态", db_status)

    st.divider()

    # Sidebar filters
    st.sidebar.header("筛选条件")

    # Fund type filter
    fund_type_options = ["全部", "股票型", "债券型", "混合型", "货币型", "其他"]
    selected_fund_type = st.sidebar.selectbox(
        "基金类型",
        options=fund_type_options,
        index=0
    )

    # Market filter
    market_options = ["全部", "E", "O"]
    selected_market = st.sidebar.selectbox(
        "市场",
        options=market_options,
        index=0,
        help="E: 场内市场, O: 场外市场"
    )

    # Page size filter
    page_size_options = [20, 50, 100]
    page_size = st.sidebar.selectbox(
        "每页显示",
        options=page_size_options,
        index=0
    )

    # Build filters dictionary
    filters = {}
    if selected_fund_type != "全部":
        filters["fund_type"] = selected_fund_type
    if selected_market != "全部":
        filters["market"] = selected_market

    # Search bar
    search_query = render_search_bar(placeholder="搜索基金代码、名称或管理人...")

    # Load fund list with filters and pagination
    result = load_fund_list(
        filters=filters if filters else None,
        page=st.session_state.page,
        page_size=page_size
    )

    funds = result["funds"]
    total = result["total"]
    total_pages = result["pages"]

    # Apply search if query exists
    if search_query:
        funds = search_funds(search_query, funds)
        st.info(f"找到 {len(funds)} 个匹配的基金")

    # Display fund cards in 3-column grid
    if funds:
        # Create 3-column layout
        cols = st.columns(3)

        for idx, fund in enumerate(funds):
            with cols[idx % 3]:
                render_fund_card(fund, clickable=True)
    else:
        st.warning("没有找到符合条件的基金")

    # Pagination controls
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("上一页", disabled=(st.session_state.page <= 1), use_container_width=True):
            st.session_state.page -= 1
            st.rerun()

    with col2:
        st.markdown(
            f"<div style='text-align: center; padding: 8px;'>第 {st.session_state.page} 页 / 共 {total_pages} 页 (共 {total} 条记录)</div>",
            unsafe_allow_html=True
        )

    with col3:
        if st.button("下一页", disabled=(st.session_state.page >= total_pages), use_container_width=True):
            st.session_state.page += 1
            st.rerun()

except Exception as e:
    st.error(f"加载数据时出错: {str(e)}")
    st.error("请检查数据库连接或联系管理员")
