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

# ---------- FUNCTIONS ----------

@st.cache_data(show_spinner=False)
def load_excel(file) -> list:
    """Load list of tickers from uploaded Excel file."""
    df = pd.read_excel(file)
    return df["Ticker"].dropna().unique().tolist()

@st.cache_data(show_spinner=False)
def load_local_csv(ticker: str, csv_folder: str) -> pd.DataFrame:
    """Load historical data from local CSV."""
    path = os.path.join(csv_folder, f"{ticker}.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, parse_dates=["Date"])
    return df[df["Date"] <= pd.Timestamp("2025-11-01")]

@st.cache_data(show_spinner=False)
def fetch_latest_data(ticker: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Fetch latest stock data from Yahoo Finance."""
    df_new = yf.download(ticker, start=start_date, end=end_date)
    df_new.reset_index(inplace=True)
    return df_new.rename(columns={"Date": "Date"})

def combine_data(df_old, df_new):
    """Merge old and new data."""
    if df_old.empty:
        return df_new
    df_all = pd.concat([df_old, df_new], ignore_index=True).drop_duplicates(subset=["Date"])
    return df_all

def compute_drop(df_all: pd.DataFrame, n_days: int):
    """Compute current price, highest price in last n days, and drop %."""
    cutoff = datetime.today() - timedelta(days=n_days)
    df_window = df_all[df_all["Date"] >= cutoff]
    if df_window.empty:
        return None
    current_price = df_window.iloc[-1]["Close"]
    highest_price = df_window["Close"].max()
    drop_pct = (current_price - highest_price) / highest_price * 100
    return round(current_price, 2), round(highest_price, 2), round(drop_pct, 2), df_window


# ---------- UI ----------
excel_file = st.file_uploader("📂 Upload Excel file with 'Ticker' column", type=["xlsx"])
csv_folder = st.text_input("📁 Enter folder path where your CSV files are stored (one CSV per ticker)")

n_option = st.selectbox("Select lookback period", list(LOOKBACK_OPTIONS.keys()))
n_days = LOOKBACK_OPTIONS[n_option]

refresh_data = st.button("🔄 Refresh All (Download Latest Prices)")

# ---------- MAIN ----------
if excel_file and csv_folder:
    tickers = load_excel(excel_file)
    today = datetime.today().date()
    start_date = datetime(2025, 11, 2).date()

    results = []
    chart_data = {}

    st.write(f"Processing **{len(tickers)}** tickers...")

    for ticker in tickers:
        df_old = load_local_csv(ticker, csv_folder)

        if refresh_data:
            with st.spinner(f"Fetching latest data for {ticker}..."):
                df_new = fetch_latest_data(ticker, start_date, today + timedelta(days=1))
                st.cache_data.clear()  # clear cache to allow new data
        else:
            df_new = pd.DataFrame()

        df_all = combine_data(df_old, df_new)

        if df_all.empty:
            st.warning(f"No data found for {ticker}, skipping.")
            continue

        result = compute_drop(df_all, n_days)
        if not result:
            continue

        current_price, highest_price, drop_pct, df_window = result
        results.append({
            "Ticker": ticker,
            "Current Price": current_price,
            f"Highest ({n_option})": highest_price,
            f"Drop % ({n_option})": drop_pct
        })
        chart_data[ticker] = df_window[["Date", "Close"]]

    if results:
        df_results = pd.DataFrame(results)
        drop_col = f"Drop % ({n_option})"

        # --- Color gradient style ---
        styled_df = (
            df_results.style
            .background_gradient(subset=[drop_col], cmap='RdYlGn_r', vmin=-50, vmax=0)
            .format({drop_col: "{:.2f}%"})
        )

        st.subheader("📋 Summary Table")
        st.dataframe(styled_df, use_container_width=True)

        # --- Download button ---
        csv_buffer = io.StringIO()
        df_results.to_csv(csv_buffer, index=False)
        st.download_button(
            label="💾 Download Results as CSV",
            data=csv_buffer.getvalue(),
            file_name="stock_drop_summary.csv",
            mime="text/csv"
        )

        # --- Charts ---
        st.subheader("📈 Price Charts (Last Period)")
        for ticker, df_plot in chart_data.items():
            st.markdown(f"**{ticker}**")
            st.line_chart(df_plot.set_index("Date")["Close"])

    else:
        st.info("No data available yet.")

else:
    st.warning("Please upload your Excel file and specify the CSV folder path.")