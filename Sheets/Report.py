import streamlit as st

# ── Catch import errors ──────────────────────────────────────
try:
    from Sheets.generate_pdf_report import generate_pdf_report
except Exception as e:
    st.error(f"❌ Failed to import PDF generator: {e}")
    st.stop()
# ─────────────────────────────────────────────────────────────

import sys, os
sys.path.append(os.path.dirname(__file__))

st.write("Working Directory:", os.getcwd())
st.title("📄 Generate Final PDF Report")

# --- Form to collect report inputs ---
with st.form("report_inputs"):
    client_name = st.session_state.get("client_name", "Client Name")
    investment_amount = st.session_state.get("investment_amount", 0)
    executive_summary = st.text_area("Executive Summary", height=200)
    macro_context      = st.text_area("Macroeconomic Overview", height=200)

    st.markdown("### Asset Class Comments")
    equities_comment     = st.text_area("Equities", height=150)
    fixed_income_comment = st.text_area("Fixed Income", height=150)
    real_estate_comment  = st.text_area("Real Estate", height=150)
    commodities_comment  = st.text_area("Commodities", height=150)
    alternatives_comment = st.text_area("Alternatives", height=150)

    generate_report = st.form_submit_button("📄 Generate Report")

# --- Generate and download PDF ---
if generate_report:
    asset_class_comments = {
        "Equities": equities_comment,
        "Fixed Income": fixed_income_comment,
        "Real Estate": real_estate_comment,
        "Commodities": commodities_comment,
        "Alternatives": alternatives_comment,
    }

    # Wrap PDF generation in try/except
    try:
        pdf_buffer = generate_pdf_report(
            client_name,
            investment_amount,
            executive_summary,
            macro_context,
            asset_class_comments,
            st.session_state.get("current_allocation", {}),
            st.session_state.get("manual_asset_alloc", {})
        )
    except Exception as e:
        st.error(f"❌ Error generating PDF: {e}")
        st.stop()

    st.success("✅ Report generated successfully!")
    st.download_button(
        label=f"📥 Download {client_name}_Report.pdf",
        data=pdf_buffer,
        file_name=f"{client_name}_QuantOptima_Report.pdf",
        mime="application/pdf"
    )
