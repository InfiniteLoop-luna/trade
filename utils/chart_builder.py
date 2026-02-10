"""
Chart builder utility for creating interactive Plotly charts.

This module provides functions to create standardized, interactive charts
for displaying fund data trends using Plotly.
"""

import plotly.graph_objects as go
import pandas as pd
from typing import Optional


def create_line_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    x_label: str,
    y_label: str,
    show_range_selector: bool = True
) -> go.Figure:
    """
    Create an interactive line chart using Plotly.

    This function creates a line chart with customizable styling and optional
    time range selector buttons for easy data exploration.

    Args:
        data: pandas DataFrame containing the data to plot
        x_col: Column name for x-axis values
        y_col: Column name for y-axis values
        title: Chart title
        x_label: Label for x-axis
        y_label: Label for y-axis
        show_range_selector: Whether to show time range selector buttons (default: True)

    Returns:
        go.Figure: Configured Plotly Figure object ready to display

    Example:
        >>> df = pd.DataFrame({
        ...     'date': pd.date_range('2024-01-01', periods=100),
        ...     'nav': [1.0 + i*0.01 for i in range(100)]
        ... })
        >>> fig = create_line_chart(
        ...     data=df,
        ...     x_col='date',
        ...     y_col='nav',
        ...     title='Fund NAV Trend',
        ...     x_label='Date',
        ...     y_label='Net Asset Value'
        ... )
    """
    # Create the line trace
    trace = go.Scatter(
        x=data[x_col],
        y=data[y_col],
        mode='lines',
        line=dict(color='#1f77b4', width=2),
        name=y_label
    )

    # Create the figure
    fig = go.Figure(data=[trace])

    # Update layout with title and labels
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        hovermode='x unified',
        template='plotly_white'
    )

    # Add range selector if requested
    if show_range_selector:
        fig.update_xaxes(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(label="All", step="all")
                ]
            ),
            rangeslider=dict(visible=False)
        )

    return fig
