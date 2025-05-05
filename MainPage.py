# MainPage.py

import streamlit as st

# =========================================================================================
# Authentication Setup
# =========================================================================================

USERNAME = "BlackRock"
PASSWORD = "DemoAccess123"

# Store login state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Hide sidebar before login
hide_sidebar_style = """
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
"""

def authenticate():
    st.title("🔒 QuantOptima Login")
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")

    if username_input == USERNAME and password_input == PASSWORD:
        st.session_state.authenticated = True
        st.session_state.username = username_input
        st.success("Login successful!")
        st.rerun()
    elif username_input and password_input:
        st.error("Invalid credentials. Please try again.")

def logout():
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()

# Authentication Gate
if not st.session_state.authenticated:
    st.markdown(hide_sidebar_style, unsafe_allow_html=True)
    authenticate()
    st.stop()

# =========================================================================================
# Sidebar after login
# =========================================================================================

with st.sidebar:
    st.image("assets/Quant Optima3.png", use_container_width=True)    # Adjust path & sizing as needed
    st.markdown(f"**Logged in as:** {st.session_state.username}")
    if st.button("Logout ❌"):
        logout()

#*******************************************************************************************
#*******************************************************************************************
# Page Setup
#*******************************************************************************************
#*******************************************************************************************

Main_Page = st.Page(
    page="Sheets/main.py",  # Updated path to reflect the "Sheets" directory
    title="Home Page",
    icon="🏠",
    default=True)

Client_Setup = st.Page(
    page="Sheets/ClientSetup.py",  # Updated path to reflect the "Sheets" directory
    title="1- Client Setup",
    icon="💬",)

About_page = st.Page(
    page="Sheets/about_me.py",  # Updated path
    title="About Me",
    icon="🤵",)

Asset_Selection = st.Page(
    page="Sheets/AssetSelection.py",  # Updated path
    title="2- Asset Selection",
    icon="🎢",)

Port_Optimization = st.Page(
    page="Sheets/PortfolioOptimization.py",  # Updated path
    title="3- Portfolio Optimization",
    icon="🎯",)

Results_page = st.Page(
    page="Sheets/Report.py",  # Updated path
    title="4- Generate Report",
    icon="📚",)

#*******************************************************************************************
#*******************************************************************************************
# Navigation Setup
#*******************************************************************************************
#*******************************************************************************************

pg = st.navigation(
    {
        "Main Page": [Main_Page],
        "Asset Selection & Optimization": [Client_Setup, Asset_Selection, Port_Optimization],
        "Results ": [Results_page],
        "Info": [About_page],
    }
)
#*******************************************************************************************
#*******************************************************************************************
# Run
#*******************************************************************************************
#*******************************************************************************************

pg.run()      # Run the navigation and Sheets