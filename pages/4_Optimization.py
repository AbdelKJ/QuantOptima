#======================================================================================================================
# Dependant Libraries
#======================================================================================================================
import streamlit as st
st.set_page_config(page_title="📈 Optimization", layout="wide")
import pandas as pd
import numpy as np
import requests
from datetime import date
import warnings
import os
from dotenv import load_dotenv
from utils.layout_utils import render_sidebar
import riskfolio as rp
import json
import plotly.express as px


#======================================================================================================================
# Page Setup
#======================================================================================================================
render_sidebar()
warnings.filterwarnings("ignore")


#======================================================================================================================
# Helper Functions
#======================================================================================================================
load_dotenv()
# FMP_API_KEY = os.getenv("FMP_API_KEY")
# if not FMP_API_KEY:
#     st.error("❌ FMP_API_KEY not found. Please add it to your .env file.")
#     st.stop()
load_dotenv()

# Try Streamlit secrets first, fallback to .env
FMP_API_KEY = st.secrets["api"]["fmp_key"] if "api" in st.secrets else os.getenv("FMP_API_KEY")

if not FMP_API_KEY:
    st.error("❌ FMP_API_KEY not found. Please add it to Streamlit Secrets or your .env file.")
    st.stop()

# === helper to save selected file
def save_selected_portfolio(name: str, weights: dict, metrics: dict) -> bool:
    if "client_profile" not in st.session_state:
        st.error("❌ No client profile found.")
        return False

    client_name = st.session_state["client_profile"]["name"]
    folder_name = client_name.replace(" ", "_")
    client_dir = f"data/clients/{folder_name}"
    json_file = f"{client_dir}/{folder_name}.json"

    if not os.path.exists(json_file):
        st.error(f"❌ JSON file not found: {json_file}")
        return False

    try:
        with open(json_file, "r") as f:
            client_data = json.load(f)

        client_data["Selected Portfolio"] = {
            "Name": name,
            "Weights": {k: round(v, 4) for k, v in weights.items()},
            "Metrics": {
                "Return": round(metrics.get("Return", 0), 4),
                "Volatility": round(metrics.get("Volatility", 0), 4),
                "Sharpe Ratio": round(metrics.get("Sharpe Ratio", 0), 4)
            }
        }

        with open(json_file, "w") as f:
            json.dump(client_data, f, indent=4)

        return True

    except Exception as e:
        st.exception(e)
        return False


#======================================================================================================================
# Selected ETFs Overview
#======================================================================================================================
st.markdown("<h2 style='color:gold;'>1. Selected ETFs Overview</h2>", unsafe_allow_html=True)
st.markdown("---")

if "selected_etfs" not in st.session_state:
    st.warning("⚠️ No ETFs found from previous page.")
    st.stop()

try:
    raw_data = st.session_state["selected_etfs"]
    df_etfs = pd.DataFrame(raw_data)
    expected_cols = ["Name", "Ticker", "Asset Class"]
    for col in expected_cols:
        if col not in df_etfs.columns:
            df_etfs[col] = None
    df_etfs = df_etfs[expected_cols]
except Exception as e:
    st.error(f"❌ Error loading selected ETFs: {e}")
    st.stop()

st.dataframe(df_etfs, use_container_width=True)


#======================================================================================================================
# Download Historical Data
#======================================================================================================================
st.markdown("<h2 style='color:gold;'>2. Historical Data Configuration</h2>", unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    start_date = st.date_input("Start Date", value=date(2020, 1, 1))
with col2:
    end_date = st.date_input("End Date", value=date.today())
with col3:
    timeframe = st.selectbox("Timeframe", ["Daily", "Monthly", "Annual"], index=0)

# Download Historical Data from FMP
#-----------------------------------
if "price_data" not in st.session_state:
    st.session_state["price_data"] = None

def fetch_fmp_prices(ticker, start, end):
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={start}&to={end}&apikey={FMP_API_KEY}"
        response = requests.get(url)
        data = response.json()
        hist = data.get("historical", [])
        if hist:
            df = pd.DataFrame(hist)
            df["date"] = pd.to_datetime(df["date"])
            df = df[["date", "close"]].rename(columns={"close": ticker})
            return df.set_index("date")
        else:
            return pd.DataFrame()
    except Exception as e:
        st.warning(f"⚠️ Failed to fetch data for {ticker}: {e}")
        return pd.DataFrame()

if st.button("📥 Download Historical Data from FMP"):
    if "client_profile" not in st.session_state:
        st.error("❌ Client profile not found.")
        st.stop()

    client_name = st.session_state["client_profile"]["name"].replace(" ", "_")
    today_str = date.today().strftime("%Y-%m-%d")
    folder_path = f"data/clients/{client_name}"
    os.makedirs(folder_path, exist_ok=True)
    csv_path = os.path.join(folder_path, f"{client_name}_{today_str}.csv")

    if os.path.exists(csv_path):
        combined_df = pd.read_csv(csv_path, parse_dates=["date"])
        st.success("✅ Loaded existing historical data from CSV.")
    else:
        combined_df = pd.DataFrame()
        for ticker in df_etfs["Ticker"]:
            df = fetch_fmp_prices(ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            if not df.empty:
                if combined_df.empty:
                    combined_df = df
                else:
                    combined_df = combined_df.join(df, how="outer")

        if combined_df.empty:
            st.error("❌ No historical data could be downloaded.")
            st.stop()
        else:
            combined_df.reset_index(inplace=True)
            combined_df.to_csv(csv_path, index=False)
            st.session_state["price_data"] = combined_df
            st.success(f"✅ Historical data downloaded and saved to: {csv_path}")

# Download Historical Data json
#-----------------------------------
if st.button("📂 Use Last Downloaded Data"):
    if "client_profile" not in st.session_state:
        st.error("❌ Client profile not found.")
        st.stop()

    client_name = st.session_state["client_profile"]["name"].replace(" ", "_")
    folder_path = f"data/clients/{client_name}"

    try:
        csv_files = [f for f in os.listdir(folder_path) if f.startswith(client_name) and f.endswith(".csv")]
        if not csv_files:
            st.warning("⚠️ No historical data files found for this client.")
        else:
            # Sort files by date extracted from filename
            csv_files.sort(reverse=True)  # Latest should be first assuming ISO date
            latest_file = csv_files[0]
            latest_path = os.path.join(folder_path, latest_file)

            combined_df = pd.read_csv(latest_path, parse_dates=["date"])
            st.session_state["price_data"] = combined_df
            st.success(f"✅ Loaded historical data from: {latest_file}")
    except Exception as e:
        st.error(f"❌ Failed to load historical data: {e}")


#======================================================================================================================
# Optimization Section
#======================================================================================================================
st.markdown("<h2 style='color:gold;'>3. Optimization</h2>", unsafe_allow_html=True)
st.markdown("---")

if st.session_state["price_data"] is None:
    st.warning("⚠️ Please download historical price data first.")
    st.stop()

prices = st.session_state["price_data"].set_index("date")
returns = prices.pct_change().dropna()

if st.button("🚀 Run Multi-Objective Optimization"):
    st.session_state["just_ran_optimization"] = True
    st.session_state["opt_run"] = False

    objectives = ["Sharpe", "MinRisk", "Utility", "MaxRet"]
    port = rp.Portfolio(returns=returns, sht=False)
    port.assets_stats(method_mu="hist", method_cov="hist")
    n_assets = returns.shape[1]
    weights_dict = {}
    performance_data = []
    risk_lambda = float(st.session_state.get("risk_lambda", 2))

    for obj in objectives:
        try:
            kwargs = dict(model="Classic", rm="MAD", hist=True)
            if obj == "Utility":
                kwargs["l"] = risk_lambda
            if obj == "Sharpe":
                kwargs["rf"] = 0.00
            w = port.optimization(obj=obj, **kwargs)

            if w is not None and not w.empty:
                weights_dict[obj] = w.squeeze()
                w_arr = w.values.reshape(-1).astype(float)
                ret = float(np.dot(port.mu, w_arr))
                vol = float(np.sqrt(np.dot(w_arr.T, np.dot(port.cov, w_arr))))
                performance_data.append({"Objective": obj, "Return": ret, "Volatility": vol})
        except Exception as e:
            st.warning(f"⚠️ Optimization failed for {obj}: {e}")

            print(f"Optimization result for {obj}:\n{w}")

    # Equal Weighted
    # -----------------------------------
    equal_w = pd.Series(1 / n_assets, index=returns.columns)
    weights_dict["Equal"] = equal_w
    ret_eq = float(np.dot(port.mu, equal_w))
    vol_eq = float(np.sqrt(np.dot(equal_w.T, np.dot(port.cov, equal_w))))
    performance_data.append({"Objective": "Equal", "Return": ret_eq, "Volatility": vol_eq})

    st.session_state["opt_weights"] = weights_dict
    perf_df = pd.DataFrame(performance_data).set_index("Objective")
    perf_df["Sharpe Ratio"] = perf_df["Return"] / perf_df["Volatility"]
    st.session_state["opt_performance"] = perf_df
    st.session_state["port"] = port
    st.session_state["opt_run"] = True

    # Saving to  json
    # -----------------------------------
    if "client_profile" in st.session_state:
        client = st.session_state["client_profile"]
        client_name = client["name"]
        folder_name = client_name.replace(" ", "_")
        client_dir = f"data/clients/{folder_name}"
        json_file = f"{client_dir}/{folder_name}.json"

        try:
            if os.path.exists(json_file):
                with open(json_file, "r") as f:
                    client_data = json.load(f)
            else:
                client_data = client  # fallback if file doesn't exist

            perf_dict = perf_df.round(4).to_dict("index")
            weights_serialized = {k: v.round(4).to_dict() for k, v in weights_dict.items()}

            client_data["Quantitative Portfolios Performance"] = {
                obj: {
                    "Weights": weights_serialized[obj],
                    "Metrics": perf_dict[obj]
                } for obj in weights_dict.keys()
            }

            with open(json_file, "w") as f:
                json.dump(client_data, f, indent=4)

            st.success("📊 Optimization results saved to client profile.")
        except Exception as e:
            st.warning(f"⚠️ Failed to save optimization data: {e}")


    #Charts
    # -----------------------------------
    st.subheader("📊 Portfolio Weights Comparison")
    df_weights = pd.DataFrame(weights_dict).T
    fig_bar = px.bar(df_weights.T, barmode="group", title="Weight Allocation by Objective",
                     labels={"value": "Weight", "variable": "Objective"}, height=450)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📋 Risk & Return Metrics")
    styled_perf_df = perf_df.style.format({
        "Return": "{:.2%}",
        "Volatility": "{:.2%}",
        "Sharpe Ratio": "{:.2f}"
    }).highlight_max(subset=["Sharpe Ratio"], axis=0, color='#B8860B') \
     .set_properties(**{"text-align": "center"}) \
     .set_table_styles([{'selector': 'th', 'props': [('text-align', 'left')]}])
    st.dataframe(styled_perf_df, use_container_width=True)


#======================================================================================================================
# Selecting a Portfolio Section
#======================================================================================================================
st.markdown("<h2 style='color:gold;'>4. Select Portfolio</h2>", unsafe_allow_html=True)
st.markdown("---")

if st.session_state.get("opt_run"):
    all_choices = list(st.session_state["opt_weights"].keys()) + ["Manual"]
    selection = st.selectbox("Choose a portfolio:", all_choices)
    st.session_state["selection"] = selection

    weights_dict = st.session_state["opt_weights"]
    perf_df = st.session_state["opt_performance"]

    if selection != "Manual":
        selected_weights = weights_dict[selection]
        selected_perf = perf_df.loc[selection]

        col1, spacer, col2 = st.columns([2.5, 0.3, 1.2])
        with col1:
            df = selected_weights.reset_index()
            df.columns = ['Asset', 'Weight']
            fig = px.pie(df[df["Weight"] > 0.001], names='Asset', values='Weight',
                         title=f"{selection} Allocation", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.metric("Expected Return", f"{selected_perf['Return']:.2%}")
            st.metric("Volatility", f"{selected_perf['Volatility']:.2%}")
            st.metric("Sharpe Ratio", f"{selected_perf['Sharpe Ratio']:.2f}")

        if st.button("💾 Save Allocation and Generate Report"):
            success = save_selected_portfolio(
                name=selection,
                weights=selected_weights,
                metrics={
                    "Return": selected_perf["Return"],
                    "Volatility": selected_perf["Volatility"],
                    "Sharpe Ratio": selected_perf["Sharpe Ratio"]
                }
            )
            if success:
                st.success("✅ Selected portfolio saved to client file.")
                st.switch_page("pages/5_PDF_Report.py")

    else:
        st.subheader("✍️ Manual Allocation")
        manual_weights = {}
        total = 0
        manual_cols = st.columns(3)
        for idx, ticker in enumerate(df_etfs["Ticker"]):
            col = manual_cols[idx % 3]
            with col:
                val = st.number_input(f"{ticker} Weight (%)", min_value=0.0, max_value=100.0, step=1.0,
                                      value=0.0, key=f"manual_{ticker}")
                manual_weights[ticker] = val / 100
                total += val

        st.write(f"**Total Weight Entered:** {total:.2f}%")

        if total <= 100:
            cash_weight = 1 - sum(manual_weights.values())
            manual_weights["CASH"] = cash_weight if cash_weight > 0 else 0
            weights_series = pd.Series(manual_weights)
            weights_series = weights_series[weights_series > 0]

            if st.button("💾 Save Allocation and Generate Report"):
                portfolio = st.session_state["port"]
                w_arr = weights_series.reindex(portfolio.returns.columns, fill_value=0).values
                ret = float(np.dot(portfolio.mu, w_arr))
                vol = float(np.sqrt(np.dot(w_arr.T, np.dot(portfolio.cov, w_arr))))
                sharpe = ret / vol if vol > 0 else 0

                success = save_selected_portfolio(
                    name="Manual",
                    weights=weights_series.to_dict(),
                    metrics={
                        "Return": ret,
                        "Volatility": vol,
                        "Sharpe Ratio": sharpe
                    }
                )
                if success:
                    st.success("✅ Manual portfolio saved successfully.")
                    st.switch_page("pages/5_PDF_Report.py")

