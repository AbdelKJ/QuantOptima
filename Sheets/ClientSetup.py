import streamlit as st
import pandas as pd
import plotly.express as px

# ==================== INITIAL STATE ====================
if "client_name" not in st.session_state:
    st.session_state.client_name = ""
if "investment_amount" not in st.session_state:
    st.session_state.investment_amount = 10000
if "current_allocation" not in st.session_state:
    st.session_state.current_allocation = {
        "Equities": 50,
        "Real Estate": 20,
        "Commodities": 20,
        "Fixed Income": 10,
        "Alternatives": 0,
        "Cash": 0
    }

st.title("🧑‍💼 Client Setup")
st.markdown("Please input the client's basic information to get started.")

# ==================== FORM ====================
with st.form("client_setup_form"):
    client_name = st.text_input(
        "Client Name",
        value=st.session_state.client_name,
        placeholder="Enter full name..."
    )
    investment_amount = st.number_input(
        "Hypothetical Capital (USD)",
        min_value=10000,
        step=10000,
        value=st.session_state.investment_amount
    )

    st.markdown("### Current Allocation")
    equities_pct = st.slider("Equities (%)", 0, 100, st.session_state.current_allocation.get("Equities", 50))
    real_estate_pct = st.slider("Real Estate (%)", 0, 100, st.session_state.current_allocation.get("Real Estate", 20))
    commodities_pct = st.slider("Commodities (%)", 0, 100, st.session_state.current_allocation.get("Commodities", 20))
    fixed_income_pct = st.slider("Fixed Income (%)", 0, 100, st.session_state.current_allocation.get("Fixed Income", 10))
    alternatives_pct = st.slider("Alternatives (%)", 0, 100, st.session_state.current_allocation.get("Alternatives", 0))

    # 🔥 Buttons side by side
    col1, col2 = st.columns([1, 1])
    with col1:
        submitted = st.form_submit_button("✅ Save Client Info")
    with col2:
        clear_clicked = st.form_submit_button("🗑️ Clear Client Info")

# ==================== SAVE ====================
if submitted:
    total_alloc = equities_pct + real_estate_pct + commodities_pct + fixed_income_pct + alternatives_pct

    if total_alloc > 100:
        st.error(f"❌ Total allocation exceeds 100%! Your total is {total_alloc}%. Please adjust.")
    else:
        cash_pct = 100 - total_alloc
        st.session_state.client_name = client_name
        st.session_state.investment_amount = investment_amount
        st.session_state.current_allocation = {
            "Equities": equities_pct,
            "Real Estate": real_estate_pct,
            "Commodities": commodities_pct,
            "Fixed Income": fixed_income_pct,
            "Alternatives": alternatives_pct,
            "Cash": cash_pct
        }

        st.success(f"✅ Client information saved for {client_name}!")

        # === Summary
        st.write("### Summary:")
        st.write(f"**Client Name:** {client_name}")
        st.write(f"**Capital to Invest:** ${investment_amount:,.0f}")

        allocation_df = pd.DataFrame({
            "Asset Class": list(st.session_state.current_allocation.keys()),
            "Allocation (%)": list(st.session_state.current_allocation.values())
        })
        allocation_df["Dollar Value (USD)"] = (allocation_df["Allocation (%)"] / 100) * investment_amount

        st.dataframe(allocation_df, use_container_width=True)

        fig = px.pie(
            allocation_df,
            names="Asset Class",
            values="Allocation (%)",
            title="Portfolio Allocation Breakdown",
            hole=0.3,
            color_discrete_sequence=px.colors.sequential.YlOrBr
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=True)

        st.plotly_chart(fig, use_container_width=True)

# ==================== CLEAR ====================
if clear_clicked:
    st.session_state.client_name = ""
    st.session_state.investment_amount = 10000
    st.session_state.current_allocation = {
        "Equities": 50,
        "Real Estate": 20,
        "Commodities": 20,
        "Fixed Income": 10,
        "Alternatives": 0,
        "Cash": 0
    }
    st.success("✅ Client information cleared!")

    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        st.warning("Please manually refresh the page to see cleared values.")

# ==================== NAVIGATION ====================
if st.session_state.client_name:
    st.success(f"Client data for {st.session_state.client_name} is saved and ready.")
    if st.button("➡️ Proceed to Asset Selection"):
        st.switch_page("Sheets/AssetSelection.py")
