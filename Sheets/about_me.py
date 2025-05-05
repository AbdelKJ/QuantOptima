import streamlit as st

# ========================================================
# ABOUT ME PAGE
# ========================================================

# --- Fancy Divider Function ---
def fancy_divider():
    st.markdown(
        """
        <hr style="border: 0; height: 2px; background: linear-gradient(to right, #FFB343, #6F1D1B); margin: 20px 0;">
        """,
        unsafe_allow_html=True,
    )

st.title("About Me 🤵")
st.write("Welcome to QuantOptima! Here's a bit about the creator of this platform.")

# -----------------------------------
# Contact Button with Real Info
# -----------------------------------
@st.dialog("Contact Me")
def show_contact_form():
    st.write("📧 Email: abdel.joubaili@gmail.com")
    st.write("📞 Phone: +965 9725-3715")
    st.write("[🔗 LinkedIn Profile](https://www.linkedin.com/in/abdel-karim-joubaili-ab120540/)")

# -----------------------------------
# Hero Section (Photo + Profile)
# -----------------------------------
col1, col2 = st.columns(2, gap="small")
with col1:
    st.image("./assets/myPhoto2.jpg", width=230)
with col2:
    st.header("Dr. Abdel Karim Joubaili", anchor=False)
    st.caption("Executive Director, Asset Management")
    st.caption("National Investments Company, Kuwait")
    st.markdown("**PhD in Economics | 15+ Years Asset Management | Quantitative Finance Expert**")
    if st.button("✉️ Contact Me"):
        show_contact_form()

fancy_divider()

# -----------------------------------
# Short Summary
# -----------------------------------
st.markdown("""
Accomplished and intuitive Asset Management Executive with over 15 years of experience managing multi-billion-dollar portfolios across equities, fixed income, real estate, and alternative investments.

Strong expertise in Strategic Asset Management, Quantitative Research, and Data-Driven Portfolio Optimization.

Passionate about blending finance, economics, and technology to deliver high-performance investment solutions tailored to client needs.
""")

fancy_divider()

# -----------------------------------
# Education
# -----------------------------------
st.subheader("🎓 Education", anchor=False)
st.markdown("""
- **PhD in Economics** – Macquarie University, Sydney, Australia  
  *(Thesis: Empirical Investigation into Dynamic Asset Allocation Models)*
- **Master of Science in Economics** – Macquarie University, Sydney, Australia
- **Bachelor of Science in Economics** – Macquarie University, Sydney, Australia
""")

fancy_divider()

# -----------------------------------
# Professional Experience
# -----------------------------------
st.subheader("🏢 Professional Experience", anchor=False)
st.markdown("""
- **Executive Director, Asset Management**  
  *National Investments Company, Kuwait*  
  - Managing USD 3.5 billion+ across multi-asset portfolios
  - Leading portfolio management, fund management, trading, and research teams
  - Member of investment committees shaping asset allocation strategies

- **Head of Quantitative Asset Management**  
  *KFH Capital, Kuwait*  
  - Established Quantitative Asset Management and Market-Making departments
  - Developed systematic strategies for portfolio construction and risk management

- **VP, Equities Portfolio Management**  
  *Gulf Investment Corporation, Kuwait*  
  - Led regional and international equity strategies
  - Focused on alpha generation, risk control, and multi-asset research
""")

fancy_divider()

# -----------------------------------
# Areas of Expertise
# -----------------------------------
st.subheader("🛠️ Areas of Expertise", anchor=False)
st.markdown("""
- Strategic Asset Allocation & Management
- Portfolio Optimization & Risk-Adjusted Returns
- Quantitative Research & Data Analysis
- Financial Modeling & Technology Integration
- Multi-Asset Investing: Equities, Fixed Income, Real Estate, Alternatives
- Economic Research & Market Intelligence
- Client Engagement & Relationship Management
""")

fancy_divider()

# -----------------------------------
# Technical Skills
# -----------------------------------
st.subheader("💻 Technical Skills", anchor=False)
st.markdown("""
- **Programming**: Python, VBA, Matlab
- **Financial Tools**: Bloomberg, Reuters, FactSet
- **Quantitative Techniques**: Portfolio Optimization, Machine Learning for Finance, Risk Management
""")

fancy_divider()

# -----------------------------------
# Languages
# -----------------------------------
st.subheader("🌍 Languages", anchor=False)
st.markdown("""
- English (Fluent)
- Arabic (Fluent)
""")

# ========================================================
# END OF PAGE
# ========================================================

