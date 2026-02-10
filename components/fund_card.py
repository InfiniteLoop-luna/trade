import streamlit as st
from typing import Dict, Any


def render_fund_card(fund_data: Dict[str, Any], clickable: bool = True) -> None:
    """Render a fund card with fund information

    Args:
        fund_data: Dictionary containing fund information from data_loader
        clickable: If True, adds a detail button that navigates to detail page
    """
    with st.container():
        # Fund code as header
        if fund_data.get('ts_code'):
            st.markdown(f"### {fund_data['ts_code']}")

        # Fund name in bold
        if fund_data.get('name'):
            st.write(f"**{fund_data['name']}**")

        # Manager as caption
        if fund_data.get('management'):
            st.caption(f"管理人: {fund_data['management']}")

        # Fund type as caption
        if fund_data.get('fund_type'):
            st.caption(f"基金类型: {fund_data['fund_type']}")

        # Issue amount as caption (already in 亿 units)
        if fund_data.get('issue_amount') is not None:
            st.caption(f"发行规模: {fund_data['issue_amount']:.2f}亿")

        # Add detail button if clickable
        if clickable and fund_data.get('ts_code'):
            if st.button("查看详情", key=fund_data['ts_code']):
                st.session_state['selected_fund'] = fund_data['ts_code']
                st.switch_page("pages/2_fund_detail.py")

        # Add divider at the end
        st.divider()
