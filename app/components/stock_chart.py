import streamlit as st
import pandas as pd


def render_stock_chart(stock_data, kpi: str):
    """Render a line chart for the selected KPI."""
    st.line_chart(stock_data[[kpi]])


def render_portfolio_chart(portfolio_history: pd.DataFrame):
    """
    Render a line chart showing portfolio value over time.

    Args:
        portfolio_history: DataFrame with 'date' and 'portfolio_value' columns
    """
    if portfolio_history.empty:
        st.info("No portfolio history available yet.")
        return

    # Set date as index for better chart display
    chart_data = portfolio_history.set_index("date")

    st.line_chart(chart_data["portfolio_value"], use_container_width=True)
