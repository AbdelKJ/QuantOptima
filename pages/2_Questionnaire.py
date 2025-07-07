#======================================================================================================================
# Dependant Libraries
#======================================================================================================================
import streamlit as st
import json
import os
from utils.layout_utils import render_sidebar


#======================================================================================================================
# Page Setup
#======================================================================================================================
st.set_page_config(page_title="Risk Questionnaire", layout="wide")
render_sidebar()

st.markdown(
    "<h1 style='color: #CC9900;'>📊 Risk Profile Questionnaire</h1>",
    unsafe_allow_html=True
)


#======================================================================================================================
# Questionnaire
# =====================================================================================================================
st.markdown("Please answer the following questions to help us assess your risk tolerance and return expectations.")

# === Load Existing Answers ===
existing_answers = {}
if "client_profile" in st.session_state:
    client_name = st.session_state["client_profile"]["name"]
    json_path = f"data/clients/{client_name}/{client_name}.json"
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            existing_answers = json.load(f).get("risk_answers", {})

questions = [
    ("What is your investment horizon?", ["< 1 year", "1-3 years", "3-5 years", "> 5 years"]),
    ("What is your primary investment goal?", ["Capital Preservation", "Income", "Balanced Growth", "Aggressive Growth"]),
    ("How would you react to a 10% drop in your portfolio value?", ["Sell immediately", "Reduce exposure", "Hold", "Buy more"]),
    ("How much risk are you willing to take to achieve higher returns?", ["Very Low", "Low", "Moderate", "High"]),
    ("What percentage of your total wealth is this portfolio?", ["< 10%", "10%-25%", "25%-50%", "> 50%"]),
    ("How frequently do you monitor your investments?", ["Daily", "Weekly", "Monthly", "Rarely"]),
    ("How familiar are you with financial products?", ["Not at all", "Somewhat", "Well-informed", "Expert"]),
    ("What best describes your income stability?", ["Very unstable", "Unstable", "Stable", "Very stable"]),
    ("Where is your current portfolio primarily invested?", ["Domestic markets", "Regional markets (e.g., GCC, MENA)", "Global markets"]),
    ("Where would you prefer new investments to be allocated?", ["Domestic markets", "Regional markets (e.g., GCC, MENA)", "Global markets"]),
    ("Are you open to investing in emerging markets?", ["No", "Limited exposure", "Yes, if returns justify the risk"]),
    ("Are you open to investing in developed markets?", ["No", "Limited exposure", "Yes"]),
    ("Are you comfortable with short selling?", ["No", "Maybe", "Yes"]),
    ("Are you comfortable with portfolio leverage (borrowing to invest more)?", ["No", "Somewhat", "Yes"])
]

responses = {}
left, right = st.columns(2)
for i, (q, options) in enumerate(questions):
    with (left if i % 2 == 0 else right):
        responses[q] = st.radio(q, options, index=options.index(existing_answers.get(q, options[0])), key=q)


#======================================================================================================================
# Scoring
# =====================================================================================================================
def score_profile(res):
    scores = {
        "< 1 year": 1, "1-3 years": 2, "3-5 years": 3, "> 5 years": 4,
        "Capital Preservation": 1, "Income": 2, "Balanced Growth": 3, "Aggressive Growth": 4,
        "Sell immediately": 1, "Reduce exposure": 2, "Hold": 3, "Buy more": 4,
        "Very Low": 1, "Low": 2, "Moderate": 3, "High": 4,
        "< 10%": 1, "10%-25%": 2, "25%-50%": 3, "> 50%": 4,
        "Daily": 1, "Weekly": 2, "Monthly": 3, "Rarely": 4,
        "Not at all": 1, "Somewhat": 2, "Well-informed": 3, "Expert": 4,
        "Very unstable": 1, "Unstable": 2, "Stable": 3, "Very stable": 4
    }
    return sum(scores.get(res[q], 0) for q in res)

def map_score_to_lambda(score):
    return 1 if score >= 42 else 3 if score >= 35 else 5 if score >= 28 else 10 if score >= 21 else 20

def explain_asset_allocation(level):
    if level == "Aggressive":
        return "You are suited for a growth-oriented portfolio: higher equities (global and emerging markets), tech, thematic ETFs, and low bond exposure."
    elif level == "Moderate":
        return "A balanced mix of global equities, sector ETFs, and medium-duration bonds fits your profile well."
    elif level == "Conservative":
        return "Focus on capital preservation with exposure to high-quality bonds, defensive sectors, dividend-paying equities, and regional exposure."
    else:
        return "A highly conservative allocation focused on low-volatility assets, capital protection strategies, and stable income products is recommended."


#======================================================================================================================
# Button controls
# =====================================================================================================================
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("✅ Submit Questionnaire"):
        risk_score = score_profile(responses)
        risk_level = "Aggressive" if risk_score >= 42 else "Moderate" if risk_score >= 28 else "Conservative"
        lambda_val = map_score_to_lambda(risk_score)
        explanation = explain_asset_allocation(risk_level)

        st.session_state.update({
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_lambda": lambda_val,
            "risk_answers": responses,
            "allow_short": responses.get("Are you comfortable with short selling?", "No") == "Yes",
            "allow_leverage": responses.get("Are you comfortable with portfolio leverage (borrowing to invest more)?", "No") == "Yes"
        })

        if "client_profile" in st.session_state:
            client_name = st.session_state["client_profile"]["name"]
            folder_name = client_name.replace(" ", "_")  # Normalized folder
            client_dir = f"data/clients/{folder_name}"
            json_file = f"{client_dir}/{folder_name}.json"

            os.makedirs(client_dir, exist_ok=True)

            if os.path.exists(json_file):
                with open(json_file, "r") as f:
                    client_data = json.load(f)
            else:
                client_data = st.session_state["client_profile"]

            client_data.update({
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_lambda": lambda_val,
                "risk_answers": responses,
                "allow_short": st.session_state["allow_short"],
                "allow_leverage": st.session_state["allow_leverage"]
            })

            with open(json_file, "w") as f:
                json.dump(client_data, f, indent=4)

            st.success(f"✅ Risk Profile Saved")
            st.info(f"📈 Risk Level: **{risk_level}** | 🔢 Score: {risk_score} | λ = **{lambda_val}**")
            st.markdown(f"🧠 **AI Insight:** {explanation}")
        else:
            st.error("⚠️ No client found. Please fill in Client Info page first.")

with col2:
    if st.button("🔁 Keep Answers"):
        st.success("✅ Previous answers retained.")

with col3:
    if st.button("➡️ Asset Selection"):
        st.switch_page("pages/3_Asset_Selection.py")