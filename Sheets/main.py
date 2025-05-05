import streamlit as st


st.write("Use the sidebar to navigate to different Sheets.")
# --- Sidebar Logo ---
#st.sidebar.image("assets/Quant Sphere.jpeg", use_container_width=True)

# --- Welcome sheets ---
st.image("assets/Quant Optima3.png", use_container_width=True)  # ✅ Add this line

st.markdown(
    """
    <h1 style="color:#FFFFFF; text-align:center;">Welcome to Quant Optima Dashboard</h1>
    <p style="text-align:center; font-size:18px; color:#FFFFFF;">
        Optimize your portfolio with advanced algorithms, AI-driven analytics, and risk-adjusted strategies for superior performance.
        QuantOptima equips you with cutting-edge tools to construct, analyze, and optimize portfolios with precision.


    </p>
    <hr style="border:1px solid #FFFFFF;">
    """, unsafe_allow_html=True
)
