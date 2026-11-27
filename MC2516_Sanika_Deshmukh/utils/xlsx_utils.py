"""
utils/xlsx_utils.py
────────────────────────────────────────────────────────────────────────
Builds a formatted, multi-sheet .xlsx export of a PlatePal session —
the same underlying data as utils/csv_utils.build_export_csv(), just laid
out so it's actually readable in Excel:

  • one sheet per section (Overview, Food Analysis, Conversation History,
    RAG Retrieval, Recipes, Weather Match, Cultural Origin, Price in
    Currencies, Product Search)
  • the food photo is embedded as a real image instead of 359 rows of
    Base64 text
  • headers are styled, columns are wrapped/sized, panes are frozen

Drop this file in your `utils/` folder next to csv_utils.py.

NOTE: This module was written by inspecting how app.py *calls*
build_export_csv() and how app.py itself unpacks the recipes / weather /
culture / exchange_rates / products dicts in its tabs — utils/csv_utils.py
and utils/food_apis.py weren't available when this was written. If a field
comes back blank in a sheet, it likely means one of those dicts uses a
slightly different key name in your actual code — check the `.get(...)`
calls below against food_apis.py and adjust the key names to match.
"""
import io
import re
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage

FONT_NAME = "Arial"
HEADER_FILL = PatternFill(start_color="2F5233", end_color="2F5233", fill_type="solid")
HEADER_FONT = Font(name=FONT_NAME, bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(name=FONT_NAME, bold=True, size=14, color="2F5233")
LABEL_FONT = Font(name=FONT_NAME, bold=True, size=10)
BODY_FONT = Font(name=FONT_NAME, size=10)
ITALIC_NOTE = Font(name=FONT_NAME, italic=True, size=9, color="666666")
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")


def _parse_ticket_fields(raw_text):
    """Same **Label:** value pattern app.py's render_ticket() parses."""
    pattern = re.compile(r"\*\*([^*]+?):?\*\*\s*(.*?)(?=\*\*[^*]+?:?\*\*|$)", re.DOTALL)
    return [(l.strip(), v.strip().strip("*").strip())
            for l, v in pattern.findall(raw_text or "") if l.strip() and v.strip()]


def _kv_sheet(wb, name, title, pairs, col_widths=(24, 90)):
    ws = wb.create_sheet(name[:31])
    ws.sheet_view.showGridLines = False
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws.merge_cells("A1:B1")
    ws["A3"] = "Field"; ws["B3"] = "Value"
    for c in ("A3", "B3"):
        ws[c].font = HEADER_FONT
        ws[c].fill = HEADER_FILL
        ws[c].border = BORDER
    r = 4
    for k, v in pairs:
        ws.cell(row=r, column=1, value=k).font = LABEL_FONT
        ws.cell(row=r, column=1).border = BORDER
        vcell = ws.cell(row=r, column=2, value=v)
        vcell.font = BODY_FONT
        vcell.alignment = WRAP
        vcell.border = BORDER
        r += 1
    ws.column_dimensions["A"].width = col_widths[0]
    ws.column_dimensions["B"].width = col_widths[1]
    ws.freeze_panes = "A4"
    return ws


def _table_sheet(wb, name, title, header, rows, col_widths):
    ws = wb.create_sheet(name[:31])
    ws.sheet_view.showGridLines = False
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(len(header), 1))
    start_row = 3
    for j, h in enumerate(header, start=1):
        c = ws.cell(row=start_row, column=j, value=h)
        c.font = HEADER_FONT
        c.fill = HEADER_FILL
        c.border = BORDER
    for i, row in enumerate(rows, start=start_row + 1):
        for j, val in enumerate(row, start=1):
            c = ws.cell(row=i, column=j, value=val)
            c.font = BODY_FONT
            c.border = BORDER
            c.alignment = WRAP
    ws.freeze_panes = ws.cell(row=start_row + 1, column=1)
    for j, w in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(j)].width = w
    if not rows:
        ws.cell(row=start_row + 1, column=1, value="— none for this session —").font = ITALIC_NOTE
    return ws


def _build_fusion_record(analysis_text, messages, language, model, image_info,
                          api_results, rag_results):
    """
    Flattens every data source (photo info, food analysis, chat, and all 5
    APIs) into ONE ordered dict — one column per field, one row per session.
    This backs both the 'Fusion Data' xlsx sheet and the clean fusion CSV,
    so the two downloads always match exactly.
    """
    api_results = api_results or {}
    rag_results = rag_results or []
    messages = messages or []
    image_info = image_info or {}

    fields = dict(_parse_ticket_fields(analysis_text))

    convo = " || ".join(
        f'{str(m.get("role","")).upper()}: {(m.get("content","") or "")[:200]}'
        for m in messages
    )

    rag_summary = "; ".join(
        f'{h.get("dish_name", h.get("dish",""))}'
        for h in rag_results if isinstance(h, dict)
    ) or "None found"

    recipes = api_results.get("recipes", {})
    recipe_names = ", ".join(
        r.get("name", "") for r in recipes.get("recipes", [])
    ) if recipes.get("ok") else "Not checked"

    wx = api_results.get("weather", {})
    culture = api_results.get("culture", {})
    wiki = culture.get("wiki", {})
    fx = api_results.get("exchange_rates", {})
    fx_summary = ", ".join(
        f'{c.get("symbol","")}{c.get("cost","")} {c.get("currency","")}'
        for c in fx.get("conversions", [])
    ) if fx.get("ok") else "Not checked"

    products = api_results.get("products", {})
    product_summary = "; ".join(
        f'{p.get("name","")} ({p.get("brand","")})'
        for p in products.get("products", [])
    ) if products.get("ok") else "Not checked"

    return {
        "Export Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Language": language,
        "AI Model": model,
        "Image Filename": image_info.get("filename", "—"),
        "Image Size (KB)": image_info.get("size_kb", "—"),
        "Dish": fields.get("Dish", ""),
        "Cuisine": fields.get("Cuisine", ""),
        "Ingredients (Likely)": fields.get("Ingredients (likely)", fields.get("Ingredients (Likely)", "")),
        "Estimated Calories": fields.get("Estimated calories", fields.get("Estimated Calories", "")),
        "Macros": fields.get("Macros (approx per serving)", fields.get("Macros (Approx Per Serving)", "")),
        "Health Notes": fields.get("Health notes", fields.get("Health Notes", "")),
        "Conversation (all turns)": convo,
        "RAG — Similar Past Dishes": rag_summary,
        "Recipes Found (TheMealDB)": recipe_names,
        "Weather City": wx.get("city", "Not checked") if wx.get("ok") else "Not checked",
        "Weather Condition": wx.get("condition", "") if wx.get("ok") else "",
        "Weather Temp (C)": wx.get("temp_c", "") if wx.get("ok") else "",
        "Weather Advice": wx.get("advice", "") if wx.get("ok") else "",
        "Cultural Origin": culture.get("origin", "Not checked") if culture.get("ok") else "Not checked",
        "Cuisine Type": culture.get("cuisine_type", "") if culture.get("ok") else "",
        "Wikipedia Summary": wiki.get("extract", "") if culture.get("ok") else "",
        "Base Cost (INR)": fx.get("cost_inr", "") if fx.get("ok") else "",
        "Price in Other Currencies": fx_summary,
        "Product Search Results": product_summary,
    }


def _fusion_sheet(wb, record):
    """Column-wise: field names across row 3 as headers, one data row below —
    the single flat table combining photo/chat/analysis/all-API data."""
    header = list(record.keys())
    row = [list(record.values())]
    col_widths = [22] * len(header)
    # widen the long free-text columns
    long_cols = {"Conversation (all turns)", "Health Notes", "Wikipedia Summary",
                 "Weather Advice", "Ingredients (Likely)", "Recipes Found (TheMealDB)",
                 "Product Search Results", "Price in Other Currencies"}
    col_widths = [45 if h in long_cols else 20 for h in header]
    return _table_sheet(wb, "Fusion Data", "Fusion Data — All Sources, One Row Per Session",
                         header, row, col_widths)


def build_fusion_csv(analysis_text="", messages=None, language="English", model="",
                      image_info=None, api_results=None, rag_results=None,
                      pil_image=None) -> bytes:
    """
    Same fused record as the xlsx 'Fusion Data' sheet, but as a clean,
    readable CSV — one header row + one data row, no Base64 image chunks.
    (pil_image is accepted but unused — a photo can't go in a CSV cell;
    it's noted by filename only, same as the xlsx Overview sheet's caption.)
    """
    import csv as _csv
    record = _build_fusion_record(analysis_text, messages, language, model,
                                   image_info, api_results, rag_results)
    buf = io.StringIO()
    writer = _csv.writer(buf)
    writer.writerow(record.keys())
    writer.writerow(record.values())
    return buf.getvalue().encode("utf-8-sig")  # BOM so Excel opens it cleanly


def build_export_xlsx(analysis_text="", messages=None, language="English", model="",
                       image_info=None, api_results=None, rag_results=None,
                       pil_image=None) -> bytes:
    """
    Mirrors build_export_csv()'s signature so you can call it the same way
    from app.py. Returns raw .xlsx bytes ready for st.download_button.
    """
    messages = messages or []
    image_info = image_info or {}
    api_results = api_results or {}
    rag_results = rag_results or []

    wb = Workbook()
    wb.remove(wb.active)

    # ---------- Overview ----------
    ws = wb.create_sheet("Overview")
    ws.sheet_view.showGridLines = False
    ws["A1"] = "PlatePal Export Summary"
    ws["A1"].font = Font(name=FONT_NAME, bold=True, size=16, color="2F5233")
    ws.merge_cells("A1:C1")

    dims = (f'{image_info.get("width")}x{image_info.get("height")}px'
            if image_info.get("width") else "—")
    meta_pairs = [
        ("Export Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Language", language),
        ("AI Model", model),
        ("Image Filename", image_info.get("filename", "—")),
        ("Image Dimensions", dims),
        ("Image Size (KB)", image_info.get("size_kb", "—")),
    ]
    ws["A3"] = "Session Metadata"
    ws["A3"].font = Font(name=FONT_NAME, bold=True, size=12)
    r = 4
    for k, v in meta_pairs:
        ws.cell(row=r, column=1, value=k).font = LABEL_FONT
        ws.cell(row=r, column=2, value=v).font = BODY_FONT
        r += 1
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 45

    # Embed the actual food photo instead of a Base64 text dump
    if pil_image is not None:
        try:
            img_buf = io.BytesIO()
            pil_image.convert("RGB").save(img_buf, format="PNG")
            img_buf.seek(0)
            xl_img = XLImage(img_buf)
            xl_img.width = 260
            xl_img.height = 260
            ws.add_image(xl_img, "D3")
        except Exception:
            pass  # never let a bad/missing image break the export

    r += 1
    ws.cell(row=r, column=1, value="Converted for readability — the raw Base64 image chunks from").font = ITALIC_NOTE
    r += 1
    ws.cell(row=r, column=1, value="the CSV export are replaced here with the actual embedded photo.").font = ITALIC_NOTE

    # ---------- Fusion Data (combined, one row per session) ----------
    fusion_record = _build_fusion_record(analysis_text, messages, language, model,
                                          image_info, api_results, rag_results)
    _fusion_sheet(wb, fusion_record)

    # ---------- Food Analysis ----------
    fields = _parse_ticket_fields(analysis_text)
    _table_sheet(wb, "Food Analysis", "Food Analysis (Gemini Vision AI)",
                 ["Field", "Value"], fields, [24, 90])

    # ---------- Conversation History ----------
    conv_rows = []
    for i, m in enumerate(messages, start=1):
        role = str(m.get("role", "")).upper()
        content = m.get("content", "")
        conv_rows.append([i, role, content])
    _table_sheet(wb, "Conversation History", "Conversation History",
                 ["#", "Role", "Message"], conv_rows, [5, 12, 100])

    # ---------- RAG Retrieval ----------
    if rag_results:
        rag_rows = []
        for hit in rag_results:
            if isinstance(hit, dict):
                rag_rows.append([
                    hit.get("dish_name", hit.get("dish", "")),
                    hit.get("timestamp", ""),
                    (hit.get("text", "") or "")[:500],
                    hit.get("score", hit.get("similarity", "")),
                ])
        _table_sheet(wb, "RAG Retrieval", "RAG Retrieval (Similar Past Analyses)",
                     ["Dish", "Timestamp", "Text (truncated)", "Similarity"],
                     rag_rows, [20, 16, 70, 12])
    else:
        _table_sheet(wb, "RAG Retrieval", "RAG Retrieval (Similar Past Analyses)",
                     ["Status"], [["No similar past analyses found yet"]], [50])

    # ---------- Recipes ----------
    recipes = api_results.get("recipes", {})
    rec_rows = []
    for rec in recipes.get("recipes", []) if recipes.get("ok") else []:
        rec_rows.append([
            rec.get("name", ""), rec.get("category", ""), rec.get("area", ""),
            rec.get("youtube", ""),
            " | ".join(rec.get("ingredients", [])[:5]),
        ])
    _table_sheet(wb, "Recipes", "Recipes (TheMealDB)",
                 ["Recipe", "Category", "Area", "YouTube", "Ingredients (first 5)"],
                 rec_rows, [22, 14, 12, 45, 60])

    # ---------- Weather Match ----------
    wx = api_results.get("weather", {})
    if wx.get("ok"):
        wx_pairs = [
            ("City", wx.get("city", "")), ("Country", wx.get("country", "")),
            ("Temp C", wx.get("temp_c", "")), ("Feels C", wx.get("feels_c", "")),
            ("Humidity", wx.get("humidity", "")), ("Condition", wx.get("condition", "")),
            ("Wind Kmh", wx.get("wind_kmh", "")), ("Advice", wx.get("advice", "")),
        ]
    else:
        wx_pairs = [("Status", "Not checked this session")]
    _kv_sheet(wb, "Weather Match", "Weather Match (OpenWeatherMap)", wx_pairs, (16, 60))

    # ---------- Cultural Origin ----------
    culture = api_results.get("culture", {})
    if culture.get("ok"):
        wiki = culture.get("wiki", {})
        cul_pairs = [
            ("Dish", culture.get("dish", "")), ("Origin", culture.get("origin", "")),
            ("Cuisine Type", culture.get("cuisine_type", "")),
            ("Wikipedia Title", wiki.get("title", "")),
            ("Wikipedia Summary", wiki.get("extract", "")),
            ("Wikipedia URL", wiki.get("url", "")),
        ]
    else:
        cul_pairs = [("Status", "Not looked up this session")]
    _kv_sheet(wb, "Cultural Origin", "Cultural Origin (Wikipedia)", cul_pairs, (18, 90))

    # ---------- Price in Currencies ----------
    fx = api_results.get("exchange_rates", {})
    if fx.get("ok"):
        fx_header = ["Currency", "Symbol", "Rate (from INR)", "Dish Cost"]
        fx_rows = [[c.get("currency", ""), c.get("symbol", ""), c.get("rate", ""), c.get("cost", "")]
                   for c in fx.get("conversions", [])]
        ws_px = _table_sheet(wb, "Price in Currencies", "Price in Currencies (ExchangeRate API)",
                              fx_header, fx_rows, [10, 8, 16, 12])
        r = ws_px.max_row + 2
        for k, v in [("Base Cost (INR)", fx.get("cost_inr", "")),
                     ("Rates Last Updated", fx.get("last_updated", ""))]:
            ws_px.cell(row=r, column=1, value=k).font = LABEL_FONT
            ws_px.cell(row=r, column=2, value=v).font = BODY_FONT
            r += 1
    else:
        _table_sheet(wb, "Price in Currencies", "Price in Currencies (ExchangeRate API)",
                     ["Status"], [["Not checked this session"]], [50])

    # ---------- Product Search ----------
    products = api_results.get("products", {})
    ps_rows = []
    for p in products.get("products", []) if products.get("ok") else []:
        ps_rows.append([
            p.get("name", ""), p.get("brand", ""), p.get("quantity", ""),
            p.get("nutriscore", ""), p.get("calories_100g", ""),
            p.get("protein_100g", ""), p.get("carbs_100g", ""), p.get("fat_100g", ""),
        ])
    _table_sheet(wb, "Product Search", "Product Search (Open Food Facts)",
                 ["Product", "Brand", "Quantity", "Nutri-Score",
                  "Cal/100g", "Protein/100g", "Carbs/100g", "Fat/100g"],
                 ps_rows, [24, 22, 12, 12, 10, 14, 14, 10])

    wb.move_sheet("Overview", offset=-len(wb.sheetnames))

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()