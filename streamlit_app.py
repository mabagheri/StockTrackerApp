import streamlit as st
import pandas as pd
import yfinance as yf
import os
from datetime import datetime, timedelta
import io

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Stock Drop Tracker", layout="wide")
st.title("📉 Stock Drop Tracker")

# ---------- SETTINGS ----------
LOOKBACK_OPTIONS = {
    "1 Week": 7,
    "1 Month": 30,
    "6 Months": 180,
    "1 Year": 365
}

EXCEL_PATH = "Data/IndexList.xlsx"
CSV_ROOT = "Data"

# ---------- CACHED FUNCTIONS ----------
@st.cache_data(show_spinner=False)
def load_index_tickers(sheet_name):
    """Load tickers from the specified index sheet."""
    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
    df = df.dropna(subset=["Ticker"])
    return df["Ticker"].unique().tolist()

@st.cache_data(show_spinner=False)
def load_local_csv(ticker: str, folder: str) -> pd.DataFrame:
    path = os.path.join(folder, f"{ticker}.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, parse_dates=["Date"])
    return df

@st.cache_data(show_spinner=False)
def fetch_latest_data(ticker: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    df_new = yf.download(ticker, start=start_date, end=end_date)
    df_new.reset_index(inplace=True)
    return df_new.rename(columns={"Date": "Date"})

def compute_drop(df_all: pd.DataFrame, n_days: int):
    cutoff = datetime.today() - timedelta(days=n_days)
    df_window = df_all[df_all["Date"] >= cutoff]
    if df_window.empty:
        return None
    current_price = df_window.iloc[-1]["Close"]
    highest_price = df_window["Close"].max()
    drop_pct = (current_price - highest_price) / highest_price * 100
    return round(drop_pct, 2), df_window  # return drop only


# ---------- UI ----------
index_choice = st.radio("📈 Select Index", ["Nasdaq100", "SP500", "SP500_TSX"])
selected_windows = st.multiselect(
    "⏳ Select Lookback Periods (choose multiple)",
    list(LOOKBACK_OPTIONS.keys()),
    default=["1 Month", "6 Months"]
)

refresh_data = st.button("🔄 Refresh All Data (Update from Yahoo Finance)")

if not selected_windows:
    st.warning("Please select at least one lookback window.")
    st.stop()

# ---------- MAIN ----------
tickers = load_index_tickers(index_choice)
csv_folder = os.path.join(CSV_ROOT, index_choice)

today = datetime.today().date()
start_date = datetime(2025, 11, 2).date()

results = []
chart_data = {}

st.write(f"Processing **{len(tickers)}** tickers from {index_choice}...")

for ticker in tickers:
    df_old = load_local_csv(ticker, csv_folder)

    # If user clicked refresh, fetch latest data
    if refresh_data:
        df_new = fetch_latest_data(ticker, start_date, today + timedelta(days=1))
        df_all = pd.concat([df_old, df_new]).drop_duplicates(subset=["Date"])
    else:
        df_all = df_old.copy()

    if df_all.empty:
        continue

    row_result = {"Ticker": ticker}

    max_drop = None

    for period in selected_windows:
        n_days = LOOKBACK_OPTIONS[period]
        drop_result = compute_drop(df_all, n_days)
        if not drop_result:
            continue

        drop_pct, df_window = drop_result
        row_result[f"Drop {period}"] = drop_pct

        # track max (worst) drop
        if max_drop is None or drop_pct < max_drop:
            max_drop = drop_pct
            chart_data[ticker] = df_window[["Date", "Close"]]

    row_result["Max Drop"] = max_drop
    results.append(row_result)

# ---------- DISPLAY ----------
if results:
    df_results = pd.DataFrame(results)

    # Apply gradient to Max Drop
    styled = (
        df_results.style
        .background_gradient(subset=["Max Drop"], cmap="RdYlGn_r", vmin=-50, vmax=0)
    )

    st.subheader("📋 Drop Summary Table (Max Drop Across Selected Windows)")
    st.dataframe(styled, use_container_width=True)

    # CSV download
    csv_buffer = io.StringIO()
    df_results.to_csv(csv_buffer, index=False)
    st.download_button(
        label="💾 Download Summary CSV",
        data=csv_buffer.getvalue(),
        file_name=f"{index_choice}_drop_summary.csv",
        mime="text/csv"
    )

    # Charts
    st.subheader("📈 Price Chart for Ticker with Max Drop")
    for ticker, df_plot in chart_data.items():
        st.markdown(f"### {ticker}")
        st.line_chart(df_plot.set_index("Date")["Close"])

else:
    st.info("No valid data found for selected index.")