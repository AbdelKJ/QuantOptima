from io import BytesIO
import pandas as pd
from datetime import date
import streamlit as st
import yfinance as yf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle


#======================================================================================================================
#==========================================   Helper Functions    =====================================================
# =====================================================================================================================

def generate_pdf_report(
    client_name,
    investment_amount,
    executive_summary,
    macro_context,
    asset_class_comments,
    current_allocation,
    proposed_allocation,
    logo_path="assets/QuantOptima.png",
    background_path="assets/Report12.png",
    selected_etfs_total=st.session_state.selected_etfs,
    population=st.session_state.population,
    metrics_list=st.session_state.metrics_list
):

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left_margin = 50
    right_margin = width - 50
    footer_margin = 70
    current_page = 1
    toc_entries = []

    # NEW SPACING CONSTANTS
    GAP_SMALL = 10
    GAP_MEDIUM = 20
    GAP_LARGE = 40

#-----------------------------------------------------------------------------------------------------------------------
    def add_toc_entry(title, page):
        toc_entries.append((title, page))

# -----------------------------------------------------------------------------------------------------------------------
    def ensure_space(required_space):
        nonlocal y_pos, current_page
        if y_pos < required_space + footer_margin + 30:
            c.showPage()
            current_page += 1
            draw_header_footer(current_page)
            y_pos = height - 100
            # 💥 Reset font/color after new page
            c.setFont("Times-Roman", 14)
            c.setFillColor(colors.black)

# ----------------------------------------------------------------------------------------------------------------------

    def draw_header_footer(page_num):
        if page_num > 1:
            c.setFont("Times-Bold", 12)
            c.setFillColor(colors.HexColor("#6F1D1B"))
            c.drawCentredString(width / 2, height - 40, "Asset Allocation Report")
            try:
                logo = ImageReader(logo_path)
                c.drawImage(logo, width - 100, height - 80, width=80, height=50, mask='auto')
            except:
                pass
            c.setStrokeColor(colors.HexColor("#6F1D1B"))
            c.setLineWidth(1)
            c.line(40, height - 60, width - 40, height - 60)
            c.setFont("Times-Roman", 10)
            c.setFillColor(colors.black)
            c.drawCentredString(width / 2, 30, f"Page {page_num}")

# ----------------------------------------------------------------------------------------------------------------------
    def draw_paragraph(text, start_y):
        nonlocal current_page
        max_width = right_margin - left_margin
        y_cursor = start_y
        c.setFont("Times-Roman", 14)
        c.setFillColor(colors.black)
        paragraphs = text.split('\n')

        for paragraph in paragraphs:
            lines = simpleSplit(paragraph, "Times-Roman", 14, max_width)
            for i, line in enumerate(lines):
                if y_cursor < footer_margin + 30:
                    c.showPage()
                    current_page += 1
                    draw_header_footer(current_page)
                    y_cursor = height - 100
                    # 🔥 Reset font and color after new page
                    c.setFont("Times-Roman", 14)
                    c.setFillColor(colors.black)

                words = line.split()
                if not words:
                    y_cursor -= 18
                    continue

                if i == len(lines) - 1 or len(words) == 1:
                    # Last line or single-word line → draw normally, left aligned
                    c.drawString(left_margin, y_cursor, line)
                else:
                    total_text_width = sum(c.stringWidth(word, "Times-Roman", 14) for word in words)
                    space_count = len(words) - 1
                    extra_space = (max_width - total_text_width) / space_count

                    x = left_margin
                    for word in words:
                        c.drawString(x, y_cursor, word)
                        x += c.stringWidth(word, "Times-Roman", 14) + extra_space

                y_cursor -= 18
            y_cursor -= 10  # space between paragraphs

        return y_cursor

    # ------------------------------------------------------------------------------------------------------------------
    def draw_dynamic_etf_table(c, x_start, y_start, etf_list):
        nonlocal current_page

        c.setFont("Times-Bold", 16)
        c.setFillColor(colors.HexColor("#6F1D1B"))
        c.drawString(x_start, y_start, "Investment Universe")
        y_pos = y_start - 20

        c.setFont("Times-Roman", 11)
        c.setFillColor(colors.black)

        max_text_width = right_margin - x_start - 15  # leave space for padding

        for etf in etf_list:
            wrapped_lines = simpleSplit(f"- {etf}", "Times-Roman", 11, max_text_width)

            for line in wrapped_lines:
                if y_pos < 70:  # avoid footer overlap
                    c.showPage()
                    current_page += 1
                    draw_header_footer(current_page)
                    y_pos = height - 100
                    c.setFont("Times-Roman", 11)
                    c.setFillColor(colors.black)

                c.drawString(x_start + 5, y_pos, line)
                y_pos -= 14

        return y_pos

    # ---------------------------------------------------------------------------------------------------------------------
    def ensure_space(required_space):
        nonlocal y_pos, current_page
        if y_pos < required_space + footer_margin + 30:
            c.showPage()
            current_page += 1
            draw_header_footer(current_page)
            y_pos = height - 100

    # ---------------------------------------------------------------------------------------------------------------------
    def draw_allocation_table(allocation_dict, page_title, y_start):
        nonlocal current_page
        if y_start < 200:
            c.showPage()
            current_page += 1
            draw_header_footer(current_page)
            y_start = height - 100

        table_x = left_margin
        table_y = y_start

        # Section title (only draw and subtract space if title is not blank)
        # -------------------------------------------------------------------------------------------------------------
        if page_title.strip():
            c.setFont("Times-Bold", 16)
            c.setFillColor(colors.HexColor("#6F1D1B"))
            c.drawString(table_x, table_y, page_title)
            table_y -= 30

        header_height = 22
        c.setFillColor(colors.HexColor("#6F1D1B"))
        c.rect(table_x - 5, table_y - header_height, right_margin - left_margin + 10, header_height, fill=1, stroke=0)

        # Header labels
        c.setFont("Times-Bold", 12)
        c.setFillColor(colors.white)
        text_offset = header_height / 1.5 - 3
        c.drawString(table_x, table_y - text_offset, "Asset Class")
        c.drawString(table_x + 250, table_y - text_offset, "Allocation (%)")

        # Table body
        c.setFont("Times-Roman", 11)
        sorted_allocation = {k: v for k, v in allocation_dict.items() if v > 0}
        row_y = table_y - header_height - 8
        row_height = 20
        fill_colors = [colors.whitesmoke, colors.lightgrey]
        i = 0

        for asset, alloc in sorted_allocation.items():
            if row_y < footer_margin + row_height + 20:
                c.showPage()
                current_page += 1
                draw_header_footer(current_page)
                row_y = height - 100

            c.setFillColor(fill_colors[i % 2])
            c.rect(table_x - 5, row_y - 4, right_margin - left_margin + 10, row_height, fill=1, stroke=0)

            c.setFillColor(colors.black)
            c.drawString(table_x, row_y + 4, asset)
            c.drawString(table_x + 250, row_y + 4, f"{alloc:.2f}%")

            row_y -= row_height
            i += 1

        return row_y - 30

    # dRAW JUSTIFIED PARAGRAPH
    # ----------------------------------------------------------------------------------------------------------------
    def draw_justified_paragraph(text, y_pos, current_page_ref):
        paragraphs = text.split('\n')
        max_width = right_margin - left_margin
        font_name = "Times-Roman"
        font_size = 14
        line_height = 18

        c.setFont(font_name, font_size)
        c.setFillColor(colors.black)

        for paragraph in paragraphs:
            lines = simpleSplit(paragraph, font_name, font_size, max_width)
            for i, line in enumerate(lines):
                if y_pos < footer_margin + 30:
                    c.showPage()
                    current_page_ref[0] += 1
                    draw_header_footer(current_page_ref[0])
                    y_pos = height - 100

                    # 💥 RE-APPLY font and color after new page!
                    c.setFont(font_name, font_size)
                    c.setFillColor(colors.black)

                words = line.split()
                if not words:
                    y_pos -= line_height
                    continue

                is_last_line = (i == len(lines) - 1 or len(words) == 1)
                if is_last_line:
                    c.drawString(left_margin, y_pos, line)
                else:
                    total_text_width = sum(c.stringWidth(word, font_name, font_size) for word in words)
                    space_count = len(words) - 1
                    extra_space = (max_width - total_text_width) / space_count if space_count > 0 else 0

                    x = left_margin
                    for word in words:
                        c.drawString(x, y_pos, word)
                        x += c.stringWidth(word, font_name, font_size) + extra_space

                y_pos -= line_height
            y_pos -= 5  # space between paragraphs

        return y_pos

# ---------------------------------------------------------------------------------------------------------------------
    def ai_generate_allocation_text(allocation_dict, add_transition=False):
        import random
        sorted_allocations = sorted(allocation_dict.items(), key=lambda x: -x[1])
        major = [a for a, w in sorted_allocations if w >= 20]
        minor = [a for a, w in sorted_allocations if 0 < w < 20]
        dom_asset, dom_weight = sorted_allocations[0]
        text = random.choice([
            "The portfolio reflects a thoughtful balance across key asset classes. ",
            "A strategically diversified structure characterizes the portfolio. ",
            "The current allocation demonstrates a disciplined investment approach. ",
        ])
        if dom_weight > 65:
            text += (f"A significant allocation of {dom_weight:.1f}% is concentrated in {dom_asset}, indicating a "
                     f"focused strategy. ")
        elif len(major) >= 2:
            major_text = ", ".join(major[:-1]) + f", and {major[-1]}" if len(major) > 1 else major[0]
            text += f"The portfolio is primarily distributed among {major_text}. "
        elif len(major) == 1:
            text += f"{major[0]} is the dominant position, supported by broader diversification. "
        if minor:
            minor_text = ", ".join(minor[:-1]) + f", and {minor[-1]}" if len(minor) > 1 else minor[0]
            text += f"Additional allocations to {minor_text} enhance diversification. "
        text += "This structure aims to optimize returns while maintaining prudent risk exposure."
        if add_transition:
            text += ("\n\nBuilding on the existing composition, the following proposed allocation aims to further enhance "
                     "risk-adjusted returns.")
        return text

# ---------------------------------------------------------------------------------------------------------------------
    def generate_change_commentary(current, proposed):
        lines = []
        increases = []
        decreases = []
        unchanged = []

        for asset in current:
            old = current[asset]
            new = proposed.get(asset, 0)
            diff = new - old

            if abs(diff) < 1:
                unchanged.append(asset)
            elif diff > 0:
                increases.append((asset, diff))
            else:
                decreases.append((asset, -diff))

        # First paragraph: High-level overview
        # -------------------------------------------------------------------------------------------------------------
        paragraph1 = ("The proposed portfolio introduces a number of strategic allocation shifts to enhance "
                      "diversification and improve the portfolio’s overall risk-return profile.")

        # Second paragraph: Increases
        # -------------------------------------------------------------------------------------------------------------
        paragraph2 = ""
        if increases:
            inc_text = ", ".join(f"{a} (+{d:.1f}pp)" for a, d in increases)
            paragraph2 = (f"Increased exposures were allocated to the following asset classes: {inc_text}. These "
                          f"additions are intended to capitalize on evolving market opportunities and provide greater "
                          f"upside potential.")

        # Third paragraph: Decreases
        # -------------------------------------------------------------------------------------------------------------
        paragraph3 = ""
        if decreases:
            dec_text = ", ".join(f"{a} (-{d:.1f}pp)" for a, d in decreases)
            paragraph3 = (f"Conversely, allocations were reduced in: {dec_text}, reflecting either profit-taking or a "
                          f"repositioning to manage volatility and downside risk.")

        # Optional paragraph: unchanged
        # --------------------------------------------------------------------------------------------------------------
        paragraph4 = ""
        if unchanged:
            paragraph4 = (f"Allocations to {', '.join(unchanged)} remained largely unchanged, maintaining the core "
                          f"structure of the original portfolio.")

        # Fallback if no change
        # --------------------------------------------------------------------------------------------------------------
        if not increases and not decreases:
            return ("No significant changes were made in the proposed allocation. The structure remains consistent "
                    "with the existing portfolio.")

        return "\n\n".join([paragraph1, paragraph2, paragraph3, paragraph4]).strip()

#=======================================================================================================================
#==========================================   PAGES    =================================================================
# ======================================================================================================================

# Cover Page
#----------------------------------------------------------------------------------------------------------------------
    c.drawImage(background_path, 0, 0, width=width, height=height, preserveAspectRatio=False, mask='auto')
    c.setFillColor(colors.HexColor("#FFA800"))
    c.setFont("Times-Bold", 46)
    c.drawCentredString(width / 2, height - 540, "Asset Allocation Report")
    c.setFont("Times-Roman", 24)
    c.drawCentredString(width / 2, height - 590, "Quantitative Portfolio Optimization")
    c.setFont("Times-Italic", 28)
    c.drawCentredString(width / 2, height - 690, client_name)
    c.setFont("Times-Italic", 16)
    c.drawCentredString(width / 2, height - 730, date.today().strftime('%B %d, %Y'))
    c.showPage()
    current_page += 1

# ======================================================================================================================
# ==========================================   I. Executive Summary       ==============================================
# ======================================================================================================================

    title_to_paragraph_gap = 30  # distance from title baseline to paragraph top
    subheader_to_paragraph_gap = 20
    paragraph_line_spacing = 18
    asset_commentary_gap = 20
    table_to_title_gap = 30

    draw_header_footer(current_page)
    add_toc_entry("I. Executive Summary", current_page)
    c.setFont("Times-Bold", 20)
    c.setFillColor(colors.HexColor("#6F1D1B"))
    title_y = height - 100
    c.drawString(left_margin, title_y, "I. Executive Summary")

    # Unified spacing
    # ------------------------------------------------------------------------------------------------------------------
    y_pos = draw_paragraph(executive_summary, title_y - title_to_paragraph_gap)

# ======================================================================================================================
# ==========================================   II. Macroeconomic Overview    ===========================================
# ======================================================================================================================
    if y_pos < 300:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    add_toc_entry("II. Macroeconomic Overview", current_page)
    c.setFont("Times-Bold", 20)
    c.setFillColor(colors.HexColor("#6F1D1B"))
    title_y = y_pos
    c.drawString(left_margin, title_y, "II. Macroeconomic Overview")

    # Unified spacing
    # ------------------------------------------------------------------------------------------------------------------
    y_pos = draw_paragraph(macro_context, title_y - title_to_paragraph_gap)

# ======================================================================================================================
# ==========================================   III. Asset Classes Outlook      =========================================
# ======================================================================================================================
    if y_pos < 300:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    add_toc_entry("III. Asset Classes Outlook", current_page)

    # Main section title
    # ------------------------------------------------------------------------------------------------------------------
    c.setFont("Times-Bold", 20)
    c.setFillColor(colors.HexColor("#6F1D1B"))
    title_y = y_pos
    c.drawString(left_margin, title_y, "III. Asset Classes Outlook")
    y_pos = title_y - title_to_paragraph_gap

    for asset, commentary in asset_class_comments.items():
        title_printed = False
        lines = simpleSplit(commentary, "Times-Roman", 14, right_margin - left_margin)

        line_idx = 0
        while line_idx < len(lines):
            if y_pos < footer_margin + 60:
                c.showPage()
                current_page += 1
                draw_header_footer(current_page)
                y_pos = height - 100

            # Subheader (asset name)
            # ------------------------------------------------------------------------------------------------------------------
            if not title_printed:
                c.setFont("Times-Bold", 16)
                c.setFillColor(colors.black)
                subheader_y = y_pos
                c.drawString(left_margin + 10, subheader_y, asset)
                y_pos = subheader_y - subheader_to_paragraph_gap
                title_printed = True

                add_toc_entry(f"  {asset}", current_page)

            # Paragraph lines
            # ------------------------------------------------------------------------------------------------------------------
            c.setFont("Times-Roman", 14)
            c.setFillColor(colors.black)

            while line_idx < len(lines) and y_pos >= footer_margin + 30:
                line = lines[line_idx]
                words = line.split()
                if not words:
                    y_pos -= paragraph_line_spacing
                    line_idx += 1
                    continue

                is_last_line = (line_idx == len(lines) - 1)
                is_short_line = len(words) < 4

                if is_last_line or is_short_line:
                    c.drawString(left_margin + 20, y_pos, line)
                else:
                    total_text_width = sum(c.stringWidth(word, "Times-Roman", 14) for word in words)
                    space_count = len(words) - 1
                    base_space = 3
                    max_extra = 10
                    extra_space = min((right_margin - (left_margin + 20) - total_text_width) / space_count, max_extra)

                    x = left_margin + 20
                    for word in words:
                        c.drawString(x, y_pos, word)
                        x += c.stringWidth(word, "Times-Roman", 14) + extra_space

                y_pos -= paragraph_line_spacing
                line_idx += 1

        # After full asset commentary, add uniform gap
        # ------------------------------------------------------------------------------------------------------------------
        y_pos -= asset_commentary_gap

# ======================================================================================================================
# ==========================================   IV. Asset Allocation      ===============================================
# ======================================================================================================================


    # Asset Allocation & Optimization (TOC + Title)
    # ------------------------------------------------------------------------------------------------------------------
    # TOC Entry + Title
    add_toc_entry("IV. Asset Allocation & Optimization", current_page)

    # Main Section Title
    c.setFont("Times-Bold", 20)
    c.setFillColor(colors.HexColor("#6F1D1B"))
    title_y = y_pos
    c.drawString(left_margin, title_y, "IV. Asset Allocation & Optimization")
    y_pos = title_y - title_to_paragraph_gap

    # Current Portfolio Allocation
    # ------------------------------------------------------------------------------------------------------------------
    add_toc_entry("    Current Portfolio Allocation", current_page)

    if y_pos < 150:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    # === Title
    c.setFont("Times-Bold", 16)
    c.setFillColor(colors.black)
    c.drawString(left_margin + 10, y_pos, "Current Portfolio Allocation")
    y_pos -= 30

    # === Build table data
    allocation_data = [["Asset Class", "Allocation (%)"]]
    for asset, pct in current_allocation.items():
        allocation_data.append([asset, f"{pct:.1f}%"])

    # === Create Table
    alloc_table = Table(allocation_data, colWidths=[140, 80])

    alloc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#6F1D1B")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        # ✅ no grid
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
    ]))

    # === Measure table dimensions
    w_table, h_table = alloc_table.wrapOn(c, width - left_margin * 2, y_pos - footer_margin)

    # === Set positions
    table_x = left_margin
    table_y = y_pos - h_table

    # === Draw table
    alloc_table.drawOn(c, table_x, table_y)

    # ✅ Store bottom Y of table
    table_bottom_y = table_y

    # === Commentary (RIGHT side)
    largest_alloc_asset = max(current_allocation, key=current_allocation.get)
    smallest_alloc_asset = min(current_allocation, key=current_allocation.get)

    commentary_text = (
        f"The current portfolio reflects a diversified allocation across asset classes, "
        f"with the largest exposure allocated to {largest_alloc_asset} at {current_allocation[largest_alloc_asset]:.1f}%, "
        f"while {smallest_alloc_asset} holds the smallest weight at {current_allocation[smallest_alloc_asset]:.1f}%. "
        f"This allocation provides a baseline view of existing investment positioning."
    )

    # === Set commentary starting position
    comment_x = left_margin + w_table + 40  # adjust horizontal gap if needed
    comment_y = y_pos  # align top of commentary to top of table

    # === Wrap and draw commentary
    comment_width = right_margin - comment_x
    comment_lines = simpleSplit(commentary_text, "Times-Italic", 11, comment_width)

    c.setFont("Times-Italic", 11)
    c.setFillColor(colors.HexColor("#6F1D1B"))
    text_obj = c.beginText(comment_x, comment_y)
    text_obj.setLeading(14)
    for line in comment_lines:
        text_obj.textLine(line)
    c.drawText(text_obj)

    # ✅ Store bottom Y of commentary
    commentary_bottom_y = text_obj.getY()

    # === Calculate new y_pos
    y_pos = min(table_bottom_y, commentary_bottom_y) - 30

    # === Check for space before next section
    if y_pos < footer_margin + 50:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    # Optimization Models
    # ------------------------------------------------------------------------------------------------------------------
    add_toc_entry("    Optimisation Models", current_page)

    c.setFont("Times-Bold", 16)
    c.setFillColor(colors.black)
    c.drawString(left_margin + 10, y_pos, "Optimisation Models")
    y_pos -= 20

    # Optimization Models Summary Table
    # ------------------------------------------------------------------------------------------------------------------
    summary_df = population.summary()

    # Reset index so metric names are first column
    summary_df_reset = summary_df.reset_index()
    data = [summary_df_reset.columns.tolist()] + summary_df_reset.values.tolist()

    # Rename index column
    data[0][0] = 'Metric'

    # Optional: Add line breaks for long headers
    data[0] = [col.replace(' ', '\n') if len(col) > 12 else col for col in data[0]]

    # Format numeric cells
    for i in range(1, len(data)):
        row = data[i]
        for j, val in enumerate(row):
            if isinstance(val, float):
                row[j] = f"{val:.2f}"

    # Define column widths
    table_width = right_margin - left_margin
    first_col_width = 120
    remaining_width = table_width - first_col_width
    other_col_width = remaining_width / (len(data[0]) - 1)
    col_widths = [first_col_width] + [other_col_width] * (len(data[0]) - 1)

    # Define TableStyle once
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#6F1D1B")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        #('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
    ])

    # Create initial table
    pdf_table = Table(data, colWidths=col_widths, repeatRows=1)
    pdf_table.setStyle(table_style)

    # Handle multi-page split
    # ------------------------------------------------------------------------------------------------------------------
    available_height = y_pos - footer_margin
    remaining_table = pdf_table

    while True:
        table_parts = remaining_table.split(width - left_margin * 2, available_height)

        this_part = table_parts[0]
        w, h = this_part.wrapOn(c, width - left_margin * 2, available_height)
        this_part.drawOn(c, left_margin, y_pos - h)

        y_pos -= h + 20

        if len(table_parts) == 1:
            break

        # Else → need new page
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100
        available_height = y_pos - footer_margin

        # Build new table for remaining rows
        remaining_table = Table(table_parts[1]._cellvalues, colWidths=col_widths, repeatRows=1)
        remaining_table.setStyle(table_style)

    # SMART COMMENTARY BEFORE OPTIMIZATION TABLE
    # ------------------------------------------------------------------------------------------------------------------
    # Define helper to safely convert string with %
    def safe_float(val):
        try:
            if isinstance(val, str):
                val = val.strip().rstrip('%')
            return float(val)
        except (ValueError, TypeError):
            return None

    # Retrieve metrics by index
    try:
        cvar_row = summary_df.loc['CVaR at 95%']
        sortino_row = summary_df.loc['Sortino Ratio']
        sharpe_row = summary_df.loc['Sharpe Ratio']
    except KeyError as e:
        raise ValueError(f"Metric not found in summary table: {e}")

    # Identify best portfolios
    best_cvar_portfolio = cvar_row.idxmin()  # lower CVaR better
    best_sortino_portfolio = sortino_row.idxmax()  # higher Sortino better
    best_sharpe_portfolio = sharpe_row.idxmax()  # higher Sharpe better

    # Values
    best_cvar_value = safe_float(cvar_row[best_cvar_portfolio])
    best_sortino_value = safe_float(sortino_row[best_sortino_portfolio])
    best_sharpe_value = safe_float(sharpe_row[best_sharpe_portfolio])

    # Build commentary text
    commentary_text = (
        "The Optimization Models Table above provides a detailed comparison across key risk-adjusted performance metrics. "
        "Each model showcases a unique balance of return and risk, supporting tailored investment decisions.\n\n"
        f"The \"{best_sharpe_portfolio}\" portfolio achieved the highest Sharpe Ratio ({best_sharpe_value:.2f}), "
        f"while the \"{best_sortino_portfolio}\" strategy demonstrated the strongest downside protection with a "
        f"Sortino Ratio of {best_sortino_value:.2f}. "
        f"For tail risk mitigation, the \"{best_cvar_portfolio}\" portfolio reported the lowest CVaR at 95% "
        f"({best_cvar_value:.2f}).\n\n"
    )

    # Add extra spacing after table
    y_pos -= 20  # ⬅️ adjust this number for more or less space
    # Ensure space before drawing text
    if y_pos < 150:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    # Draw commentary neatly justified
    y_pos = draw_justified_paragraph(commentary_text, y_pos, [current_page])

    # # Proposed Portfolio Allocation Pie Chart and smart commentary
    #------------------------------------------------------------------------------------------------------------------
    # Estimate commentary height BEFORE drawing
    comment_lines = simpleSplit(commentary_text, "Times-Italic", 11, right_margin - (left_margin + 300))
    estimated_comment_height = len(comment_lines) * 14  # 14 = line height

    # Determine the max height needed for pie or commentary
    content_height = max(200, estimated_comment_height)  # 200 = pie_height

    # Check if enough vertical space BEFORE drawing
    if y_pos - content_height < footer_margin + 50:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    # ========== Title ==========
    c.setFont("Times-Bold", 16)
    c.setFillColor(colors.black)
    y_pos -= 30
    c.drawString(left_margin + 10, y_pos, "Proposed Portfolio Allocation")
    add_toc_entry("    Proposed Portfolio Allocation", current_page)
    y_pos -= 20

    # ========== Pie Chart ==========
    import matplotlib.pyplot as plt
    gold_colors = ['#FFD700', '#FFB700', '#E5A400', '#CC9200', '#B57F00', '#A06E00']

    filtered_items = [(label, value) for label, value in proposed_allocation.items() if value > 0]
    pie_labels = [label for label, value in filtered_items]
    pie_values = [value for label, value in filtered_items]

    fig, ax = plt.subplots(figsize=(4.5, 4.5), dpi=300)
    wedges, texts, autotexts = ax.pie(
        pie_values, labels=pie_labels, autopct='%1.1f%%', startangle=90,
        colors=gold_colors[:len(pie_labels)],
        textprops={'fontsize': 8, 'color': 'black'}
    )
    for text in autotexts:
        text.set_fontsize(7)
        text.set_color('black')

    chart_buf = BytesIO()
    plt.savefig(chart_buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    chart_buf.seek(0)

    pie_top_y = y_pos
    pie_height = 200
    c.drawImage(ImageReader(chart_buf), left_margin, pie_top_y - pie_height, width=200, height=200)

    # ========== Commentary ==========
    text_x = left_margin + 300
    text_y = pie_top_y

    c.setFont("Times-Italic", 11)
    c.setFillColor(colors.HexColor("#6F1D1B"))
    text_obj = c.beginText(text_x, text_y)
    text_obj.setLeading(14)
    for line in comment_lines:
        text_obj.textLine(line)
    c.drawText(text_obj)

    # Update y_pos
    pie_bottom_y = pie_top_y - pie_height
    text_bottom_y = text_obj.getY()
    y_pos = min(pie_bottom_y, text_bottom_y) - 30

    # Final check for footer overflow for downstream content
    if y_pos < footer_margin + 50:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    # Current vs Proposed Bar Chart
    # ------------------------------------------------------------------------------------------------------------------
    if y_pos < 250:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 50

    c.setFont("Times-Bold", 16)
    c.setFillColor(colors.black)
    c.drawString(left_margin + 10, y_pos, "Current vs Target Allocation")
    y_pos -= 10

    import numpy as np
    labels = list(current_allocation.keys())
    curr_vals = [current_allocation.get(a, 0) for a in labels]
    prop_vals = [proposed_allocation.get(a, 0) for a in labels]
    x = np.arange(len(labels))
    width_bars = 0.35

    fig, ax = plt.subplots(figsize=(7.5, 3), dpi=400)
    bars1 = ax.bar(x - width_bars / 2, curr_vals, width_bars, label='Current', color='#6F1D1B')
    bars2 = ax.bar(x + width_bars / 2, prop_vals, width_bars, label='Proposed', color='#FFB343')

    def add_labels(bars, values):
        for bar, value in zip(bars, values):
            ax.annotate(f'{value:.1f}%', (bar.get_x() + bar.get_width() / 2, value),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)

    add_labels(bars1, curr_vals)
    add_labels(bars2, prop_vals)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
    ax.tick_params(axis='y', labelsize=9)
    ax.legend(fontsize=9, frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.grid(True, axis='y', linestyle='--', linewidth=0.5, alpha=0.6)
    fig.tight_layout()

    chart_buf = BytesIO()
    plt.savefig(chart_buf, format='png', dpi=400)
    plt.close(fig)
    chart_buf.seek(0)

    if y_pos < 300:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    chart_width = width - left_margin - (width - right_margin)
    c.drawImage(ImageReader(chart_buf), left_margin, y_pos - 200, width=chart_width, height=180)
    y_pos -= 230
    bar_chart_bottom_y = y_pos
    # Adjust y for next
    y_pos = bar_chart_bottom_y

    # Allocation Delta Table
    # ------------------------------------------------------------------------------------------------------------------
    title_height = 20  # height needed for the title
    header_height = 24
    row_height = 18
    required_space = title_height + header_height + (2 * row_height)

    if y_pos < footer_margin + required_space:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    # === Table Title (centered) ===
    table_title = "Allocation Delta Table"
    table_width = right_margin - (left_margin + 20)

    c.setFont("Times-Bold", 14)
    c.setFillColor(colors.black)
    title_y = y_pos
    c.drawCentredString(left_margin + 10 + table_width / 2, title_y, table_title)
    y_pos = title_y - 20

    # === Table Header ===
    c.setFillColor(colors.HexColor("#6F1D1B"))
    c.rect(left_margin + 10, y_pos - header_height + 12, table_width, header_height, fill=1, stroke=0)

    col1 = left_margin + 15
    col2 = col1 + 160
    col3 = col2 + 120
    col4 = col3 + 100

    c.setFont("Times-Bold", 12)
    c.setFillColor(colors.white)
    c.drawString(col1, y_pos, "Asset Class")
    c.drawString(col2, y_pos, "Current (%)")
    c.drawString(col3, y_pos, "Proposed (%)")
    c.drawString(col4, y_pos, "Change (%)")
    y_pos -= row_height

    c.setFont("Times-Roman", 11)
    c.setFillColor(colors.black)

    all_assets = sorted(set(current_allocation.keys()).union(set(proposed_allocation.keys())))
    fill_colors = [colors.whitesmoke, colors.lightgrey]
    i = 0

    for asset in all_assets:
        cur = current_allocation.get(asset, 0)
        prop = proposed_allocation.get(asset, 0)
        delta = prop - cur

        # CHECK if enough space for next row, else start new page
        if y_pos < footer_margin + row_height:
            c.showPage()
            current_page += 1
            draw_header_footer(current_page)
            y_pos = height - 100

            # redraw table header on new page
            c.setFont("Times-Bold", 14)
            c.setFillColor(colors.black)
            c.drawCentredString(left_margin + 10 + table_width / 2, y_pos, table_title)
            y_pos -= 20

            c.setFillColor(colors.HexColor("#6F1D1B"))
            c.rect(left_margin + 10, y_pos - header_height + 12, table_width, header_height, fill=1, stroke=0)

            c.setFont("Times-Bold", 12)
            c.setFillColor(colors.white)
            c.drawString(col1, y_pos, "Asset Class")
            c.drawString(col2, y_pos, "Current (%)")
            c.drawString(col3, y_pos, "Proposed (%)")
            c.drawString(col4, y_pos, "Change (%)")
            y_pos -= row_height

            c.setFont("Times-Roman", 11)

        # draw alternating background
        c.setFillColor(fill_colors[i % 2])
        c.rect(left_margin + 10, y_pos - 4, table_width, row_height, fill=1, stroke=0)

        c.setFillColor(colors.black)
        c.drawString(col1, y_pos, asset)
        c.drawString(col2, y_pos, f"{cur:.1f}")
        c.drawString(col3, y_pos, f"{prop:.1f}")
        c.drawString(col4, y_pos, f"{delta:+.1f}")
        y_pos -= row_height
        i += 1

    y_pos -= 20

    # Commentary text
    # ----------------------------------------------------------------------------------------------------------------------
    if all_assets:
        largest_increase_asset = max(all_assets,
                                     key=lambda a: proposed_allocation.get(a, 0) - current_allocation.get(a, 0))
        largest_decrease_asset = min(all_assets,
                                     key=lambda a: proposed_allocation.get(a, 0) - current_allocation.get(a, 0))
        largest_increase_value = proposed_allocation.get(largest_increase_asset, 0) - current_allocation.get(
            largest_increase_asset, 0)
        largest_decrease_value = proposed_allocation.get(largest_decrease_asset, 0) - current_allocation.get(
            largest_decrease_asset, 0)

        commentary_text = (
            "The Allocation Delta Table summarizes adjustments between the current and proposed portfolios. "
            "Positive changes indicate increased exposure, while negative values reflect reduced allocations. "
            "This transition aims to align the portfolio closer to its strategic objectives.\n\n"
            f"Notably, the largest increase was in {largest_increase_asset} (+{largest_increase_value:.1f} percentage points), "
            f"while the largest reduction was in {largest_decrease_asset} ({largest_decrease_value:+.1f} percentage points)."
        )
    else:
        commentary_text = (
            "No asset allocation changes detected. The current and proposed portfolios are identical."
        )

    y_pos = draw_justified_paragraph(commentary_text, y_pos, [current_page])

# ======================================================================================================================
# ================================== V. Target Portfolio Composition & Insights ========================================
# ======================================================================================================================

    section_gap_above_title = 30  # or 60 if you want more space
    y_pos -= section_gap_above_title # Push y_pos down more before starting section title

    # === Check if enough space for title + content ===
    min_space_needed = 30  # estimated vertical space for title + content
    if y_pos < footer_margin + min_space_needed:
        # c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 50

    add_toc_entry("V. Target Portfolio Composition & Insights", current_page)

    # Main section title
    #----------------------
    c.setFont("Times-Bold", 20)
    c.setFillColor(colors.HexColor("#6F1D1B"))
    title_y = y_pos
    c.drawString(left_margin, title_y, "V. Target Portfolio Composition & Insights")
    y_pos = title_y - title_to_paragraph_gap

    # Investment Universe table
    #----------------------------
    c.setFont("Times-Bold", 16)
    c.setFillColor(colors.black)
    c.drawString(left_margin + 10, y_pos, "Proposed Portfolio Composition")
    add_toc_entry("    Proposed Portfolio Composition", current_page)
    y_pos -= 30

    # --------- Proposed ETF's table ---------
    row_height = 22
    table_width = right_margin - left_margin
    col1_x = left_margin + 15
    col2_x = left_margin + (table_width / 2) + 15
    col_width = (table_width / 2) - 30  # 15 margin padding

    fill_colors = [colors.whitesmoke, colors.lightgrey]

    num_items = len(selected_etfs_total)
    split_index = (num_items + 1) // 2
    col1_items = selected_etfs_total[:split_index]
    col2_items = selected_etfs_total[split_index:]
    max_rows = max(len(col1_items), len(col2_items))

    for i in range(max_rows):
        if y_pos < footer_margin + row_height * 2:  # ✅ reserve space
            c.showPage()
            current_page += 1
            draw_header_footer(current_page)
            y_pos = height - 100
            c.setFont("Times-Bold", 14)
            c.setFillColor(colors.black)
            y_pos -= 20

        # alternating row color
        c.setFillColor(fill_colors[i % 2])
        c.rect(left_margin, y_pos - row_height + 5, table_width, row_height, fill=1, stroke=0)

        # draw ETF names with wrapping
        c.setFont("Times-Roman", 11)
        c.setFillColor(colors.black)

        etf1_text = col1_items[i] if i < len(col1_items) else ""
        etf2_text = col2_items[i] if i < len(col2_items) else ""

        etf1_lines = simpleSplit(etf1_text, "Times-Roman", 11, col_width)
        etf2_lines = simpleSplit(etf2_text, "Times-Roman", 11, col_width)

        for line_idx, line in enumerate(etf1_lines[:2]):  # ✅ limit to 2 lines
            c.drawString(col1_x, y_pos - (line_idx * 12), line)
        for line_idx, line in enumerate(etf2_lines[:2]):
            c.drawString(col2_x, y_pos - (line_idx * 12), line)

        y_pos -= row_height

    y_pos -= 20  # extra gap after table

    investment_universe_bottom_y = y_pos

    # Smart Commentary Below
    #-------------------------------------------------------------------------------------------------------------------
    commentary_text = (
        "The selected ETFs reflect a diversified approach across key asset classes, balancing growth and defensive positions. "
        "High Sharpe Ratio ETFs aim to enhance risk-adjusted returns, while inclusion of lower-volatility assets "
        "helps cushion downside risk. "
        "This selection was informed by recent market dynamics, historical performance, and complementary correlations "
        "to optimize portfolio resilience."
    )

    y_pos = draw_justified_paragraph(commentary_text, y_pos, [current_page])

    investment_universe_section_bottom = y_pos

# Assets Returns Analysis
#-----------------------------------------------------------------------------------------------------------------------
    if y_pos < 300:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 30
    else:
        y_pos -= 20  # 🔥 add extra space above title if staying on same page

    c.setFont("Times-Bold", 16)
    c.setFillColor(colors.black)
    c.drawString(left_margin + 10, y_pos, "Assets Returns Overview")
    add_toc_entry("    Assets Returns Overview", current_page)
    y_pos -= 30

    # Plotting assets returns chart
    # ------------------------------------------------------------------------------------------------------------------
    price_data = st.session_state.close_prices  # Assumed to be a DataFrame
    rebased_prices = price_data / price_data.iloc[0] * 100
    fig, ax = plt.subplots(figsize=(6.5, 3.5), dpi=600)
    for col in rebased_prices.columns:
        ax.plot(rebased_prices.index, rebased_prices[col], label=col)

    ax.set_title("Rebased Assets Returns (Indexed to 100)", fontsize=10)
    ax.set_ylabel("Rebased Value")
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
    ax.tick_params(axis='x', labelsize=8)
    ax.tick_params(axis='y', labelsize=8)
    ax.legend(fontsize=6, loc='upper left', ncol=2, frameon=False)
    ax.set_facecolor('white')
    fig.patch.set_visible(False)
    ax.set_frame_on(False)
    fig.tight_layout()

    chart_buf = BytesIO()
    plt.savefig(chart_buf, format='png', dpi=600, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    chart_buf.seek(0)

    # Draw Chart
    #------------------------------------------------------------------------------------------------------------------
    chart_height = 180
    chart_width = 270
    c.drawImage(ImageReader(chart_buf), left_margin, y_pos - chart_height, width=chart_width, height=chart_height)

    chart_end_y = y_pos - chart_height  # bottom y of chart

    # === Write explanation text ===
    rebased_final = rebased_prices.iloc[-1].sort_values(ascending=False)
    top = rebased_final.idxmax()
    bottom = rebased_final.idxmin()
    top_val = rebased_final.max()
    bottom_val = rebased_final.min()

    explanation_text = (
        f"Among the selected ETFs, {top} showed the strongest cumulative return, finishing near {top_val:.1f}, "
        f"while {bottom} lagged behind at approximately {bottom_val:.1f}. This illustrates a significant dispersion "
        f"in relative performance. The chart highlights the strength of trending assets and helps in identifying "
        f"leaders versus laggards."
    )

    text_x = left_margin + chart_width + 30
    text_y = y_pos - 10  # initial y for text

    c.setFont("Times-Italic", 11)
    c.setFillColor(colors.HexColor("#6F1D1B"))
    text_obj = c.beginText(text_x, text_y)
    text_obj.setLeading(14)

    wrapped_lines = simpleSplit(explanation_text, "Times-Italic", 11, right_margin - text_x)
    for line in wrapped_lines:
        text_obj.textLine(line)
    c.drawText(text_obj)

    # Calculate end y of text block
    text_end_y = text_y - (len(wrapped_lines) * 14)

    # === Find lower y between chart and text ===
    y_pos = min(chart_end_y, text_end_y) - 50  # add a gap after lower element

    # Check for page overflow
    if y_pos < 200:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100  # reset y_pos at top margin

    # Compute metrics Table
    #------------------------------------------------------------------------------------------------------------------
    returns = price_data.pct_change().dropna()
    mean_returns = returns.mean() * 252
    volatility = returns.std() * (252 ** 0.5)
    cumulative = (price_data.iloc[-1] / price_data.iloc[0]) - 1
    sharpe_ratios = mean_returns / volatility

    # Table title
    #-------------------------------------------------------------------------------------------------------------------
    header_height = 24
    row_height = 18
    title_text = "Returns Metrics Summary"
    c.setFont("Times-Bold", 14)
    c.setFillColor(colors.HexColor("#000000"))
    c.drawCentredString(left_margin + table_width / 2, y_pos + header_height, title_text)

    # Draw table header
    # -------------------------------------------------------------------------------------------------------------------
    def draw_table_header(y_pos):
        c.setFillColor(colors.HexColor("#6F1D1B"))
        c.rect(left_margin, y_pos - header_height + 10, table_width, header_height, fill=1, stroke=0)
        c.setFont("Times-Bold", 10)
        c.setFillColor(colors.white)
        c.drawString(left_margin + 5, y_pos, "ETF")
        c.drawString(left_margin + 120, y_pos, "Cumulative Return")
        c.drawString(left_margin + 230, y_pos, "Annual Return")
        c.drawString(left_margin + 330, y_pos, "Volatility")
        c.drawString(left_margin + 420, y_pos, "Sharpe Ratio")

    draw_table_header(y_pos)
    y_pos -= row_height

    #Table rows
    #-------------------------------------------------------------------------------------------------------------------
    fill_colors = [colors.whitesmoke, colors.lightgrey]
    i = 0
    for etf in price_data.columns:
        if y_pos < 70:
            c.showPage()
            current_page += 1
            draw_header_footer(current_page)
            y_pos = height - 100
            draw_table_header(y_pos)
            y_pos -= row_height

        c.setFillColor(fill_colors[i % 2])
        c.rect(left_margin, y_pos - 4, table_width, row_height, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Times-Roman", 9)
        c.drawString(left_margin + 5, y_pos, etf)
        c.drawString(left_margin + 120, y_pos, f"{cumulative[etf] * 100:.1f}%")
        c.drawString(left_margin + 230, y_pos, f"{mean_returns[etf] * 100:.1f}%")
        c.drawString(left_margin + 330, y_pos, f"{volatility[etf] * 100:.1f}%")
        c.drawString(left_margin + 420, y_pos, f"{sharpe_ratios[etf]:.2f}")
        y_pos -= row_height
        i += 1

    y_pos -= 20  # final padding

    # Assets Risk Analysis
    #-----------------------------------------------------------------------------------------------------------------------
    if y_pos < 300:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    c.setFont("Times-Bold", 16)
    c.setFillColor(colors.black)
    c.drawString(left_margin + 10, y_pos, "Assets Risk Overview")
    add_toc_entry("    Assets Risk Overview", current_page)
    y_pos -= 30

    # Prepare data for bar chart
    sorted_volatility = volatility.sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(6.5, 3.5), dpi=600)
    bars = ax.bar(sorted_volatility.index, sorted_volatility.values * 100, color="#FFB343")
    ax.set_title("Annualized Volatility per ETF", fontsize=10)
    ax.set_ylabel("Volatility (%)")
    ax.set_xlabel("ETF")
    ax.tick_params(axis='x', rotation=45, labelsize=8)
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
    ax.set_facecolor('white')
    fig.patch.set_visible(False)
    ax.set_frame_on(False)

    # Add percentage labels on bars
    for bar, value in zip(bars, sorted_volatility.values * 100):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.5, f"{value:.1f}%", ha='center', va='bottom', fontsize=6,
                color='black')

    fig.tight_layout()

    risk_buf = BytesIO()
    plt.savefig(risk_buf, format='png', dpi=600, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    risk_buf.seek(0)

    # Draw chart left
    chart_height = 180
    chart_width = 270
    c.drawImage(ImageReader(risk_buf), left_margin, y_pos - chart_height, width=chart_width, height=chart_height)

    # Write-up on right
    text_x = left_margin + chart_width + 30
    text_y = y_pos - 10
    most_volatile = sorted_volatility.index[0]
    least_volatile = sorted_volatility.index[-1]
    most_val = sorted_volatility.iloc[0] * 100
    least_val = sorted_volatility.iloc[-1] * 100

    risk_text = (
        f"Among the selected ETFs, {most_volatile} exhibits the highest annualized volatility at {most_val:.1f}%, "
        f"implying greater risk and potential fluctuation in returns. In contrast, {least_volatile} maintains a lower "
        f"volatility at {least_val:.1f}%, offering a more stable performance profile. This chart ranks ETFs by risk level, "
        f"helping to identify which positions may dominate portfolio volatility."
    )

    c.setFont("Times-Italic", 11)
    c.setFillColor(colors.HexColor("#6F1D1B"))
    text_obj = c.beginText(text_x, text_y)
    text_obj.setLeading(14)
    for line in simpleSplit(risk_text, "Times-Italic", 11, right_margin - text_x):
        text_obj.textLine(line)
    c.drawText(text_obj)

    y_pos -= chart_height + 30

    # Risk Metrics Summary Table
    # ------------------------------------------------------------------------------------------------------------------
    # Check if there's space for title + table
    min_space_needed = 100
    if y_pos < footer_margin + min_space_needed:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    # Calculate metrics
    #-------------------------------------------------------------------------------------------------------------------
    returns = price_data.pct_change().dropna()
    rolling_max = price_data.cummax()
    drawdowns = (price_data / rolling_max - 1).min()
    max_drawdown = drawdowns * 100

    downside_returns = returns.copy()
    downside_returns[downside_returns > 0] = 0
    downside_deviation = downside_returns.std() * (252 ** 0.5) * 100  # annualized

    #Centered Table Title (closer to table)
    # -------------------------------------------------------------------------------------------------------------------
    table_width = right_margin - left_margin
    table_title = "Risk Metrics Summary"

    c.setFont("Times-Bold", 14)
    c.setFillColor(colors.black)
    table_title_y = y_pos - 5  # lower it closer to table
    c.drawCentredString(left_margin + table_width / 2, table_title_y, table_title)

    y_pos = table_title_y - 15  # move y_pos down for table header row

    # Table Header Row
    # -------------------------------------------------------------------------------------------------------------------
    header_height = 20
    row_height = 18

    c.setFillColor(colors.HexColor("#6F1D1B"))
    c.rect(left_margin, y_pos - header_height + 10, table_width, header_height, fill=1, stroke=0)

    c.setFont("Times-Bold", 10)
    c.setFillColor(colors.white)
    c.drawString(left_margin + 5, y_pos, "ETF")
    c.drawString(left_margin + 150, y_pos, "Annual Volatility (%)")
    c.drawString(left_margin + 300, y_pos, "Max Drawdown (%)")
    c.drawString(left_margin + 450, y_pos, "Downside Deviation (%)")
    y_pos -= row_height

    # Table rows
    # -------------------------------------------------------------------------------------------------------------------
    fill_colors = [colors.whitesmoke, colors.lightgrey]
    i = 0

    for etf in price_data.columns:
        vol = returns[etf].std() * (252 ** 0.5) * 100
        dd = max_drawdown[etf]
        dd_dev = downside_deviation[etf]

        # 💥 Check if space left for row, else new page + redraw header
        if y_pos < footer_margin + row_height:
            c.showPage()
            current_page += 1
            draw_header_footer(current_page)
            y_pos = height - 100

            # REDRAW TABLE HEADER on new page
            # -------------------------------------------------------------------------------------------------------------------
            c.setFont("Times-Bold", 14)
            c.setFillColor(colors.black)
            table_title_y = y_pos - 5
            c.drawCentredString(left_margin + table_width / 2, table_title_y, "Risk Metrics Summary")

            y_pos = table_title_y - 15

            c.setFillColor(colors.HexColor("#6F1D1B"))
            c.rect(left_margin, y_pos - header_height + 10, table_width, header_height, fill=1, stroke=0)

            c.setFont("Times-Bold", 10)
            c.setFillColor(colors.white)
            c.drawString(left_margin + 5, y_pos, "ETF")
            c.drawString(left_margin + 150, y_pos, "Annual Volatility (%)")
            c.drawString(left_margin + 300, y_pos, "Max Drawdown (%)")
            c.drawString(left_margin + 450, y_pos, "Downside Deviation (%)")
            y_pos -= row_height

        # Draw data row
        # -------------------------------------------------------------------------------------------------------------------
        c.setFillColor(fill_colors[i % 2])
        c.rect(left_margin, y_pos - 4, table_width, row_height, fill=1, stroke=0)

        c.setFont("Times-Roman", 10)
        c.setFillColor(colors.black)
        c.drawString(left_margin + 5, y_pos, etf)
        c.drawString(left_margin + 150, y_pos, f"{vol:.1f}")
        c.drawString(left_margin + 300, y_pos, f"{dd:.1f}")
        c.drawString(left_margin + 450, y_pos, f"{dd_dev:.1f}")

        y_pos -= row_height
        i += 1

    y_pos -= 20

    # Risk Commentary Write-up
    #-------------------------------------------------------------------------------------------------------------------
    # Identify key metrics
    most_volatile_etf = volatility.idxmax()
    least_volatile_etf = volatility.idxmin()
    highest_vol = volatility[most_volatile_etf] * 100
    lowest_vol = volatility[least_volatile_etf] * 100

    deepest_drawdown_etf = max_drawdown.idxmin()
    deepest_drawdown_val = max_drawdown[deepest_drawdown_etf]

    highest_dd_etf = downside_deviation.idxmax()
    highest_dd_val = downside_deviation[highest_dd_etf]

    # Build smart commentary
    # -------------------------------------------------------------------------------------------------------------------
    risk_commentary = (
        f"The Risk Metrics Summary Table provides insight into each ETF's historical risk profile. "
        f"{most_volatile_etf} exhibits the highest annualized volatility at {highest_vol:.1f}%, "
        f"while {least_volatile_etf} maintains the lowest volatility at {lowest_vol:.1f}%, reflecting relative stability.\n"
        f"In drawdown analysis, {deepest_drawdown_etf} faced the largest peak-to-trough loss of {deepest_drawdown_val:.1f}%, "
        f"highlighting its vulnerability during downturns.\n"
        f"{highest_dd_etf} shows the highest downside deviation at {highest_dd_val:.1f}%, signaling greater dispersion "
        f"in negative returns. "
        f"Overall, this risk analysis highlights which ETFs may amplify or cushion portfolio-level risk exposure."
    )
    # Draw the commentary
    # -------------------------------------------------------------------------------------------------------------------
    y_pos = draw_paragraph(risk_commentary, y_pos)

    # Target Portfolio Insights
    # -----------------------------------------------------------------------------------------------------------------------
    if y_pos < 300:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    c.setFont("Times-Bold", 16)
    c.setFillColor(colors.black)
    c.drawString(left_margin + 10, y_pos, "Target Portfolio Insights")
    add_toc_entry("    Target Portfolio Insights", current_page)
    y_pos -= 30

# Assets Risk/Return Analysis
#-----------------------------------------------------------------------------------------------------------------------
    if y_pos < 300:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    c.setFont("Times-Bold", 16)
    c.setFillColor(colors.black)
    c.drawString(left_margin + 10, y_pos, "Risk/Return Analysis")
    y_pos -= 30

# Sharpe Ratio Bar Chart
# -----------------------------------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(6.5, 3.5), dpi=600)
    sorted_sharpe = sharpe_ratios.sort_values(ascending=True)

    # Draw bars without border
    # -------------------------------------------------------------------------------------------------------------------
    bars = ax.barh(sorted_sharpe.index, sorted_sharpe.values, color="#DB9200", edgecolor='none')

    # Add % labels inside bars
    # -------------------------------------------------------------------------------------------------------------------
    for i, (index, value) in enumerate(sorted_sharpe.items()):
        ax.text(value + 0.01, i, f"{value:.2f}", va='center', ha='left', fontsize=8)

    ax.set_title("Sharpe Ratio per ETF", fontsize=10)
    ax.set_xlabel("Sharpe Ratio")
    ax.tick_params(axis='x', labelsize=8)
    ax.tick_params(axis='y', labelsize=8)
    ax.grid(axis='x', linestyle='--', linewidth=0.5, alpha=0.6)

    # Remove outer box borders
    # -------------------------------------------------------------------------------------------------------------------
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()

    # Save to buffer
    # -------------------------------------------------------------------------------------------------------------------
    sr_buf = BytesIO()
    plt.savefig(sr_buf, format='png', dpi=600, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    sr_buf.seek(0)

    # Draw chart full-width
    # -------------------------------------------------------------------------------------------------------------------
    chart_height = 180
    chart_width = right_margin - left_margin
    c.drawImage(ImageReader(sr_buf), left_margin, y_pos - chart_height, width=chart_width, height=chart_height)
    y_pos -= chart_height + 10

    # Add commentary text below chart
    # -------------------------------------------------------------------------------------------------------------------
    commentary = (
        f"The Sharpe Ratio analysis reveals that {sorted_sharpe.index[-1]} delivered the highest risk-adjusted return "
        f"({sorted_sharpe.values[-1]:.2f}), "
        f"while {sorted_sharpe.index[0]} underperformed with the lowest Sharpe Ratio ({sorted_sharpe.values[0]:.2f}). "
        f"Higher Sharpe ratios indicate better compensation for each unit of risk, suggesting "
        f"that {sorted_sharpe.index[-1]} may be preferable "
        "for investors seeking efficient returns, while caution may be warranted for lower-ranked ETFs."
    )

    y_pos = draw_justified_paragraph(commentary.strip(), y_pos - 20, [current_page])

# Correlation Heatmap
# -----------------------------------------------------------------------------------------------------------------------
    if y_pos < 300:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100

    c.setFont("Times-Bold", 16)
    c.setFillColor(colors.black)
    c.drawString(left_margin + 10, y_pos, "Correlation Heatmap")
    y_pos -= 30

    # Compute correlation matrix
    # -------------------------------------------------------------------------------------------------------------------
    correlation_matrix = returns.corr()

    fig, ax = plt.subplots(figsize=(6.5, 4.5), dpi=600)
    cax = ax.imshow(correlation_matrix, cmap='RdBu_r', vmin=-1, vmax=1)

    # Set axis ticks
    # -------------------------------------------------------------------------------------------------------------------
    ax.set_xticks(np.arange(len(correlation_matrix.columns)))
    ax.set_yticks(np.arange(len(correlation_matrix.index)))
    ax.set_xticklabels(correlation_matrix.columns, rotation=45, ha='right', fontsize=6)
    ax.set_yticklabels(correlation_matrix.index, fontsize=6)

    # Add correlation values inside each box
    # -------------------------------------------------------------------------------------------------------------------
    for i in range(len(correlation_matrix.index)):
        for j in range(len(correlation_matrix.columns)):
            corr_value = correlation_matrix.iloc[i, j]
            ax.text(j, i, f"{corr_value:.2f}", ha='center', va='center', fontsize=6, color='black')

    # Clean up plot style
    # -------------------------------------------------------------------------------------------------------------------
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()

    # Save figure to buffer
    # -------------------------------------------------------------------------------------------------------------------
    heatmap_buf = BytesIO()
    plt.savefig(heatmap_buf, format='png', dpi=600, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    heatmap_buf.seek(0)

    # Draw heatmap in PDF
    # -------------------------------------------------------------------------------------------------------------------
    chart_height = 200
    chart_width = right_margin - left_margin
    c.drawImage(ImageReader(heatmap_buf), left_margin, y_pos - chart_height, width=chart_width, height=chart_height)
    y_pos -= chart_height + 10  # move y_pos down after chart

    # Smart explanation below
    correlation_text = (
        "This heatmap visualizes the pairwise correlations between selected ETFs. Strong correlations (red) suggest "
        "similar movements, "
        "while weaker or negative correlations (blue) indicate diversification potential. These insights can inform "
        "asset selection and "
        "portfolio construction for optimal diversification."
    ).strip()

    y_pos = draw_justified_paragraph(correlation_text.strip(), y_pos - 20, [current_page])

#Efficient Frontier
# -----------------------------------------------------------------------------------------------------------------------
    num_portfolios = 5000
    num_assets = len(price_data.columns)
    returns_data = price_data.pct_change().dropna()

    # Expected returns & covariance
    exp_returns = returns_data.mean() * 252
    cov_matrix = returns_data.cov() * 252

    simulated_returns = []
    simulated_risks = []
    simulated_sharpes = []

    for _ in range(num_portfolios):
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)

        portfolio_return = np.dot(weights, exp_returns)
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = portfolio_return / portfolio_vol if portfolio_vol != 0 else 0

        simulated_returns.append(portfolio_return)
        simulated_risks.append(portfolio_vol)
        simulated_sharpes.append(sharpe)

    # Optimal portfolio (max Sharpe)
    max_sharpe_idx = np.argmax(simulated_sharpes)
    opt_return = simulated_returns[max_sharpe_idx]
    opt_risk = simulated_risks[max_sharpe_idx]

    # Plot
    fig, ax = plt.subplots(figsize=(7.5, 3.5), dpi=600)
    sc = ax.scatter(simulated_risks, simulated_returns, c=simulated_sharpes, cmap='viridis', s=10, alpha=0.5,
                    label='Simulated Portfolios')
    ax.scatter(opt_risk, opt_return, color='gold', s=60, label='Max Sharpe')

    ax.set_xlabel("Volatility (Risk)", fontsize=10)
    ax.set_ylabel("Expected Return", fontsize=10)
    ax.set_title("Efficient Frontier", fontsize=12)
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
    ax.legend(fontsize=8)

    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label('Sharpe Ratio')
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()

    # Save
    ef_buf = BytesIO()
    plt.savefig(ef_buf, format='png', dpi=600, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    ef_buf.seek(0)

    # Draw in PDF
    c.drawImage(ImageReader(ef_buf), left_margin, y_pos - 180, width=right_margin - left_margin, height=180)
    y_pos -= 200

    explanation_text = (
        "The Efficient Frontier illustrates the optimal balance between risk and expected return across simulated "
        "portfolios. "
        "Each point represents a unique combination of asset weights, showing the trade-off between higher returns and "
        "higher volatility. "
        "Portfolios lying closer to the frontier offer more efficient outcomes, delivering better returns for each unit "
        "of risk taken. "
        "The highlighted gold point identifies the portfolio with the highest Sharpe ratio, representing the most "
        "favorable risk-adjusted performance among all simulations."
    )

    y_pos = draw_justified_paragraph(explanation_text, y_pos - 20, [current_page])

    # ======================================================================================================================
    # ================================== VI. Portfolio Analysis Section ====================================================
    # ======================================================================================================================
    section_gap_above_title = 30
    y_pos -= section_gap_above_title  # Push y_pos down before title

    # Estimate total title height dynamically
    wrapped_lines = simpleSplit("VI. Portfolio Backtested and Forecasts Performance", "Times-Bold", 20,
                                right_margin - left_margin)
    title_height = len(wrapped_lines) * 24  # 24 = line height for font size 20

    min_space_needed = title_height + 50  # 50 extra padding

    if y_pos < footer_margin + min_space_needed:
        c.showPage()
        current_page += 1
        draw_header_footer(current_page)
        y_pos = height - 100  # top margin for new page

    add_toc_entry("VI. Portfolio Backtested and Forecasts Performance", current_page)

    c.setFillColor(colors.HexColor("#6F1D1B"))  # ✅ fixed typo
    c.setFont("Times-Bold", 20)

    for line in wrapped_lines:
        c.drawString(left_margin, y_pos, line)
        y_pos -= 24  # move down per line height

    c.setFillColor(colors.black)  # reset color after title
    y_pos -= 20  # extra gap below title

    # add_toc_entry("VI. Portfolio Backtested and Forecasts Performance", current_page)

    # Historical Portfolio Performance
    # ------------------------------------------------------------------------------------------------------------------
    tickers = st.session_state.get('selected_tickers', [])

    if 'close_prices' in st.session_state and st.session_state['close_prices'] is not None:
        prices = st.session_state['close_prices']
    else:
        if tickers:
            prices = yf.download(tickers=tickers, start='2020-01-01', end=pd.Timestamp.today(), progress=False)['Close']
            if len(tickers) == 1:
                prices = prices.to_frame(name=tickers[0])
        else:
            raise ValueError("No tickers selected or available.")


    # GET USER ASSET ALLOCATION
    #-------------------------------------------------------------------------------------------------------------------
    manual_alloc_assetclass = st.session_state.get('manual_asset_alloc', {})
    asset_class_map = st.session_state.get('asset_class_map', {})

    # Initialize per-ticker weights
    weights_per_ticker = {}

    for asset_class, alloc_pct in manual_alloc_assetclass.items():
        etfs_in_class = [ticker for ticker in prices.columns if asset_class_map.get(ticker) == asset_class]

        if etfs_in_class:
            equal_weight = alloc_pct / 100 / len(etfs_in_class)  # convert % to fraction and equally split
            for ticker in etfs_in_class:
                weights_per_ticker[ticker] = equal_weight

    # Any ETF not in user allocation → 0 weight
    for ticker in prices.columns:
        if ticker not in weights_per_ticker:
            weights_per_ticker[ticker] = 0

    weights_series = pd.Series(weights_per_ticker)

    # HISTORICAL PORTFOLIO PRICE
    portfolio_prices = (prices[weights_series.index] * weights_series).sum(axis=1)

    # Drop any missing data
    portfolio_prices = portfolio_prices.dropna()

    # Rebase portfolio to 100
    rebased_portfolio = portfolio_prices / portfolio_prices.iloc[0] * 100

    # PLOT
    fig, ax = plt.subplots(figsize=(7.5, 3.5), dpi=600)
    ax.plot(rebased_portfolio.index, rebased_portfolio.values, color="#DB9200", linewidth=2)
    ax.set_title("Historical Portfolio Performance (Rebased to 100)", fontsize=12)
    ax.set_xlabel("Date", fontsize=10)
    ax.set_ylabel("Portfolio Value", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)

    # Remove borders
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()

    # SAVE TO BUFFER
    portfolio_buf = BytesIO()
    plt.savefig(portfolio_buf, format='png', dpi=600, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    portfolio_buf.seek(0)

    # DRAW IN PDF
    chart_height = 180
    chart_width = right_margin - left_margin

    c.drawImage(ImageReader(portfolio_buf), left_margin, y_pos - chart_height, width=chart_width, height=chart_height)
    y_pos -= chart_height + 20

    # COMMENTARY BELOW CHART
    performance_text = (
        "This chart illustrates the historical performance of the proposed portfolio based on the user-defined "
        "allocation across asset classes. "
        "Each ETF within an asset class is equally weighted to reflect an unbiased exposure. The portfolio has been "
        "rebased to 100 for clarity, "
        "showing its cumulative growth trajectory over the selected time period."
    )

# Draw commentary justified
# -----------------------------------------------------------------------------------------------------------------------
    y_pos = draw_justified_paragraph(performance_text.strip(), y_pos - 20, [current_page])

# MONTE CARLO SIMULATION
# -----------------------------------------------------------------------------------------------------------------------
    returns = prices[weights_series.index].pct_change().dropna()
    mu = returns.mean() * 252
    cov = returns.cov() * 252

    expected_return = weights_series @ mu
    portfolio_vol = np.sqrt(weights_series.T @ cov @ weights_series)

    simulations = 1000
    days = 252
    initial_value = rebased_portfolio.iloc[-1]  # START where historical left off

    simulated_paths = np.zeros((days, simulations))
    simulated_paths[0] = initial_value

    for t in range(1, days):
        rand_returns = np.random.normal(expected_return / days, portfolio_vol / np.sqrt(days), simulations)
        simulated_paths[t] = simulated_paths[t - 1] * (1 + rand_returns)

    # PLOT
    # ------------------------------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.5, 3.5), dpi=600)

    # Plot historical up to last point
    ax.plot(rebased_portfolio.index, rebased_portfolio.values, color="#DB9200", linewidth=2,
            label="Historical Portfolio")

    # Plot simulation paths
    sim_dates = pd.date_range(start=rebased_portfolio.index[-1], periods=days + 1, freq='B')[1:]
    for i in range(simulations):
        ax.plot(sim_dates, simulated_paths[:, i], color='gray', alpha=0.05)

    # Plot average simulated path
    # ------------------------------------------------------------------------------------------------------------------
    ax.plot(sim_dates, simulated_paths.mean(axis=1), color="#6F1D1B", linewidth=2, label="Monte Carlo Mean")

    ax.set_title("Monte Carlo Simulation (1-Year Forecast)", fontsize=12)
    ax.set_xlabel("Date", fontsize=10)
    ax.set_ylabel("Portfolio Value", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=8)

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()

    # SAVE TO BUFFER
    # ------------------------------------------------------------------------------------------------------------------
    mc_buf = BytesIO()
    plt.savefig(mc_buf, format='png', dpi=600, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    mc_buf.seek(0)

    # DRAW IN PDF
    # ------------------------------------------------------------------------------------------------------------------
    c.drawImage(ImageReader(mc_buf), left_margin, y_pos - 180, width=right_margin - left_margin, height=180)
    y_pos -= 200

    # COMMENTARY
    # ------------------------------------------------------------------------------------------------------------------
    mc_text = (
        "This chart extends the historical portfolio performance into the future using a Monte Carlo simulation of 1,000 "
        "potential paths. "
        "Each gray line represents a simulated outcome based on the portfolio’s historical return and volatility, while "
        "the dark line "
        "shows the average projection. This visualization captures the range of uncertainty in portfolio value over the "
        "next year, "
        "highlighting the probabilistic nature of investment outcomes."
    )

    y_pos = draw_justified_paragraph(mc_text.strip(), y_pos - 20, [current_page])

# ======================================================================================================================
# ======================================================================================================================
# Save and Finish
# ======================================================================================================================
# ======================================================================================================================
    c.save()
    buffer.seek(0)

# ======================================================================================================================
# ==========================================   Table of Contents           =============================================
# ======================================================================================================================

    toc_buffer = BytesIO()
    toc_canvas = canvas.Canvas(toc_buffer, pagesize=A4)

    # TOC title in burgundy
    # ------------------------------------------------------------------------------------------------------------------
    toc_canvas.setFont("Times-Bold", 26)
    toc_canvas.setFillColor(HexColor("#6F1D1B"))
    toc_canvas.drawString(left_margin, height - 100, "Table of Contents")
    toc_canvas.setFillColor("black")  # reset color for entries

    toc_canvas.setFont("Times-Roman", 12)
    y_toc = height - 150

    for title, page_num in toc_entries:
        if y_toc < 70:
            toc_canvas.showPage()
            toc_canvas.setFont("Times-Roman", 12)
            y_toc = height - 100

        # Determine indent for subsections (if title starts with space or dash or similar)
        # --------------------------------------------------------------------------------------------------------------
        indent = left_margin + 20
        if title.startswith("  ") or title.startswith("- "):
            indent += 20
        elif title.startswith("- "):  # dash marker
            indent += 20

        # Create dot leaders
        # -------------------------------------------------------------------------------------------------------------
        text_width = toc_canvas.stringWidth(title.strip(), "Times-Roman", 12)
        available_width = right_margin - indent - 40  # leave space for page number
        dot_count = max(0, int((available_width - text_width) / toc_canvas.stringWidth('.', "Times-Roman", 12)))
        dots = '.' * dot_count

        toc_canvas.drawString(indent, y_toc, f"{title.strip()} {dots}")
        toc_canvas.drawRightString(right_margin - 20, y_toc, str(page_num))
        y_toc -= 20

    toc_canvas.showPage()
    toc_canvas.save()
    toc_buffer.seek(0)

    # MERGE TOC + MAIN PDF
    # ------------------------------------------------------------------------------------------------------------------
    reader_toc = PdfReader(toc_buffer)
    reader_main = PdfReader(buffer)
    writer = PdfWriter()

    # 1️⃣ Add cover page
    # ------------------------------------------------------------------------------------------------------------------
    writer.add_page(reader_main.pages[0])

    # 2️⃣ Add TOC Sheets
    # ------------------------------------------------------------------------------------------------------------------
    for page in reader_toc.pages:
        writer.add_page(page)

    # 3️⃣ Add rest of main report (SKIP first page → cover already added)
    # ------------------------------------------------------------------------------------------------------------------
    for page in reader_main.pages[1:]:
        writer.add_page(page)

    # OUTPUT FINAL PDF
    final_buffer = BytesIO()
    writer.write(final_buffer)
    final_buffer.seek(0)

    return final_buffer