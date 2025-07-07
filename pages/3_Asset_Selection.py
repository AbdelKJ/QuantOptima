#======================================================================================================================
# Dependant Libraries
#======================================================================================================================
import streamlit as st
st.set_page_config(page_title="Asset Selection", layout="wide")
import pandas as pd
import os
import requests
import json
from dotenv import load_dotenv
from utils.layout_utils import render_sidebar


#======================================================================================================================
# Page Setup
#======================================================================================================================
render_sidebar()

# ==== Load API Key ====
load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")
if not FMP_API_KEY:
    st.error("❌ FMP_API_KEY not found. Please add it to your .env file.")
    st.stop()


#======================================================================================================================
# Asset Classes Lists Download and Mapping
#======================================================================================================================
data_path = "data/data_lists.xlsx"
sheet_name = "ETF"
try:
    df = pd.read_excel(data_path, sheet_name=sheet_name)
except Exception as e:
    st.error(f"❌ Failed to load Excel data: {e}")
    st.stop()

if "Asset Class" not in df.columns:
    st.error("❌ 'Asset Class' column not found.")
    st.stop()

# ==== Asset Class Mapping ====
asset_class_map = {
    "Equities": ["Domestic Equity", "Canadian Equity", "Emerging Market Equity", "Australasian Equities",
                 "Consumer Discretionary", "Consumer Staples", "Banks", "Biotechnology", "Aerospace & Defense",
                 "Cyber Security", "E-Commerce", "Currency-hedged, Equities, International"],
    "Fixed Income": ["Active Fixed Income", "Bond", "Canadian Fixed Income", "Emerging Market Bonds",
                     "Convertible Securities"],
    "Commodities": ["Commodities", "Commodity", "Agriculture"],
    "Real Estate": ["Alternative | Real Estate", "REITs", "Global Real Estate", "Real Estate"],
    "Private Equity": ["Private Equity", "Buyout Funds", "Venture Capital"],
    "Alternatives": ["Alternative", "Alternative Energy", "Alternative Investments", "Alternative Equity Focused",
                     "Alternative Credit Focused", "Alternative | Infrastructure", "Alternative | Managed Futures",
                     "Alternative | Mid-Stream Energy", "Alternative | Multi-Strategy"],
    "Multi-Asset": ["Balanced", "Balanced/Diversified", "Asset Allocation",
                    "Active Equity Income and Green/Renewable", "Capital Efficient ETFs", "Alternatives, Equities"],
    "Other": ["Cash", "Cash and Cash Equivalents", "Currency", "Community Bank"],
    "Crypto": [ "Crypto ETPs", "Crypto-Linked","Digital Assets", "Currencies"],
    "Private Credit": [ "Private Credit"]
}

reverse_map = {sub.lower(): broad for broad, subs in asset_class_map.items() for sub in subs}
df["Broad Asset Class"] = df["Asset Class"].apply(lambda x: reverse_map.get(str(x).lower(), "Unclassified"))


#======================================================================================================================
# Asset Class Selection
#======================================================================================================================
if "etf_selection_by_class" not in st.session_state:
    st.session_state.etf_selection_by_class = {}

# ==== Current Allocation ====
st.markdown("<h1 style='color: #CC9900;'>📊 Current Allocation</h1>", unsafe_allow_html=True)
existing_allocation = {}
client_data = {}

if "client_profile" in st.session_state:
    client_name = st.session_state["client_profile"]["name"]
    client_dir = f"data/clients/{client_name.replace(' ', '_')}"
    os.makedirs(client_dir, exist_ok=True)
    client_file = f"{client_dir}/{client_name.replace(' ', '_')}.json"
    if os.path.exists(client_file):
        with open(client_file, "r") as f:
            client_data = json.load(f)
            existing_allocation = client_data.get("current_allocation", {})

cols = st.columns(3)
allocation_inputs = {}
total_alloc = 0

for idx, asset_class in enumerate(asset_class_map.keys()):
    default = existing_allocation.get(asset_class, 0.0)
    with cols[idx % 3]:
        val = st.number_input(f"{asset_class} (%)", min_value=0.0, max_value=100.0, value=default, step=1.0)
        allocation_inputs[asset_class] = val
        total_alloc += val

remaining_cash = max(0.0, 100.0 - total_alloc)
st.write(f"🧮 Total: {total_alloc:.2f}%, 💰 Cash: {remaining_cash:.2f}%")

if st.button("💾 Save Current Allocation"):
    if total_alloc > 100:
        st.error("❌ Allocation exceeds 100%.")
    else:
        final_alloc = {ac: pct for ac, pct in allocation_inputs.items() if pct > 0}
        if remaining_cash > 0:
            final_alloc["Cash"] = round(remaining_cash, 2)

        st.session_state["current_allocation"] = final_alloc
        st.success("✅ Allocation saved to session.")

        if "client_profile" in st.session_state:
            client_data["current_allocation"] = final_alloc
            with open(client_file, "w") as f:
                json.dump(client_data, f, indent=4)
            st.success("✅ Allocation saved to client JSON.")


#======================================================================================================================
# Selected Asset Classes
#======================================================================================================================
st.markdown("---")
st.markdown("<h1 style='color: #CC9900;'>📂 Asset Selection</h1>", unsafe_allow_html=True)

cols = st.columns(3)
for idx, broad_class in enumerate(asset_class_map.keys()):
    subset = df[df["Broad Asset Class"] == broad_class]
    if not subset.empty:
        with cols[idx % 3]:
            st.markdown(f"###### {broad_class}")
            options = [f"{row['name']} – {row['symbol']}" for _, row in subset.iterrows()]
            selected = st.multiselect(f"Select ETFs for {broad_class}", options,
                                      key=f"etfs_{broad_class}_{idx}")
            st.session_state.etf_selection_by_class[broad_class] = selected

# ==== Show Selected ETFs ====
st.markdown("---")
st.markdown("<h2 style='color: #CC9900;'>📋 Selected ETFs</h2>", unsafe_allow_html=True)

selected_symbols = [item.split("–")[-1].strip()
                    for lst in st.session_state.etf_selection_by_class.values() for item in lst]

selected_df = df[df["symbol"].isin(selected_symbols)]
st.dataframe(selected_df)

def fetch_etf_metadata(ticker, api_key):
    base_v4 = "https://financialmodelingprep.com/api/v4"
    base_v3 = "https://financialmodelingprep.com/api/v3"

    def safe_json(url):
        try:
            return requests.get(url).json()
        except:
            return {}

    # General ETF profile info
    profile = safe_json(f"{base_v4}/etf-info?symbol={ticker}&apikey={api_key}")

    # Weights
    sector = safe_json(f"{base_v3}/etf-sector-weightings/{ticker}?apikey={api_key}")
    country = safe_json(f"{base_v3}/etf-country-weightings/{ticker}?apikey={api_key}")

    # Performance metrics
    performance = safe_json(f"{base_v3}/stock-price-change/{ticker}?apikey={api_key}")
    perf_data = performance[0] if performance else {}

    return {
        "name": profile[0].get("name", "") if profile else "",
        "assetClass": profile[0].get("assetClass", "") if profile else "",
        "description": profile[0].get("description", "") if profile else "",
        "expenseRatio": profile[0].get("expenseRatio", None) if profile else None,
        "etfCompany": profile[0].get("etfCompany", "") if profile else "",
        "price": profile[0].get("price", None) if profile else None,
        "exchange": profile[0].get("exchange", "") if profile else "",
        "country_weights": {
            d["country"]: d["weightPercentage"]
            for d in country if "country" in d
        },
        "sector_weights": {
            d["sector"]: d["weightPercentage"]
            for d in sector if "sector" in d
        },
        "performance": {
            k: v for k, v in perf_data.items()
            if k in ["3M", "6M", "YTD", "1Y", "3Y", "5Y"]
        }
    }

col1, col2 = st.columns(2)

with col1:
    if st.button("💾 Confirm Selection"):
        etf_df = selected_df.rename(columns={
            "name": "Name",
            "symbol": "Ticker",
            "Asset Class": "Asset Class"
        })[["Name", "Ticker", "Asset Class"]]
        selected_etfs = etf_df.to_dict("records")

        for etf in selected_etfs:
            try:
                etf["meta"] = fetch_etf_metadata(etf["Ticker"], FMP_API_KEY)
            except Exception as e:
                st.warning(f"⚠️ Could not fetch metadata for {etf['Ticker']}: {e}")

        st.session_state["selected_etfs"] = selected_etfs

        if "client_profile" in st.session_state:
            client_data["selected_etfs"] = selected_etfs
            with open(client_file, "w") as f:
                json.dump(client_data, f, indent=4)
            st.success("✅ Selection with metadata saved to client JSON.")

with col2:
    if st.button("🧾 View Selected Portfolio"):
        selected_portfolio = client_data.get("Selected Portfolio", {})
        if selected_portfolio:
            st.markdown(f"**Strategy:** `{selected_portfolio.get('Name', 'N/A')}`")
            st.markdown("**Weights (%):**")
            for ticker, weight in selected_portfolio.get("Weights", {}).items():
                st.markdown(f"- {ticker}: **{weight * 100:.2f}%**")
        else:
            st.warning("⚠️ No selected portfolio found in the client file.")

    if st.button("📥 Use Saved ETFs"):
        selected_portfolio = client_data.get("Selected Portfolio", {})
        tickers = list(selected_portfolio.get("Weights", {}).keys())

        if tickers:
            selected_etfs = []
            all_etfs = client_data.get("selected_etfs", [])

            for ticker in tickers:
                match = next((etf for etf in all_etfs if etf.get("Ticker") == ticker), None)
                if match:
                    selected_etfs.append(match)
                else:
                    # If missing, fallback to name-only entry
                    selected_etfs.append({
                        "Name": ticker,
                        "Ticker": ticker,
                        "Asset Class": "N/A",
                        "meta": {}
                    })

            st.session_state["selected_etfs"] = selected_etfs
            st.success("✅ Loaded ETFs from saved portfolio.")
        else:
            st.warning("⚠️ No ETF tickers found in selected portfolio.")


#======================================================================================================================
# Navigation
#======================================================================================================================
st.markdown("---")
if st.button("➡️ Optimization"):
    st.switch_page("pages/4_Optimization.py")
