#======================================================================================================================
#======================================================================================================================
# Dependant Libraries
#======================================================================================================================
#======================================================================================================================
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
import json
import os
import re
import matplotlib.pyplot as plt
from reportlab.lib.utils import ImageReader
import matplotlib.colors as mcolors
from io import BytesIO
from reportlab.lib.colors import Color
from collections import Counter
from collections import defaultdict
from datetime import date, timedelta
import pandas as pd
import riskfolio as rp
import seaborn as sns
import numpy as np
import scipy.stats as stats
import bt
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

pdfmetrics.registerFont(TTFont('Times-Italic', 'timesi.ttf'))


#======================================================================================================================
# Page Layout
#======================================================================================================================
PAGE_WIDTH, PAGE_HEIGHT = A4
TOP_MARGIN = 70
BOTTOM_MARGIN = 70
LEFT_MARGIN = 60
RIGHT_MARGIN = 60
LINE_HEIGHT = 14
TOC_LINE_SPACING = 22
FONT_NAME = "Times-Roman"
TITLE_COLOR = HexColor("#8B7500")
TEXT_COLOR = HexColor("#000000")


#======================================================================================================================
# Calling Json File for Client
#======================================================================================================================
client_data = {}
objective_commentary = ""

if "client_profile" in st.session_state:
    client_name = st.session_state["client_profile"]["name"]
    folder_name = client_name.replace(" ", "_")
    client_file = f"data/clients/{folder_name}/{folder_name}.json"

    if os.path.exists(client_file):
        with open(client_file, "r") as f:
            client_data = json.load(f)
        st.session_state["client_data"] = client_data
        objective_commentary = client_data.get("final_objective_text", "")
    else:
        st.error(f"❌ Client JSON file not found at: {client_file}")
else:
    st.error("❌ No client profile found in session state.")


#======================================================================================================================
# Streamlit Interface
#======================================================================================================================
st.markdown("<h1 style='color: #CC9900;'>📄 Asset Allocation Report</h1>", unsafe_allow_html=True)
inv_note = st.text_area("Investment Note")
exec_summary = st.text_area("Executive Summary")
macro_perspective = st.text_area("Macro & Markets Perspective")
st.markdown("<h3 style='color: #CC9900;'>Asset Classes Outlook</h3>", unsafe_allow_html=True)
asset_outlooks = {ac: st.text_area(f"Outlook for {ac}") for ac in ["Equities", "Fixed Income", "Alternatives",
                                                                   "Commodities", "Real Estate"]}

#======================================================================================================================
# Helper Functions for Text Wrapping
#======================================================================================================================

# Text Wrapping
#-------------------------------------------
def draw_wrapped_text(c, text, y_pos, indent=0, font_name=FONT_NAME, font_size=12, font_color=TEXT_COLOR):
    """
    Draws multi-line wrapped text with proper page-break handling.

    Returns:
        new_y_pos (float or None): Updated vertical position after drawing. None if new page is needed.
        remaining_text (str or None): Remaining text to draw if page break occurred, else None.
    """
    c.setFont(font_name, font_size)
    c.setFillColor(font_color)

    usable_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN - indent
    paragraphs = text.split("\n\n")

    for para_index, para in enumerate(paragraphs):
        cleaned = ' '.join(para.strip().splitlines())
        words = cleaned.split()
        line = ""
        word_index = 0

        while word_index < len(words):
            test_line = f"{line}{words[word_index]} "
            if stringWidth(test_line, font_name, font_size) <= usable_width:
                line = test_line
                word_index += 1
            else:
                c.drawString(LEFT_MARGIN + indent, y_pos, line.strip())
                y_pos -= LINE_HEIGHT
                if y_pos < BOTTOM_MARGIN:
                    remaining_current = " ".join(words[word_index:]).strip()
                    remaining_text = "\n\n".join(
                        [remaining_current] + paragraphs[para_index + 1:]
                    ) if remaining_current else "\n\n".join(paragraphs[para_index + 1:])
                    return None, remaining_text
                line = ""

        if line:
            c.drawString(LEFT_MARGIN + indent, y_pos, line.strip())
            y_pos -= LINE_HEIGHT
            if y_pos < BOTTOM_MARGIN:
                remaining_text = "\n\n".join(paragraphs[para_index:])
                return None, remaining_text

        y_pos -= LINE_HEIGHT  # Space between paragraphs

    return y_pos, None


def measure_wrapped_text_height(c, text, indent=0):
    usable_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN - indent
    total_height = 0

    paragraphs = text.split("\n\n")
    for para in paragraphs:
        cleaned = ' '.join(para.strip().splitlines())
        words = cleaned.split()
        line = ""
        for word in words:
            test_line = f"{line}{word} "
            if stringWidth(test_line, FONT_NAME, 12) <= usable_width:
                line = test_line
            else:
                total_height += LINE_HEIGHT
                line = f"{word} "
        if line:
            total_height += LINE_HEIGHT
        total_height += LINE_HEIGHT  # Extra space between paragraphs

    return total_height


# Drawing Tables
#-------------------------------------------
def draw_table(c, x, y, col_widths, headers, rows, table_title, zebra_color, new_page_fn):
    global y_pos
    row_height = LINE_HEIGHT + 2

    if table_title:
        c.setFont("Times-Bold", 11)
        c.setFillColor(TEXT_COLOR)
        c.drawString(x, y, table_title)
        y -= LINE_HEIGHT * 2

    c.setFont("Times-Bold", 10)
    c.setFillColor(TITLE_COLOR)
    for i, header in enumerate(headers):
        c.drawString(x + sum(col_widths[:i]), y, header)
    y -= row_height * 1.2

    c.setLineWidth(1)
    c.setStrokeColor(TITLE_COLOR)
    c.line(x, y + row_height - 2, x + sum(col_widths), y + row_height - 2)

    c.setFont(FONT_NAME, 10)
    alternate = False

    for row in rows:
        if y < BOTTOM_MARGIN + row_height * 2:
            new_page_fn()
            y = PAGE_HEIGHT - TOP_MARGIN

            if table_title:
                c.setFont("Times-Bold", 11)
                c.setFillColor(TITLE_COLOR)
                c.drawString(x, y, table_title)
                y -= LINE_HEIGHT * 1.2

            c.setFont("Times-Bold", 10)
            c.setFillColor(TITLE_COLOR)
            for i, header in enumerate(headers):
                c.drawString(x + sum(col_widths[:i]), y, header)
            y -= row_height

            c.setStrokeColor(TITLE_COLOR)
            c.line(x, y + row_height - 2, x + sum(col_widths), y + row_height - 2)

            c.setFont(FONT_NAME, 10)

        if alternate:
            c.setFillColor(zebra_color)
            c.rect(x - 2, y - 2, sum(col_widths) + 4, row_height + 2, fill=1, stroke=0)
        c.setFillColor(TEXT_COLOR)

        text_y = y + (row_height / 2) - 4
        for i, val in enumerate(row):
            c.drawString(x + sum(col_widths[:i]), text_y, str(val))

        y -= row_height
        alternate = not alternate

    return y - LINE_HEIGHT * 1.5


# Last Downloaded CSV File
#,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
def load_latest_client_csv():
    """Loads the latest historical CSV for the active client. Returns (df, filename) or (None, None)."""
    if "client_profile" not in st.session_state:
        st.error("❌ Client profile not found.")
        return None, None

    client_name = st.session_state["client_profile"]["name"].replace(" ", "_")
    folder_path = f"data/clients/{client_name}"

    try:
        csv_files = [f for f in os.listdir(folder_path) if f.startswith(client_name) and f.endswith(".csv")]
        if not csv_files:
            st.warning("⚠️ No historical data files found for this client.")
            return None, None

        csv_files.sort(reverse=True)
        latest_file = csv_files[0]
        latest_path = os.path.join(folder_path, latest_file)

        df = pd.read_csv(latest_path, parse_dates=["date"])
        df.set_index("date", inplace=True)  # ✅ Set index so comparisons work
        return df, latest_file

    except Exception as e:
        st.error(f"❌ Failed to load historical data: {e}")
        return None, None

# Text Wrapping over pages
#,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
def draw_wrapped_text(c, text, y_pos, indent=0, font_name=FONT_NAME, font_size=12, font_color=TEXT_COLOR):
    c.setFont(font_name, font_size)
    c.setFillColor(font_color)

    usable_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN - indent
    paragraphs = text.split("\n\n")

    for para in paragraphs:
        cleaned = ' '.join(para.strip().splitlines())
        words = cleaned.split()
        line = ""
        for word in words:
            test_line = f"{line}{word} "
            if stringWidth(test_line, font_name, font_size) <= usable_width:
                line = test_line
            else:
                c.drawString(LEFT_MARGIN + indent, y_pos, line.strip())
                y_pos -= LINE_HEIGHT
                if y_pos < BOTTOM_MARGIN:
                    return None
                line = f"{word} "

        if line:
            c.drawString(LEFT_MARGIN + indent, y_pos, line.strip())
            y_pos -= LINE_HEIGHT
            if y_pos < BOTTOM_MARGIN:
                return None

        y_pos -= LINE_HEIGHT

    return y_pos

#======================================================================================================================
# PDF Generator
#======================================================================================================================
def generate_continuous_pdf(inv_note, executive_summary, macro_perspective, asset_outlooks):
    toc_entries = []

    def add_toc(title, page_num, indent=False):
        toc_entries.append({"title": title, "page": page_num, "indent": indent})

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont(FONT_NAME, 12)

    # === Cover Page ===
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    c.drawImage("assets/coverpage6.png", 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
    c.showPage()

    # === TOC Placeholder ===
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    toc_start = c.getPageNumber()
    c.setFont(FONT_NAME, 18)
    c.setFillColor(TITLE_COLOR)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 110, "Table of Contents")
    c.showPage()

    def draw_header(c):
        try:
            c.drawInlineImage("assets/QuantOptima_WhiteGold.png", (PAGE_WIDTH - 100) / 2, PAGE_HEIGHT - 60,
                              width=100, height=60)
        except:
            pass
        c.setStrokeColor(TITLE_COLOR)
        c.setLineWidth(1)
        c.line(LEFT_MARGIN, PAGE_HEIGHT - 45, PAGE_WIDTH - RIGHT_MARGIN, PAGE_HEIGHT - 45)

    def draw_footer(c, page_number):
        c.setStrokeColor(TITLE_COLOR)
        c.setLineWidth(1)
        c.line(LEFT_MARGIN, 60, PAGE_WIDTH - RIGHT_MARGIN, 60)
        if page_number >= 1:
            c.setFont(FONT_NAME, 10)
            c.setFillColor(TEXT_COLOR)
            c.drawCentredString(PAGE_WIDTH / 2, 45, f"Page {page_number}")

    page_number = 1
    y_pos = PAGE_HEIGHT - TOP_MARGIN
    draw_header(c)
    draw_footer(c, page_number)

    def new_page():
        nonlocal page_number, y_pos
        c.showPage()
        page_number += 1
        y_pos = PAGE_HEIGHT - TOP_MARGIN
        c.setFont(FONT_NAME, 12)
        draw_header(c)
        draw_footer(c, page_number)

    def draw_section(title, content, indent=False, required_space=80):
        nonlocal y_pos, page_number
        # If not enough vertical space for section + content, go to new page
        if y_pos < (BOTTOM_MARGIN + required_space):
            new_page()
        add_toc(title, page_number, indent=indent)

        # Section title
        c.setFont(FONT_NAME, 16 if not indent else 14)
        c.setFillColor(TITLE_COLOR)
        c.drawString(LEFT_MARGIN + (20 if indent else 0), y_pos, title)
        y_pos -= 1.5 * LINE_HEIGHT
        c.setFont(FONT_NAME, 12)
        c.setFillColor(TEXT_COLOR)

        # Paragraph content (if any)
        if content:
            while content:
                new_y = draw_wrapped_text(c, content, y_pos, indent=20 if indent else 0)
                if new_y is None:
                    new_page()
                    y_pos = PAGE_HEIGHT - TOP_MARGIN
                    c.setFont(FONT_NAME, 12)
                    continue
                y_pos = new_y - LINE_HEIGHT
                break

    # ==================================================================================================================
    # I. Executive Summary
    # ==================================================================================================================
    draw_section("I. Executive Summary", executive_summary)


    # ==================================================================================================================
    # II. Macro Perspective
    # ==================================================================================================================
    draw_section("II. Macro & Markets Perspective", macro_perspective)


    # ==================================================================================================================
    # III. Market Outlook by Asset Class
    # ==================================================================================================================
    draw_section("III. Asset Classes Outlook", "")
    for ac in asset_outlooks:
        if asset_outlooks[ac].strip():
            draw_section(ac, asset_outlooks[ac], indent=True)


    # ==================================================================================================================
    # IV - Client Profile and Objectives
    # ==================================================================================================================
    draw_section("IV. Client Profile and Objectives", "", indent=False)
    y_pos -= 10  # Add vertical spacing between the header and the table title

    if client_data:
        # Table Data Preparation
        zebra_color = Color(250 / 255, 249 / 255, 208 / 255)

        general_rows = [
            ["Name", client_data.get("name", "")],
            ["Email", client_data.get("email", "")],
            ["Phone", client_data.get("phone", "")],
            ["Country", client_data.get("country", "")]
        ]

        financial_rows = [
            ["Company", client_data.get("company", "")],
            ["Risk Level", client_data.get("risk_level", "")],
            ["Risk Score", str(client_data.get("risk_score", ""))]
        ]

        # Draw Tables side by side at same vertical position
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        left_x = LEFT_MARGIN
        right_x = PAGE_WIDTH / 2
        table_top_y = y_pos  # Save common starting Y position for both tables

        # Draw left table
        left_y_end = draw_table(c, left_x, table_top_y, [90, 90], ["Label", "Value"], general_rows,
                                "General Information",
                                zebra_color, new_page)

        # Draw right table
        right_y_end = draw_table(c, right_x, table_top_y, [90, 90], ["Label", "Value"], financial_rows,
                                 "Financial Information",
                                 zebra_color, new_page)

        # Update y_pos to the lower of the two tables
        y_pos = min(left_y_end, right_y_end) - 10  # 10 for spacing below both tables


        # Current Allocation
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        # required_block_height = 100  # Pie chart
        # commentary_estimate = LINE_HEIGHT * 6
        # title_height = LINE_HEIGHT * 1.5
        # total_required = required_block_height + commentary_estimate + title_height
        #
        # if y_pos < BOTTOM_MARGIN +  total_required:
        #     new_page()
        #
        # draw_section("Current Allocation", "",indent=True)


        # Pie chart + commentary
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        # Estimate space required for pie + commentary + title
        required_block_height = 100  # Pie chart
        commentary_estimate = LINE_HEIGHT * 6
        title_height = LINE_HEIGHT * 1.5
        total_required = required_block_height + commentary_estimate + title_height

        if y_pos < BOTTOM_MARGIN + total_required:
            new_page()

        # Draw title safely after confirming space
        draw_section("Current Allocation", "", indent=True)
        block_top = y_pos  # y_pos already adjusted by draw_section

        if client_data.get("current_allocation"):
            allocation = client_data["current_allocation"]
            labels = list(allocation.keys())
            values = list(allocation.values())

            gold_black_colors = ["#8B7500", "#B8860B", "#FFD700", "#555555", "#000000", "#D4AF37", "#4B4B4B"]
            colors = (gold_black_colors * ((len(labels) // len(gold_black_colors)) + 1))[:len(labels)]

            fig, ax = plt.subplots(figsize=(4, 4), dpi=300)
            wedges, _, _ = ax.pie(values, labels=None, autopct="%1.1f%%", startangle=140, colors=colors,
                                  textprops={'color': "white", 'fontsize': 9})
            legend = ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)
            legend.get_frame().set_linewidth(0)
            legend.get_frame().set_facecolor("none")
            ax.axis("equal")
            fig.tight_layout()

            pie_buf = BytesIO()
            fig.savefig(pie_buf, format="PNG", bbox_inches="tight", dpi=300)
            plt.close(fig)
            pie_buf.seek(0)
            pie_image = ImageReader(pie_buf)

            major_alloc = sorted(allocation.items(), key=lambda x: x[1], reverse=True)
            commentary_parts = []
            for asset, weight in major_alloc:
                if weight >= 40:
                    commentary_parts.append(
                        f"{asset} dominates the portfolio, indicating a highly cautious or strategic allocation.")
                elif weight >= 20:
                    commentary_parts.append(
                        f"{asset} holds a significant position, suggesting it plays a key role in diversification.")
                elif weight >= 10:
                    commentary_parts.append(
                        f"{asset} has a modest allocation, likely used for balancing risk and return.")
                else:
                    commentary_parts.append(f"{asset} is minimally allocated, likely opportunistic or exploratory.")
            commentary_text = " ".join(commentary_parts)

            pie_top = block_top
            pie_height = 180
            text_top = pie_top
            text_x = LEFT_MARGIN + 240 + 10
            comment_width = PAGE_WIDTH - text_x - RIGHT_MARGIN

            c.drawImage(pie_image, LEFT_MARGIN, pie_top - pie_height, width=220, height=220)

            c.setFont("Times-Italic", 11)
            c.setFillColor(HexColor("#800020"))

            words = commentary_text.split()
            line = ""
            text_y = text_top
            for word in words:
                test_line = f"{line}{word} "
                if stringWidth(test_line, FONT_NAME, 11) <= comment_width:
                    line = test_line
                else:
                    c.drawString(text_x, text_y, line.strip())
                    text_y -= LINE_HEIGHT
                    line = f"{word} "
            if line:
                c.drawString(text_x, text_y, line.strip())
                text_y -= LINE_HEIGHT

            y_pos = min(pie_top - pie_height, text_y) - LINE_HEIGHT


        # Investment Objectives
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        draw_section("Investment Objectives", inv_note, indent=True)


    # ==================================================================================================================
    # V. Portfolio Design and Construction
    #===================================================================================================================
    draw_section("V. Portfolio Design and Construction", "", indent=False)

    def generate_asset_selection_purpose(client_data):
        risk_level = client_data.get("risk_level", "")
        risk_score = client_data.get("risk_score", "")
        answers = client_data.get("risk_answers", {})
        selected_etfs = client_data.get("selected_etfs", [])

        # Count asset class usage
        asset_classes = [etf.get("Asset Class", "") for etf in selected_etfs]
        asset_counter = Counter(asset_classes)
        paragraph = []


        # Risk orientation
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        if risk_level and risk_score:
            paragraph.append(
                f"Given the client's {risk_level.lower()} risk level and a score of {risk_score}, "
                "the selected assets aim to balance caution with measured exposure to growth opportunities."
            )


        # Time horizon and objective
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        horizon = answers.get("What is your investment horizon?", "")
        goal = answers.get("What is your primary investment goal?", "")
        if horizon and goal:
            paragraph.append(
                f"With a time horizon of {horizon.lower()} and a focus on {goal.lower()}, "
                "the chosen instruments reflect a mix of capital preservation and selective return-seeking."
            )


        # Commentary by asset type
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        for asset, count in asset_counter.items():
            asset_lc = asset.lower()
            if "fixed" in asset_lc or "bond" in asset_lc:
                paragraph.append("Fixed income instruments were included to provide income and mitigate volatility.")
            elif "equity" in asset_lc:
                paragraph.append("Equity ETFs were selected to offer potential for capital appreciation.")
            elif "private" in asset_lc:
                paragraph.append(
                    "Exposure to private markets enhances diversification and may capture niche opportunities.")
            elif "real estate" in asset_lc:
                paragraph.append("Real estate ETFs provide income and help diversify macro sensitivities.")
            elif "commodity" in asset_lc:
                paragraph.append("Commodities were selected to hedge inflation and enhance diversification.")
            elif "alternative" in asset_lc:
                paragraph.append(
                    "Alternative instruments provide differentiated return drivers and downside buffering.")


        # Market preference
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        if "Global" in answers.get("Where would you prefer new investments to be allocated?", ""):
            paragraph.append(
                "Global diversification is embedded in the asset mix, aligning with stated geographic preference.")


        # Market behavior
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        reaction = answers.get("How would you react to a 10% drop in your portfolio value?", "")
        if "hold" in reaction.lower():
            paragraph.append(
                "The client's intent to hold during market drawdowns supports a diversified allocation with "
                "longer-term resilience.")


        # Final remark
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        paragraph.append(
            "Together, these choices support a resilient, goal-aligned investment universe consistent with the client's "
            "profile.")

        return " ".join(paragraph)


    # Asset Selection Purpose
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    purpose_text = generate_asset_selection_purpose(client_data)
    new_y = draw_wrapped_text(c, purpose_text, y_pos, indent=0)  # ✅ no indentation

    if new_y is None:
        new_page()
        y_pos = draw_wrapped_text(c, purpose_text, PAGE_HEIGHT - TOP_MARGIN, indent=0)
    else:
        y_pos = new_y - LINE_HEIGHT


    # Investment Universe List Table
    #===================================================================================================================
    draw_section("Investment Universe List", "", indent=True)
    y_pos -= 10  # Slight space below section title

    # Prepare headers and rows
    headers = ["Ticker", "Name", "Asset Class"]
    col_widths = [70, 230, 130]  # Adjust as needed for proper spacing

    rows = []
    for etf in client_data.get("selected_etfs", []):
        rows.append([
            etf.get("Ticker", ""),
            etf.get("Name", "")[:35],  # Truncate more conservatively
            etf.get("Asset Class", "")[:20]  # Ensure Asset Class fits
        ])

    # Define zebra color
    zebra_color = Color(250 / 255, 249 / 255, 208 / 255)

    # Draw table
    y_pos = draw_table(c, LEFT_MARGIN + 20, y_pos, col_widths, headers, rows, "", zebra_color, new_page)


    # Add vertical spacing before new subsection and next subtitle
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    y_pos -= LINE_HEIGHT


    # ETF Details and Characteristics
    # ==================================================================================================================
    draw_section("ETF Details and Characteristics", "", indent=True)

    from textwrap import wrap
    import matplotlib.dates as mdates
    zebra_color = HexColor("#f5e8c4")
    etfs = client_data.get("selected_etfs", [])
    client_name = client_data.get("name", "").replace(" ", "_")

    def load_latest_client_csv():
        folder_path = f"data/clients/{client_name}"
        csv_files = [f for f in os.listdir(folder_path) if f.startswith(client_name) and f.endswith(".csv")]
        if not csv_files:
            return pd.DataFrame(), None
        csv_files.sort(reverse=True)
        latest_path = os.path.join(folder_path, csv_files[0])
        try:
            price_df = pd.read_csv(latest_path, parse_dates=["date"]).set_index("date")
        except:
            price_df = pd.DataFrame()
        return price_df, latest_path

    price_df, csv_path = load_latest_client_csv()

    try:
        number_years = date.today() - pd.DateOffset(years=3)
        price_df = price_df[price_df.index >= number_years]
    except:
        price_df = pd.DataFrame()

    indent_x = LEFT_MARGIN + 20
    label_width_fixed = 100
    content_start_x = indent_x + label_width_fixed
    max_content_width = PAGE_WIDTH - RIGHT_MARGIN - 10
    wrap_width = int(max_content_width / 6.0)

    for i, etf in enumerate(etfs, start=1):
        meta = etf.get("meta", {})
        ticker = etf.get("Ticker", "")
        name = meta.get("name", etf.get("Name", ticker))
        desc = meta.get("description") or "N/A"
        asset_class = meta.get("assetClass", etf.get("Asset Class", "N/A"))

        min_space_needed = LINE_HEIGHT * 5
        if y_pos < BOTTOM_MARGIN + min_space_needed:
            new_page()
            y_pos = PAGE_HEIGHT - TOP_MARGIN

        y_pos -= LINE_HEIGHT * 2
        c.setFont("Times-Bold", 12)
        full_title = f"{i}. {name} ({ticker})"
        c.drawString(indent_x, y_pos, full_title)
        y_pos -= LINE_HEIGHT * 1.5

        for label, content in [("Asset Class:", asset_class), ("Description:", desc)]:
            required_height = measure_wrapped_text_height(c, content, indent=content_start_x - LEFT_MARGIN)

            if y_pos < BOTTOM_MARGIN + LINE_HEIGHT:
                new_page()
                y_pos = PAGE_HEIGHT - TOP_MARGIN

            c.setFont("Times-Bold", 10)
            c.drawString(indent_x, y_pos, label)

            new_y = draw_wrapped_text(c, content, y_pos, indent=content_start_x - LEFT_MARGIN)
            if new_y is None:
                new_page()
                y_pos = PAGE_HEIGHT - TOP_MARGIN
                c.setFont("Times-Bold", 10)
                c.drawString(indent_x, y_pos, label)
                new_y = draw_wrapped_text(c, content, y_pos, indent=content_start_x - LEFT_MARGIN)

            y_pos = new_y - LINE_HEIGHT * 0.5

        sector = meta.get("sector_weights", {}) or {"N/A": "N/A"}
        country = meta.get("country_weights", {}) or {"N/A": "N/A"}

        sector_text = ", ".join([f"{k} ({float(str(v).replace('%', '').strip()):.2f}%)" if str(v).replace('%',
                                                                                                          '').strip().replace(
            '.', '', 1).isdigit() else f"{k} ({v})" for k, v in sector.items()])
        country_text = ", ".join([f"{k} ({float(str(v).replace('%', '').strip()):.2f}%)" if str(v).replace('%',
                                                                                                           '').strip().replace(
            '.', '', 1).isdigit() else f"{k} ({v})" for k, v in country.items()])

        for label, content in [("Sector Allocation:", sector_text), ("Country Allocation:", country_text)]:
            required_height = measure_wrapped_text_height(c, content, indent=content_start_x - LEFT_MARGIN)

            if y_pos < BOTTOM_MARGIN + LINE_HEIGHT:
                new_page()
                y_pos = PAGE_HEIGHT - TOP_MARGIN

            c.setFont("Times-Bold", 10)
            c.drawString(indent_x, y_pos, label)

            new_y = draw_wrapped_text(c, content, y_pos, indent=content_start_x - LEFT_MARGIN)
            if new_y is None:
                new_page()
                y_pos = PAGE_HEIGHT - TOP_MARGIN
                c.setFont("Times-Bold", 10)
                c.drawString(indent_x, y_pos, label)
                new_y = draw_wrapped_text(c, content, y_pos, indent=content_start_x - LEFT_MARGIN)

            y_pos = new_y - LINE_HEIGHT * 0.5

        chart_width = (PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN - 20) / 2
        chart_height = 100

        if y_pos < BOTTOM_MARGIN + chart_height + 10:
            new_page()
            y_pos = PAGE_HEIGHT - TOP_MARGIN

        matching_cols = [col for col in price_df.columns if col.strip().upper() == ticker.strip().upper()]
        if matching_cols and price_df[matching_cols[0]].dropna().shape[0] > 1:
            price_series = price_df[matching_cols[0]].fillna(method="ffill").fillna(method="bfill")
            rebased = price_series / price_series.iloc[0] * 100

            if rebased.dropna().shape[0] > 1:
                fig, ax = plt.subplots(figsize=(3, 1.5), dpi=300)
                ax.plot(rebased, linewidth=1)
                ax.set_title("Price Chart", fontsize=9, fontname="Times New Roman")
                ax.tick_params(labelsize=7)
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%y'))
                fig.autofmt_xdate()
                for spine in ax.spines.values():
                    spine.set_visible(False)
                buf = BytesIO()
                fig.tight_layout(pad=0.2)
                fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
                plt.close(fig)
                buf.seek(0)
                img = ImageReader(buf)
                c.drawImage(img, indent_x, y_pos - chart_height, width=chart_width, height=chart_height)

        perf = meta.get("performance", {})
        if perf:
            keys = list(perf.keys())
            vals = [perf[k] for k in keys]

            fig, ax = plt.subplots(figsize=(3, 1.5), dpi=300)
            bars = ax.bar(keys, vals, color="#B8860B")
            for bar, val in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width() / 2, val + max(vals) * 0.03, f"{val:.2f}%", ha='center',
                        va='bottom', fontsize=7)
            ax.set_title("Performance", fontsize=9, fontname="Times New Roman")
            ax.tick_params(labelsize=7)
            for spine in ax.spines.values():
                spine.set_visible(False)
            buf = BytesIO()
            fig.tight_layout(pad=0.2)
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            img = ImageReader(buf)
            c.drawImage(img, indent_x + chart_width + 20, y_pos - chart_height, width=chart_width, height=chart_height)

        y_pos -= chart_height + 20

    # ==================================================================================================================
    # VI. Portfolio Recommendation
    # ==================================================================================================================
    draw_section("VI. Portfolio Recommendation", "", indent=False)

    # AI-Generated Introduction
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    intro_parts = []
    risk_level = client_data.get("risk_level", "N/A")
    risk_score = client_data.get("risk_score", "N/A")
    models_perf = client_data.get("Quantitative Portfolios Performance", {})
    model_names = list(models_perf.keys())

    if risk_level and risk_score:
        intro_parts.append(
            f"Based on the client's {risk_level.lower()} risk profile and score of {risk_score}, a series of "
            f"quantitative models were employed to construct efficient portfolios."
        )
    if model_names:
        intro_parts.append(
            f"The models applied include: {', '.join(model_names)}. Each model was assessed based on its return, "
            f"volatility, and risk-adjusted performance."
        )
    else:
        intro_parts.append("A series of optimization models were applied to design an optimal asset allocation.")

    intro_text = " ".join(intro_parts)
    new_y = draw_wrapped_text(c, intro_text, y_pos)
    if new_y is None:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN
        y_pos = draw_wrapped_text(c, intro_text, y_pos)
    else:
        y_pos = new_y - LINE_HEIGHT


    # Quantitative Portfolio Optimization
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    # Estimate required space BEFORE drawing title
    table_height_estimate = LINE_HEIGHT * 15  # Estimate table height roughly
    chart_height_estimate = 140
    title_height = LINE_HEIGHT * 2
    total_required = title_height + table_height_estimate + chart_height_estimate + 40  # Include padding

    if y_pos - total_required < BOTTOM_MARGIN:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN

    # Now safe to draw title
    draw_section("Quantitative Portfolio Optimization", "", indent=True)
    y_pos -= 20


    try:
        price_df, latest_file = load_latest_client_csv()
        if price_df is None:
            raise ValueError("No historical price data available.")

        price_df = price_df[price_df.index >= number_years]

        # === Compute ETF Stats
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        stats_rows = []
        daily_returns = price_df.pct_change().dropna()

        for etf in price_df.columns:
            etf_ret = daily_returns[etf]
            annual_ret = etf_ret.mean() * 252
            annual_vol = etf_ret.std() * (252 ** 0.5)
            sharpe = annual_ret / annual_vol if annual_vol > 0 else 0
            rolling_max = price_df[etf].cummax()
            drawdown = price_df[etf] / rolling_max - 1
            max_drawdown = drawdown.min()

            stats_rows.append([
                etf,
                f"{annual_ret:.2%}",
                f"{annual_vol:.2%}",
                f"{sharpe:.2f}",
                f"{max_drawdown:.2%}"
            ])

        # Multi-line header
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        headers = ["ETF", "Annual\nReturn", "Volatility", "Sharpe\nRatio", "Max\nDrawdown"]
        col_widths = [60, 45, 45, 45, 55]

        left_x = LEFT_MARGIN +10
        right_x = PAGE_WIDTH / 2 + 30
        table_y = y_pos

        # === Cumulative Returns Chart
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        rebased = price_df / price_df.iloc[0] * 100
        fig, ax = plt.subplots(figsize=(4, 2), dpi=600)
        rebased.plot(ax=ax, legend=False)

        ax.set_title("")
        ax.set_xlabel("")  # Remove x-axis label entirely
        ax.tick_params(axis='x', labelsize=5)
        ax.tick_params(axis='y', labelsize=5)
        for spine in ax.spines.values():
            spine.set_visible(False)

        buf = BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=500)
        plt.close(fig)
        buf.seek(0)
        img = ImageReader(buf)

        chart_width = PAGE_WIDTH - right_x - RIGHT_MARGIN   # Give extra margin on right if needed
        chart_height = 140

        min_needed = chart_height + 40
        if table_y - min_needed < BOTTOM_MARGIN:
            new_page()
            table_y = PAGE_HEIGHT - TOP_MARGIN

        # Table and Chart Titles
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        block_top_y = y_pos  # Save current vertical position
        c.setFont("Times-Bold", 11)
        c.setFillColor(TEXT_COLOR)
        c.drawString(left_x, block_top_y, "Selected ETFs Risk & Return Summary")
        c.drawString(right_x, block_top_y, "Selected ETFs Prices (Rebased to 100)")
        table_y = block_top_y - LINE_HEIGHT * 3.5  # Applies to both sides consistently

        # Draw Chart on Right
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        c.drawImage(img, right_x, table_y - (chart_height-15), width=chart_width, height=chart_height)

        # Draw Multi-line Headers Centered
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        header_row_height = LINE_HEIGHT * 2.5
        c.setFont("Times-Bold", 9)
        c.setFillColor(TITLE_COLOR)

        for i, header in enumerate(headers):
            x_center = left_x + sum(col_widths[:i]) + (col_widths[i] / 2)
            header_lines = header.split('\n')

            total_text_height = len(header_lines) * LINE_HEIGHT
            first_line_y = table_y + (header_row_height / 2) + (total_text_height / 2) - LINE_HEIGHT

            for idx, line in enumerate(header_lines):
                line_width = stringWidth(line, "Times-Bold", 9)
                line_y = first_line_y - (idx * LINE_HEIGHT)
                c.drawString(x_center - (line_width / 2), line_y, line)

        c.setStrokeColor(TITLE_COLOR)
        c.setLineWidth(1)
        c.line(left_x, table_y, left_x + sum(col_widths), table_y)
        table_y -= header_row_height

        # Draw Data Rows Centered
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        row_height = LINE_HEIGHT + 2
        c.setFont(FONT_NAME, 9)
        alternate = False

        for row in stats_rows:
            if table_y < BOTTOM_MARGIN + row_height * 2:
                new_page()
                table_y = PAGE_HEIGHT - TOP_MARGIN

                # Redraw Titles
                c.setFont("Times-Bold", 11)
                c.setFillColor(TEXT_COLOR)
                c.drawString(left_x, table_y, "Selected ETFs Risk & Return Summary")
                c.drawString(right_x, table_y, "Selected ETFs Prices (Rebased to 100)")
                table_y -= LINE_HEIGHT * 3

                c.setFont("Times-Bold", 9)
                for i, header in enumerate(headers):
                    x_center = left_x + sum(col_widths[:i]) + (col_widths[i] / 2)
                    header_lines = header.split('\n')
                    first_line_y = table_y + (header_row_height / 2)
                    second_line_y = table_y + (header_row_height / 2) - LINE_HEIGHT

                    for idx, line in enumerate(header_lines):
                        line_width = stringWidth(line, "Times-Bold", 9)
                        line_y = first_line_y - (idx * LINE_HEIGHT)
                        c.drawString(x_center - (line_width / 2), line_y, line)

                c.setStrokeColor(TITLE_COLOR)
                c.setLineWidth(1)
                c.line(left_x, table_y, left_x + sum(col_widths), table_y)
                table_y -= header_row_height
                c.setFont(FONT_NAME, 9)

            if alternate:
                c.setFillColor(zebra_color)
                c.rect(left_x - 2, table_y - 2, sum(col_widths) + 4, row_height + 2, fill=1, stroke=0)
            c.setFillColor(TEXT_COLOR)

            for i, val in enumerate(row):
                val_str = str(val)
                val_width = stringWidth(val_str, FONT_NAME, 9)
                if i == 0:
                    # First column: left aligned with small padding
                    x_pos = left_x + sum(col_widths[:i]) + 2
                else:
                    # Other columns: centered
                    x_center = left_x + sum(col_widths[:i]) + (col_widths[i] / 2)
                    x_pos = x_center - (val_width / 2)

                text_y = table_y + (row_height / 2) - 4
                c.drawString(x_pos, text_y, val_str)

            table_y -= row_height
            alternate = not alternate

        y_pos = table_y - 20

    except Exception as e:
        y_pos -= LINE_HEIGHT
        c.setFont(FONT_NAME, 10)
        c.setFillColor(TEXT_COLOR)
        c.drawString(LEFT_MARGIN, y_pos, f"Cumulative returns chart and stats unavailable: {e}")
        y_pos -= LINE_HEIGHT * 2


    # Explanatory commentary Paragraph on Risk and Returns
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    y_pos = table_y - LINE_HEIGHT * 1.5

    if y_pos < BOTTOM_MARGIN + LINE_HEIGHT * 5:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN

    explanation = (
        "The above table summarizes key risk and return characteristics for each selected ETF over the "
        "analysis period. Annualized returns indicate the average growth rate, while volatility reflects "
        "the degree of price fluctuation. The Sharpe Ratio provides a standardized measure of risk-adjusted "
        "performance, with higher values indicating superior returns relative to risk. Max Drawdown highlights "
        "the largest observed peak-to-trough decline, offering insight into downside risk. These metrics "
        "collectively help assess the risk-return trade-offs within the ETF universe."
    )

    required_indent = left_x - LEFT_MARGIN
    new_y = draw_wrapped_text(c, explanation, y_pos, indent=required_indent)

    if new_y is None:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN
        new_y = draw_wrapped_text(c, explanation, y_pos, indent=required_indent)

    y_pos = new_y - LINE_HEIGHT


    # Calculate correlation matrix
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    returns = price_df.pct_change().dropna()
    corr_matrix = returns.corr()

    # Define left_x for consistency
    left_x = LEFT_MARGIN + 10

    # Estimate required space:
    title_height = LINE_HEIGHT * 1.5
    chart_height = 200
    commentary_estimated_height = LINE_HEIGHT * 5  # Approximate for paragraph

    required_space = title_height + chart_height + 10  # Small buffer

    #Check available space:
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    if y_pos - required_space < BOTTOM_MARGIN:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN

    # Draw title above heatmap
    c.setFont("Times-Bold", 11)
    c.setFillColor(TEXT_COLOR)
    c.drawString(left_x, y_pos, "Asset Return Correlation Heatmap")

    # Adjust y_pos down before drawing chart
    y_pos -= LINE_HEIGHT # Spacing below title

    # Plot heatmap
    fig, ax = plt.subplots(figsize=(4.5, 4.5), dpi=600)

    # Large fonts for annotations and axis ticks
    sns.heatmap(
        corr_matrix, annot=True, cmap='cividis', center=0, fmt=".2f", ax=ax,
        annot_kws={"size": 9}  # Annotation font size
    )
    plt.title("")
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()

    # Save image safely
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=500)
    plt.close(fig)
    buf.seek(0)
    img = ImageReader(buf)

    # Layout positioning
    left_x = LEFT_MARGIN + 10
    right_x = PAGE_WIDTH / 2 + 30
    chart_width = PAGE_WIDTH / 2 - LEFT_MARGIN + 20
    chart_height = 240
    comment_width = PAGE_WIDTH - right_x - RIGHT_MARGIN

    # Space check
    if y_pos < BOTTOM_MARGIN + chart_height + 10:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN

    # Draw heatmap on left
    c.drawImage(img, left_x, y_pos - chart_height, width=chart_width, height=chart_height)


    # Generate dynamic commentary
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    most_corr = None
    least_corr = None
    max_corr = -2
    min_corr = 2

    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            val = corr_matrix.iloc[i, j]
            if val > max_corr:
                max_corr = val
                most_corr = (corr_matrix.columns[i], corr_matrix.columns[j])
            if val < min_corr:
                min_corr = val
                least_corr = (corr_matrix.columns[i], corr_matrix.columns[j])

    commentary = (
        "The heatmap visualizes the correlation between asset returns. Values closer to 1 indicate strong positive "
        "correlation, while values near -1 imply strong negative correlation. In this portfolio, the most positively "
        f"correlated pair is {most_corr[0]} and {most_corr[1]} ({max_corr:.2f}), suggesting similar price movements. "
        f"The least correlated (most diversifying) pair is {least_corr[0]} and {least_corr[1]} ({min_corr:.2f}). "
        "These relationships inform portfolio diversification and risk management."
    )

    # Layout adjustments
    left_x = LEFT_MARGIN + 10
    chart_width = (PAGE_WIDTH * 0.6) - left_x - 20
    right_x = left_x + chart_width + 20
    comment_width = PAGE_WIDTH - right_x - RIGHT_MARGIN

    # Define positioning
    text_y = y_pos - 20
    required_indent = right_x - LEFT_MARGIN + 5

    # # Draw commentary with custom style
    new_y = draw_wrapped_text(
        c, commentary, text_y, indent=required_indent,
        font_name="Times-Italic", font_size=11, font_color=HexColor("#800020")
    )

    # Handle potential page break
    if new_y is None:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN
        new_y = draw_wrapped_text(
            c, commentary, y_pos, indent=required_indent,
            font_name="Times-Italic", font_size=11, font_color=HexColor("#800020")
        )

    # Update y_pos after drawing
    y_pos = min(y_pos - chart_height - 30, new_y - LINE_HEIGHT)

    # Reset text styling
    c.setFillColor(TEXT_COLOR)
    c.setFont(FONT_NAME, 12)


    # # === Models Performance Table
    # # # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

    # Estimate space needed:
    min_table_rows = len(models_perf) + 3  # 3 for title + header + buffer
    row_height = LINE_HEIGHT + 4
    required_space = LINE_HEIGHT * 2.5 + (min_table_rows * row_height)

    if y_pos < BOTTOM_MARGIN + required_space:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN

    # === Models Performance Table Title ===
    c.setFont("Times-Bold", 11)
    c.setFillColor(TEXT_COLOR)
    c.drawString(LEFT_MARGIN + 30, y_pos, "Quantitative Models Performance Summary")
    y_pos -= LINE_HEIGHT * 2.5  # Adds space after title

    # === Table Drawing ===
    if models_perf:
        col_widths = [180, 100, 100, 100]
        headers = ["Model", "Return", "Volatility", "Sharpe Ratio"]
        table_x = LEFT_MARGIN + 10
        table_y = y_pos + 5

        c.setFont("Times-Bold", 10)
        c.setFillColor(TITLE_COLOR)
        for i, header in enumerate(headers):
            c.drawString(table_x + sum(col_widths[:i]), table_y, header)
        table_y -= row_height

        c.setStrokeColor(TITLE_COLOR)
        c.setLineWidth(1)
        c.line(table_x, table_y + row_height - 4, table_x + sum(col_widths), table_y + row_height - 4)

        c.setFont(FONT_NAME, 10)
        alternate = False

        for model, metrics in models_perf.items():
            if table_y < BOTTOM_MARGIN + row_height * 2:
                new_page()
                table_y = PAGE_HEIGHT - TOP_MARGIN

                c.setFont("Times-Bold", 10)
                c.setFillColor(TITLE_COLOR)
                for i, header in enumerate(headers):
                    c.drawString(table_x + sum(col_widths[:i]), table_y, header)
                table_y -= row_height
                c.line(table_x, table_y + row_height - 4, table_x + sum(col_widths), table_y + row_height - 4)

                c.setFont(FONT_NAME, 10)

            if alternate:
                c.setFillColor(HexColor("#f5e8c4"))
                c.rect(table_x - 2, table_y - 2, sum(col_widths) + 4, row_height + 2, fill=1, stroke=0)
            c.setFillColor(TEXT_COLOR)

            text_y = table_y + (row_height / 2) - 4
            c.drawString(table_x, text_y, model)

            ret = metrics.get("Metrics", {}).get("Return", 0)
            vol = metrics.get("Metrics", {}).get("Volatility", 0)
            sharpe = metrics.get("Metrics", {}).get("Sharpe Ratio", 0)
            c.drawString(table_x + col_widths[0], text_y, f"{ret:.2%}")
            c.drawString(table_x + col_widths[0] + col_widths[1], text_y, f"{vol:.2%}")
            c.drawString(table_x + col_widths[0] + col_widths[1] + col_widths[2], text_y, f"{sharpe:.2f}")

            table_y -= row_height
            alternate = not alternate

        y_pos = table_y - LINE_HEIGHT

        # Explanatory commentary Paragraph on Optimisation Models
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        y_pos = table_y - LINE_HEIGHT * 1.2

        # Estimate required space for paragraph
        min_text_space = LINE_HEIGHT * 5
        if y_pos < BOTTOM_MARGIN + min_text_space:
            new_page()
            y_pos = PAGE_HEIGHT - TOP_MARGIN

        # Paragraph aligned with table indent
        table_indent = LEFT_MARGIN + 10
        required_indent = table_indent - LEFT_MARGIN

        # Commentary text
        commentary = (
            "The above table compares the performance characteristics of different portfolio optimization models. "
            "Higher returns and Sharpe Ratios indicate superior risk-adjusted performance, while lower volatility "
            "suggests reduced portfolio fluctuations. These insights help evaluate which model provides the most "
            "suitable balance between return and risk for the client's investment objectives."
        )

        # Draw paragraph
        new_y = draw_wrapped_text(c, commentary, y_pos, indent=required_indent)

        if new_y is None:
            new_page()
            y_pos = PAGE_HEIGHT - TOP_MARGIN
            new_y = draw_wrapped_text(c, commentary, y_pos, indent=required_indent)

        y_pos = new_y - LINE_HEIGHT


 # Proposed Asset Allocation Pie & Table
 #================================================================================================================
    draw_section("Proposed Asset Allocation", "", indent=True)

    selected_portfolio = client_data.get("Selected Portfolio", {})
    weights = selected_portfolio.get("Weights", {})
    performance = selected_portfolio.get("Metrics", {})

    if not weights:
        y_pos -= LINE_HEIGHT
        c.setFont(FONT_NAME, 10)
        c.setFillColor(TEXT_COLOR)
        c.drawString(LEFT_MARGIN, y_pos, "No selected portfolio data found.")
        y_pos -= LINE_HEIGHT
    else:
        pie_height = 220
        title_space = LINE_HEIGHT * 0.5 #(title space between title and table)
        row_height = LINE_HEIGHT + 4
        metrics_table_height = row_height * 4 + title_space
        commentary_text = (
            "The portfolio allocation presented reflects the combined impact of asset class outlooks, prevailing macroeconomic "
            "conditions, and quantitative optimization techniques. ETFs have been selected to provide diversified exposure "
            "across risk profiles, regions, and sectors. The resulting allocation balances return potential with risk mitigation, "
            "as informed by both the client's objectives and market expectations. The selected portfolio distribution is outlined "
            "below, while its risk and return characteristics are summarized alongside."
        )

        commentary_estimated_height = LINE_HEIGHT * 5  # Approximate
        total_required = title_space + pie_height + metrics_table_height + 10

        y_pos -= LINE_HEIGHT - 10  # Space after section title

        # Save Y position for pie/table titles BEFORE drawing commentary
        pie_title_y = y_pos - LINE_HEIGHT * 1.5  # Add some spacing below section title

        # Paragraph aligned with section title indent
        indent_x = 20
        new_y = draw_wrapped_text(c, commentary_text, y_pos, indent=indent_x)
        while new_y is None:
            new_page()
            pie_title_y = PAGE_HEIGHT - TOP_MARGIN - LINE_HEIGHT * 1.5  # Recalculate for new page
            new_y = draw_wrapped_text(c, commentary_text, PAGE_HEIGHT - TOP_MARGIN, indent=indent_x)

        y_pos = new_y - LINE_HEIGHT * 2  # Space below paragraph

        # NOW check space for pie and table after updated y_pos
        total_required = title_space + pie_height + metrics_table_height + 10
        if y_pos - total_required < BOTTOM_MARGIN:
            new_page()
            pie_title_y = PAGE_HEIGHT - TOP_MARGIN - LINE_HEIGHT * 1.5
            y_pos = PAGE_HEIGHT - TOP_MARGIN


        # Pie and Table Titles
        # ================================================================================================================
        title_y = y_pos
        c.setFont("Times-Bold", 11)
        c.setFillColor(TEXT_COLOR)
        c.drawString(LEFT_MARGIN, title_y, "Asset Allocation by Selected Portfolio")
        table_x = LEFT_MARGIN + 280
        c.drawString(table_x, title_y, "Asset Class Weights Summary")

        y_pos -= LINE_HEIGHT * 2  # Space below titles

        # Pie Chart
        fig, ax = plt.subplots(figsize=(4.2, 4.2), dpi=500)
        labels = list(weights.keys())
        values = [v * 100 for v in weights.values()]
        colors = ["#B8860B", "#FFD700", "#8B7500", "#4B4B4B", "#000000"] * 5

        wedges, _, _ = ax.pie(values, labels=None, autopct="%1.1f%%", startangle=140, colors=colors[:len(labels)],
                              textprops={'fontsize': 9, 'color': "white"})
        ax.axis("equal")
        ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0.5), fontsize=9, frameon=False)

        pie_buf = BytesIO()
        fig.tight_layout()
        fig.savefig(pie_buf, format="png", bbox_inches="tight", dpi=500)
        plt.close(fig)
        pie_buf.seek(0)
        pie_img = ImageReader(pie_buf)

        pie_height = 220  # Adjust as desired
        c.drawImage(pie_img, LEFT_MARGIN, y_pos - pie_height + 20, width=240, height=pie_height)

        # Asset Class Weights Table
        # ================================================================================================================
        # Aggregate weights by asset class
        etf_list = client_data["selected_etfs"]
        weights_dict = weights  # Assuming you already have this from "Selected Portfolio"
        ticker_to_class = {etf["Ticker"]: etf["Asset Class"] for etf in etf_list}

        class_weights = {}
        for ticker, weight in weights_dict.items():
            if ticker == "CASH":
                class_weights["Cash"] = class_weights.get("Cash", 0) + weight * 100
            else:
                asset_class = ticker_to_class.get(ticker, "Other")
                class_weights[asset_class] = class_weights.get(asset_class, 0) + weight * 100

        # Table data
        rows = []
        for asset_class, total_weight in sorted(class_weights.items(), key=lambda x: -x[1]):
            rows.append([asset_class, f"{total_weight:.2f}%"])

        # Layout for table
        table_y = y_pos
        row_height = LINE_HEIGHT + 4
        col_widths = [120, 100]
        headers = ["Asset Class", "Weight"]
        zebra_color = Color(250 / 255, 249 / 255, 208 / 255)

        table_y -= LINE_HEIGHT * 1.2  # Space below title

        # Header row
        c.setFont("Times-Bold", 10)
        c.setFillColor(TITLE_COLOR)
        for i, header in enumerate(headers):
            c.drawString(table_x + sum(col_widths[:i]), table_y, header)
        table_y -= row_height

        # Divider
        c.setStrokeColor(TITLE_COLOR)
        c.setLineWidth(1)
        c.line(table_x, table_y + row_height - 2, table_x + sum(col_widths), table_y + row_height - 2)

        # Draw rows
        c.setFont(FONT_NAME, 10)
        alternate = False
        for row in rows:
            if alternate:
                c.setFillColor(zebra_color)
                c.rect(table_x - 2, table_y - 2, sum(col_widths) + 4, row_height + 2, fill=1, stroke=0)
            c.setFillColor(TEXT_COLOR)

            text_y = table_y + (row_height / 2) - 4
            for i, val in enumerate(row):
                c.drawString(table_x + sum(col_widths[:i]), text_y, str(val))

            table_y -= row_height
            alternate = not alternate

        # Final y_pos update after both elements
        y_pos -= pie_height + 10

    # Efficient Frontier
    #================================================================================================================
    # Extract selected portfolio weights
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    selected_portfolio = client_data.get("Selected Portfolio", {})
    weights_dict = selected_portfolio.get("Weights", {})

    # Ensure weights include all assets in price_df (missing ones set to 0)
    w_series = pd.Series(weights_dict).reindex(price_df.columns, fill_value=0)

    # If CASH is present but missing from price_df, inject constant price series
    if "CASH" in w_series.index and "CASH" not in price_df.columns:
        annual_cash_return = 0.02
        daily_cash_return = (1 + annual_cash_return) ** (1 / 252) - 1
        price_df["CASH"] = (1 + daily_cash_return) ** np.arange(len(price_df))

    # setting optimisation models for selected portfolio
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    if not price_df.empty:

        returns = price_df.pct_change().dropna()

        port = rp.Portfolio(returns=returns)
        port.assets_stats(method_mu='hist', method_cov='hist')

        model = 'Classic'
        rm = 'MAD'
        hist = True
        rf = 0
        l = 0
        points = 50

        selected_portfolio = client_data.get("Selected Portfolio", {})
        obj = selected_portfolio.get("Name", "Sharpe")

        if obj in ["Sharpe", "MinRisk", "Utility", "MaxRet"]:
            w = port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=l, hist=hist)
            w_series = w.squeeze()
            w_vector = w_series.reindex(returns.columns, fill_value=0).values.flatten()

            mu_est = port.mu.values.flatten()
            cov_est = port.cov.values
            exp_ret = float(np.dot(mu_est, w_vector))
            risk = float(np.sqrt(w_vector.T @ cov_est @ w_vector))

        elif obj == "Equal":
            n_assets = returns.shape[1]
            w_series = pd.Series(1 / n_assets, index=returns.columns)
            w_vector = w_series.values.flatten()

            mu_est = port.mu.values.flatten()
            cov_est = port.cov.values
            exp_ret = float(np.dot(mu_est, w_vector))
            risk = float(np.sqrt(w_vector.T @ cov_est @ w_vector))
            w = pd.DataFrame([w_series])

        elif obj == "Manual":
            weights_dict = selected_portfolio.get("Weights", {})
            w_series = pd.Series(weights_dict).reindex(returns.columns, fill_value=0)
            w_vector = w_series.values.flatten()

            exp_ret = selected_portfolio.get("Metrics", {}).get("Return", 0)
            risk = selected_portfolio.get("Metrics", {}).get("Volatility", 0)
            w = pd.DataFrame([w_series])

        else:
            print("⚠ Unrecognized portfolio, defaulting to Sharpe.")
            obj = "Sharpe"
            w = port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=l, hist=hist)
            w_series = w.squeeze()
            w_vector = w_series.reindex(returns.columns, fill_value=0).values.flatten()

            mu_est = port.mu.values.flatten()
            cov_est = port.cov.values
            exp_ret = float(np.dot(mu_est, w_vector))
            risk = float(np.sqrt(w_vector.T @ cov_est @ w_vector))

        # Calculating and plotting the efficient frontier points
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        frontier = port.efficient_frontier(model=model, rm=rm, points=points, rf=rf, hist=hist)

        # Plot frontier
        ax = rp.plot_frontier(w_frontier=frontier, mu=port.mu, cov=port.cov, returns=returns,
                              rm=rm, rf=rf, alpha=0.05, cmap='viridis', w=w, marker='*', s=16,height=6, width=10, ax=None)

        # Remove default Riskfolio title
        ax.set_title("")

        label_lookup = {
            "Sharpe": "Max Risk Adjusted Return Portfolio",
            "MinRisk": "Minimum Risk Portfolio",
            "Utility": "Maximum Utility Portfolio",
            "MaxRet": "Maximum Return Portfolio",
            "Equal": "Equal Weighted Portfolio",
            "Manual": "Manually Selected Portfolio"
        }
        label = label_lookup.get(obj, "Selected Portfolio")

        # Title in PDF
        c.setFont("Times-Bold", 11)
        c.setFillColor(TEXT_COLOR)
        c.drawString(LEFT_MARGIN, y_pos +20, f"Efficient Frontier with {label}")

        # Adjust y_pos before placing chart
        y_pos -= LINE_HEIGHT -20 # Space below title

        # Space check
        chart_height = 10
        if y_pos < BOTTOM_MARGIN + chart_height:
            new_page()
            y_pos = PAGE_HEIGHT - TOP_MARGIN

        y_pos -= chart_height

        plt.legend()

        # Axis control
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        x_padding = (x_max - x_min) * 0.05
        y_padding = (y_max - y_min) * 0.05
        ax.set_xlim(x_min + x_padding, x_max - x_padding)
        ax.set_ylim(y_min + y_padding, y_max - y_padding)

        # Save to PDF
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=500)
        plt.close()
        buf.seek(0)
        img = ImageReader(buf)

        chart_height = 180
        if y_pos < BOTTOM_MARGIN + chart_height:
            new_page()
            y_pos = PAGE_HEIGHT - TOP_MARGIN

        c.drawImage(img, LEFT_MARGIN, y_pos - chart_height, width=PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN,
                    height=chart_height)
        y_pos -= chart_height + 30 # space between efficient frontier and next section

    else:
        print("⚠ Could not generate returns histogram after fallback.")

    # Explanatory Commentary Below Efficient Frontier ===
    #-----------------------------------------------------------------------------------
    # Space check
    estimated_paragraph_height = LINE_HEIGHT * 6
    if y_pos < BOTTOM_MARGIN + estimated_paragraph_height:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN

    # Commentary text
    commentary_text = (
        "The Efficient Frontier illustrates the set of optimal portfolios offering the highest expected return "
        "for a given level of risk, based on the risk and return characteristics of the selected ETFs. "
        "Portfolios along this curve represent the most efficient trade-offs between risk and return achievable "
        "through diversification.\n\n"
        f"The selected portfolio, constructed using the {label.lower()}, is positioned on this frontier, "
        "reflecting the client's preferences and risk profile. Its placement represents a carefully chosen balance "
        "between expected return and volatility, aligned with the stated investment objectives."
    )

    # Draw paragraph
    new_y = draw_wrapped_text(c, commentary_text, y_pos, indent=0)

    # Handle potential page break during paragraph
    while new_y is None:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN
        new_y = draw_wrapped_text(c, commentary_text, y_pos, indent=0)

    y_pos = new_y - LINE_HEIGHT  # Final y_pos after paragraph\


    # ===============================================================================================================
    # V. Backtested Portfolio Performance
    # ===============================================================================================================
    draw_section("Backtested Portfolio Performance", "", indent=True)

    # Introductory Commentary
    #,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    intro_text = (
        "This section presents a backtested analysis of the selected portfolio's historical performance. "
        "The results are based on the most recent price data and reflect how the portfolio would have behaved "
        "over the past period, including overall growth, return distributions, and risk characteristics."
    )
    new_y = draw_wrapped_text(c, intro_text, y_pos, indent=0)
    while new_y is None:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN
        new_y = draw_wrapped_text(c, intro_text, y_pos, indent=0)
    y_pos = new_y - LINE_HEIGHT * 1.2  # Extra space before charts

    # Run Backtest with bt
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    results = None
    try:
        weights_dict = client_data.get("Selected Portfolio", {}).get("Weights", {})
        w_series = pd.Series(weights_dict).reindex(price_df.columns, fill_value=0)

        if "CASH" in w_series.index and "CASH" not in price_df.columns:
            annual_cash_return = 0.02
            daily_cash_return = (1 + annual_cash_return) ** (1 / 252) - 1
            price_df["CASH"] = (1 + daily_cash_return) ** np.arange(len(price_df))

        price_df = price_df.sort_index().ffill().bfill()

        s = bt.Strategy(
            "Selected Portfolio",
            [bt.algos.RunOnce(),
             bt.algos.SelectAll(),
             bt.algos.WeighSpecified(**w_series.to_dict()),
             bt.algos.Rebalance()]
        )
        backtest = bt.Backtest(s, price_df)
        results = bt.run(backtest)
    except Exception as e:
        y_pos -= LINE_HEIGHT
        c.setFont(FONT_NAME, 10)
        c.setFillColor(TEXT_COLOR)
        c.drawString(LEFT_MARGIN, y_pos, f"⚠ Backtest failed: {e}")
        y_pos -= LINE_HEIGHT * 2

    # If Results Exist, Generate Charts and Stats
    # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    if results and results[0].stats is not None:

        stats_df = results[0].stats.to_frame(name="Value")

        # Extract key stats safely
        def safe_stat(stat):
            val = stats_df.loc[stat, "Value"] if stat in stats_df.index else None
            return val

        returns_stats = [
            ("Total Return", safe_stat("total_return")),
            ("CAGR", safe_stat("cagr")),
            ("Best Year", safe_stat("best_year")),
            ("Worst Year", safe_stat("worst_year")),
            ("Avg. Up Month", safe_stat("avg_up_month")),
            ("Avg. Down Month", safe_stat("avg_down_month"))
        ]

        risk_stats = [
            ("Max Drawdown", safe_stat("max_drawdown")),
            ("Daily Vol (ann.)", safe_stat("daily_vol")),
            ("Monthly Vol (ann.)", safe_stat("monthly_vol")),
            ("Yearly Vol (ann.)", safe_stat("yearly_vol")),
            ("Daily Sharpe", safe_stat("daily_sharpe")),
            ("Daily Sortino", safe_stat("daily_sortino"))
        ]

        # Rebased cumulative returns
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        cumulative_returns = results[0].prices / results[0].prices.iloc[0]
        daily_returns = cumulative_returns.pct_change().dropna()


        # Layout for Returns Chart and Histogram Side by Side
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        chart_height = 180
        chart_width = (PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN - 40) / 2
        left_x = LEFT_MARGIN
        right_x = LEFT_MARGIN + chart_width + 40

        if y_pos < BOTTOM_MARGIN + chart_height + 40:
            new_page()
            y_pos = PAGE_HEIGHT - TOP_MARGIN

        # Left Side: Portfolio Returns Chart
        c.setFont("Times-Bold", 11)
        c.setFillColor(TEXT_COLOR)
        c.drawString(LEFT_MARGIN, y_pos, "Portfolio Cumulative Returns")
        c.drawString(PAGE_WIDTH / 2 + 20, y_pos, "Portfolio Returns Histogram with Key Statistics")

        # Adjust space below titles
        y_pos -= LINE_HEIGHT * 2

        chart_height = 200
        chart_width = (PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN - 40) / 2

        if y_pos < BOTTOM_MARGIN + chart_height:
            new_page()
            y_pos = PAGE_HEIGHT - TOP_MARGIN

        # Cumulative Returns Plot
        fig, ax = plt.subplots(figsize=(3.25, 4.5), dpi=300)
        cumulative_returns.plot(ax=ax, color="#000080", linewidth=1.5)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(axis='both', labelsize=9)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontname("Times New Roman")
        ax.set_title("")
        ax.set_xlabel("")
        ax.set_ylabel("Portfolio Value (Rebased)", fontsize=9, fontname="Times New Roman")
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=500)
        plt.close(fig)
        buf.seek(0)
        img = ImageReader(buf)
        c.drawImage(img, LEFT_MARGIN, y_pos - chart_height, width=chart_width, height=chart_height)

        # Histogram Plot (Full Width on Right Side)
        portfolio_returns = returns @ w_series
        mean_ret = portfolio_returns.mean()
        median_ret = portfolio_returns.median()
        std_ret = portfolio_returns.std()
        mode_estimate = portfolio_returns.mode().iloc[0] if not portfolio_returns.mode().empty else None

        fig, ax = plt.subplots(figsize=(3.25, 4.5), dpi=300)
        ax.hist(portfolio_returns, bins=50, color='gold', edgecolor='black', alpha=0.7)
        ax.axvline(mean_ret, color='blue', linestyle='dashed', linewidth=1.5, label=f"Mean: {mean_ret:.4%}")
        ax.axvline(median_ret, color='green', linestyle='dashed', linewidth=1.5, label=f"Median: {median_ret:.4%}")
        ax.axvline(mean_ret - std_ret, color='red', linestyle='dotted', linewidth=1, label="-1 Std Dev")
        ax.axvline(mean_ret + std_ret, color='red', linestyle='dotted', linewidth=1, label="+1 Std Dev")
        ax.axvline(mean_ret - 2 * std_ret, color='orange', linestyle='dotted', linewidth=1, label="-2 Std Dev")
        ax.axvline(mean_ret + 2 * std_ret, color='orange', linestyle='dotted', linewidth=1, label="+2 Std Dev")
        ax.axvline(mean_ret - 3 * std_ret, color='purple', linestyle='dotted', linewidth=1, label="-3 Std Dev")
        ax.axvline(mean_ret + 3 * std_ret, color='purple', linestyle='dotted', linewidth=1, label="+3 Std Dev")
        if mode_estimate is not None:
            ax.axvline(mode_estimate, color='darkmagenta', linestyle='dashdot', linewidth=1.5,
                       label=f"Mode: {mode_estimate:.4%}")
        ax.set_xlabel("Daily Return", fontsize=9, fontname="Times New Roman")
        ax.set_ylabel("Frequency", fontsize=9, fontname="Times New Roman")
        ax.tick_params(axis='both', labelsize=9)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.legend(fontsize=6, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=500)
        plt.close()
        buf.seek(0)
        img = ImageReader(buf)
        c.drawImage(img, PAGE_WIDTH / 2 + 20, y_pos - chart_height, width=chart_width, height=chart_height)

        y_pos -= chart_height + 30

        # Commentary Below Charts
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        commentary_text = (
            "The chart on the left illustrates the cumulative growth of the selected portfolio, inclusive of the "
            "cash allocation earning a 2% annual return. The histogram on the right displays the distribution of "
            "daily portfolio returns. The relatively concentrated distribution, along with low occurrence of extreme "
            "outliers beyond ±2 or 3 standard deviations, reflects stable risk characteristics and consistent behavior."
        )
        new_y = draw_wrapped_text(c, commentary_text, y_pos, indent=0)

        while new_y is None:
            new_page()
            y_pos = PAGE_HEIGHT - TOP_MARGIN
            new_y = draw_wrapped_text(c, commentary_text, y_pos, indent=0)
        y_pos = new_y - LINE_HEIGHT

        # ===== Returns and Risk Tables Side by Side =====
        table_height = LINE_HEIGHT * max(len(returns_stats), len(risk_stats)) + LINE_HEIGHT * 4
        if y_pos < BOTTOM_MARGIN + table_height:
            new_page()
            y_pos = PAGE_HEIGHT - TOP_MARGIN

        left_x = LEFT_MARGIN
        right_x = PAGE_WIDTH / 2 + 10
        col_widths = [130, 80]
        zebra_color = HexColor("#f5e8c4")

        # Prepare table rows
        rows_left = [(label, f"{val:.2%}" if isinstance(val, (float, np.floating)) else "N/A") for label, val in
                     returns_stats]
        rows_right = [(label, f"{val:.2%}" if isinstance(val, (float, np.floating)) else "N/A") for label, val in
                      risk_stats]

        left_end_y = draw_table(c, left_x, y_pos, col_widths, ["Returns Statistics", "Value"], rows_left,
                                table_title="", zebra_color=zebra_color, new_page_fn=new_page)
        right_end_y = draw_table(c, right_x, y_pos, col_widths, ["Risk Statistics", "Value"], rows_right,
                                 table_title="", zebra_color=zebra_color, new_page_fn=new_page)

        y_pos = min(left_end_y, right_end_y) - LINE_HEIGHT

        # Final Commentary
        # ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
        commentary_text = (
            "The performance summary tables provide further insight into the portfolio's historical characteristics. "
            "The observed returns, including metrics like CAGR and win rates, demonstrate the growth potential, while risk metrics such as "
            "volatility and drawdowns reflect its stability. The strong Sharpe and Sortino ratios indicate favorable risk-adjusted performance, "
            "consistent with the intended investment objectives."
        )
        new_y = draw_wrapped_text(c, commentary_text, y_pos, indent=0)
        while new_y is None:
            new_page()
            y_pos = PAGE_HEIGHT - TOP_MARGIN
            new_y = draw_wrapped_text(c, commentary_text, y_pos, indent=0)
        y_pos = new_y - LINE_HEIGHT


    # Portfolio Forecasting
    # #=======================================================================================================
    draw_section("Portfolio Outlook and Projections", "", indent=True)

    # Monte Carlo Simulation - Portfolio Outlook & Projections
    #------------------------------------------------------------------------------------------

    # Compute cumulative returns
    cumulative_returns = results[0].prices / results[0].prices.iloc[0]
    daily_returns = cumulative_returns.pct_change().dropna()

    # Monte Carlo Simulation Parameters
    projection_years = 3
    simulations = 10000
    days_per_year = 252
    total_days = projection_years * days_per_year

    # Estimate parameters from historical data
    annual_return = daily_returns.mean() * 252
    annual_volatility = daily_returns.std() * (252 ** 0.5)

    # Daily parameters
    daily_drift = (annual_return - 0.5 * annual_volatility ** 2) / days_per_year
    daily_vol = annual_volatility / (days_per_year ** 0.5)

    # Initial portfolio value
    initial_value = cumulative_returns.iloc[-1]

    # Simulate paths
    sim_paths = np.zeros((total_days, simulations))
    sim_paths[0] = initial_value

    for t in range(1, total_days):
        random_shocks = np.random.normal(0, 1, simulations)
        sim_paths[t] = sim_paths[t - 1] * np.exp(daily_drift + daily_vol * random_shocks)

    # Percentile fan chart
    percentiles = [5, 25, 50, 75, 95]
    percentile_paths = np.percentile(sim_paths, percentiles, axis=1)

    # Combined time axis
    historical_days = len(cumulative_returns) - 1
    projection_days = total_days
    total_x = np.arange(historical_days + projection_days) / days_per_year
    projection_time = np.arange(projection_days) / days_per_year + historical_days / days_per_year

    # Space check
    chart_height = 220
    if y_pos < BOTTOM_MARGIN + chart_height:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN

    # Title
    c.setFont("Times-Bold", 11)
    c.setFillColor(TEXT_COLOR)
    c.drawString(LEFT_MARGIN, y_pos, "Historical and Simulated Portfolio Projections")
    y_pos -= LINE_HEIGHT * 2

    # Plot combined chart
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)

    # Historical cumulative returns
    ax.plot(total_x[:historical_days + 1], cumulative_returns.values, color="blue", linewidth=1.5,
            label="Historical Cumulative Returns")

    # Vertical separator for projection start
    transition_time = historical_days / days_per_year
    ax.axvline(transition_time, color="black", linestyle="dotted", linewidth=1, label="Projection Start")

    # Monte Carlo fan chart
    ax.plot(projection_time, percentile_paths[2], color="green", linewidth=1.5, label="Median Projection")
    ax.fill_between(projection_time, percentile_paths[0], percentile_paths[4], color="gold", alpha=0.3,
                    label="5th - 95th Percentile")
    ax.fill_between(projection_time, percentile_paths[1], percentile_paths[3], color="orange", alpha=0.4,
                    label="25th - 75th Percentile")

    # Styling
    ax.set_xlabel("Years", fontsize=9, fontname="Times New Roman")
    ax.set_ylabel("Portfolio Value", fontsize=9, fontname="Times New Roman")
    ax.tick_params(labelsize=8)
    ax.set_title("")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(fontsize=7, loc="upper left")

    plt.tight_layout()

    # Export to PDF
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=500)
    plt.close()
    buf.seek(0)
    img = ImageReader(buf)

    c.drawImage(img, LEFT_MARGIN, y_pos - chart_height,
                width=PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN, height=chart_height)
    y_pos -= chart_height + 20

    # Commentary below
    commentary_text = (
        "The above chart illustrates 10,000 simulated portfolio trajectories over a 3-year horizon using a Monte Carlo approach. "
        "The shaded regions represent the 25th-75th and 5th-95th percentile ranges, providing insight into potential future portfolio outcomes. "
        "This analysis reflects both the historical return characteristics and inherent market uncertainty, supporting informed expectation management."
    )

    new_y = draw_wrapped_text(c, commentary_text, y_pos, indent=0)
    while new_y is None:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN
        new_y = draw_wrapped_text(c, commentary_text, y_pos, indent=0)

    y_pos = new_y - LINE_HEIGHT

    #Projected Return & Risk Table
    projected_return = annual_return
    projected_vol = annual_volatility
    VaR_95 = initial_value * (
                np.exp(daily_drift * total_days + daily_vol * np.percentile(np.random.normal(0, 1, 100000), 5)) - 1)
    best_case = np.percentile(sim_paths[-1], 95)
    worst_case = np.percentile(sim_paths[-1], 5)


    # ===== Layout for Projected Return Table and Horizon Distribution Side by Side =====
    # Space check for full side-by-side layout
    chart_height = 140  # Define common height for side by side
    if y_pos < BOTTOM_MARGIN + chart_height:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN

    left_x = LEFT_MARGIN
    right_x = PAGE_WIDTH / 2 + 10
    col_widths = [120, 100]

    # Titles aligned
    c.setFont("Times-Bold", 11)
    c.setFillColor(TEXT_COLOR)
    c.drawString(left_x, y_pos, "Projected Return & Risk")
    c.drawString(right_x, y_pos, "Projected Distribution at Horizon")
    y_pos -= LINE_HEIGHT * 2  # Space after titles

    # Capture Y for aligned layout
    table_y = y_pos

    # ===== LEFT TABLE =====
    rows_left = [
        ["Expected Return (Ann.)", f"{projected_return:.2%}"],
        ["Expected Volatility (Ann.)", f"{projected_vol:.2%}"],
        ["95% VaR", f"{VaR_95:.2f}"],
        ["Expected Best Case", f"{best_case:.2f}"],
        ["Expected Worst Case", f"{worst_case:.2f}"],
    ]
    y_pos = draw_table(c, left_x, table_y, col_widths, ["Metric", "Value"], rows_left,
                       table_title=None, zebra_color=HexColor("#f5e8c4"), new_page_fn=new_page)

    # ===== RIGHT HISTOGRAM =====
    horizon_values = sim_paths[-1]
    fig, ax = plt.subplots(figsize=(3.2, 2.5), dpi=300)
    ax.hist(horizon_values, bins=50, color='lightblue', edgecolor='black', alpha=0.7, density=True)

    # Add vertical lines for 25% bear, 25% bull, and 50% fair value estimate range
    bear_case = np.percentile(horizon_values, 25)
    bull_case = np.percentile(horizon_values, 75)
    ax.axvline(bear_case, color='red', linestyle='dashed', linewidth=1.5, label="25% Bear Case")
    ax.axvline(bull_case, color='green', linestyle='dashed', linewidth=1.5, label="25% Bull Case")
    ax.axvspan(bear_case, bull_case, color='gold', alpha=0.2, label="Central 50% Range")

    ax.set_xlabel("Portfolio Value at Year 3", fontsize=7)
    ax.set_ylabel("Probability Density", fontsize=7)
    ax.tick_params(labelsize=6)
    ax.set_title("")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=500)
    plt.close()
    buf.seek(0)
    img = ImageReader(buf)

    # Histogram drawn at SAME Y as the left table
    c.drawImage(img, right_x, table_y - chart_height,
                width=PAGE_WIDTH / 2 - RIGHT_MARGIN - 20, height=chart_height)

    # Compute bottom Y of both elements
    table_bottom_y = y_pos
    histogram_bottom_y = table_y - chart_height

    # Determine the lower point
    content_bottom_y = min(table_bottom_y, histogram_bottom_y)

    # Position for commentary, adding neat space (e.g., 15 pts)
    y_pos = content_bottom_y - 15

    # Final Commentary
    commentary_text = (
        "The table and distribution chart above summarize the projected return characteristics and potential portfolio outcomes over the 3-year horizon. "
        "The probability distribution reflects simulated uncertainty, highlighting both likely ranges and tail risks, aiding in realistic expectation setting."
    )

    new_y = draw_wrapped_text(c, commentary_text, y_pos, indent=0)
    while new_y is None:
        new_page()
        y_pos = PAGE_HEIGHT - TOP_MARGIN
        new_y = draw_wrapped_text(c, commentary_text, y_pos, indent=0)

    y_pos = new_y - LINE_HEIGHT

    # # VII. Appendices======== ==============================================================================
    # #=======================================================================================================
    # draw_section("VII. Appendices", "Additional notes, assumptions or disclosures...")

    c.save()
    buffer.seek(0)

    # === TOC Rendering ===
    toc_buffer = BytesIO()
    toc_canvas = canvas.Canvas(toc_buffer, pagesize=A4)
    toc_canvas.setFont(FONT_NAME, 18)
    toc_canvas.setFillColor(TITLE_COLOR)
    toc_canvas.drawString(LEFT_MARGIN, PAGE_HEIGHT - 100, "Table of Contents")
    toc_canvas.setFont(FONT_NAME, 12)
    toc_canvas.setFillColor(TEXT_COLOR)
    y = PAGE_HEIGHT - 140
    for entry in toc_entries:
        indent = LEFT_MARGIN + (20 if entry["indent"] else 0)
        text_width = stringWidth(entry["title"], FONT_NAME, 12)
        dots = '.' * max(0, int((PAGE_WIDTH - indent - RIGHT_MARGIN - 40 - text_width) / stringWidth('.', FONT_NAME, 12)))
        toc_canvas.drawString(indent, y, f"{entry['title']} {dots}")
        toc_canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y, str(entry["page"]))
        y -= TOC_LINE_SPACING
        if y < BOTTOM_MARGIN:
            toc_canvas.showPage()
            y = PAGE_HEIGHT - TOP_MARGIN
    toc_canvas.showPage()
    toc_canvas.save()
    toc_buffer.seek(0)

    # === Merge PDF (cover + TOC + body) ===
    reader_main = PdfReader(buffer)
    reader_toc = PdfReader(toc_buffer)
    writer = PdfWriter()
    writer.add_page(reader_main.pages[0])  # cover
    for toc_page in reader_toc.pages:
        writer.add_page(toc_page)
    for page in reader_main.pages[2:]:
        writer.add_page(page)

    final_buffer = BytesIO()
    writer.write(final_buffer)
    final_buffer.seek(0)
    return final_buffer.getvalue()

# === Trigger PDF Download ===
if st.button("📥 Generate PDF Report"):
    pdf_bytes = generate_continuous_pdf(inv_note, exec_summary, macro_perspective, asset_outlooks)
    st.download_button("📩 Download PDF", data=pdf_bytes, file_name="QuantOptima_Report.pdf")