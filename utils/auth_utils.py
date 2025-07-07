# utils/auth_utils.py
import streamlit as st
import toml
import os

# === Load Credentials from config ===
def load_credentials():
    credentials_path = os.path.join("config", "credentials.toml")
    if not os.path.exists(credentials_path):
        raise FileNotFoundError("❌ credentials.toml file not found in config folder")
    return toml.load(credentials_path)

# === Authenticate Function ===
def authenticate():
    st.title("Login")
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")

    credentials = load_credentials().get("users", [])
    valid_user = next((u for u in credentials if u["username"] == username_input and u["password"] == password_input), None)

    if valid_user:
        st.session_state.authenticated = True
        st.session_state.username = username_input
        st.success("✅ Logged in successfully!")
        st.rerun()
    elif username_input and password_input:
        st.error("❌ Invalid credentials. Please try again.")

# === Logout Function ===
def logout():
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()
