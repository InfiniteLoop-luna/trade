"""
Search bar component for filtering funds.

This module provides a reusable search bar component with a clear button
for use across different pages in the fund data display system.
"""

import streamlit as st


def render_search_bar(placeholder: str = "搜索基金...") -> str:
    """
    Render a search bar with a clear button.

    Creates a two-column layout with a text input for searching and a clear button.
    The search query is stored in session state and can be cleared with the button.

    Args:
        placeholder: Placeholder text for the search input. Defaults to "搜索基金...".

    Returns:
        str: The current search query string.
    """
    # Create 2-column layout with 4:1 ratio
    col1, col2 = st.columns([4, 1])

    # Column 1: Search input
    with col1:
        search_query = st.text_input(
            label="Search",
            placeholder=placeholder,
            label_visibility="collapsed",
            key="search_input"
        )

    # Column 2: Clear button
    with col2:
        if st.button("清除", use_container_width=True):
            st.session_state['search_query'] = ""
            st.rerun()

    return search_query
