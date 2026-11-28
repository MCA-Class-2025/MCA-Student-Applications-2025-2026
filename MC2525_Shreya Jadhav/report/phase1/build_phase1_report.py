from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
OUT = HERE / "FemCare_Phase_1_Report.docx"
RESULTS = json.loads((ASSETS / "analysis_results.json").read_text(encoding="utf-8"))

BLUE = "2E74B5"
DARK_BLUE = "1F4D78"
NAVY = "264653"
PINK = "D53F8C"
PLUM = "7A2E67"
LIGHT_PINK = "FCE4EC"
LIGHT_BLUE = "E8EEF5"
LIGHT_GRAY = "F2F4F7"
MID_GRAY = "D7DCE2"
TEXT = "30343B"
MUTED = "666666"
WHITE = "FFFFFF"


def rgb(hex_value):
    return RGBColor.from_string(hex_value)


def set_font(run, name="Calibri", size=11, bold=None, italic=None, color=TEXT):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    run.font.color.rgb = rgb(color)


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=90, start=120, bottom=90, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_geometry(table, widths):
    total = sum(widths)
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(total))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), "120")
    tbl_ind.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)
    for row in table.rows:
        for index, cell in enumerate(row.cells):
            cell.width = Inches(widths[index] / 1440)
            tc_w = cell._tc.get_or_add_tcPr().find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                cell._tc.get_or_add_tcPr().append(tc_w)
            tc_w.set(qn("w:w"), str(widths[index]))
            tc_w.set(qn("w:type"), "dxa")
            set_cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def prevent_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    tr_pr.append(cant_split)


def add_table(doc, headers, rows, widths=None, font_size=9.2):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    header = table.rows[0]
    repeat_header(header)
    for i, value in enumerate(headers):
        cell = header.cells[i]
        shade(cell, LIGHT_BLUE)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(p.add_run(str(value)), size=font_size, bold=True, color=NAVY)
    for row_data in rows:
        row = table.add_row()
        prevent_split(row)
        for i, value in enumerate(row_data):
            p = row.cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.05
            set_font(p.add_run(str(value)), size=font_size, color=TEXT)
    if widths is None:
        widths = [9360 // len(headers)] * len(headers)
        widths[-1] += 9360 - sum(widths)
    set_table_geometry(table, widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_para(doc, text="", bold_prefix=None, italic=False, align=None, after=6, keep=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.10
    p.paragraph_format.keep_with_next = keep
    if align is not None:
        p.alignment = align
    if bold_prefix and text.startswith(bold_prefix):
        set_font(p.add_run(bold_prefix), bold=True)
        set_font(p.add_run(text[len(bold_prefix):]), italic=italic)
    else:
        set_font(p.add_run(text), italic=italic)
    return p


def add_bullets(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Inches(0.5)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.10
        set_font(p.add_run(item))


def add_numbered(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.left_indent = Inches(0.5)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        p.paragraph_format.space_after = Pt(5)
        set_font(p.add_run(item))


def heading(doc, text, level=1):
    p = doc.add_paragraph(text, style=f"Heading {level}")
    p.paragraph_format.keep_with_next = True
    return p


def callout(doc, title, text, fill=LIGHT_PINK):
    table = doc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    cell = table.cell(0, 0)
    shade(cell, fill)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    set_font(p.add_run(title + ": "), bold=True, color=PLUM)
    set_font(p.add_run(text), color=TEXT)
    set_table_geometry(table, [9360])
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def add_code(doc, code):
    table = doc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    cell = table.cell(0, 0)
    shade(cell, "F6F8FA")
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    set_font(p.add_run(code), name="Consolas", size=8.2, color="24292F")
    set_table_geometry(table, [9360])
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def add_figure(doc, path, caption, width=6.35):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    shape = p.add_run().add_picture(str(path), width=Inches(width))
    shape._inline.docPr.set("descr", caption)
    shape._inline.docPr.set("title", Path(path).stem.replace("_", " "))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_before = Pt(0)
    c.paragraph_format.space_after = Pt(8)
    set_font(c.add_run(caption), size=9, italic=True, color=MUTED)


def page_break(doc):
    doc.add_page_break()


def set_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("Page ")
    set_font(run, size=9, color=MUTED)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    paragraph._p.append(fld)


def build_document():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.492)
    section.different_first_page_header_footer = True

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.font.color.rgb = rgb(TEXT)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.10
    for style_name, size, color, before, after in (
        ("Heading 1", 16, BLUE, 16, 8),
        ("Heading 2", 13, BLUE, 12, 6),
        ("Heading 3", 12, DARK_BLUE, 8, 4),
    ):
        style = doc.styles[style_name]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = rgb(color)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    header = section.header
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_font(hp.add_run("FemCare AI  |  Phase 1 Report"), size=9, bold=True, color=MUTED)
    footer = section.footer
    set_page_number(footer.paragraphs[0])

    # Cover page - editorial report cover.
    for _ in range(5):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    set_font(p.add_run("PHASE 1 REPORT"), size=12, bold=True, color=PINK)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    set_font(p.add_run("FemCare AI"), size=30, bold=True, color=NAVY)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(28)
    set_font(p.add_run("LLM-API Data Fusion and Exploratory Data Analysis"), size=17, color=PLUM)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(48)
    set_font(p.add_run("Parts A-E | Submission deadline: 31 August 2026"), size=11, bold=True, color=MUTED)
    add_table(doc, ["Submission detail", "Information"], [
        ["Student name", "[Enter student name]"],
        ["Roll number", "[Enter roll number]"],
        ["Programme / course", "[Enter programme and course]"],
        ["Faculty / supervisor", "[Enter faculty name]"],
        ["Project", "FemCare AI - Menstrual Health Assistant"],
        ["Report date", "30 August 2026"],
    ], widths=[2200, 7160], font_size=10)
    add_para(doc, "This report documents only the Phase 1 scope defined in the assignment timeline: Parts A through E. Phase 2 work is identified as future work and is not presented as completed.", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=0)

    page_break(doc)
    heading(doc, "Executive Summary", 1)
    add_para(doc, "FemCare AI is a local menstrual-health application built with Streamlit, Llama 3.2, MiniLM embeddings and a FAISS vector store. The original cycle-level dataset contained 17,976 records, 2,000 users and 34 attributes. During Phase 1, the dataset was enriched with demographic context from the 2024 American Community Survey (ACS), public-health context from CDC PLACES, and daily environmental context from Open-Meteo.")
    add_para(doc, "The fusion used left joins: state was the key for Census and CDC data, while state plus cycle start date was used for weather. The row count remained 17,976, confirming that no original cycle records were lost. The intermediate fused dataset contained 54 columns; two transparent quality flags were added during final cleaning, producing 56 columns.")
    callout(doc, "Main result", "The APIs expanded the kinds of questions that can be investigated, but the observed linear relationships between weather or state-level public-health context and individual pain/stress were weak. This is a valid analytical finding and prevents unsupported causal claims.")
    add_table(doc, ["Measure", "Result"], [
        ["Final dataset", "17,976 rows x 56 columns"],
        ["Unique users / states", "2,000 users / 50 states"],
        ["Duplicate user-cycle keys", "0"],
        ["Missing cells", "2,642 of 1,006,656 (0.262%)"],
        ["Rows lost during fusion", "0"],
        ["Phase 1 status", "API collection, fusion, validation, quality assessment and EDA completed"],
    ], widths=[2800, 6560])

    heading(doc, "Contents", 1)
    add_numbered(doc, [
        "Introduction and problem statement",
        "Part A - Original dataset and existing LLM/RAG application",
        "Part B - API data collection",
        "Part C - Data fusion",
        "Part D - Data quality assessment",
        "Part E - Exploratory data analysis of the fused dataset",
        "Conclusions, limitations and Phase 2 readiness",
        "References",
        "Appendices",
    ])

    page_break(doc)
    heading(doc, "1. Introduction and Problem Statement", 1)
    add_para(doc, "The purpose of Phase 1 is to move beyond simply calling an API. The work must show that external data were validated, joined correctly, assessed for quality and used for meaningful analysis. In FemCare, external data enrich the menstrual-cycle records with state-level demographic and public-health context and date-specific weather context.")
    callout(doc, "Problem statement", "How can external API-generated data be integrated with an existing dataset to enrich the knowledge available to an LLM-based application, and what new insights can be obtained from the resulting fused dataset?", fill=LIGHT_BLUE)
    heading(doc, "1.1 Phase 1 objectives", 2)
    add_bullets(doc, [
        "Describe the original dataset and the existing FemCare LLM/RAG application.",
        "Document API purpose, requests, responses, parsing and structured outputs.",
        "Explain and validate the fusion keys and join methods.",
        "Assess structure, missingness, consistency, duplicates and outliers.",
        "Perform univariate, bivariate and multivariate analysis focused on newly introduced API variables.",
        "State what the enrichment enables without claiming that Phase 2 RAG integration is already complete.",
    ])
    add_figure(doc, ASSETS / "fig00_fusion_pipeline.png", "Figure 1. Phase 1 data-fusion workflow used in FemCare.")

    page_break(doc)
    heading(doc, "2. Part A - Original Dataset and Existing LLM/RAG Application", 1)
    heading(doc, "2.1 Original dataset", 2)
    add_table(doc, ["Item", "Description"], [
        ["Dataset name", "FemCare menstrual cycle dataset (menstrual_dataset.csv)"],
        ["Dataset source", "Existing project dataset supplied/used for the earlier LLM phase. The repository does not record an external publisher or download URL; this provenance gap must be corrected before external publication."],
        ["Unit of observation", "One menstrual-cycle record for one user"],
        ["Dimensions", "17,976 rows x 34 columns"],
        ["Coverage", "2,000 users, 50 US states, 1 January 2024 to 5 April 2025"],
        ["Unique identifier", "Composite key: user_id + cycle_number"],
        ["Duplicate identifier count", "0"],
        ["Missing cells", "5,486: 2,000 previous-cycle values and 3,486 exercise-frequency values"],
    ], widths=[2300, 7060])
    heading(doc, "2.2 Important original attributes", 2)
    add_table(doc, ["Group", "Attributes", "Purpose"], [
        ["Identity and time", "user_id, cycle_number, start_date, state", "Track cycles and provide fusion keys."],
        ["Cycle and symptoms", "cycle length, previous length, phase, flow, pain, PMS, ovulation", "Describe the menstrual event and symptoms."],
        ["Wellness", "mood, stress, sleep, energy, concentration, work hours lost, health score", "Measure daily experience and functional impact."],
        ["Hormonal", "estrogen, progesterone", "Provide cycle-related biological context."],
        ["Lifestyle and history", "age, BMI, diet, exercise, hydration, caffeine, alcohol, smoking, birth control, PCOS", "Support lifestyle and health-pattern analysis."],
    ], widths=[1650, 4110, 3600], font_size=8.7)

    heading(doc, "2.3 Existing FemCare LLM/RAG application", 2)
    add_para(doc, "LLM used: Llama 3.2 3B, executed locally through Ollama. General medical questions are routed to a retrieval-augmented generation pipeline. The retriever uses sentence-transformers/all-MiniLM-L6-v2 embeddings and a FAISS vector database. Streamlit provides the user interface.")
    add_para(doc, "The original system could answer educational questions such as what PCOS is, why menstrual cramps occur, normal cycle length, how stress or sleep may affect periods, and when symptoms may require medical attention. It could also interpret structured symptom descriptions through a rule-based clinical assessment layer. It is an educational assistant, not a diagnostic system.")
    add_figure(doc, ROOT / "screenshots" / "chat_pcos_rag.png", "Figure 2. Existing FemCare RAG application answering a PCOS question and showing that medical knowledge was retrieved.", width=6.4)

    heading(doc, "2.4 EDA performed on the original dataset", 2)
    add_para(doc, "The earlier dashboard summarized the original records through counts, means and distributions. It reported 17,976 records, 2,000 users, average age 25.8 years, average BMI 23.0, average cycle length 27.8 days, average pain 4.9/10, average stress 5.7/10 and 1,478 PCOS-positive records.")
    add_figure(doc, ROOT / "screenshots" / "analytics_dashboard_1.png", "Figure 3. Existing EDA dashboard showing original dataset metrics and distributions.", width=6.4)
    original_eda_summary = add_para(doc, "The original EDA established strong within-record patterns: pain was positively correlated with stress (r = 0.607) and work hours lost (r = 0.823), and negatively correlated with mood (r = -0.646), energy (r = -0.707), concentration (r = -0.727) and overall health (r = -0.921). These are associations in the project dataset, not causal effects.")
    original_eda_summary.paragraph_format.keep_together = True

    heading(doc, "3. Part B - API Data Collection", 1)
    add_para(doc, "Three APIs form the final analytical fusion. Nominatim is additionally used to geocode state capitals for the weather collector. USDA and OpenStreetMap healthcare data were collected for separate application features but were not joined into the final cycle-level CSV because no reliable cycle-level join key was available.")
    heading(doc, "3.1 API information", 2)
    add_table(doc, ["API", "Provider and purpose", "Method / format", "Authentication"], [
        ["2024 ACS 5-Year", "US Census Bureau; population, female age groups and median household income by state", "GET / JSON", "API key in query parameter"],
        ["CDC PLACES", "US CDC; county-level obesity, inactivity, smoking and depression estimates aggregated to state", "GET (Socrata) / JSON", "No key in current collector"],
        ["Open-Meteo Historical Weather", "Open-Meteo; daily temperature, humidity, precipitation and wind", "GET / JSON", "No key"],
        ["Nominatim Search", "OpenStreetMap; verifies state-capital coordinates used in weather requests", "GET / JSON", "No key; descriptive User-Agent"],
    ], widths=[1700, 3970, 1750, 1940], font_size=8.5)

    heading(doc, "3.2 Collected API datasets", 2)
    add_table(doc, ["Structured file", "Records", "Attributes", "Key / granularity", "Missing / duplicate status"], [
        ["census_state.csv", "52", "8", "One row per state-equivalent", "0 missing; 0 duplicate states"],
        ["cdc_places_state.csv", "51", "8", "One aggregated row per state-equivalent", "0 missing after documented median imputation; 0 duplicate states"],
        ["open_meteo_row_level.csv", "17,976", "40", "Cycle rows plus 6 weather fields; state + date", "321 latitude and 321 longitude missing; weather measures complete; 0 duplicate full rows"],
    ], widths=[2200, 900, 1000, 2480, 2780], font_size=8.4)
    add_para(doc, "Census returned the 50 states plus the District of Columbia and Puerto Rico. CDC returned the 50 states plus the District of Columbia. Only the 50 states present in the original menstrual dataset participated in the final joins.")

    heading(doc, "3.3 Important API fields", 2)
    add_table(doc, ["Source", "Fields retained", "Reason"], [
        ["Census", "state FIPS, total population, female population, female 20-24, 25-29, 30-34, median household income", "Adds demographic and socioeconomic context relevant to reproductive-age populations."],
        ["CDC", "state abbreviation, represented population, obesity, physical inactivity, smoking, depression, imputation flag", "Adds public-health and lifestyle context while keeping missing-value treatment visible."],
        ["Open-Meteo", "latitude, longitude, mean temperature, mean humidity, precipitation, mean wind speed", "Adds date-specific environmental context without importing unnecessary weather variables."],
    ], widths=[1500, 4560, 3300], font_size=8.6)

    heading(doc, "3.4 Request-response evidence and parsing", 2)
    add_figure(doc, ASSETS / "fig_api_request_response.png", "Figure 4. Sanitized Open-Meteo request/response evidence reconstructed from the collector schema and a stored parsed row. Raw JSON was not retained, which is documented as a reproducibility limitation.")
    add_code(doc, "params = {\n    'latitude': latitude,\n    'longitude': longitude,\n    'start_date': start_date.strftime('%Y-%m-%d'),\n    'end_date': end_date.strftime('%Y-%m-%d'),\n    'daily': 'temperature_2m_mean,relative_humidity_2m_mean,'\n             'precipitation_sum,wind_speed_10m_mean'\n}\nresponse = requests.get(WEATHER_URL, params=params, timeout=60)\nresponse.raise_for_status()\ndata = response.json()")
    add_para(doc, "The collection process followed the required sequence: request construction, HTTP response validation, JSON parsing, numeric conversion, missing-value checks, field renaming and CSV storage. Network errors were caught and reported rather than silently converted into zeros.")
    heading(doc, "3.5 API collection code", 2)
    add_table(doc, ["File", "Role"], [
        ["scripts/api_census.py", "Requests selected ACS variables, combines ages 20-24 and stores the state table."],
        ["scripts/api_cdc_places.py", "Requests selected county fields, computes population-weighted state averages and records imputation."],
        ["scripts/api_open_meteo.py", "Geocodes capitals, retrieves daily weather and creates row-level weather-enriched records."],
        ["scripts/retry_indiana_weather.py", "One-time support script used to recover Indiana weather coverage."],
    ], widths=[3000, 6360])

    heading(doc, "4. Part C - Data Fusion", 1)
    heading(doc, "4.1 Common attributes", 2)
    add_table(doc, ["Fusion", "Common attribute", "Reason"], [
        ["Menstrual + Census", "state", "Both sources contain normalized US state names; Census is one row per state."],
        ["Menstrual + CDC", "state", "County records were first aggregated to state, matching the granularity available in the menstrual dataset."],
        ["Menstrual + weather", "state + start_date", "A weather observation must match both the user state context and the cycle date."],
    ], widths=[2500, 2200, 4660])
    heading(doc, "4.2 Fusion method", 2)
    add_para(doc, "All three integrations used left joins. A left join was appropriate because the original menstrual dataset is the analytical backbone: every original cycle record must remain even when an external value is unavailable. Census and CDC merges were validated as many-to-one. Weather was reduced to one row per state-date key before a many-to-one merge.")
    add_code(doc, "fused = menstrual.merge(census_small, on='state', how='left', validate='many_to_one')\nfused = fused.merge(cdc_small, on='state', how='left', validate='many_to_one')\nfused = fused.merge(weather_small, on=['state', 'start_date'],\n                    how='left', validate='many_to_one')")

    heading(doc, "4.3 Included and excluded features", 2)
    add_table(doc, ["Decision", "Features / source", "Reason"], [
        ["Included", "All 34 original menstrual columns", "Preserves the earlier analytical and LLM information."],
        ["Included", "7 Census additions", "Target-population and socioeconomic context."],
        ["Included", "7 CDC additions", "Public-health context and transparent imputation metadata."],
        ["Included", "6 weather additions", "Small, interpretable set of environmental variables."],
        ["Derived", "has_previous_cycle, coordinates_available", "Distinguishes structural missingness from collection availability."],
        ["Excluded", "Temporary Census age-20, age-21 and age-22-24 columns", "Combined into census_female_20_24 to avoid redundant components."],
        ["Excluded", "CDC countyname and raw county rows", "The original dataset has no county key; state aggregation avoids an invalid county join."],
        ["Excluded", "Duplicate menstrual columns in weather output", "Only the six weather additions were selected during final fusion."],
        ["Excluded", "USDA food table", "No record of food consumption connects a food item to a user-cycle row."],
        ["Excluded", "Stored Overpass healthcare table", "Collection is incomplete and healthcare facilities have no reliable cycle-level key."],
        ["Excluded", "Older WHO, air-quality and experimental raw-fusion outputs", "They belong to an earlier pipeline and are not read by final_fusion.py."],
    ], widths=[1300, 3500, 4560], font_size=8.15)

    heading(doc, "4.4 Dataset comparison", 2)
    add_table(doc, ["Parameter", "Original", "API layers", "Final cleaned"], [
        ["Records", "17,976", "Census 52; CDC 51; weather row-level 17,976", "17,976"],
        ["Attributes", "34", "8 Census; 8 CDC; 6 new weather fields", "56"],
        ["Unique identifier", "user_id + cycle_number", "state; state + date", "user_id + cycle_number"],
        ["Missing cells", "5,486", "Census 0; CDC 0; coordinates 642 cells", "2,642 (0.262%)"],
        ["Duplicate records", "0", "0 full-row duplicates", "0"],
    ], widths=[1900, 1900, 3650, 1910], font_size=8.5)

    heading(doc, "4.5 Fusion validation", 2)
    add_table(doc, ["Validation check", "Observed result", "Interpretation"], [
        ["Original vs final row count", "17,976 vs 17,976", "All original records preserved."],
        ["Census state matches", "50 of 50 base states", "0 unmatched cycle rows."],
        ["CDC state matches", "50 of 50 base states", "0 unmatched cycle rows."],
        ["Weather measure matches", "17,976 cycle rows", "0 rows missing temperature, humidity, precipitation or wind."],
        ["Repeated weather state-date keys", "7,164 repeated rows in row-level weather output", "Expected because multiple users can share a state/date; reduced to one key before merge."],
        ["Duplicate user-cycle keys", "0", "Fusion did not multiply records."],
        ["Records lost", "0", "Confirmed by left-join row-count check."],
        ["Conflicting columns", "0 merged-name conflicts", "External columns were renamed and selected before merging."],
        ["Coordinate availability", "321 Indiana rows missing coordinates", "Recorded through coordinates_available; weather measures were recovered separately."],
    ], widths=[2650, 2450, 4260], font_size=8.35)

    heading(doc, "5. Part D - Data Quality Assessment", 1)
    heading(doc, "5.1 Structural checks", 2)
    add_table(doc, ["Check", "Result"], [
        ["Dimensions", "17,976 rows x 56 columns"],
        ["Parsed data types", "23 floating-point, 21 integer, 11 text and 1 date column"],
        ["Unique users", "2,000"],
        ["Unique states", "50"],
        ["Duplicate full rows", "0"],
        ["Duplicate user-cycle identifiers", "0"],
        ["Date range", "1 January 2024 to 5 April 2025"],
    ], widths=[3000, 6360])
    heading(doc, "5.2 Missing-data assessment and treatment", 2)
    add_table(doc, ["Attribute", "Missing", "% of rows", "Treatment and justification"], [
        ["prev_cycle_length", "2,000", "11.126%", "Retained as missing because each user's first cycle has no previous cycle; has_previous_cycle was added."],
        ["exercise_frequency before cleaning", "3,486", "19.393%", "Changed to 'Not reported'; missing must not be interpreted as no exercise."],
        ["latitude", "321", "1.786%", "Retained as missing; coordinates_available records collection status."],
        ["longitude", "321", "1.786%", "Retained as missing; coordinates_available records collection status."],
        ["Four weather measures", "0", "0%", "All cycle rows have usable daily weather values."],
    ], widths=[2250, 1050, 1250, 4810], font_size=8.5)
    add_para(doc, "After cleaning, the dataset contains 2,642 missing cells out of 1,006,656, equal to 0.262%. The remaining missing values are documented rather than replaced with misleading zeros.")

    heading(doc, "5.3 Consistency checks", 2)
    add_bullets(doc, [
        "State names were converted to text, trimmed and matched against the 50 states in the base data.",
        "Original dates were parsed with day-first handling and external dates were converted to the same date type.",
        "CDC categorical missingness was not coded as zero; median imputation was recorded with cdc_imputation_flag.",
        "Flow, cycle phase and other categorical values were inspected through frequency tables; no conflicting API values overwrite original clinical fields.",
        "Numeric fields were converted with invalid values becoming missing, allowing validation rather than silent string processing.",
    ])

    heading(doc, "5.4 Outlier assessment", 2)
    add_figure(doc, ASSETS / "fig02_cycle_length_boxplot.png", "Figure 5. IQR assessment of cycle length. The 374 flagged records are long cycles above 33.5 days, not automatically errors.")
    add_table(doc, ["Variable", "IQR bounds", "Flagged", "Decision"], [
        ["Cycle length", "21.5 to 33.5 days", "374 (2.08%)", "Retained. Values range from 22 to 44 days and can represent plausible irregular or long cycles."],
        ["Mean temperature", "-12.85 to 44.35 C", "55 (0.31%)", "Retained. Low winter temperatures are plausible for US state capitals."],
        ["Median household income", "$46,299.50 to $114,719.50", "0", "No IQR outliers in the 50 matched states."],
    ], widths=[1800, 2200, 1500, 3860], font_size=8.4)
    callout(doc, "Outlier policy", "An IQR flag is a signal for review, not proof of an error. Values were retained when they were within plausible domain ranges and supported by the source context.", fill=LIGHT_BLUE)

    heading(doc, "5.5 Quality limitations", 2)
    add_bullets(doc, [
        "The repository does not document the external provenance or collection method of the original menstrual dataset.",
        "Weather uses state-capital coordinates as an approximation; it is not the user's exact local weather.",
        "CDC and Census variables are state-level context repeated across individual cycle rows. They must not be interpreted as personal measurements.",
        "Raw API JSON responses were not archived, so the structured CSV and collection code are the main audit trail.",
        "The Census collector currently contains an API credential in source code; it must be revoked and moved to an environment variable before repository submission.",
    ])

    heading(doc, "6. Part E - Exploratory Data Analysis of the Fused Dataset", 1)
    add_para(doc, "EDA was selected to answer questions introduced by fusion: whether weather conditions relate to menstrual pain, whether state public-health context relates to cycle outcomes, and how API variables interact with the original clinical variables. Pearson correlations describe linear association only and do not establish causation.")
    heading(doc, "6.1 Univariate analysis", 2)
    add_table(doc, ["Variable", "Mean", "Median", "Std. dev.", "Min", "Q1", "Q3", "Max"], [
        ["Cycle length (days)", "27.817", "28.0", "2.400", "22.0", "26.0", "29.0", "44.0"],
        ["Pain level", "4.854", "5.0", "2.230", "1.0", "3.0", "6.0", "10.0"],
        ["Cycle stress", "5.749", "5.8", "1.772", "1.0", "4.5", "7.0", "10.0"],
        ["Cycle sleep (hours)", "6.960", "7.0", "1.315", "4.5", "6.0", "7.9", "10.0"],
        ["Mean temperature (C)", "15.505", "17.3", "9.404", "-29.4", "8.6", "22.9", "39.3"],
        ["Mean humidity (%)", "66.426", "69.0", "16.643", "8.0", "57.0", "78.0", "100.0"],
        ["Precipitation", "2.908", "0.0", "6.947", "0.0", "0.0", "2.1", "86.7"],
        ["CDC obesity (%)", "34.078", "34.496", "3.679", "25.607", "31.497", "36.643", "40.655"],
        ["CDC depression (%)", "22.607", "22.680", "3.123", "15.128", "20.697", "24.887", "30.452"],
        ["Median income ($)", "79,962", "77,485", "12,501", "56,447", "71,957", "89,062", "103,960"],
    ], widths=[1900, 1050, 1050, 1150, 1000, 1000, 1000, 1210], font_size=7.5)
    add_figure(doc, ASSETS / "fig01_pain_distribution.png", "Figure 6. Pain levels are concentrated around the middle of the 1-10 scale; the mean is 4.854 and median is 5.")

    heading(doc, "6.2 Bivariate analysis: API variables vs original variables", 2)
    add_figure(doc, ASSETS / "fig03_temperature_vs_pain.png", "Figure 7. Mean temperature and pain show an almost zero row-level linear correlation (r = -0.0165). Temperature groups fluctuate slightly, but there is no consistent trend.")
    add_para(doc, "Other weather-pain correlations were also negligible: humidity r = -0.0036, precipitation r = -0.0020 and wind speed r = 0.0125. Therefore, this dataset does not support a claim that these weather measurements are strong linear predictors of pain.")
    add_figure(doc, ASSETS / "fig04_inactivity_vs_pain.png", "Figure 8. At the state level, CDC physical inactivity and average menstrual pain show a very weak negative correlation (r = -0.0862).")
    add_para(doc, "State aggregation is used for this comparison because CDC prevalence is a state-level contextual value. Treating 17,976 repeated state values as independent observations would exaggerate the effective sample size.")

    heading(doc, "6.3 Multivariate analysis", 2)
    add_figure(doc, ASSETS / "fig05_correlation_heatmap.png", "Figure 9. Correlation heatmap combining selected original and API-derived variables.")
    add_para(doc, "The strongest relationships remain among original cycle variables: pain rises with stress (r = 0.61) and falls with mood (r = -0.65) and energy (r = -0.71). API-derived weather and contextual health values have correlations close to zero with pain. At the contextual level, CDC obesity and Census household income are strongly negatively correlated (approximately r = -0.74), but this is an ecological state-level association and must not be interpreted as an individual relationship.")

    heading(doc, "6.4 Fusion-specific visualization", 2)
    add_figure(doc, ASSETS / "fig06_fusion_insight.png", "Figure 10. CDC depression prevalence versus average cycle stress by state, with bubble size representing Census population. The correlation is essentially zero (r = 0.008).")
    add_para(doc, "This fusion-specific analysis demonstrates the new capability created by API integration: individual cycle outcomes can now be compared carefully with external population context. In this case, the result is a useful null finding rather than evidence of a strong relationship.")

    heading(doc, "6.5 Findings, evidence and interpretation", 2)
    add_table(doc, ["Finding", "Evidence", "Interpretation"], [
        ["Fusion preserved the analytical population.", "17,976 original and final rows; 0 duplicate user-cycle keys.", "External enrichment did not remove or multiply cycle records."],
        ["Weather is not strongly associated with pain in this dataset.", "Temperature r=-0.0165; humidity r=-0.0036; precipitation r=-0.0020; wind r=0.0125.", "Weather adds useful context, but it should not be presented as a strong pain predictor."],
        ["State inactivity does not explain state-average pain.", "50-state correlation r=-0.0862.", "Public-health context broadens analysis but the observed relationship is weak."],
        ["Original cycle variables carry the strongest signal.", "Pain-stress r=0.61, pain-mood r=-0.65 and pain-energy r=-0.71.", "Personal cycle measures are more directly informative for current symptom analysis."],
        ["Contextual socioeconomic variables are interrelated.", "CDC obesity vs Census median income is approximately r=-0.74.", "The fused data supports ecological comparisons unavailable before fusion, but not individual causal conclusions."],
        ["Remaining missingness is small and explainable.", "2,642 missing cells (0.262%), primarily first-cycle history and Indiana coordinates.", "Transparent flags preserve meaning better than replacing values with zero."],
    ], widths=[2700, 3300, 3360], font_size=7.95)

    page_break(doc)
    heading(doc, "7. Conclusions, Limitations and Phase 2 Readiness", 1)
    add_para(doc, "Phase 1 successfully created and validated a fused CSV that expands the original 34-column cycle dataset to 56 columns while preserving all 17,976 records. Census ACS contributed demographic and income context, CDC PLACES contributed state health indicators, and Open-Meteo contributed daily environmental information.")
    add_para(doc, "The EDA shows that enrichment is valuable even when it does not produce strong correlations. It enables new questions and provides evidence against overstating weather or state-context effects in the present data. The most useful predictors of pain remain original cycle-level variables such as stress, mood, energy, concentration and overall health.")
    callout(doc, "Phase boundary", "The final fused CSV is prepared for Phase 2, but the existing FAISS index is still built from data/cleaned_dataset.csv rather than femcare_final_cleaned.csv. Rebuilding the RAG knowledge base and conducting before/after LLM testing belong to the Phase 2 submission due 25 September 2026.")
    heading(doc, "7.1 Recommended Phase 2 workflow", 2)
    add_numbered(doc, [
        "Remove identifiers and select safe, explainable fused fields for retrieval documents.",
        "Convert each fused record or state/date summary into a source-labelled text document.",
        "Rebuild embeddings and a separate FAISS index for fused knowledge.",
        "Prepare five original-data questions and five questions requiring API context.",
        "Compare correctness, completeness, relevance, hallucination and response time before and after enrichment.",
        "Retain citations and clearly distinguish individual observations from state-level context in generated answers.",
    ])

    heading(doc, "References", 1)
    references = [
        "U.S. Census Bureau. 2024 ACS 5-Year Data API. https://api.census.gov/data/2024/acs/acs5.html (accessed 29 August 2026).",
        "U.S. Census Bureau. American Community Survey 5-Year Data 2024. https://www.census.gov/data/developers/data-sets/acs-5year/2024.html (accessed 29 August 2026).",
        "Centers for Disease Control and Prevention. PLACES Data Portal. https://www.cdc.gov/places/tools/data-portal.html (accessed 29 August 2026).",
        "Open-Meteo. Historical Weather API documentation. https://open-meteo.com/en/docs/historical-weather-api (accessed 29 August 2026).",
        "Nominatim. Search API documentation. https://nominatim.org/release-docs/latest/api/Search/ (accessed 29 August 2026).",
        "FemCare project source files: scripts/api_census.py, scripts/api_cdc_places.py, scripts/api_open_meteo.py, scripts/final_fusion.py and scripts/clean_final_dataset.py.",
        "Assignment timeline: LLM-API-Data Fusion and Exploratory Data Analysis Phase 1, Parts A-E, submission deadline 31 August 2026.",
    ]
    add_numbered(doc, references)

    heading(doc, "Appendix A - Final Dataset Feature Inventory", 1)
    add_table(doc, ["Source", "Count", "Final columns"], [
        ["Original menstrual", "34", "user_id; cycle_number; start_date; cycle_length_days; prev_cycle_length; cycle_phase; flow_level; pain_level; pms_symptoms; mood_score; stress_score_cycle; sleep_hours_cycle; energy_level; concentration_score; work_hours_lost; estrogen_pgml; progesterone_ngml; ovulation_result; overall_health_score; log_consistency_score; prepared_before_period; state; age; bmi; diet_quality; exercise_frequency; sleep_hours; caffeine_intake; water_intake_liters; alcohol_consumption; smoking_status; birth_control_use; pcos_diagnosed; stress_score_baseline"],
        ["Census ACS additions", "7", "state_fips; census_total_population; census_female_population; census_female_20_24; census_female_25_29; census_female_30_34; census_median_household_income"],
        ["CDC additions", "7", "state_abbr; cdc_total_population; cdc_obesity_prevalence; cdc_physical_inactivity_prevalence; cdc_smoking_prevalence; cdc_depression_prevalence; cdc_imputation_flag"],
        ["Open-Meteo additions", "6", "latitude; longitude; temperature_mean; humidity_mean; precipitation; wind_speed_mean"],
        ["Cleaning flags", "2", "has_previous_cycle; coordinates_available"],
    ], widths=[2100, 900, 6360], font_size=7.65)

    heading(doc, "Appendix B - Reproducible Execution Order", 1)
    add_numbered(doc, [
        "Run scripts/api_census.py to create data/api_fusion/static/census_state.csv.",
        "Run scripts/api_cdc_places.py to create data/api_fusion/static/cdc_places_state.csv.",
        "Run scripts/api_open_meteo.py to create state-capital coordinates and open_meteo_row_level.csv.",
        "Run scripts/final_fusion.py to create femcare_final_fused_dataset.csv (17,976 x 54).",
        "Run scripts/clean_final_dataset.py to create femcare_final_cleaned.csv (17,976 x 56).",
        "Run scripts/eda_final_dataset.py or the analytics module to reproduce summaries and visualizations.",
    ])
    heading(doc, "Appendix C - Files to Submit for Phase 1", 1)
    add_table(doc, ["Deliverable", "Project file(s)"], [
        ["Original dataset", "data/menstrual_dataset.csv"],
        ["API datasets", "data/api_fusion/static/*.csv and data/api_fusion/dynamic/open_meteo_row_level.csv"],
        ["Final fused dataset", "data/api_fusion/final/femcare_final_cleaned.csv"],
        ["API code", "scripts/api_census.py; api_cdc_places.py; api_open_meteo.py"],
        ["Fusion and cleaning code", "scripts/final_fusion.py; scripts/clean_final_dataset.py"],
        ["EDA code", "scripts/eda_final_dataset.py; analytics/eda.py"],
        ["Existing LLM/RAG code", "rag/retriever.py; rag/llm.py; embeddings/create_vector_db.py; app.py"],
    ], widths=[2700, 6660], font_size=6.8)

    doc.core_properties.title = "FemCare AI - LLM-API Data Fusion and EDA Phase 1 Report"
    doc.core_properties.subject = "Phase 1 report covering Parts A-E"
    doc.core_properties.author = "FemCare Project Team"
    doc.core_properties.keywords = "FemCare, LLM, API, data fusion, EDA, Census, CDC, Open-Meteo"
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build_document()
