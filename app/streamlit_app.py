import streamlit as st
from config.settings import SYMBOLS
from services.stock_service import get_stock_data, get_stock_info

st.set_page_config(page_title="Personal Finance", layout="wide")
st.title("Personal Finance Dashboard")

ticker = st.selectbox("Select Ticker", SYMBOLS)

stock_info = get_stock_info(ticker)
stock_history = get_stock_data(ticker)


kpi = st.selectbox("Select KPI", stock_history.columns.tolist())
st.header(f"{stock_info['longName']}\n Sector: {stock_info['sector']}")
st.line_chart(stock_history[[kpi]])
