import streamlit as st
import pandas as pd

st.set_page_config(page_title="Personal Finance", layout="wide")
st.title("Personal Finance Dashboard")


st.write("attempting to load data")
st.write(pd.DataFrame({
    'first column': [1, 2, 3, 4],
    'second column': [10, 20, 30, 40]
}))
