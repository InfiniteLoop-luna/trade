"""
Fund Detail Page - Comprehensive information and charts for a selected fund

This page displays detailed information about a specific fund including:
- Basic fund information
- Share size trend charts
- Historical data tables
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
from utils.data_loader import load_fund_detail, load_share_size_data
from utils.chart_builder import create_line_chart


# Page configuration
st.set_page_config(
    page_title="基金详情 - ETF数据管理系统",
    page_icon="📈",
    layout="wide"
)


def format_value(value: Any, value_type: str = "text") -> str:
    """Format value for display, handling None values gracefully

    Args:
        value: Value to format
        value_type: Type of formatting (text, date, amount)

    Returns:
        Formatted string
    """
    if value is None:
        return "N/A"

    if value_type == "date":
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        return str(value)
    elif value_type == "amount":
        try:
            return f"{float(value):,.2f}"
        except (ValueError, TypeError):
            return "N/A"
    else:
        return str(value)


try:
    # Check if a fund has been selected
    if 'selected_fund' not in st.session_state:
        st.warning("请先从基金列表中选择一个基金")
        if st.button("返回基金列表", use_container_width=True):
            st.switch_page("pages/1_fund_list.py")
        st.stop()

    # Get selected fund code
    ts_code = st.session_state['selected_fund']

    # Load fund detail
    fund = load_fund_detail(ts_code)

    if not fund:
        st.error(f"未找到基金: {ts_code}")
        if st.button("返回基金列表", use_container_width=True):
            st.switch_page("pages/1_fund_list.py")
        st.stop()

    # Fund header
    st.title(f"📈 {fund.get('name', 'N/A')}")
    st.caption(f"代码: {fund.get('ts_code', 'N/A')}")

    # 4-column metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("管理人", format_value(fund.get('management')))

    with col2:
        st.metric("基金类型", format_value(fund.get('fund_type')))

    with col3:
        issue_amount = fund.get('issue_amount')
        if issue_amount is not None:
            st.metric("发行份额", f"{issue_amount:.2f}亿")
        else:
            st.metric("发行份额", "N/A")

    with col4:
        st.metric("上市日期", format_value(fund.get('list_date'), "date"))

    st.divider()

    # Tab navigation
    tab1, tab2, tab3 = st.tabs(["📊 份额规模", "📋 基本信息", "⚙️ 设置"])

    # Tab 1: Share size chart
    with tab1:
        st.subheader("份额规模趋势")

        # Slider for days
        days = st.slider(
            "选择时间范围（天）",
            min_value=7,
            max_value=365,
            value=90,
            step=1
        )

        # Load share size data
        share_data = load_share_size_data(ts_code, days=days)

        if share_data:
            # Convert to DataFrame
            df = pd.DataFrame(share_data)

            # Create chart
            fig = create_line_chart(
                data=df,
                x_col='trade_date',
                y_col='fund_share',
                title=f"{fund.get('name', 'N/A')} - 份额规模趋势",
                x_label="日期",
                y_label="份额（份）",
                show_range_selector=True
            )

            # Display chart
            st.plotly_chart(fig, use_container_width=True)

            # Show data table in expander
            with st.expander("查看数据表"):
                # Format the dataframe for display
                display_df = df.copy()
                display_df['trade_date'] = pd.to_datetime(display_df['trade_date']).dt.strftime('%Y-%m-%d')
                display_df['fund_share'] = display_df['fund_share'].apply(lambda x: f"{x:,.2f}" if x is not None else "N/A")
                display_df.columns = ['交易日期', '份额（份）']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无份额规模数据")

    # Tab 2: Basic information
    with tab2:
        st.subheader("基金基本信息")

        # Display fund information in 2-column layout
        info_items = [
            ("基金代码", fund.get('ts_code')),
            ("基金名称", fund.get('name')),
            ("管理人", fund.get('management')),
            ("托管人", fund.get('custodian')),
            ("基金类型", fund.get('fund_type')),
            ("成立日期", format_value(fund.get('found_date'), "date")),
            ("到期日期", format_value(fund.get('due_date'), "date")),
            ("上市日期", format_value(fund.get('list_date'), "date")),
            ("发行日期", format_value(fund.get('issue_date'), "date")),
            ("退市日期", format_value(fund.get('delist_date'), "date")),
            ("发行份额", format_value(fund.get('issue_amount'), "amount") if fund.get('issue_amount') else "N/A"),
            ("市场类型", format_value(fund.get('market'))),
        ]

        # Create 2-column layout for key-value pairs
        for i in range(0, len(info_items), 2):
            col1, col2 = st.columns(2)

            with col1:
                key, value = info_items[i]
                st.markdown(f"**{key}:** {value if value else 'N/A'}")

            if i + 1 < len(info_items):
                with col2:
                    key, value = info_items[i + 1]
                    st.markdown(f"**{key}:** {value if value else 'N/A'}")

    # Tab 3: Settings
    with tab3:
        st.subheader("设置")
        st.info("此功能正在开发中")

        if st.button("返回基金列表", use_container_width=True):
            st.switch_page("pages/1_fund_list.py")

except Exception as e:
    st.error(f"加载基金详情时出错: {str(e)}")
    st.error("请检查数据库连接或联系管理员")
    if st.button("返回基金列表", use_container_width=True):
        st.switch_page("pages/1_fund_list.py")
