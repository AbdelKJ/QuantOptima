# utils/layout_utils.py
import streamlit as st
from utils.auth_utils import logout

def render_sidebar():
    with st.sidebar:
        if st.button("Logout ❌"):
            logout()
        st.image("assets/QuantFiniti_BlackGold.png", use_container_width=True)
        st.markdown(f"**Logged in as:** {st.session_state.username}")
        st.divider()
