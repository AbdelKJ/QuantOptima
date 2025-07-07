import streamlit as st
st.set_page_config(page_title="About Me", layout="wide")
import base64
import os
from utils.layout_utils import render_sidebar

# === Page Setup ===
# Run sidebar for all pages
render_sidebar()


# === Fancy Divider ===
def fancy_divider():
    st.markdown(
        """<hr style="border: 0; height: 2px; background: linear-gradient(to right, #FFB343, #6F1D1B); margin: 30px 0;">""",
        unsafe_allow_html=True
    )

# === Contact Info Display ===
def show_contact_info():
    st.markdown("""
    **📧 Email**: [abdel.joubaili@gmail.com](mailto:abdel.joubaili@gmail.com)  
    **📞 Phone**: +965 9725-3715  
    **🔗 LinkedIn**: [Visit Profile](https://www.linkedin.com/in/abdel-karim-joubaili-ab120540/)
    """)

# === Download PDF Button ===
def download_pdf_button(pdf_path, label="📄 Download My CV"):
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        href = f'<a href="data:application/octet-stream;base64,{base64_pdf}" download="Abdel_Karim_Joubaili_CV.pdf">{label}</a>'
        st.markdown(href, unsafe_allow_html=True)

# === Header Section ===
col1, col2 = st.columns([1, 2], gap="large")
with col1:
    st.image("assets/myphoto.jpg", width=250)
with col2:
    st.title("👋 Dr. Abdel Karim Joubaili")
    st.caption("Executive Director – Asset Management, National Investments Company, Kuwait")
    st.markdown("**PhD in Economics | 15+ Years in Asset Management | Quantitative Finance Expert**")
    st.markdown("Welcome to **QuantOptima**, part of the Q-Finity ecosystem.")

    contact_clicked = st.button("✉️ Contact Me", key="contact_button")
    if os.path.exists("assets/Karim_CV.pdf"):
        download_pdf_button("assets/Karim_CV.pdf")
    else:
        st.info("📄 CV is currently unavailable for download.")

if contact_clicked:
    fancy_divider()
    st.subheader("📬 Contact Information")
    show_contact_info()

fancy_divider()

# === About Me ===
st.subheader("📖 About Me")
st.markdown("""
I am an accomplished and intuitive **Asset Management Executive** with over 15 years of experience managing multi-billion-dollar portfolios across equities, fixed income, real estate, and alternative investments.

My expertise lies in **strategic asset allocation**, **quantitative research**, and **data-driven portfolio optimization**, blending finance, economics, and technology to deliver high-performance investment solutions tailored to client needs.
""")

fancy_divider()

# === Education ===
st.subheader("🎓 Education")
st.markdown("""
- **PhD in Economics** – Macquarie University, Sydney  
  *(Thesis: Empirical Investigation into Dynamic Asset Allocation Models)*  
- **MSc in Economics** – Macquarie University, Sydney  
- **BSc in Economics** – Macquarie University, Sydney  
""")

fancy_divider()

# === Experience ===
st.subheader("💼 Professional Experience")
st.markdown("""
### 🔹 Executive Director – National Investments Company, Kuwait  
- Manage USD 3.5 billion+ across multi-asset portfolios.  
- Lead portfolio management, fund management, trading, and research teams.  
- Serve on investment committees shaping asset allocation strategies.  

### 🔹 Head of Quantitative Asset Management – KFH Capital, Kuwait  
- Established Quantitative Asset Management and Market-Making departments.  
- Developed systematic strategies for portfolio construction and risk management.  

### 🔹 VP, Equities Portfolio Management – Gulf Investment Corporation, Kuwait  
- Led regional and international equity strategies.  
- Focused on alpha generation, risk control, and multi-asset research.  
""")

fancy_divider()

# === Expertise ===
st.subheader("🛠️ Areas of Expertise")
st.markdown("""
✅ Strategic Asset Allocation & Management  
✅ Portfolio Optimization & Risk-Adjusted Returns  
✅ Quantitative Research & Data Analysis  
✅ Financial Modeling & Technology Integration  
✅ Multi-Asset Investing: Equities, Fixed Income, Real Estate, Alternatives  
✅ Economic Research & Market Intelligence  
✅ Client Engagement & Relationship Management  
""")

fancy_divider()

# === Technical Skills ===
st.subheader("💻 Technical Skills")
st.markdown("""
- **Programming**: Python, VBA, Matlab  
- **Financial Tools**: Bloomberg, Refinitiv, FactSet  
- **Quant Techniques**: Optimization, Machine Learning for Finance, CVaR, Risk Budgeting  
""")

fancy_divider()

# === Languages ===
st.subheader("🌍 Languages")
st.markdown("""
- English (Fluent)  
- Arabic (Fluent)  
""")

fancy_divider()
