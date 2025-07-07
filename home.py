# import streamlit as st
# from utils.auth_utils import authenticate, logout
#
# # === Initialize session state ===
# if "authenticated" not in st.session_state:
#     st.session_state.authenticated = False
#
# # === Hide sidebar until authenticated ===
# if not st.session_state.authenticated:
#     st.markdown("""
#         <style>
#             [data-testid="stSidebar"] { display: none; }
#         </style>
#     """, unsafe_allow_html=True)
#     authenticate()
#     st.stop()
#
# # === Sidebar after login ===
# with st.sidebar:
#     if st.button("Logout ❌"):
#         logout()
#
#     st.image("assets/QuantFiniti_BlackGold.png", use_container_width=True)
#     st.markdown(f"**Logged in as:** {st.session_state.username}")
#     st.divider()
#
# # === Main Dashboard Header ===
# st.image("assets/QuantOptima_BlackGold.png", use_container_width=True)
#
# st.markdown(
#     """
#         <h1 style="color:#CC9900; text-align:center;">Welcome to QuantOptima Dashboard</h1>
#     <p style="text-align:center; font-size:18px; color:#CC9900;">
#         Leverage smart allocation, risk-aware optimization, and AI-powered insights to build resilient portfolios.<br>
#         QuantOptima equips asset managers and investors with institutional-grade tools for performance excellence.
#     </p>
#     <hr style="border:1px solid #CC9900;">
#     """, unsafe_allow_html=True
# )


import streamlit as st
from utils.auth_utils import authenticate, logout

# === Initialize session state ===
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# === Sidebar after login ===
if st.session_state.authenticated:
    with st.sidebar:
        if st.button("Logout ❌"):
            logout()

        st.image("assets/QuantFiniti_BlackGold.png", use_container_width=True)
        st.markdown(f"**Logged in as:** {st.session_state.username}")
        st.divider()

# === Authentication Gate ===
if not st.session_state.authenticated:
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }
        </style>
    """, unsafe_allow_html=True)
    authenticate()
    st.stop()

# === Main Dashboard Header ===
st.image("assets/QuantOptima_BlackGold.png", use_container_width=True)

st.markdown(
    """
        <h1 style="color:#CC9900; text-align:center;">Welcome to QuantOptima Dashboard</h1>
    <p style="text-align:center; font-size:18px; color:#CC9900;">
        Leverage smart allocation, risk-aware optimization, and AI-powered insights to build resilient portfolios.<br>
        QuantOptima equips asset managers and investors with institutional-grade tools for performance excellence.
    </p>
    <hr style="border:1px solid #CC9900;">
    """, unsafe_allow_html=True
)
