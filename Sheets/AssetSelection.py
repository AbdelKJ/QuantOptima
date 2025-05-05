import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import date
import plotly.express as px
import numpy as np
import plotly.figure_factory as ff

st.title("🏦 Asset Selection & Price Data")

# Load ETF Master File
file_path = 'data/All_Tickers.xlsx'

try:
    df_ETF = pd.read_excel(file_path, sheet_name=0)
    df_ETF.columns = df_ETF.columns.str.strip()
    assets = sorted(df_ETF["Asset"].dropna().astype(str).unique().tolist())
except FileNotFoundError:
    st.error(f"❌ Could not find {file_path}. Please upload or check the path.")
    st.stop()

# Initialize session state
if "selected_asset_classes" not in st.session_state:
    st.session_state.selected_asset_classes = []
if "selected_etfs" not in st.session_state:
    st.session_state.selected_etfs = []
if "selected_tickers" not in st.session_state:
    st.session_state.selected_tickers = []

# ---------------------------
# Step 1: Select Asset Classes
# ---------------------------
st.subheader("Step 1: Select Asset Classes")
selected_asset_classes = []
with st.spinner("⏳ Loading asset classes..."):
    cols = st.columns(3)
    for idx, asset in enumerate(assets):
        col = cols[idx % 3]
        if col.checkbox(asset, key=f"asset_class_{asset}"):
            selected_asset_classes.append(asset)
st.session_state.selected_asset_classes = selected_asset_classes

# ---------------------------
# Step 2: Select ETFs
# ---------------------------
st.subheader("Step 2: Select ETFs")
selected_etfs_total = []
selected_tickers_total = []
asset_class_map = {}

for asset in selected_asset_classes:
    st.markdown(f"### ETFs for {asset}")
    etf_options = df_ETF[df_ETF["Asset"] == asset]["ETF Name"].dropna().unique().tolist()
    selected_etfs = st.multiselect(f"Select {asset} ETFs:", etf_options, key=f"etf_select_{asset}")

    selected_etfs_total.extend(selected_etfs)
    tickers = df_ETF[df_ETF["ETF Name"].isin(selected_etfs)]["Ticker"].dropna().unique().tolist()
    selected_tickers_total.extend(tickers)
    for etf in selected_etfs:
        asset_class_map[etf] = asset

st.session_state.selected_etfs = selected_etfs_total
st.session_state.selected_tickers = selected_tickers_total

# ---------------------------
# Show summaries
# ---------------------------
if selected_asset_classes:
    st.markdown("### 🧩 Selected Asset Classes")
    st.dataframe(pd.DataFrame({"Selected Asset Classes": selected_asset_classes}), use_container_width=True)

if selected_etfs_total:
    st.markdown("### 📈 Selected ETFs")
    etf_summary = []
    for asset in selected_asset_classes:
        selected_etfs = st.session_state.get(f"etf_select_{asset}", [])
        for etf in selected_etfs:
            ticker_row = df_ETF[df_ETF["ETF Name"] == etf]
            if not ticker_row.empty:
                ticker = ticker_row.iloc[0]["Ticker"]
                etf_summary.append({"ETF Name": etf, "Ticker": ticker})

    summary_df = pd.DataFrame(etf_summary)
    st.dataframe(summary_df, use_container_width=True)

    selected_etfs_total = summary_df["ETF Name"].tolist()
    selected_tickers_total = summary_df["Ticker"].tolist()

    st.session_state.selected_etfs = selected_etfs_total
    st.session_state.selected_tickers = selected_tickers_total

# ---------------------------
# Step 3: Download Price Data
# ---------------------------
st.subheader("Step 3: Download Price Data")

with st.form("price_download_form"):
    start_date = st.date_input("Start Date", value=date(2020, 1, 1))
    end_date = st.date_input("End Date", value=date.today())

    col1, col2 = st.columns([2, 1])
    with col1:
        download_submitted = st.form_submit_button("Download Price Data")
    with col2:
        clear_submitted = st.form_submit_button("🗑️ Clear Selections")
        if clear_submitted:
            for key in ["selected_asset_classes", "selected_etfs", "selected_tickers", "close_prices"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()  # ✅ replaced experimental_rerun with rerun

if download_submitted:
    if not selected_tickers_total:
        st.error("❌ Please select at least one ETF before downloading data.")
    elif start_date >= end_date:
        st.error("❌ Start Date must be earlier than End Date.")
    else:
        try:
            with st.spinner("📈 Downloading price data..."):
                price_data = yf.download(
                    tickers=selected_tickers_total,
                    start=start_date,
                    end=end_date,
                    progress=False,
                    auto_adjust=False
                )

                close_prices = price_data["Close"] if len(selected_tickers_total) > 1 else price_data[["Close"]]
                if len(selected_tickers_total) == 1:
                    close_prices.columns = [selected_tickers_total[0]]

                st.session_state.close_prices = close_prices
                st.success("✅ Data downloaded successfully!")

                daily_returns = close_prices.pct_change().dropna()

                st.subheader("📊 Risk and Return Metrics")
                risk_return_summary = pd.DataFrame({
                    "Annualized Return (%)": (daily_returns.mean() * 252) * 100,
                    "Annualized Volatility (%)": (daily_returns.std() * np.sqrt(252)) * 100,
                    "Max Drawdown (%)": ((close_prices / close_prices.cummax() - 1).min()) * 100
                }).round(2)
                st.dataframe(risk_return_summary, use_container_width=True)

                st.subheader("📈 Historical Prices (Rebased to 100)")
                rebased = close_prices / close_prices.iloc[0] * 100
                fig_rebased = px.line(
                    rebased,
                    labels={"value": "Rebased Price", "index": "Date", "variable": "ETF"},
                    color_discrete_map={etf: px.colors.qualitative.Plotly[i % 10] for i, etf in enumerate(rebased.columns)}
                )
                fig_rebased.update_layout(legend_orientation="h", legend_y=-0.3)
                st.plotly_chart(fig_rebased, use_container_width=True)

                st.subheader("📈 Rolling Volatility (30-Day)")
                rolling_vol = daily_returns.rolling(window=30).std() * np.sqrt(252) * 100
                fig_vol = px.line(
                    rolling_vol,
                    labels={"value": "Rolling Volatility (%)", "index": "Date", "variable": "Ticker"},
                    color_discrete_map={etf: px.colors.qualitative.Plotly[i % 10] for i, etf in enumerate(rolling_vol.columns)},
                    template="plotly_white"
                )
                fig_vol.update_layout(legend_orientation="h", legend_y=-0.3)
                st.plotly_chart(fig_vol, use_container_width=True)

                st.subheader("🔥 Correlation Heatmap")
                corr = daily_returns.corr().round(2)
                fig_corr = ff.create_annotated_heatmap(
                    z=corr.values,
                    x=list(corr.columns),
                    y=list(corr.index),
                    annotation_text=corr.values.round(2).astype(str),
                    colorscale='YlOrBr',
                    showscale=True,
                    zmin=-1, zmax=1
                )
                st.plotly_chart(fig_corr, use_container_width=True)

        except Exception as e:
            st.error(f"❌ An error occurred during download: {e}")

# ---------------------------
# ✅ Proceed button appears after data download
# ---------------------------
if 'close_prices' in st.session_state and not st.session_state.close_prices.empty:
    if st.button("➡️ Proceed to Portfolio Optimization"):
        st.switch_page("Sheets/PortfolioOptimization.py")
else:
    st.info("ℹ️ Download price data to proceed to portfolio optimization.")