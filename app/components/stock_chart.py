import streamlit as st


def render_stock_chart(stock_data, kpi: str):
    """Render a line chart for the selected KPI."""
    st.line_chart(stock_data[[kpi]])
