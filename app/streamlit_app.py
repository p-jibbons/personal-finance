import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Personal Finance", layout="wide")
st.title("Personal Finance Dashboard")



tickers = st.selectbox("Select Ticker", ["MSFT", "AAPL", "GOOGL"])
dat = yf.Ticker(tickers)


stock_history = dat.history(period="1y")
st.write("attempting to load data")
# st.write(stock_history)

kpi_in_context = stock_history.columns.tolist()
kpi = st.selectbox("Select KPI", kpi_in_context)
st.line_chart(stock_history[[kpi]])
