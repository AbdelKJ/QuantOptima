#======================================================================================================================
# Dependant Libraries
#======================================================================================================================
import streamlit as st
st.set_page_config(page_title="Client Information", layout="wide")
import json
import os
from utils.layout_utils import render_sidebar


#======================================================================================================================
# Page Setup
#======================================================================================================================
# Run sidebar for all pages
render_sidebar()

st.markdown(
    "<h1 style='color: #CC9900;'>🧾 Client Setup</h1>",
    unsafe_allow_html=True
)


#======================================================================================================================
# Helper Functions
#======================================================================================================================
def get_client_folder(name):
    return f"data/clients/{name.replace(' ', '_')}"

def get_client_file(name):
    folder = get_client_folder(name)
    return os.path.join(folder, f"{name.replace(' ', '_')}.json")

def load_client_data(name):
    path = get_client_file(name)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


#======================================================================================================================
# Client Setup
#======================================================================================================================
client_type = st.radio("Client Type", ["New", "Existing"], horizontal=True)

if client_type == "Existing":
    os.makedirs("data/clients", exist_ok=True)

    # Get all folders (each folder is a client)
    folders = [f for f in os.listdir("data/clients") if os.path.isdir(os.path.join("data/clients", f))]

    client_options = []
    valid_clients = {}

    for folder in folders:
        client_json_path = os.path.join("data/clients", folder, f"{folder}.json")
        if os.path.exists(client_json_path):
            # Display with spaces, keep folder key internally
            display_name = folder.replace("_", " ")
            client_options.append(display_name)
            valid_clients[display_name] = client_json_path

    if client_options:
        client_option = st.selectbox("Select Existing Client", client_options)
        if client_option:
            # Load the correct JSON based on the displayed name
            client_file_path = valid_clients[client_option]
            with open(client_file_path, "r") as f:
                client_data = json.load(f)

            # Save to session for later use
            st.session_state["client_profile"] = client_data
            st.session_state["client_file"] = client_file_path  # optional: in case you want to reference the path later


            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("<h2 style='color: #CC9900;'>🧾 Client Information</h2>", unsafe_allow_html=True)
                name = st.text_input("Name", value=client_data.get("name", ""))
                email = st.text_input("Email", value=client_data.get("email", ""))
                phone = st.text_input("Phone", value=client_data.get("phone", ""))
                country = st.text_input("Country", value=client_data.get("country", ""))
                company = st.text_input("Company", value=client_data.get("company", ""))

                if st.button("💾 Edit Client Info"):
                    client_data.update({
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "country": country,
                        "company": company
                    })
                    folder = get_client_folder(name)
                    os.makedirs(folder, exist_ok=True)
                    with open(get_client_file(name), "w") as f:
                        json.dump(client_data, f, indent=4)
                    st.success("✅ Client information updated.")

            with col2:
                st.markdown("<h2 style='color: #CC9900;'>📉 Risk Aversion Information</h2>", unsafe_allow_html=True)
                risk_score = client_data.get("risk_score", "N/A")
                risk_level = client_data.get("risk_level", "N/A")
                risk_answers = client_data.get("risk_answers", {})

                st.markdown(f"**Risk Level:** {risk_level}")
                st.markdown(f"**Risk Score:** {risk_score}")

                if risk_answers:
                    st.markdown("**📋 Questionnaire Answers:**")
                    for q, a in risk_answers.items():
                        st.markdown(f"- {q}: **{a}**")
                else:
                    st.markdown("No questionnaire answers found.")

                if st.button("✏️ Edit Questionnaire"):
                    st.switch_page("pages/2_Questionnaire.py")

            with col3:
                st.markdown("<h2 style='color: #CC9900;'>📊 Allocation Information</h2>", unsafe_allow_html=True)
                selected_portfolio = client_data.get("Selected Portfolio", {})
                etfs = client_data.get("selected_etfs")

                if selected_portfolio:
                    portfolio_name = selected_portfolio.get("Name", "N/A")
                    weights = selected_portfolio.get("Weights", {})

                    st.markdown(f"**Selected Portfolio Strategy:** `{portfolio_name}`")
                    st.markdown("**Weights (%):**")
                    for ticker, weight in weights.items():
                        st.markdown(f"- {ticker}: **{weight * 100:.2f}%**")
                else:
                    st.markdown("⚠️ No selected portfolio found in the JSON.")

                if etfs:
                    st.markdown("**Selected ETFs (%):**")
                    for etf in etfs:
                        name = etf.get("Name", "Unknown")
                        weight = etf.get("Weight", "N/A")
                        st.markdown(f"- {name}: **{weight}%**")

                if st.button("✏️ Edit Allocation"):
                    st.switch_page("pages/3_Asset_Selection.py")

            # Footer Actions
            st.markdown("---")
            colA, colB = st.columns(2)

            with colB:
                if st.button("🗑️ Delete Client"):
                    if "client_profile" in st.session_state and st.session_state.client_profile.get("name"):
                        client_name = st.session_state.client_profile.get("name").replace(" ", "_")
                        folder = get_client_folder(client_name)
                        try:
                            if os.path.exists(folder):
                                import shutil

                                shutil.rmtree(folder)
                                st.success(f"✅ Client '{client_name}' deleted.")
                                st.rerun()
                            else:
                                st.error("❌ Client folder not found.")
                        except Exception as e:
                            st.error(f"❌ Failed to delete client: {e}")
                    else:
                        st.error("⚠️ No client selected to delete.")

            with colA:
                if st.button("➡️ Generate Report"):
                    if "client_profile" in st.session_state and st.session_state.client_profile.get("name"):
                        st.switch_page("pages/5_PDF_Report.py")
                    else:
                        st.error("❌ Please select or create a client first.")

elif client_type == "New":
    st.markdown("<h2 style='color: #CC9900;'>📝 Enter New Client Details</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Client Name")
        email = st.text_input("Email")
        country = st.text_input("Country")
    with col2:
        phone = st.text_input("Phone Number")
        company = st.text_input("Company")

    if st.button("✅ Save New Client"):
        if name and email:
            new_client_data = {
                "name": name,
                "email": email,
                "phone": phone,
                "country": country,
                "company": company,
            }
            folder = get_client_folder(name)
            os.makedirs(folder, exist_ok=True)
            with open(get_client_file(name), "w") as f:
                json.dump(new_client_data, f, indent=4)

            st.session_state.client_profile = new_client_data
            st.success(f"New client '{name}' saved.")

            # 🔁 Do NOT rerun if you plan to switch pages
            st.switch_page("pages/2_Questionnaire.py")
        else:
            st.error("Name and Email are required.")