# app.py – NutriCare AI v29 – Cleaned Fusion + Google Books Ayurvedic + Gemini-Powered Locator
import os, sys, time, json, pandas as pd, io, urllib.parse, re, textwrap
import numpy as np
from datetime import datetime
import streamlit as st
from fusion.multi_source_fusion import build_facility_dataset
from PIL import Image
import altair as alt
from dotenv import load_dotenv
import requests
import folium
from streamlit_folium import folium_static

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---------- Imports ----------
from rag.load_documents import load_all_markdown
from rag.chunking import chunk_all_documents
from rag.vector_store import VectorStore
from rag.search import semantic_search, format_context, unique_sources
from llm.prompt import build_rag_prompt, append_disclaimer, EXAMPLE_QUESTIONS
from llm.llm import generate_response
from nutrition.nutrition_db import get_nutrition, search_food
from nutrition.nutrition_fusion_lookup import get_nutrition_with_fallback, SOURCE_LABELS
from recipe.recipe_db import search_recipes
from memory.memory import ConversationMemory
from utils.utils import ensure_dir, timestamp, get_logger
from utils.language_detector import LANGUAGE_CODES
from utils.api_helpers import search_youtube_video, get_spoonacular_nutrition
from chat_db import init_db, save_chat, get_all_chats, clear_all_chats, delete_chat
from gtts import gTTS
from fusion.fusion import (
    build_unified_dataset, compute_correlation, prettify,
    RAW_COLS, FEATURE_COLS, GEO_COLS, fetch_raw_sources,
)

GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ---------- Gemini (optional, for AI-powered city-based cancer center search) ----------
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

# -------------------- CSS --------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #023020, #06402b, #0a5a3a, #0e6b44, #1a7d4a, #228B22, #2E8B57, #3A8F5A, #4C9A6A, #5A9A7A, #6AAA8A, #7ABAA0, #8ACAB0, #9ADAC0);
        background-size: 400% 400%;
        animation: gradientBG 20s ease infinite;
        color: #e8f5e9;
        font-family: 'Segoe UI', sans-serif;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    section[data-testid="stSidebar"] {
        background-color: #06402b !important;
        backdrop-filter: none !important;
        border-right: 1px solid #0a5a3a;
        color: #d0f0d0;
    }
    .stSidebar hr { border-top: 1px solid #4caf50 !important; opacity: 0.6; margin: 10px 0; }
    .stSidebar .stButton > button {
        background: linear-gradient(135deg, #f97316, #eab308, #22c55e) !important;
        background-size: 200% 200% !important;
        animation: gradientMove 4s ease infinite !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1rem !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(234, 179, 8, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    .stSidebar .stButton > button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(234, 179, 8, 0.6) !important;
    }
    .main-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .main-header h1 {
        font-size: 2.8rem;
        font-weight: 700;
        color: #ffffff;
        text-shadow: 0 0 20px rgba(74, 222, 128, 0.3);
        margin: 0;
    }
    .main-header p {
        font-size: 1.2rem;
        color: #a5d6a7;
        font-style: italic;
        margin: 0;
        letter-spacing: 0.5px;
    }
    .answer-card {
        background-color: #ffffff;
        color: #1a1a1a;
        padding: 1.5rem 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        margin: 1rem 0;
        border-left: 6px solid #2e7d32;
        font-size: 1rem;
        line-height: 1.6;
        white-space: normal;
        overflow-wrap: break-word;
    }
    .answer-card h1, .answer-card h2, .answer-card h3, .answer-card h4 { color: #1a3a1a !important; }
    .answer-card strong { color: #2e7d32; }
    .answer-card ul, .answer-card ol { margin: 0.5rem 0; padding-left: 1.5rem; }
    .answer-card p { margin: 0.3rem 0; }
    .source-tag {
        display: inline-block;
        background-color: #e8f5e9;
        color: #1a5a2a;
        padding: 3px 12px;
        margin: 2px;
        border-radius: 12px;
        font-size: 0.75rem;
        border: 1px solid #2e7d32;
    }
    .chip-btn {
        background: transparent !important;
        border: 1px solid #4caf50 !important;
        color: white !important;
        border-radius: 24px !important;
        padding: 10px 20px !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
        width: 100% !important;
        text-align: center !important;
        background-image: none !important;
        animation: none !important;
    }
    .chip-btn:hover {
        background: rgba(76, 175, 80, 0.15) !important;
        border-color: #66bb6a !important;
        transform: scale(1.02);
    }
    .stButton > button {
        background: linear-gradient(135deg, #f97316, #eab308, #22c55e) !important;
        background-size: 200% 200% !important;
        animation: gradientMove 4s ease infinite !important;
        color: white !important;
        border: none !important;
        border-radius: 30px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.8rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(234, 179, 8, 0.3) !important;
    }
    .stButton > button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 8px 30px rgba(234, 179, 8, 0.6) !important;
    }
    .stButton > button:active { transform: scale(0.97) !important; }
    @keyframes gradientMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1a2a1a !important;
        color: #e0f0e0 !important;
        border: 1px solid #2a5a2a !important;
        border-radius: 12px !important;
        box-shadow: none !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #4caf50 !important;
        box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.2) !important;
    }
    [data-testid="stChatInput"] {
        background-color: #1a2a1a !important;
        border: 1px solid #2a5a2a !important;
        border-radius: 12px !important;
    }
    [data-testid="stChatInput"] textarea {
        background-color: #1a2a1a !important;
        color: #e0f0e0 !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #8fae8f !important;
        opacity: 1 !important;
    }
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 0.2rem;
        font-size: 2.5rem;
        line-height: 1;
    }
    .logo-container span {
        background: linear-gradient(135deg, #4ade80, #16a34a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2rem;
    }
    .tagline { font-size: 1.0rem; color: #a5d6a7; margin-top: -0.2rem; font-style: italic; font-weight: 300; letter-spacing: 0.3px; }
    .sidebar-description { font-size: 0.95rem; line-height: 1.6; color: #c8e6c9; margin: 0.5rem 0; }
    .tech-item {
        background: rgba(255,255,255,0.06);
        padding: 4px 10px;
        border-radius: 6px;
        margin: 2px 0;
        font-size: 0.85rem;
        display: inline-block;
        border-left: 3px solid #4caf50;
    }
    .disclaimer {
        font-size: 0.8rem;
        color: #e0f0e0;
        text-align: center;
        padding-top: 1rem;
        border-top: 1px solid #2a5a2a;
    }
    .chat-thread {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 8px;
        border-left: 3px solid #4caf50;
    }
    .chat-thread:hover {
        background: rgba(255,255,255,0.08);
    }
    .chat-question { font-weight: 600; color: #a5d6a7; cursor: pointer; }
    .chat-answer { color: #e0e0e0; font-size: 0.9rem; margin-top: 4px; }
    .chat-meta { font-size: 0.7rem; color: #90a8a8; }
    .about-card {
        background: rgba(255,255,255,0.05);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 16px;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .about-card h3 { color: #4ade80; margin-bottom: 8px; }
    .book-card {
        background: rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        border-left: 4px solid #4ade80;
    }
    .book-title { font-weight: 600; color: #a5d6a7; font-size: 1rem; }
    .book-author { color: #90c090; font-size: 0.85rem; font-style: italic; }
    .fusion-step-badge {
        display: inline-block;
        background: linear-gradient(135deg, #f97316, #eab308);
        color: white;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------- OVERPASS: oncology-filtered queries --------------------
OVERPASS_MIRRORS = [
    "https://overpass.kumi.systems/api/interpreter",   # tends to be most tolerant of cloud IPs
    "https://overpass.openstreetmap.ru/api/interpreter",
    "https://overpass-api.de/api/interpreter",          # strictest about bot-like traffic
    "https://overpass.private.coffee/api/interpreter",
]

# A full, real-browser-style header set. Free Overpass mirrors run basic
# bot/abuse filtering (User-Agent sniffing, Accept header checks) aimed at
# blocking scripted/cloud-IP traffic; a bare "User-Agent: NutriCare AI"
# header is an easy bot signature. This won't help if the mirror is
# blocking by IP range (that's an infra-level block no header can fix),
# but it does clear the lighter bot filters some mirrors use.
def _browser_like_headers(contact_ua):
    return {
        "User-Agent": contact_ua,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.openstreetmap.org/",
    }


def build_cancer_query(lat, lon, radius_m=8000):
    return textwrap.dedent(f"""
        [out:json][timeout:25];
        (
          node["amenity"="hospital"]["name"~"cancer|oncology|onco|tumou?r",i](around:{radius_m},{lat},{lon});
          node["healthcare"="hospital"]["name"~"cancer|oncology|onco|tumou?r",i](around:{radius_m},{lat},{lon});
          node["healthcare:speciality"~"oncology",i](around:{radius_m},{lat},{lon});
          node["amenity"="clinic"]["name"~"cancer|oncology|onco",i](around:{radius_m},{lat},{lon});
        );
        out body;
    """).strip()


def build_food_assistance_query(lat, lon, radius_m=8000):
    return textwrap.dedent(f"""
        [out:json][timeout:25];
        (
          node["amenity"="food_bank"](around:{radius_m},{lat},{lon});
          node["amenity"="community_kitchen"](around:{radius_m},{lat},{lon});
          node["social_facility"="food_bank"](around:{radius_m},{lat},{lon});
        );
        out body;
    """).strip()


def query_overpass_with_fallback(query, headers, timeout=30, retries_per_mirror=1, backoff_base=1.5):
    """
    Try each mirror once (retrying only on clear server overload signals),
    moving to the next mirror on any other failure. A longer timeout is used
    because Overpass mirrors that are actually processing a regex-heavy
    query (not just dead) can take 20-25s to respond — cutting them off at
    15s was killing requests that would have succeeded.

    Returns (response, None) on success, or (None, combined_error_string) if
    every mirror is exhausted.
    """
    contact_ua = headers.get("User-Agent", "NutriCare AI")
    browser_headers = _browser_like_headers(contact_ua)
    errors = []

    for url in OVERPASS_MIRRORS:
        for attempt in range(retries_per_mirror):
            try:
                resp = requests.post(url, data={"data": query}, headers=browser_headers, timeout=timeout)
                if resp.status_code == 200:
                    return resp, None
                if resp.status_code in (429, 504, 502, 503) and attempt + 1 < retries_per_mirror:
                    errors.append(f"{url} → HTTP {resp.status_code} (attempt {attempt + 1})")
                    time.sleep(backoff_base * (attempt + 1))
                    continue
                errors.append(f"{url} → HTTP {resp.status_code}")
                break
            except requests.exceptions.ConnectTimeout:
                errors.append(f"{url} → connection timed out")
                break
            except requests.exceptions.ReadTimeout:
                errors.append(f"{url} → read timed out after {timeout}s")
                break
            except requests.exceptions.ConnectionError:
                errors.append(f"{url} → connection refused/blocked")
                break
            except Exception as e:
                errors.append(f"{url} → {e}")
                break

    return None, " | ".join(errors)

# -------------------- GEMINI: AI-powered, grounded city cancer-center search --------------------
def search_cancer_centers_gemini(city, country_hint="India", max_results=25):
    """
    Uses Gemini with Google Search grounding to find REAL, currently-operating
    cancer hospitals/centers in a city. Grounding means Gemini checks live
    search results before answering instead of generating from memory alone —
    this is what keeps it from just inventing hospital names.
    Returns a list of dicts: name, address, city, country.
    """
    if not GENAI_AVAILABLE:
        st.error("google-generativeai not installed. Run: pip install google-generativeai")
        return []
    if not GEMINI_API_KEY:
        st.error("GEMINI_API_KEY not found in your .env file.")
        return []

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        tools="google_search_retrieval",  # enables live grounding
    )

    prompt = f"""
List up to {max_results} real, currently operating cancer treatment hospitals,
oncology centers, or cancer institutes located in or very near {city}, {country_hint}.
Use Google Search to verify each one actually exists — do NOT invent names or addresses.
If you are not confident a place is real, leave it out rather than guessing.

Return ONLY a JSON array, no markdown fences, no explanation, in exactly this format:
[
  {{"name": "...", "address": "...", "city": "{city}", "country": "{country_hint}"}}
]
""".strip()

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        st.error(f"Gemini search failed: {e}")
        return []


def geocode_nominatim(address, cache=None):
    """
    Geocode a single address via free Nominatim (OpenStreetMap).
    Nominatim's usage policy caps free requests at ~1/sec, so this sleeps
    briefly between calls — for 20-25 results, expect ~20-25 seconds total.
    """
    if cache is None:
        cache = {}
    if address in cache:
        return cache[address]

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": "NutriCare AI (contact: tamtadimpal654@gmail.com)"}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        time.sleep(1)  # respect Nominatim's 1 req/sec limit
        if resp.status_code == 200:
            data = resp.json()
            if data:
                lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
                cache[address] = (lat, lon)
                return (lat, lon)
    except Exception:
        pass

    cache[address] = (None, None)
    return (None, None)


def build_gemini_city_dataset(city, country_hint="India", max_results=25, progress_placeholder=None):
    """
    Full pipeline: Gemini (grounded) search -> geocode each result -> return
    a list of dicts with lat/lon, ready to plot on a folium map.
    """
    centers = search_cancer_centers_gemini(city, country_hint, max_results)
    if not centers:
        return []

    cache = {}
    results = []
    total = len(centers)

    for i, c in enumerate(centers):
        name = c.get("name", "Unknown")
        address = c.get("address", "")
        full_address = f"{name}, {address}, {c.get('city', city)}, {c.get('country', country_hint)}"

        lat, lon = geocode_nominatim(full_address, cache)
        if lat is None:
            # fallback: try just the street address without the name
            lat, lon = geocode_nominatim(f"{address}, {c.get('city', city)}", cache)

        if lat is not None:
            results.append({
                "name": name,
                "address": address,
                "city": c.get("city", city),
                "country": c.get("country", country_hint),
                "lat": lat,
                "lon": lon,
            })

        if progress_placeholder is not None:
            progress_placeholder.progress((i + 1) / total, text=f"Geocoding {i + 1}/{total}...")

    if progress_placeholder is not None:
        progress_placeholder.empty()

    return results

# -------------------- GOOGLE BOOKS: Ayurvedic grounding --------------------
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

def search_ayurvedic_books_api(query, max_results=5, api_key=None):
    params = {"q": f"{query} ayurveda remedy", "maxResults": max_results}
    if api_key:
        params["key"] = api_key
    try:
        resp = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    results = []
    for item in data.get("items", []):
        info = item.get("volumeInfo", {})
        search_info = item.get("searchInfo", {})
        results.append({
            "title": info.get("title", "Unknown title"),
            "authors": ", ".join(info.get("authors", [])) or "Unknown author",
            "snippet": search_info.get("textSnippet", "").replace("<b>", "").replace("</b>", ""),
            "link": info.get("infoLink", ""),
            "thumbnail": info.get("imageLinks", {}).get("thumbnail", ""),
        })
    return results

def build_ayurvedic_context(query, api_key=None):
    books = search_ayurvedic_books_api(query, api_key=api_key)
    if not books:
        return "", []
    context_parts = [
        f'From "{b["title"]}" by {b["authors"]}: {b["snippet"]}'
        for b in books if b["snippet"]
    ]
    return "\n\n".join(context_parts), books

# ---------- Translation ----------
try:
    from deep_translator import GoogleTranslator
    TRANS_AVAILABLE = True
except ImportError:
    TRANS_AVAILABLE = False
    GoogleTranslator = None

# ---------- PDF generation ----------
PDF_AVAILABLE = False
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    pass

# ---------- CLIP ----------
@st.cache_resource
def load_clip_model():
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", low_cpu_mem_usage=False)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return model, processor

try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    CLIP_AVAILABLE = True
    clip_model, clip_processor = load_clip_model()
except ImportError:
    CLIP_AVAILABLE = False
    clip_model = None
    clip_processor = None

logger = get_logger("app")
init_db()

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="🌿 NutriCare AI", page_icon="🌿", layout="wide")

# -------------------- SESSION STATE --------------------
if "messages" not in st.session_state: st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = VectorStore()
    st.session_state.index_ready = st.session_state.vector_store.load()
if "memory" not in st.session_state: st.session_state.memory = ConversationMemory()
if "language" not in st.session_state: st.session_state.language = "English"
if "pending_question" not in st.session_state: st.session_state.pending_question = None
if "selected_chat" not in st.session_state: st.session_state.selected_chat = None
if "current_page" not in st.session_state: st.session_state.current_page = "Medical Chat"

# -------------------- HELPERS --------------------
def save_to_history(module, question, answer, sources=""):
    lang = st.session_state.language
    save_chat(module, question, answer, lang, sources)

def translate_text(text, dest_lang="hi"):
    if not TRANS_AVAILABLE or not text or dest_lang == "en":
        return text
    try:
        return GoogleTranslator(source='auto', target=dest_lang).translate(text)
    except Exception:
        return text

def clean_text(text):
    lines = text.split('\n')
    cleaned = []
    prev_empty = False
    for line in lines:
        is_empty = line.strip() == ''
        if not is_empty or not prev_empty:
            cleaned.append(line)
        prev_empty = is_empty
    return '\n'.join(cleaned)

def format_response(text):
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        if re.match(r'^(CASE\s*[AB]\b.*)$', line.strip(), re.IGNORECASE):
            continue
        if re.match(r'^#+\s*Acknowledgement\s*', line.strip(), re.IGNORECASE):
            cleaned = re.sub(r'^#+\s*Acknowledgement\s*', '', line, flags=re.IGNORECASE)
            if cleaned.strip():
                new_lines.append(cleaned)
            continue
        if re.match(r'^#+\s*Key Information\s*$', line.strip(), re.IGNORECASE):
            new_lines.append('**Key Information**')
            continue
        if re.match(r'^#+\s*Practical Tips\s*$', line.strip(), re.IGNORECASE):
            new_lines.append('**Practical Tips**')
            continue
        if re.match(r'^\*\*Acknowledgement\*\*:?\s*$', line.strip(), re.IGNORECASE):
            continue
        cleaned = re.sub(r'^\s*\d+\.\s*\*\*?([^*]+)\*\*?:\s*', r'**\1:** ', line)
        if cleaned == line:
            cleaned = re.sub(r'^\s*\d+\.\s*([^:]+):\s*', r'**\1:** ', cleaned)
        new_lines.append(cleaned)
    result = '\n'.join(new_lines)
    return clean_text(result)

def markdown_to_plain(text):
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    return text

def render_answer_card(content_html):
    st.markdown(f'<div class="answer-card">\n\n{content_html}\n\n</div>', unsafe_allow_html=True)

def create_multi_color_chart(data_dict, title="Nutrient Values"):
    if not data_dict:
        return None
    df = pd.DataFrame({"Nutrient": list(data_dict.keys()), "Value": list(data_dict.values())})
    color_scheme = alt.Scale(
        domain=df["Nutrient"].tolist(),
        range=['#f97316', '#eab308', '#22c55e', '#06b6d4', '#8b5cf6', '#ec4899', '#14b8a6']
    )
    chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, opacity=0.85).encode(
        x=alt.X('Nutrient', sort=None, axis=alt.Axis(labelAngle=-20)),
        y=alt.Y('Value', axis=alt.Axis(gridColor='#2a5a2a')),
        color=alt.Color('Nutrient', scale=color_scheme, legend=None),
        tooltip=['Nutrient', 'Value']
    ).properties(title=title, width=600, height=350).configure_axis(
        labelColor='#c8e6c9', titleColor='#a5d6a7', gridColor='#2a5a2a'
    ).configure_title(color='#a5d6a7', fontSize=16)
    return chart

def speak_text(text, lang="en"):
    if not text.strip():
        return None
    try:
        tts = gTTS(text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        st.warning(f"TTS error: {e}")
        return None

def download_pdf(content, filename):
    if not PDF_AVAILABLE:
        st.download_button("📥 Download (as .txt)", data=content, file_name=filename.replace(".pdf", ".txt"), mime="text/plain")
        return
    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y = height - 50
        c.setFont("Helvetica", 10)
        for line in content.split('\n'):
            if y < 50:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 10)
            if len(line) > 80:
                words = line.split()
                current = ""
                for w in words:
                    if len(current) + len(w) + 1 <= 80:
                        current += " " + w
                    else:
                        c.drawString(50, y, current.strip())
                        y -= 12
                        current = w
                if current:
                    c.drawString(50, y, current.strip())
                    y -= 12
            else:
                c.drawString(50, y, line)
                y -= 12
        c.save()
        pdf_bytes = buffer.getvalue()
        st.download_button("📥 Download PDF", data=pdf_bytes, file_name=filename, mime="application/pdf")
    except Exception:
        st.download_button("📥 Download (as .txt)", data=content, file_name=filename.replace(".pdf", ".txt"), mime="text/plain")

def format_nutrition_data(data):
    if not data:
        return {}
    mapping = {
        "food_name": "Food", "energy_kcal": "Energy (kcal)", "protein_g": "Protein (g)",
        "fat_g": "Fat (g)", "carb_g": "Carbohydrates (g)", "fibre_g": "Dietary Fiber (g)",
        "calcium_mg": "Calcium (mg)", "iron_mg": "Iron (mg)", "magnesium_mg": "Magnesium (mg)",
        "potassium_mg": "Potassium (mg)", "sodium_mg": "Sodium (mg)", "zinc_mg": "Zinc (mg)",
        "vita_ug": "Vitamin A (µg)", "vite_mg": "Vitamin E (mg)", "vitc_mg": "Vitamin C (mg)",
        "folate_ug": "Folate (µg)", "vitb1_mg": "Vitamin B1 (mg)", "vitb2_mg": "Vitamin B2 (mg)",
        "vitb3_mg": "Vitamin B3 (mg)", "vitb6_mg": "Vitamin B6 (mg)", "phosphorus_mg": "Phosphorus (mg)",
        "selenium_ug": "Selenium (µg)", "copper_mg": "Copper (mg)", "manganese_mg": "Manganese (mg)",
        "cholesterol_mg": "Cholesterol (mg)", "sfa_mg": "Saturated Fat (mg)",
        "mufa_mg": "Monounsaturated Fat (mg)", "pufa_mg": "Polyunsaturated Fat (mg)",
    }
    formatted = {}
    for key, display in mapping.items():
        if key in data:
            val = data[key]
            if val is not None and val != "":
                formatted[display] = val
    return formatted

def recognize_food_from_image(image_bytes):
    if not CLIP_AVAILABLE:
        return None
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        df = pd.read_csv("knowledge_base/02_Nutrition_Database/indian_food_database.csv", encoding='latin-1')
        food_names = df["food_name"].dropna().unique().tolist()
        templated_names = [f"a photo of {name}, a food item" for name in food_names]

        all_probs = []
        batch_size = 200
        for i in range(0, len(templated_names), batch_size):
            batch = templated_names[i:i + batch_size]
            inputs = clip_processor(text=batch, images=image, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = clip_model(**inputs)
                probs = outputs.logits_per_image.softmax(dim=1)
            all_probs.append(probs[0])
        combined = torch.cat(all_probs)
        combined = combined / combined.sum()

        best_idx = combined.argmax().item()
        best_food = food_names[best_idx]
        confidence = combined[best_idx].item()

        if confidence > 0.05:
            return best_food, confidence
        return None
    except Exception as e:
        logger.error("CLIP recognition failed: %s", e)
        return None

# ==================== EMPATHY INTRO FUNCTION ====================
def add_empathy_intro(module, question, answer, symptom=None, treatment=None):
    intro = ""
    q_lower = question.lower()

    if re.search(r'\b(what is cancer|define cancer|cancer definition|explain cancer)\b', q_lower):
        intro = "Here is information about cancer.\n\n"
        return intro + answer if intro else answer

    if module == "Symptom" and symptom:
        intro = f"If you are feeling {symptom}, here are some dietary tips that may help.\n\n"
    elif module == "Treatment" and treatment:
        intro = f"If you are undergoing {treatment}, here are some dietary tips that may help.\n\n"
    elif module == "Meal Planner":
        if "symptom" in q_lower or "treatment" in q_lower:
            intro = "If you are experiencing symptoms or undergoing treatment, here is a meal plan that may help.\n\n"
        else:
            intro = "Here is a personalised meal plan.\n\n"
    elif module == "Ayurvedic":
        common_symptoms = ["nausea", "vomiting", "mouth sores", "fatigue", "diarrhea", "constipation"]
        found = next((s for s in common_symptoms if s in q_lower), None)
        if found:
            intro = f"If you are feeling {found}, here are some traditional remedies that may help.\n\n"
        else:
            intro = "Here are some traditional remedies that may help.\n\n"
    elif module == "Medical Chat":
        symptom_keywords = ["nausea", "mouth sores", "fatigue", "diarrhea", "constipation", "vomiting", "pain", "loss of appetite"]
        treatment_keywords = ["chemotherapy", "radiation", "surgery", "immunotherapy", "hormone therapy"]
        if any(kw in q_lower for kw in symptom_keywords):
            found = next((kw for kw in symptom_keywords if kw in q_lower), None)
            intro = f"If you are feeling {found}, here are some dietary tips that may help.\n\n" if found else "If you are experiencing symptoms, here are some dietary tips that may help.\n\n"
        elif any(kw in q_lower for kw in treatment_keywords):
            found = next((kw for kw in treatment_keywords if kw in q_lower), None)
            intro = f"If you are undergoing {found}, here are some dietary tips that may help.\n\n" if found else "If you are undergoing treatment, here are some dietary tips that may help.\n\n"
    return intro + answer if intro else answer

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown("""
    <div class="logo-container">
        <span>🌿</span>
        <span>NutriCare AI</span>
    </div>
    <div class="tagline">Supporting better nutrition, better recovery, better lives.</div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    pages = ["Medical Chat", "Symptom", "Treatment", "Meal Planner", "Recipe", "Nutrient", "Compare", "Ayurvedic Remedies", "Data Fusion", "Cancer Care Locator", "Chat History", "About Us"]
    for p in pages:
        if st.button(p, key=f"nav_{p}", use_container_width=True):
            st.session_state.current_page = p
            st.rerun()
    st.markdown("---")
    st.session_state.language = st.selectbox("🌐 Language", ["English", "Hindi", "Marathi"])
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        clear_all_chats()
        st.session_state.messages = []
        st.session_state.memory.clear()
        st.session_state.selected_chat = None
        st.rerun()
    st.markdown("---")
    st.markdown("### ⚙️ Tech Stack & APIs")
    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; gap: 4px;">
        <span class="tech-item">🔹 LLM: Groq (Llama 3.3 70B)</span><br>
        <span class="tech-item">🔹 Embedding: all-MiniLM-L6-v2</span><br>
        <span class="tech-item">🔹 Vector DB: FAISS</span><br>
        <span class="tech-item">🔹 Framework: Streamlit</span><br>
        <span class="tech-item">🔹 Image AI: CLIP</span><br>
        <span class="tech-item">🔹 Translation: Google Translate</span><br>
        <span class="tech-item">🔹 TTS: gTTS</span><br>
        <span class="tech-item">🔹 PDF: ReportLab</span><br>
        <span class="tech-item">🔹 APIs: Groq, Google Translate, YouTube Data, USDA, Google Books, Gemini, OpenStreetMap</span><br>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Powered by Groq · Gemini · FAISS · CLIP · Streamlit · OSM")

# -------------------- MAIN AREA --------------------
st.markdown("""
<div class="main-header">
    <h1>🌿 NutriCare AI</h1>
    <p>Supporting better nutrition, better recovery, better lives.</p>
</div>
""", unsafe_allow_html=True)

page = st.session_state.current_page

# ==================== Medical Chat ====================
if page == "Medical Chat":
    st.markdown("#### Try asking:")
    cols = st.columns(3)
    for i, q in enumerate(EXAMPLE_QUESTIONS[:6]):
        with cols[i % 3]:
            if st.button(q, key=f"chip_{i}"):
                st.session_state.pending_question = q
                st.rerun()

    for turn in st.session_state.messages:
        if turn["role"] == "user":
            with st.chat_message("user"):
                st.markdown(turn["content"])
        else:
            formatted = format_response(turn["content"])
            render_answer_card(formatted)
            if turn.get("sources"):
                tags = " ".join(f'<span class="source-tag">{s}</span>' for s in turn["sources"])
                st.markdown(tags, unsafe_allow_html=True)

    user_input = st.chat_input("Ask about nutrition, symptoms, or recipes...")
    if st.session_state.pending_question and not user_input:
        user_input = st.session_state.pending_question
        st.session_state.pending_question = None

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                store = st.session_state.vector_store
                if not store.is_ready:
                    answer = "Knowledge base not ready. Please check the vector store."
                    sources = []
                else:
                    results = semantic_search(user_input, store, top_k=5)
                    context = format_context(results)
                    history = st.session_state.memory.format_history()
                    prompt = build_rag_prompt(user_input, context, history)
                    raw = generate_response(prompt)
                    raw = raw.replace("Acknowledgement:", "").strip()
                    answer = append_disclaimer(raw)
                    answer = add_empathy_intro("Medical Chat", user_input, answer)
                    sources = unique_sources(results)
                    lang_code = LANGUAGE_CODES.get(st.session_state.language, "en")
                    if lang_code != "en":
                        answer = translate_text(answer, lang_code)
                formatted_answer = format_response(answer)
                render_answer_card(formatted_answer)
                if sources:
                    tags = " ".join(f'<span class="source-tag">{s}</span>' for s in sources)
                    st.markdown(tags, unsafe_allow_html=True)

                if st.button("🔊 Speak", key="speak_medical"):
                    audio_bytes = speak_text(answer, lang_code)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")

        st.session_state.memory.add_turn(user_input, answer)
        st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
        save_to_history("Medical Chat", user_input, answer, ", ".join(sources))
        st.rerun()

# ==================== Symptom ====================
elif page == "Symptom":
    st.markdown("### Symptom-Based Diet Advice")
    symptom = st.text_input("Enter your symptom (e.g., nausea, mouth sores)")
    lang_code = LANGUAGE_CODES.get(st.session_state.language, "en")
    if st.button("Get Advice", key="symptom_get") and symptom:
        with st.spinner("Searching..."):
            results = semantic_search(f"Diet for {symptom}", st.session_state.vector_store, top_k=5)
            context = format_context(results)
            prompt = f"""You are a compassionate oncology dietitian. Give specific foods to eat, foods to avoid, and hydration tips for the symptom: {symptom}.

Formatting rules:
- Use Markdown with clear bold section headers: **Foods to Eat**, **Foods to Avoid**, **Hydration Tips**
- Under each header, use a bullet point (- ) for EACH separate tip, one per line — never combine multiple tips into one paragraph
- Keep each bullet to 1-2 sentences
- Use only the context provided

Context: {context}
Answer:"""
            raw = generate_response(prompt)
            raw = raw.replace("Acknowledgement:", "").strip()
            answer = append_disclaimer(raw)
            answer = add_empathy_intro("Symptom", symptom, answer, symptom=symptom)
            if lang_code != "en":
                answer = translate_text(answer, lang_code)
            sources = unique_sources(results)
            st.session_state._symptom_answer = answer
            st.session_state._symptom_sources = sources
            st.session_state._symptom_query = symptom
            st.rerun()
    if "_symptom_answer" in st.session_state:
        formatted = format_response(st.session_state._symptom_answer)
        render_answer_card(formatted)
        if st.session_state._symptom_sources:
            tags = " ".join(f'<span class="source-tag">{s}</span>' for s in st.session_state._symptom_sources)
            st.markdown(tags, unsafe_allow_html=True)
        if st.button("🔊 Speak Symptom", key="speak_symptom"):
            audio_bytes = speak_text(st.session_state._symptom_answer, lang_code)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
        save_to_history("Symptom", f"Symptom: {st.session_state._symptom_query}", st.session_state._symptom_answer, ", ".join(st.session_state._symptom_sources))

# ==================== Treatment ====================
elif page == "Treatment":
    st.markdown("### Treatment-Based Nutrition")
    treatment = st.selectbox("Select Treatment", ["Chemotherapy", "Radiation", "Surgery", "Immunotherapy", "Hormone Therapy"])
    lang_code = LANGUAGE_CODES.get(st.session_state.language, "en")
    if st.button("Get Diet Plan", key="treatment_get") and treatment:
        with st.spinner("Generating..."):
            results = semantic_search(f"Nutrition for {treatment}", st.session_state.vector_store, top_k=5)
            context = format_context(results)
            prompt = f"""You are an oncology nutritionist. Provide dietary advice for {treatment} patients.

Formatting rules:
- Use Markdown with clear bold section headers: **Pre-Treatment**, **During Treatment**, **Post-Treatment**
- Under each header, use a bullet point (- ) for EACH separate tip, one per line — never combine multiple tips into one paragraph
- Keep each bullet to 1-2 sentences
- Add a final **Additional Tips** section with 2-3 bullets if relevant

Context: {context}
Answer:"""
            raw = generate_response(prompt)
            raw = raw.replace("Acknowledgement:", "").strip()
            answer = append_disclaimer(raw)
            answer = add_empathy_intro("Treatment", treatment, answer, treatment=treatment)
            if lang_code != "en":
                answer = translate_text(answer, lang_code)
            sources = unique_sources(results)
            st.session_state._treatment_answer = answer
            st.session_state._treatment_sources = sources
            st.session_state._treatment_query = treatment
            st.rerun()
    if "_treatment_answer" in st.session_state:
        formatted = format_response(st.session_state._treatment_answer)
        render_answer_card(formatted)
        if st.session_state._treatment_sources:
            tags = " ".join(f'<span class="source-tag">{s}</span>' for s in st.session_state._treatment_sources)
            st.markdown(tags, unsafe_allow_html=True)
        if st.button("🔊 Speak Treatment", key="speak_treatment"):
            audio_bytes = speak_text(st.session_state._treatment_answer, lang_code)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
        save_to_history("Treatment", f"Treatment: {st.session_state._treatment_query}", st.session_state._treatment_answer, ", ".join(st.session_state._treatment_sources))

# ==================== Meal Planner ====================
elif page == "Meal Planner":
    st.markdown("### Personalized Meal Planner")
    with st.form("meal_plan"):
        age = st.number_input("Age", min_value=1, max_value=120, value=50)
        gender = st.selectbox("Gender", ["Male", "Female"])
        diet = st.radio("Diet", ["Vegetarian", "Non-Vegetarian"])
        treatment = st.selectbox("Current Treatment", ["None", "Chemotherapy", "Radiation", "Surgery"])
        symptoms = st.text_input("Any symptoms? (optional)")
        cuisine = st.selectbox("Cuisine", ["Indian", "Chinese", "Italian", "Other"])
        meals = st.selectbox("Meals per day", [3,4,5])
        submitted = st.form_submit_button("Generate Plan")
    if submitted:
        query = f"Create a meal plan for a {age}-year-old {gender}, {diet}, undergoing {treatment}, symptoms: {symptoms}, cuisine: {cuisine}, {meals} meals/day."
        with st.spinner("Planning..."):
            results = semantic_search(query, st.session_state.vector_store, top_k=5)
            context = format_context(results)
            prompt = f"""You are a dietitian. Generate a daily meal plan.

Formatting rules:
- Use Markdown with clear bold section headers for each meal: **Breakfast**, **Lunch**, **Dinner**, **Snacks**
- Under each meal header, use a bullet point (- ) for each food item
- Add a **Hydration** section and a **Safety Tips** section, each with bullet points
- Include an estimated calorie count per meal

Context: {context}
Question: {query}
Answer:"""
            raw = generate_response(prompt)
            raw = raw.replace("Acknowledgement:", "").strip()
            answer = append_disclaimer(raw)
            answer = add_empathy_intro("Meal Planner", query, answer)
            lang_code = LANGUAGE_CODES.get(st.session_state.language, "en")
            if lang_code != "en":
                answer = translate_text(answer, lang_code)
            sources = unique_sources(results)
            st.session_state._meal_answer = answer
            st.session_state._meal_sources = sources
            st.session_state._meal_query = query
    if "_meal_answer" in st.session_state:
        formatted = format_response(st.session_state._meal_answer)
        render_answer_card(formatted)
        if st.session_state._meal_sources:
            tags = " ".join(f'<span class="source-tag">{s}</span>' for s in st.session_state._meal_sources)
            st.markdown(tags, unsafe_allow_html=True)
        lang_code = LANGUAGE_CODES.get(st.session_state.language, "en")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔊 Speak Meal Plan", key="speak_meal"):
                audio_bytes = speak_text(st.session_state._meal_answer, lang_code)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
        with col2:
            download_pdf(markdown_to_plain(st.session_state._meal_answer), f"meal_plan_{timestamp()}.pdf")
        save_to_history("Meal Planner", st.session_state._meal_query, st.session_state._meal_answer, ", ".join(st.session_state._meal_sources))

# ==================== Recipe ====================
elif page == "Recipe":
    st.markdown("### AI Recipe Generator")
    ingredients = st.text_area("Enter ingredients (comma separated)", "Rice, Paneer, Tomato, Capsicum")
    lang_code = LANGUAGE_CODES.get(st.session_state.language, "en")
    if st.button("Generate Recipe", key="recipe_gen"):
        with st.spinner("Creating..."):
            recipes = search_recipes(ingredients, limit=3)
            if recipes:
                rec = recipes[0]
                answer = f"### {rec.get('recipe_name', 'Recipe')}\n\n"
                answer += f"**Cuisine:** {rec.get('cuisine', '')}  |  **Time:** {rec.get('total_time', '')}\n\n"
                answer += f"**Calories:** {rec.get('calories', '')} kcal  |  **Protein:** {rec.get('protein', '')}g\n\n"
                answer += f"**Ingredients:** {rec.get('ingredients', '')}\n\n"
                answer += f"**Instructions:** {rec.get('instructions', '')}\n\n"
                if lang_code != "en":
                    answer = translate_text(answer, lang_code)
                st.session_state._recipe_answer = answer
                st.session_state._recipe_sources = "Recipe DB"
                st.session_state._recipe_name = rec.get('recipe_name', 'Recipe')
            else:
                results = semantic_search(f"Recipe with {ingredients}", st.session_state.vector_store, top_k=5)
                context = format_context(results)
                prompt = f"""Create a recipe using {ingredients}.

Start your response with exactly this format on the first line: ### Recipe Name
(replace "Recipe Name" with the actual dish name, e.g. ### Paneer and Vegetable Biryani)

Then provide, all in clean Markdown with proper bullet points (- ) for lists:
- **Prep Time** and **Cook Time**
- **Ingredients** (bullet list)
- **Steps** (numbered list)
- **Nutrition** (per serving, bullet list)
- **Alternatives** (bullet list)
- **Cancer-Friendly Notes** (bullet list)

Context: {context}
Answer:"""
                raw = generate_response(prompt)
                raw = raw.replace("Acknowledgement:", "").strip()
                answer = append_disclaimer(raw)
                if lang_code != "en":
                    answer = translate_text(answer, lang_code)
                st.session_state._recipe_answer = answer
                st.session_state._recipe_sources = ", ".join(unique_sources(results))
                match = re.search(r'(?:###\s*|\*{0,2}Recipe:\s*)([^\n*]+)', answer)
                st.session_state._recipe_name = match.group(1).strip() if match else "Recipe"
    if "_recipe_answer" in st.session_state:
        formatted = format_response(st.session_state._recipe_answer)
        render_answer_card(formatted)
        if st.session_state._recipe_sources and st.session_state._recipe_sources != "Recipe DB":
            tags = " ".join(f'<span class="source-tag">{s}</span>' for s in st.session_state._recipe_sources.split(", "))
            st.markdown(tags, unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔊 Speak Recipe", key="speak_recipe"):
                audio_bytes = speak_text(st.session_state._recipe_answer, lang_code)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
        with col2:
            download_pdf(st.session_state._recipe_answer, f"recipe_{timestamp()}.pdf")
        with col3:
            if st.button("🎬 Watch Video"):
                video_ids = search_youtube_video(st.session_state._recipe_name)
                if video_ids:
                    embed_url = f"https://www.youtube.com/embed/{video_ids[0]}"
                    st.markdown(f'<iframe width="560" height="315" src="{embed_url}" frameborder="0" allowfullscreen></iframe>', unsafe_allow_html=True)
                    if len(video_ids) > 1:
                        st.write("More videos:")
                        for vid in video_ids[1:]:
                            st.markdown(f'- [Watch on YouTube](https://www.youtube.com/watch?v={vid})')
                else:
                    query = urllib.parse.quote_plus(st.session_state._recipe_name + " recipe")
                    youtube_url = f"https://www.youtube.com/results?search_query={query}"
                    st.markdown(f'<a href="{youtube_url}" target="_blank"><button style="background-color:#2e7d32; color:white; border:none; border-radius:30px; padding:0.4rem 1.6rem; font-weight:500; cursor:pointer;">🎬 YouTube Search</button></a>', unsafe_allow_html=True)
        save_to_history("Recipe", f"Ingredients: {ingredients}", st.session_state._recipe_answer, st.session_state._recipe_sources)

# ==================== Nutrient ====================
elif page == "Nutrient":
    st.markdown("### Indian Food Nutrition Lookup")
    nutrient_method = st.radio("Search by:", ["Text", "Image"], horizontal=True)

    if nutrient_method == "Text":
        food = st.text_input("Enter food name (e.g., Paneer, Rice)")
        if st.button("Lookup", key="nutrient_text") and food:
            matches = search_food(food, limit=5)
            if not matches:
                st.warning("Food not found.")
            else:
                selected = st.selectbox("Did you mean:", matches)
                data = get_nutrition(selected)
                if data:
                    clean_data = format_nutrition_data(data)
                    if clean_data:
                        df_clean = pd.DataFrame([clean_data]).T
                        df_clean.columns = ["Value"]
                        st.dataframe(df_clean)
                        macro_keys = ["Energy (kcal)", "Protein (g)", "Fat (g)", "Carbohydrates (g)", "Dietary Fiber (g)"]
                        macro_vals = {k: clean_data.get(k, 0) for k in macro_keys if k in clean_data}
                        if macro_vals:
                            chart = create_multi_color_chart(macro_vals, f"Nutrients in {selected}")
                            if chart:
                                st.altair_chart(chart, use_container_width=True)
                        if st.button("🔍 Get Extra Nutrition (USDA / Spoonacular)", key="usda_btn"):
                            with st.spinner("Checking external sources..."):
                                extra_data, extra_source, _ = get_nutrition_with_fallback(selected)
                                if extra_source in ("usda", "spoonacular"):
                                    st.subheader(f"{SOURCE_LABELS[extra_source]}")
                                    for k, v in extra_data.items():
                                        st.write(f"**{k}:** {v}")
                                else:
                                    st.info("No external match found for this food.")
                    else:
                        st.warning("No nutrient data available for this food.")
                else:
                    st.warning("No data found.")
                save_to_history("Nutrient Lookup", f"Food: {food}", f"Nutrients for {selected}", "Nutrition DB")

    else:
        uploaded_file = st.file_uploader("Upload a food image (JPG, PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image_bytes = uploaded_file.read()
            st.image(image_bytes, caption="Uploaded Image", width=250)
            if st.button("🔍 Identify Food & Show Nutrition", key="nutrient_image"):
                if CLIP_AVAILABLE:
                    with st.spinner("Identifying food using AI..."):
                        result = recognize_food_from_image(image_bytes)
                    if result:
                        food_name, confidence = result
                        st.success(f"Identified as: **{food_name}** (confidence: {confidence:.2f})")
                        clean_data, source, raw_data = get_nutrition_with_fallback(
                            food_name, format_local_fn=format_nutrition_data
                        )
                        st.caption(f"Nutrition source: {SOURCE_LABELS[source]}")
                        if clean_data:
                            df_clean = pd.DataFrame([clean_data]).T
                            df_clean.columns = ["Value"]
                            st.dataframe(df_clean)
                            macro_keys = ["Energy (kcal)", "Protein (g)", "Fat (g)", "Carbohydrates (g)", "Dietary Fiber (g)"]
                            macro_vals = {k: clean_data.get(k, 0) for k in macro_keys if k in clean_data}
                            if macro_vals:
                                chart = create_multi_color_chart(macro_vals, f"Nutrients in {food_name}")
                                if chart:
                                    st.altair_chart(chart, use_container_width=True)
                        else:
                            st.warning("No source (local / USDA / Spoonacular) had nutrition data for this food.")
                        save_to_history("Nutrient Lookup (Image)", f"Image: {uploaded_file.name}",
                                         f"Identified as {food_name} via {source}", "CLIP + Fusion Cascade")
                    else:
                        st.error("Could not identify the food confidently. Please try a clearer, closer photo of a single food item, or use text search instead.")
                else:
                    st.warning("Image recognition not available (CLIP not installed). Please use text search.")

# ==================== Compare ====================
elif page == "Compare":
    st.markdown("### Compare Two Foods")
    food1 = st.text_input("Food 1", "Paneer")
    food2 = st.text_input("Food 2", "Tofu")
    if st.button("Compare", key="compare") and food1 and food2:
        d1 = get_nutrition(food1)
        d2 = get_nutrition(food2)
        if d1 and d2:
            f1 = format_nutrition_data(d1)
            f2 = format_nutrition_data(d2)
            if f1 and f2:
                common_keys = set(f1.keys()) & set(f2.keys())
                if common_keys:
                    comp_data = {}
                    for k in sorted(common_keys):
                        comp_data[k] = [f1.get(k, "N/A"), f2.get(k, "N/A")]
                    df_comp = pd.DataFrame(comp_data, index=[food1, food2]).T
                    st.dataframe(df_comp)

                    metrics = ["Energy (kcal)", "Protein (g)", "Fat (g)", "Carbohydrates (g)", "Dietary Fiber (g)", "Calcium (mg)"]
                    metrics = [m for m in metrics if m in f1 and m in f2]

                    chart_rows = []
                    for m in metrics:
                        try:
                            chart_rows.append({"Nutrient": m, "Food": food1, "Value": float(f1[m])})
                            chart_rows.append({"Nutrient": m, "Food": food2, "Value": float(f2[m])})
                        except (ValueError, TypeError):
                            continue
                    if chart_rows:
                        df_chart = pd.DataFrame(chart_rows)
                        compare_chart = alt.Chart(df_chart).mark_bar().encode(
                            x=alt.X('Nutrient', sort=None, axis=alt.Axis(labelAngle=-20)),
                            y=alt.Y('Value'),
                            color=alt.Color('Food', scale=alt.Scale(range=['#22c55e', '#f97316'])),
                            xOffset='Food',
                            tooltip=['Nutrient', 'Food', 'Value']
                        ).properties(width=600, height=350, title=f"{food1} vs {food2}").configure_axis(
                            labelColor='#c8e6c9', titleColor='#a5d6a7', gridColor='#2a5a2a'
                        ).configure_title(color='#a5d6a7', fontSize=16)
                        st.altair_chart(compare_chart, use_container_width=True)

                    st.markdown("#### 📊 Comparison Summary")
                    summary_html = '<div class="answer-card">'
                    for m in metrics:
                        v1, v2 = f1[m], f2[m]
                        try:
                            v1_f, v2_f = float(v1), float(v2)
                            if v1_f > v2_f:
                                winner = food1
                            elif v2_f > v1_f:
                                winner = food2
                            else:
                                winner = None
                            if winner:
                                summary_html += (
                                    f'<p><strong>{m}</strong>: {food1} = {v1} &nbsp;|&nbsp; '
                                    f'{food2} = {v2} &nbsp;→&nbsp; '
                                    f'<span style="color:#2e7d32; font-weight:600;">{winner} is higher</span></p>'
                                )
                            else:
                                summary_html += f'<p><strong>{m}</strong>: {v1} vs {v2} (equal)</p>'
                        except (ValueError, TypeError):
                            summary_html += f'<p><strong>{m}</strong>: {v1} vs {v2}</p>'
                    summary_html += '</div>'
                    st.markdown(summary_html, unsafe_allow_html=True)
                else:
                    st.warning("No common nutrients to compare.")
            else:
                st.warning("One or both foods have no nutrient data.")
        else:
            st.warning("One or both foods not found.")
        save_to_history("Food Comparison", f"Compare {food1} and {food2}", f"Comparison: {food1} vs {food2}", "Nutrition DB")

# ==================== Ayurvedic Remedies (Google Books) ====================
elif page == "Ayurvedic Remedies":
    st.markdown("### 🌿 Ayurvedic & Home Remedies")
    st.caption("Answers are grounded in real Ayurvedic books via Google Books — no upload needed.")

    remedy_question = st.text_input("Ask about a home remedy or traditional treatment", placeholder="e.g., 'Home remedy for nausea', 'Ayurvedic treatment for mouth sores'")
    lang_code = LANGUAGE_CODES.get(st.session_state.language, "en")

    if st.button("🔍 Get Remedy", key="remedy_get") and remedy_question:
        with st.spinner("Searching Ayurvedic books..."):
            context, books = build_ayurvedic_context(remedy_question, api_key=GOOGLE_BOOKS_API_KEY)

            prompt = f"""You are a traditional medicine expert. Provide Ayurvedic or home remedies for: {remedy_question}.

Formatting rules:
- Use Markdown with bullet points (- ) for each remedy, one per line
- Ground your answer in the book excerpts below where relevant, and mention the book title when you use one
- If the excerpts don't fully cover the question, supplement with well-established Ayurvedic knowledge, but don't fabricate book citations
- End with a note: "These are traditional/home remedies. Consult your healthcare provider before use."

Book excerpts:
{context if context else "No direct book excerpts found for this query."}

Question: {remedy_question}
Answer:"""
            raw = generate_response(prompt)
            raw = raw.replace("Acknowledgement:", "").strip()
            answer = append_disclaimer(raw)
            answer = add_empathy_intro("Ayurvedic", remedy_question, answer)
            if lang_code != "en":
                answer = translate_text(answer, lang_code)

            st.session_state._ayur_answer = answer
            st.session_state._ayur_books = books
            st.session_state._ayur_query = remedy_question
            st.rerun()

    if "_ayur_answer" in st.session_state:
        render_answer_card(format_response(st.session_state._ayur_answer))

        books = st.session_state.get("_ayur_books", [])
        if books:
            st.markdown("#### 📚 Sourced from")
            for b in books:
                thumb_col, info_col = st.columns([1, 6])
                with thumb_col:
                    if b.get("thumbnail"):
                        st.image(b["thumbnail"], width=60)
                with info_col:
                    st.markdown(f"""
                    <div class="book-card">
                        <div class="book-title">{b['title']}</div>
                        <div class="book-author">by {b['authors']}</div>
                        {f'<a href="{b["link"]}" target="_blank" style="color:#4ade80; font-size:0.85rem;">View book →</a>' if b['link'] else ''}
                    </div>
                    """, unsafe_allow_html=True)

        if st.button("🔊 Speak Remedy", key="speak_remedy"):
            audio_bytes = speak_text(st.session_state._ayur_answer, lang_code)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")

        save_to_history(
            "Ayurvedic Remedies",
            st.session_state._ayur_query,
            st.session_state._ayur_answer,
            ", ".join(b["title"] for b in books) if books else "General knowledge"
        )

# ==================== Data Fusion ====================
elif page == "Data Fusion":
    st.markdown("### 🧬 Data Fusion – Unified Indian Food Dataset")
    st.markdown("""
    This module fuses your Indian nutrient dataset (IFCT-format) with live **USDA FoodData Central**
    data, then adds **crop-production geography** — shown step by step: **fetching** from every
    source, **Raw Fusion** (values placed side-by-side), **Feature Fusion** (differences, densities,
    ratios computed from them), **Geographic Fusion** (top-producing state per crop), ending in the
    **final unified dataset** used for EDA.
    """)

    local_csv = "knowledge_base/02_Nutrition_Database/indian_food_database.csv"
    crop_csv = "knowledge_base/04_Crop_Production_Database/crop_production.csv"
    output_csv = "data/fusion/nutricare_unified_food_dataset.csv"
    os.makedirs("data/fusion", exist_ok=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        run_limit = st.number_input("Foods to process", min_value=10, max_value=2109, value=500, step=50)
        include_crop = st.checkbox("Include crop/geographic fusion", value=os.path.exists(crop_csv))
        run_fusion = st.button("🔄 Run Fusion")
    with col2:
        if os.path.exists(output_csv):
            with open(output_csv, "rb") as f:
                st.download_button("📥 Download Fused CSV", data=f.read(),
                                    file_name="nutricare_unified_food_dataset.csv", mime="text/csv")
    with col3:
        if os.path.exists(output_csv) and st.button("💾 Save copy to project root"):
            import shutil
            shutil.copy2(output_csv, os.path.join(os.getcwd(), "nutricare_unified_food_dataset.csv"))
            st.success("Saved.")

    if not os.path.exists(crop_csv) and include_crop:
        st.warning(f"Crop dataset not found at `{crop_csv}` — geographic fusion will be skipped until it's added there.")

    if run_fusion:
        with st.spinner(f"Fusing {run_limit} foods with USDA{' + crop geography' if include_crop else ''}... this may take a few minutes"):
            df_unified = build_unified_dataset(
                local_csv, output_csv, limit=run_limit,
                include_crop_fusion=include_crop, crop_csv_path=crop_csv,
            )
            st.success(f"Fusion complete — {len(df_unified)} rows saved.")
            st.rerun()

    st.markdown("---")

    # -------- Step 0: Raw source datasets, one by one --------
    st.markdown('<span class="fusion-step-badge">STEP 0</span>', unsafe_allow_html=True)
    st.subheader("📋 Raw Source Datasets")
    st.caption("The 3 datasets this module fuses, shown independently before any matching or calculations.")

    # 0a — Indian food dataset
    st.markdown("**1. Indian Food Dataset (IFCT)**")
    if os.path.exists(local_csv):
        df_local = pd.read_csv(local_csv, encoding='latin-1')
        st.dataframe(df_local.head(10), use_container_width=True)
        c1, c2 = st.columns(2)
        c1.metric("Total Rows", len(df_local))
        c2.metric("Total Columns", len(df_local.columns))
    else:
        st.warning("Local dataset not found.")

    if not os.path.exists(output_csv):
        st.info("👆 Click 'Run Fusion' above to generate the fused dataset and continue to the next steps.")
    else:
        df_unified = pd.read_csv(output_csv)

        # 0b — USDA dataset (matched rows only, USDA's own columns)
        st.markdown("---")
        st.markdown("**2. USDA FoodData Central (matched foods only)**")
        usda_cols = [c for c in df_unified.columns if c.startswith("usda_")]
        if usda_cols:
            usda_df = df_unified[["food_name"] + usda_cols].dropna(subset=["usda_calories"] if "usda_calories" in usda_cols else usda_cols, how="all")
            st.dataframe(prettify(usda_df, ["food_name"] + usda_cols).head(10), use_container_width=True)
            if "usda_calories" in df_unified.columns:
                matched = df_unified["usda_calories"].notna().sum()
                match_rate = matched / len(df_unified) * 100
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Foods", len(df_unified))
                c2.metric("USDA Matches", matched)
                c3.metric("Match Rate", f"{match_rate:.1f}%")
        else:
            st.info("No USDA columns found in the fused output.")

        # 0c — Crop production dataset
        st.markdown("---")
        st.markdown("**3. Crop Production Dataset**")
        if os.path.exists(crop_csv):
            df_crop = pd.read_csv(crop_csv)
            st.dataframe(df_crop.head(10), use_container_width=True)
            c1, c2 = st.columns(2)
            c1.metric("Total Rows", len(df_crop))
            c2.metric("Total Columns", len(df_crop.columns))
        else:
            st.info(f"Crop dataset not found at `{crop_csv}` — geographic fusion will be skipped.")

        # -------- Step 1: Raw Fusion (matched rows only) --------
        st.markdown("---")
        st.markdown('<span class="fusion-step-badge">STEP 1</span>', unsafe_allow_html=True)
        st.subheader("1️⃣ Raw Fusion — Local + USDA, side by side")
        st.caption("Local and USDA values placed next to each other for foods that had a successful USDA match — unmatched foods are left out here so no blanks show.")
        raw_available = [c for c in RAW_COLS if c in df_unified.columns]
        if "usda_calories" in df_unified.columns:
            raw_matched_df = df_unified[df_unified["usda_calories"].notna()]
        else:
            raw_matched_df = df_unified
        if len(raw_matched_df) > 0:
            st.dataframe(prettify(raw_matched_df, raw_available).head(15), use_container_width=True)
        else:
            st.info("No matched foods yet — run fusion on more foods to get USDA matches.")

        # -------- Step 2: Feature Fusion --------
        st.markdown("---")
        st.markdown('<span class="fusion-step-badge">STEP 2</span>', unsafe_allow_html=True)
        st.subheader("2️⃣ Feature Fusion — engineered from the raw values")
        st.caption("Differences, nutrient densities, and ratios computed from Step 1's raw-fused columns.")
        feat_available = ["food_name"] + [c for c in FEATURE_COLS if c in df_unified.columns]
        st.dataframe(prettify(df_unified, feat_available).head(15), use_container_width=True)

        # -------- Step 3: Geographic Fusion (crop production) --------
        st.markdown("---")
        st.markdown('<span class="fusion-step-badge">STEP 3</span>', unsafe_allow_html=True)
        st.subheader("3️⃣ Geographic Fusion — top-producing state per crop")
        geo_available = [c for c in GEO_COLS if c in df_unified.columns]
        if geo_available and df_unified[geo_available[0]].notna().any():
            st.caption(
                "Only applies to raw agricultural crops (rice, wheat, pulses, etc.) — "
                "prepared dishes and packaged foods have no crop-production equivalent, "
                "so most rows correctly show blank here."
            )
            geo_cols_display = ["food_name"] + geo_available
            geo_df = df_unified[df_unified["is_major_crop"] == True][geo_cols_display] if "is_major_crop" in df_unified.columns else df_unified[geo_cols_display]
            st.dataframe(prettify(geo_df, geo_cols_display), use_container_width=True)
            if "is_major_crop" in df_unified.columns:
                st.metric("Foods matched to a crop-production record", int(df_unified["is_major_crop"].sum()))
        else:
            st.info(f"No geographic data merged yet. Add `crop_production.csv` to `{crop_csv}` and re-run fusion with 'Include crop/geographic fusion' checked.")

        # -------- Step 4: Final Unified Dataset --------
        st.markdown("---")
        st.markdown('<span class="fusion-step-badge">STEP 4</span>', unsafe_allow_html=True)
        st.subheader("4️⃣ Final Unified Dataset")
        st.caption("Raw + feature-fused + geographic columns together — this is the dataset used for analysis below.")
        st.dataframe(df_unified.head(15), use_container_width=True)
        c1, c2 = st.columns(2)
        c1.metric("Final Rows", len(df_unified))
        c2.metric("Final Columns", len(df_unified.columns))

        # -------- Step 5: EDA --------
        st.markdown("---")
        st.markdown('<span class="fusion-step-badge">STEP 5 — EDA</span>', unsafe_allow_html=True)
        st.subheader("📊 Exploratory Data Analysis")

        tab1, tab2, tab3, tab4 = st.tabs([
            "Local vs USDA Averages", "Correlation Heatmap", "Category Distribution", "Top Producing States"
        ])

        with tab1:
            compare_pairs = [
                ("local_calories", "usda_calories", "Calories"),
                ("local_protein", "usda_protein", "Protein (g)"),
                ("local_fat", "usda_fat", "Fat (g)"),
                ("local_carbohydrates", "usda_carbohydrates", "Carbs (g)"),
                ("local_fiber", "usda_fiber", "Fiber (g)"),
            ]
            chart_rows = []
            for local_c, usda_c, label in compare_pairs:
                if local_c in df_unified.columns and usda_c in df_unified.columns:
                    chart_rows.append({"Nutrient": label, "Source": "Local (IFCT)", "Avg Value": df_unified[local_c].mean()})
                    chart_rows.append({"Nutrient": label, "Source": "USDA", "Avg Value": df_unified[usda_c].mean()})
            if chart_rows:
                df_chart = pd.DataFrame(chart_rows)
                avg_chart = alt.Chart(df_chart).mark_bar().encode(
                    x=alt.X('Nutrient', sort=None, axis=alt.Axis(labelAngle=-20)),
                    y='Avg Value',
                    color=alt.Color('Source', scale=alt.Scale(range=['#22c55e', '#f97316'])),
                    xOffset='Source',
                    tooltip=['Nutrient', 'Source', 'Avg Value']
                ).properties(width=650, height=350, title="Average Nutrient Values: Local vs USDA").configure_axis(
                    labelColor='#c8e6c9', titleColor='#a5d6a7', gridColor='#2a5a2a'
                ).configure_title(color='#a5d6a7', fontSize=16)
                st.altair_chart(avg_chart, use_container_width=True)

        with tab2:
            numeric_cols = df_unified.select_dtypes(include=[np.number]).columns.tolist()
            heatmap_candidates = raw_available + [c for c in FEATURE_COLS if c in df_unified.columns]
            heatmap_available = [c for c in heatmap_candidates if c in numeric_cols]
            if len(heatmap_available) >= 2:
                if st.button("Generate Correlation Heatmap"):
                    fig = compute_correlation(df_unified, heatmap_available)
                    if fig:
                        st.pyplot(fig)
                    else:
                        st.warning("Not enough overlapping data for correlation.")
            else:
                st.info("Not enough numeric columns for correlation yet.")

        with tab3:
            if "food_group_nin" in df_unified.columns:
                cat_counts = df_unified["food_group_nin"].value_counts().reset_index()
                cat_counts.columns = ["Category", "Count"]
                cat_chart = alt.Chart(cat_counts).mark_bar().encode(
                    x=alt.X("Count", axis=alt.Axis(gridColor='#2a5a2a')),
                    y=alt.Y("Category", sort='-x'),
                    color=alt.value("#22c55e"),
                    tooltip=["Category", "Count"]
                ).properties(width=650, height=400, title="Food Category Distribution").configure_axis(
                    labelColor='#c8e6c9', titleColor='#a5d6a7', gridColor='#2a5a2a'
                ).configure_title(color='#a5d6a7', fontSize=16)
                st.altair_chart(cat_chart, use_container_width=True)
            else:
                st.info("Category column not found.")

        with tab4:
            if "top_producing_state" in df_unified.columns and df_unified["top_producing_state"].notna().any():
                state_counts = df_unified["top_producing_state"].dropna().value_counts().reset_index()
                state_counts.columns = ["State", "Foods Led"]
                state_chart = alt.Chart(state_counts).mark_bar().encode(
                    x=alt.X("Foods Led", axis=alt.Axis(gridColor='#2a5a2a')),
                    y=alt.Y("State", sort='-x'),
                    color=alt.value("#f97316"),
                    tooltip=["State", "Foods Led"]
                ).properties(
                    width=650, height=400,
                    title="States Leading Production — Count of Matched Foods"
                ).configure_axis(
                    labelColor='#c8e6c9', titleColor='#a5d6a7', gridColor='#2a5a2a'
                ).configure_title(color='#a5d6a7', fontSize=16)
                st.altair_chart(state_chart, use_container_width=True)
                st.caption(
                    "This counts how many of your *matched* foods each state leads production of — "
                    "not national production volume. For a true choropleth map of India, you'd need "
                    "a state-boundary GeoJSON; ask if you want that added next."
                )
            else:
                st.info("No crop-production data merged yet — run fusion with geographic fusion enabled.")

# ==================== Cancer Care Locator (Gemini + CSV + optional OSM) ====================
elif page == "Cancer Care Locator":
    st.markdown("### 🏥 Cancer Care & Nutrition Assistance Locator")
    st.markdown("A world map of major cancer treatment centers, plus AI-powered per-city search.")

    cancer_centers_csv = "knowledge_base/06_Cancer_Centers/global_cancer_centers.csv"

    if not os.path.exists(cancer_centers_csv):
        st.warning(f"Cancer centers dataset not found at `{cancer_centers_csv}`.")
    else:
        df_centers = pd.read_csv(cancer_centers_csv)
        st.caption(
            f"⚠️ Coordinates and details for these {len(df_centers)} centers are curated for reference and may "
            f"have small inaccuracies — verify directly with the facility before relying on this for travel or care decisions."
        )

        filter_text = st.text_input("Filter by name, city, or country (leave blank to show all)", "")
        if filter_text.strip():
            f = filter_text.strip().lower()
            mask = (
                df_centers["name"].str.lower().str.contains(f, na=False)
                | df_centers["city"].str.lower().str.contains(f, na=False)
                | df_centers["country"].str.lower().str.contains(f, na=False)
                | df_centers["state"].astype(str).str.lower().str.contains(f, na=False)
            )
            df_shown = df_centers[mask]
        else:
            df_shown = df_centers

        st.metric("Centers shown", len(df_shown))

        if len(df_shown) > 0:
            center_lat = df_shown["lat"].mean()
            center_lon = df_shown["lon"].mean()
            zoom = 4 if len(df_shown) > 3 else 6
            m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)
            for _, row in df_shown.iterrows():
                popup_html = f"<b>{row['name']}</b><br>{row['city']}, {row.get('state', '') or ''} {row['country']}<br><i>{row.get('notes', '')}</i>"
                folium.Marker(
                    [row["lat"], row["lon"]],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=row["name"],
                    icon=folium.Icon(color="red", icon="plus-sign"),
                ).add_to(m)
            folium_static(m)

            st.markdown("#### 📋 List")
            for _, row in df_shown.iterrows():
                st.markdown(f"**{row['name']}** — {row['city']}, {row.get('state', '') or ''} {row['country']}")
        else:
            st.info("No centers match that filter. Try a different city or country.")

        with open(cancer_centers_csv, "rb") as f:
            st.download_button("📥 Download this dataset (CSV)", data=f.read(),
                                file_name="global_cancer_centers.csv", mime="text/csv")

    st.markdown("---")

    # -------- Gemini-powered city search (grounded in live Google Search) --------
    with st.expander("🤖 Search a city with Gemini (AI + live Google Search grounding)", expanded=True):
        st.caption(
            "Asks Gemini to find real cancer hospitals in a city, grounded in live Google Search "
            "(so it verifies places exist rather than guessing), then geocodes each address for the map. "
            "Covers far more cities than the static list above — but always double-check details with the "
            "facility directly before relying on this for care or travel decisions."
        )
        col_a, col_b, col_c = st.columns([2, 2, 1])
        with col_a:
            gemini_city = st.text_input("City", "Pune", key="gemini_city")
        with col_b:
            gemini_country = st.text_input("Country", "India", key="gemini_country")
        with col_c:
            gemini_max = st.number_input("Max results", min_value=5, max_value=40, value=20, key="gemini_max")

        if st.button("🔍 Search with Gemini", key="gemini_search_btn"):
            if not GEMINI_API_KEY:
                st.error("GEMINI_API_KEY not set in your .env file.")
            elif not GENAI_AVAILABLE:
                st.error("google-generativeai not installed. Run: pip install google-generativeai")
            else:
                progress_bar = st.progress(0, text="Asking Gemini...")
                with st.spinner(f"Searching for cancer centers in {gemini_city}..."):
                    gemini_results = build_gemini_city_dataset(
                        gemini_city, gemini_country, gemini_max, progress_placeholder=progress_bar
                    )
                st.session_state._gemini_locator_results = gemini_results
                st.session_state._gemini_locator_city = gemini_city
                st.rerun()

        if st.session_state.get("_gemini_locator_results"):
            gemini_results = st.session_state._gemini_locator_results
            gemini_city_used = st.session_state.get("_gemini_locator_city", gemini_city)

            if gemini_results:
                st.success(f"Found and mapped {len(gemini_results)} centers in {gemini_city_used}.")
                df_g = pd.DataFrame(gemini_results)

                m_g = folium.Map(
                    location=[df_g["lat"].mean(), df_g["lon"].mean()],
                    zoom_start=11,
                )
                for _, row in df_g.iterrows():
                    popup_html = f"<b>{row['name']}</b><br>{row['address']}<br>{row['city']}, {row['country']}"
                    folium.Marker(
                        [row["lat"], row["lon"]],
                        popup=folium.Popup(popup_html, max_width=250),
                        tooltip=row["name"],
                        icon=folium.Icon(color="blue", icon="plus-sign"),
                    ).add_to(m_g)
                folium_static(m_g)

                st.markdown("#### 📋 Results")
                st.dataframe(df_g[["name", "address", "city", "country"]], use_container_width=True)

                csv_bytes = df_g.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download these results as CSV",
                    data=csv_bytes,
                    file_name=f"cancer_centers_{gemini_city_used.replace(' ', '_')}.csv",
                    mime="text/csv",
                    key="gemini_dl",
                )

                if st.button("➕ Add these to global_cancer_centers.csv", key="append_master"):
                    master_path = "knowledge_base/06_Cancer_Centers/global_cancer_centers.csv"
                    if os.path.exists(master_path):
                        df_master = pd.read_csv(master_path)
                        df_new = df_g.rename(columns={"address": "notes"})
                        df_new["state"] = ""
                        combined = pd.concat(
                            [df_master, df_new[df_master.columns.intersection(df_new.columns)]],
                            ignore_index=True,
                        )
                        combined.drop_duplicates(subset=["name", "city"], keep="first", inplace=True)
                        combined.to_csv(master_path, index=False)
                        st.success(f"Added {len(df_new)} new centers to the master dataset.")
                    else:
                        st.warning("Master CSV not found — can't append.")
            else:
                st.warning("No results returned. Try a larger or more well-known city name.")

    with st.expander("🔍 Try a live OpenStreetMap search instead (optional — free servers are often unreliable)"):
        st.caption("This queries live OpenStreetMap data for a specific location. It depends on free public servers that frequently rate-limit or block automated requests, so it may not return results.")
        location = st.text_input("Enter your city, zip code, or address", "Mumbai")
        search_type = st.radio("What are you looking for?", ["Cancer Centers", "Food/Nutrition Assistance"])

        if st.button("Search Nearby"):
            with st.spinner("Searching using OpenStreetMap..."):
                geocode_url = "https://nominatim.openstreetmap.org/search"
                params = {"q": location, "format": "json", "limit": 1}
                headers = {"User-Agent": "Mozilla/5.0 (NutriCare AI, contact: tamtadimpal654@gmail.com)"}
                try:
                    geo_resp = requests.get(geocode_url, params=params, headers=headers, timeout=10)
                    if geo_resp.status_code == 200:
                        geo_data = geo_resp.json()
                        if geo_data:
                            lat = float(geo_data[0]["lat"])
                            lon = float(geo_data[0]["lon"])
                        else:
                            st.error("Could not geocode location. Please try a different place.")
                            st.stop()
                    else:
                        st.error(f"Geocoding failed with status {geo_resp.status_code}")
                        st.stop()
                except Exception as e:
                    st.error(f"Geocoding error: {e}")
                    st.stop()

                overpass_query = build_cancer_query(lat, lon) if search_type == "Cancer Centers" else build_food_assistance_query(lat, lon)
                overpass_resp, error = query_overpass_with_fallback(overpass_query, headers)

                if overpass_resp is not None:
                    data = overpass_resp.json()
                    elements = data.get("elements", [])
                    if elements:
                        st.success(f"Found {len(elements)} {search_type.lower()}")
                        m = folium.Map(location=[lat, lon], zoom_start=13)
                        for el in elements:
                            el_lat, el_lon = el.get("lat"), el.get("lon")
                            if el_lat is None or el_lon is None:
                                continue
                            tags = el.get("tags", {})
                            name = tags.get("name", "Unnamed")
                            icon_color = "red" if search_type == "Cancer Centers" else "green"
                            popup_text = f"<b>{name}</b><br>{tags.get('addr:street', '')} {tags.get('addr:city', '')}"
                            folium.Marker([el_lat, el_lon], popup=popup_text, icon=folium.Icon(color=icon_color)).add_to(m)
                        folium_static(m)
                        for el in elements:
                            tags = el.get("tags", {})
                            name = tags.get("name", "Unnamed")
                            st.markdown(f"**{name}** – {tags.get('addr:street', '')} {tags.get('addr:city', '')}")
                    else:
                        if search_type == "Cancer Centers":
                            st.warning("No oncology-specific facilities found nearby in OpenStreetMap's data. Try a larger city or check general hospital directories for this area.")
                        else:
                            st.warning("No food/nutrition assistance places found nearby.")
                else:
                    st.error("OpenStreetMap's free search servers are temporarily unreachable (this is on their end, not something wrong with your search).")
                    with st.expander("Technical details"):
                        st.code(error, language=None)
                    gmaps_query = urllib.parse.quote_plus(
                        f"{'cancer hospital' if search_type == 'Cancer Centers' else 'food bank'} near {location}"
                    )
                    gmaps_url = f"https://www.google.com/maps/search/?api=1&query={gmaps_query}"
                    st.markdown(f"👉 [Search **{search_type}** near {location} on Google Maps instead]({gmaps_url})")

    with st.expander("📊 Build a multi-city facility dataset (optional — also depends on live OSM search)"):
        st.caption("Build a downloadable dataset of oncology facilities + food assistance across multiple cities at once.")
        facility_output_csv = "data/fusion/nutricare_facility_dataset.csv"
        locations_input = st.text_area("Locations (one per line)", "Mumbai\nDelhi\nBengaluru")
        if st.button("🔄 Build Facility Dataset"):
            locations = [l.strip() for l in locations_input.split("\n") if l.strip()]
            with st.spinner(f"Querying OpenStreetMap for {len(locations)} location(s)..."):
                df_fac = build_facility_dataset(
                    locations,
                    search_types=("Cancer Centers", "Food/Nutrition Assistance"),
                    output_csv=facility_output_csv,
                )
                st.success(f"Done! {len(df_fac)} facilities saved.")
                st.rerun()

        if os.path.exists(facility_output_csv):
            df_fac_preview = pd.read_csv(facility_output_csv)
            st.dataframe(df_fac_preview.head(10), use_container_width=True)
            st.caption(f"Total rows: {len(df_fac_preview)}")
            with open(facility_output_csv, "rb") as f:
                st.download_button("📥 Download Facility Dataset CSV", data=f.read(),
                                    file_name="nutricare_facility_dataset.csv", mime="text/csv")

# ==================== Chat History ====================
elif page == "Chat History":
    st.markdown("### 📜 Chat History")
    st.caption("Click a question to view it, or ✕ to delete it.")

    if st.session_state.selected_chat:
        chat = st.session_state.selected_chat
        st.markdown(f"""
        <div class="chat-thread" style="border-left-color: #f97316;">
            <div style="font-weight:600; color:#4ade80;">📌 {chat['question']}</div>
            <div style="margin-top:8px; background:#1a2a1a; padding:12px; border-radius:8px; color:#e0e0e0;">
                {chat['answer']}
            </div>
            <div class="chat-meta" style="margin-top:8px;">
                🕐 {chat['timestamp']} · 📂 {chat['module']} · 🌐 {chat['language']}
                {f' · 📄 {chat["sources"]}' if chat.get("sources") else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)
        col_back, col_del = st.columns([4, 1])
        with col_back:
            if st.button("← Back to History List"):
                st.session_state.selected_chat = None
                st.rerun()
        with col_del:
            if st.button("🗑️ Delete", key="delete_selected"):
                delete_chat(chat["id"])
                st.session_state.selected_chat = None
                st.rerun()
        st.markdown("---")

    chats = get_all_chats(limit=100)
    if chats:
        for chat in chats:
            col_q, col_x = st.columns([9, 1])
            with col_q:
                if st.button(f"💬 {chat['question'][:60]}...", key=f"chat_{chat['id']}", use_container_width=True):
                    st.session_state.selected_chat = chat
                    st.rerun()
            with col_x:
                if st.button("✕", key=f"del_{chat['id']}"):
                    delete_chat(chat["id"])
                    if st.session_state.selected_chat and st.session_state.selected_chat.get("id") == chat["id"]:
                        st.session_state.selected_chat = None
                    st.rerun()
        st.markdown("---")
        if st.button("Export All as CSV"):
            df = pd.DataFrame(chats)
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", data=csv, file_name="chat_history.csv", mime="text/csv")
    else:
        st.info("No chat history yet.")

# ==================== About Us ====================
elif page == "About Us":
    st.markdown("""
    <div style="text-align:center; margin-bottom:24px;">
        <h2 style="color:#a5d6a7;">🌿 About NutriCare AI</h2>
        <p style="font-size:1.1rem; color:#c8d8d8;">An Intelligent Multilingual AI-Powered Nutrition & Diet Assistant for Cancer Patients</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="about-card">
            <h3>👨‍💻 Developer</h3>
            <p><strong>Name:</strong> Dimpal Tamta<br>
            <strong>Course:</strong> MCA<br>
            <strong>Project:</strong> Major Project – LLM & RAG</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="about-card">
            <h3>🎯 Project Goal</h3>
            <p>To provide <strong>personalised, evidence‑based, and compassionate</strong> nutrition guidance for cancer patients, caregivers, and dietitians, with support for <strong>traditional Ayurvedic remedies</strong>.</p>
            <p>Built using <strong>Retrieval-Augmented Generation (RAG)</strong> with a custom knowledge base of 85 medical documents, 2110+ Indian foods, and 100+ recipes.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="about-card">
            <h3>📚 APIs Used</h3>
            <ul style="color:#c8d8d8; padding-left:20px;">
                <li><strong>1.</strong> Groq (Llama 3.3 70B) – Main LLM</li>
                <li><strong>2.</strong> Google Translate – Multilingual (English, Hindi, Marathi)</li>
                <li><strong>3.</strong> YouTube Data API – Recipe video search</li>
                <li><strong>4.</strong> USDA FoodData Central – Nutrition data fusion</li>
                <li><strong>5.</strong> Google Books API – Ayurvedic remedy grounding</li>
                <li><strong>6.</strong> Gemini API (Google Search grounding) – AI-powered cancer center locator</li>
                <li><strong>7.</strong> OpenStreetMap – Free location services</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="about-card">
            <h3>🧠 Technology Stack</h3>
            <ul style="color:#c8d8d8; padding-left:20px;">
                <li><strong>LLM:</strong> Groq (Llama 3.3 70B)</li>
                <li><strong>Locator AI:</strong> Gemini 2.0 Flash (Google Search grounded)</li>
                <li><strong>Embedding:</strong> all-MiniLM-L6-v2</li>
                <li><strong>Vector DB:</strong> FAISS</li>
                <li><strong>Framework:</strong> Streamlit</li>
                <li><strong>Image AI:</strong> CLIP (OpenAI)</li>
                <li><strong>Translation:</strong> Google Translate API</li>
                <li><strong>TTS:</strong> gTTS</li>
                <li><strong>PDF:</strong> ReportLab</li>
                <li><strong>Data:</strong> Pandas, NumPy</li>
                <li><strong>Visualization:</strong> Altair, Folium</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="about-card">
            <h3>🔗 Links</h3>
            <ul style="color:#c8d8d8; padding-left:20px;">
                <li><strong>GitHub:</strong> <a href="#" style="color:#4ade80;">Link to repository</a></li>
                <li><strong>Deployment:</strong> <a href="#" style="color:#4ade80;">Streamlit Cloud link</a></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="about-card" style="border-left: 4px solid #f97316;">
        <h3>⚠️ Disclaimer</h3>
        <p style="color:#c8d8d8; margin:0;">This is for <strong>educational purposes only</strong>. Always consult your healthcare provider.</p>
        <p style="color:#90a8a8; margin-top:4px; font-style:italic;">Made with ❤️ for cancer patients and their families.</p>
    </div>
    """, unsafe_allow_html=True)

# -------------------- FOOTER --------------------
st.markdown("---")
st.markdown('<p class="disclaimer">NutriCare AI provides general educational information only and is not a substitute for professional medical advice.</p>', unsafe_allow_html=True)