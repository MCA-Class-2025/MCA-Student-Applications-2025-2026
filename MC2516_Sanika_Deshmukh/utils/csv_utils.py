"""
csv_utils.py — Export all PlatePal data to CSV
------------------------------------------------
Includes:
- Session metadata
- Food analysis (parsed fields)
- Image data (Base64 encoded — preserves the actual photo as data)
- Full conversation history
- RAG retrieval results
- All API results (recipes, weather, cultural, exchange rates, product search)
"""

import base64
import csv
import io
import re
from datetime import datetime


def flatten_analysis(raw_text: str) -> dict:
    """Parse Gemini's markdown analysis into flat key-value pairs for CSV."""
    fields = {}
    pattern = re.compile(r"\*\*([^*]+?):?\*\*\s*(.*?)(?=\*\*[^*]+?:?\*\*|$)", re.DOTALL)
    for label, value in pattern.findall(raw_text or ""):
        key = label.strip().lower().replace(" ", "_").replace("/", "_")
        fields[key] = value.strip().strip("*").strip()
    return fields


def pil_image_to_base64(pil_image) -> str:
    """Convert a PIL image to a Base64 JPEG string for embedding in CSV."""
    if pil_image is None:
        return ""
    try:
        buf = io.BytesIO()
        pil_image.convert("RGB").save(buf, format="JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        return ""


def build_export_csv(
    analysis_text: str,
    messages: list,
    language: str,
    model: str,
    image_info: dict,
    api_results: dict,
    rag_results: list,
    pil_image=None,
) -> bytes:
    """
    Build a comprehensive CSV with all PlatePal data including the image.
    Returns UTF-8 BOM bytes (Excel-compatible).
    """
    output = io.StringIO()
    writer = csv.writer(output)
    now    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Section 1: Session Metadata ───────────────────────────────
    writer.writerow(["=== SESSION METADATA ==="])
    writer.writerow(["Field", "Value"])
    writer.writerow(["Export Timestamp",  now])
    writer.writerow(["Language",          language])
    writer.writerow(["AI Model",          model])
    writer.writerow(["Image Filename",    image_info.get("filename",   "—")])
    writer.writerow(["Image Dimensions",  image_info.get("dimensions", "—")])
    writer.writerow(["Image Size (KB)",   image_info.get("size_kb",   "—")])
    writer.writerow([])

    # ── Section 2: Image Data (Base64) ───────────────────────────
    writer.writerow(["=== IMAGE DATA (Base64 JPEG) ==="])
    writer.writerow(["Note", "Paste the Base64 string below into https://base64.guru/converter/decode/image to view the image"])
    img_b64 = pil_image_to_base64(pil_image)
    if img_b64:
        # Split into chunks of 1000 chars so Excel doesn't truncate
        chunk_size = 1000
        chunks = [img_b64[i:i+chunk_size] for i in range(0, len(img_b64), chunk_size)]
        writer.writerow(["Total Chunks", len(chunks)])
        writer.writerow(["Format", "JPEG Base64"])
        for idx, chunk in enumerate(chunks, 1):
            writer.writerow([f"Image_Chunk_{idx:03d}", chunk])
    else:
        writer.writerow(["Image", "Not available"])
    writer.writerow([])

    # ── Section 3: Food Analysis (Gemini Vision) ──────────────────
    writer.writerow(["=== FOOD ANALYSIS (Gemini Vision AI) ==="])
    writer.writerow(["Field", "Value"])
    analysis_fields = flatten_analysis(analysis_text)
    if analysis_fields:
        for key, val in analysis_fields.items():
            writer.writerow([key.replace("_", " ").title(), val])
    else:
        writer.writerow(["Raw Analysis", (analysis_text or "")[:500]])
    writer.writerow([])

    # ── Section 4: Conversation History ───────────────────────────
    writer.writerow(["=== CONVERSATION HISTORY ==="])
    writer.writerow(["#", "Role", "Message"])
    for i, msg in enumerate(messages, 1):
        writer.writerow([i, msg.get("role","").upper(),
                         msg.get("content","").replace("\n"," ")])
    writer.writerow([])

    # ── Section 5: RAG Retrieval Results ─────────────────────────
    writer.writerow(["=== RAG RETRIEVAL (Similar Past Analyses) ==="])
    if rag_results:
        writer.writerow(["Rank","Dish","Similarity Score","Analyzed On","Summary"])
        for i, r in enumerate(rag_results, 1):
            writer.writerow([
                i, r.get("dish_name","—"), r.get("score","—"),
                r.get("timestamp","—"),
                r.get("text","")[:200].replace("\n"," "),
            ])
    else:
        writer.writerow(["Status", "No similar past analyses found yet"])
    writer.writerow([])

    # ── Section 6: Recipes (TheMealDB) ───────────────────────────
    writer.writerow(["=== RECIPES (TheMealDB) ==="])
    recipes = api_results.get("recipes", {})
    if recipes.get("ok") and recipes.get("recipes"):
        writer.writerow(["Recipe","Category","Area","YouTube","Ingredients (first 5)"])
        for r in recipes["recipes"]:
            writer.writerow([
                r.get("name","—"), r.get("category","—"), r.get("area","—"),
                r.get("youtube","—"), " | ".join(r.get("ingredients",[])[:5]),
            ])
    else:
        writer.writerow(["Status", recipes.get("error","Not fetched or no results")])
    writer.writerow([])

    # ── Section 7: Weather (OpenWeatherMap) ──────────────────────
    writer.writerow(["=== WEATHER MATCH (OpenWeatherMap) ==="])
    wx = api_results.get("weather", {})
    if wx.get("ok"):
        writer.writerow(["Field","Value"])
        for k in ["city","country","temp_c","feels_c","humidity","condition","wind_kmh","advice"]:
            writer.writerow([k.replace("_"," ").title(), wx.get(k,"—")])
    else:
        writer.writerow(["Status", wx.get("error","Not fetched")])
    writer.writerow([])

    # ── Section 8: Cultural Origin (Wikipedia) ───────────────────
    writer.writerow(["=== CULTURAL ORIGIN (Wikipedia) ==="])
    culture = api_results.get("culture", {})
    if culture.get("ok"):
        writer.writerow(["Field","Value"])
        writer.writerow(["Dish",          culture.get("dish","—")])
        writer.writerow(["Origin",        culture.get("origin","—")])
        writer.writerow(["Cuisine Type",  culture.get("cuisine_type","—")])
        wiki = culture.get("wiki",{})
        writer.writerow(["Wikipedia Title",   wiki.get("title","—")])
        writer.writerow(["Wikipedia Summary", wiki.get("extract","—")[:300].replace("\n"," ")])
        writer.writerow(["Wikipedia URL",     wiki.get("url","—")])
    else:
        writer.writerow(["Status", culture.get("error","Not fetched")])
    writer.writerow([])

    # ── Section 9: Exchange Rates ─────────────────────────────────
    writer.writerow(["=== PRICE IN CURRENCIES (ExchangeRate API) ==="])
    fx = api_results.get("exchange_rates", {})
    if fx.get("ok"):
        writer.writerow(["Currency","Symbol","Rate (from INR)","Dish Cost"])
        for conv in fx.get("conversions",[]):
            writer.writerow([conv.get("currency"), conv.get("symbol"),
                             conv.get("rate"), conv.get("cost")])
        writer.writerow(["Base Cost (INR)",   fx.get("cost_inr","—")])
        writer.writerow(["Rates Last Updated", fx.get("last_updated","—")])
    else:
        writer.writerow(["Status", fx.get("error","Not fetched")])
    writer.writerow([])

    # ── Section 10: Product Search (Open Food Facts) ──────────────
    writer.writerow(["=== PRODUCT SEARCH (Open Food Facts) ==="])
    products = api_results.get("products", {})
    if products.get("ok") and products.get("products"):
        writer.writerow(["Product","Brand","Quantity","Nutri-Score",
                         "Cal/100g","Protein/100g","Carbs/100g","Fat/100g"])
        for p in products["products"]:
            writer.writerow([
                p.get("name","—"), p.get("brand","—"), p.get("quantity","—"),
                p.get("nutriscore","—"), p.get("calories_100g","—"),
                p.get("protein_100g","—"), p.get("carbs_100g","—"),
                p.get("fat_100g","—"),
            ])
    else:
        writer.writerow(["Status", products.get("error","Not searched yet")])
    writer.writerow([])

    return output.getvalue().encode("utf-8-sig")  # UTF-8 BOM for Excel
