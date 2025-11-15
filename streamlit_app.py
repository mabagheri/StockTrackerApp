import streamlit as st
import pandas as pd
import yfinance as yf
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Drop Dashboard", layout="wide")

# -----------------------
# Sidebar Controls
# -----------------------
st.sidebar.header("Controls")

index_choice = st.sidebar.radio(
    "Select Index:",
    ["Nasdaq100", "SP500", "TSX"]
)

# Market cap filters
marketcap_choice = st.sidebar.multiselect(
    "Select Market Cap Categories:",
    ["Mega", "Large", "Mid", "Small"],
    default=["Mega", "Large", "Mid", "Small"]
)

lookback_options = {
    "1 Week": 7,
    "1 Month": 30,
    "6 Months": 180,
    "1 Year": 365
}

lookbacks_selected = st.sidebar.multiselect(
    "Lookback Periods:",
    list(lookback_options.keys()),
    default=["1 Month", "6 Months", "1 Year"]
)

# -----------------------
# RUN BUTTON
# -----------------------
run_app = st.sidebar.button("🚀 Run Analysis", type="primary")

# -----------------------
# Only run logic when button is pressed
# -----------------------
if run_app:

    st.write(f"### 📊 Results for {index_choice}")

    # Load Excel (already in repo)
    excel_path = "Data/metadata.xlsx"
    df_meta = pd.read_excel(excel_path, sheet_name=index_choice)

    tickers = df_meta["Ticker"].dropna().unique().tolist()

    # Filter market cap
    def cap_filter(cap):
        if cap == "Mega": return 200_000_000_000
        if cap == "Large": return 10_000_000_000
        if cap ==
