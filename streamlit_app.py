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
# Only run logic when the button is pressed
# -----------------------
if run_app:

    st.write(f"### 📊 Results for {index_choice}")

    # Load Excel (already in repo)
    excel_path = "Tickers_Info.xlsx"
    df_meta = pd.read_excel(excel_path, sheet_name=index_choice)

    tickers = df_meta["Ticker"].dropna().unique().tolist()

    # Filter market cap
    def cap_filter(cap):
        if cap == "Mega": return 200
        if cap == "Large": return 10
        if cap == "Mid": return 2
        if cap == "Small": return 0.3
        return 0

    # Apply market cap filtering
    mc_filtered = df_meta[df_meta["MarketCap"].isin(marketcap_choice)]
    tickers = mc_filtered["Ticker"].tolist()

    # Folder based on index
    folder_map = {
        "SP500": "Stock_data/SP500",
        "Nasdaq100": "Stock_data/Nasdaq100",
        "TSX": "Stock_data/TSX"
    }
    data_folder = folder_map[index_choice]

    summary_rows = []

    # -----------------------
    # Process each ticker
    # -----------------------
    for t in tickers:
        csv_path = f"{data_folder}/{t}.csv"
        if not os.path.exists(csv_path):
            st.write(csv_path)
            continue

        df = pd.read_csv(csv_path, parse_dates=["Date"])
        df = df.sort_values("Date")

        # Fetch latest price
        live = yf.download(t, period="5d")
        current_price = live["Close"].iloc[-1] if not live.empty else df["Close"].iloc[-1]

        row_result = {"Ticker": t, "Current": current_price}

        # Compute drop per selected lookback
        for label in lookbacks_selected:
            days = lookback_options[label]
            cutoff = datetime.now() - timedelta(days=days)

            df_recent = df[df["Date"] >= cutoff]
            if df_recent.empty:
                row_result[label] = None
                continue

            high = df_recent["Close"].max()
            drop = (current_price - high) / high * 100
            row_result[label] = round(drop, 2)

        summary_rows.append(row_result)

    df_summary = pd.DataFrame(summary_rows)

    # -----------------------
    # Display results
    # -----------------------
    st.dataframe(df_summary, use_container_width=True)

    # Download CSV
    csv = df_summary.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download CSV", csv, "summary.csv", "text/csv")

    # -----------------------
    # Show charts per ticker
    # -----------------------
    st.write("---")
    st.write("### 📈 Historical Charts")

    for t in tickers:
        csv_path = f"{data_folder}/{t}.csv"
        if not os.path.exists(csv_path):
            continue
        df = pd.read_csv(csv_path, parse_dates=["Date"])
        df = df.sort_values("Date")

        st.write(f"#### {t}")
        st.line_chart(df.set_index("Date")["Close"])
