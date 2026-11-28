
import os
import sys
import re
import urllib.parse
from typing import List, Dict, Any

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

# ==========================================================
# 1. ENVIRONMENT AND PATHS
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")

FUSED_DATASET = os.path.join(
    BASE_DIR, "fused_dataset", "final_api_fused.csv"
)

ML_DATASET = os.path.join(
    BASE_DIR, "fused_dataset", "AI_interior_designer.csv"
)

# ==========================================================
# 2. PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="AI Interior Designer",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================================
# 3. DESIGN THEME
# ==========================================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(
            135deg, #f8f5ef 0%, #f2ece3 48%, #faf8f4 100%
        );
        color: #302b27;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg, #fffdfa 0%, #f3ece4 100%
        );
        border-right: 1px solid #e5ddd2;
    }

    .brand {
        font-size: clamp(2.4rem, 4vw, 3.3rem);
        font-weight: 850;
        letter-spacing: -2px;
        color: #70432f;
        line-height: 1.1;
    }

    .brand span {
        color: #b87958;
    }

    .tagline {
        color: #786d62;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .section {
        font-size: 1.4rem;
        font-weight: 800;
        color: #49372d;
        margin: 1.4rem 0 0.8rem 0;
    }

    .card {
        background: rgba(255,255,255,.88);
        border: 1px solid #e8ded2;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
    }

    .area-card {
        background: #f1e7df;
        border: 1px solid #dfcabc;
        border-radius: 14px;
        padding: 14px;
        text-align: center;
        margin: 10px 0;
    }

    .area-number {
        font-size: 1.7rem;
        font-weight: 850;
        color: #8c4d38;
    }

    .area-label {
        font-size: .82rem;
        color: #6d625c;
    }

    .dataset-card {
        background: #fffdf9;
        border: 1px solid #e4ded3;
        border-radius: 14px;
        padding: 15px;
        min-height: 120px;
        margin-bottom: 10px;
    }

    .dataset-name {
        font-weight: 800;
        color: #302d28;
    }

    .dataset-meta {
        color: #746e66;
        font-size: .86rem;
    }

    .source-badge {
        display: inline-block;
        background: #eee8df;
        color: #62584f;
        border-radius: 20px;
        padding: 4px 9px;
        font-size: .72rem;
        margin-top: 7px;
    }

    .small-note {
        color: #77716a;
        font-size: .82rem;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        border-radius: 11px;
        font-weight: 700;
        min-height: 2.8rem;
    }

    div.stButton > button[kind="primary"] {
        background: #a35d43;
        border-color: #a35d43;
    }

    div.stButton > button[kind="primary"]:hover {
        background: #8c4d38;
        border-color: #8c4d38;
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,.85);
        border: 1px solid #e8ded2;
        padding: 15px;
        border-radius: 15px;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255,255,255,.7);
        padding: 7px;
        border: 1px solid #e8ded2;
        border-radius: 14px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# 4. IMPORT RAG AND IMAGE GENERATION
# ==========================================================

try:
    from rag_groq import (
    generate_design,
    generate_interior_image,
    get_api_configuration,
    review_design,
)

    RAG_AVAILABLE = True
    RAG_IMPORT_ERROR = None

except Exception as exc:
    RAG_AVAILABLE = False
    RAG_IMPORT_ERROR = str(exc)

# ==========================================================
# 5. LOAD FUSED DATASET
# ==========================================================

@st.cache_data(show_spinner=False)
def load_fused_dataset(path):
    if not os.path.exists(path):
        return None

    try:
        return pd.read_csv(path)
    except Exception as exc:
        print("Dataset loading error:", exc)
        return None


fused_df = load_fused_dataset(FUSED_DATASET)

# ==========================================================
# 6. DATASET COLUMN DETECTION
# ==========================================================

def find_column(df, candidates):

    if df is None:
        return None

    lower = {
        str(c).strip().lower(): c
        for c in df.columns
    }

    for name in candidates:
        if name.lower() in lower:
            return lower[name.lower()]

    for col in df.columns:
        col_lower = str(col).lower()

        if any(name.lower() in col_lower for name in candidates):
            return col

    return None


ROOM_COL = find_column(
    fused_df,
    ["room_type", "room", "room type", "space_type"]
)

STYLE_COL = find_column(
    fused_df,
    ["style", "interior_style", "design_style"]
)

CATEGORY_COL = find_column(
    fused_df,
    ["category", "product_category", "product_type", "type"]
)

PRODUCT_COL = find_column(
    fused_df,
    ["product_name", "product", "item_name", "name"]
)

PRICE_COL = find_column(
    fused_df,
    ["price", "product_price", "selling_price", "cost"]
)

RATING_COL = find_column(
    fused_df,
    ["rating", "ratings", "average_rating"]
)

IMAGE_COLS = []

if fused_df is not None:
    for col in fused_df.columns:
        name = str(col).lower()

        if "image" in name and (
            "url" in name or "urls" in name
        ):
            IMAGE_COLS.append(col)

# ==========================================================
# 7. ROOM AND BUDGET HELPERS
# ==========================================================

def calculate_room_area(length_ft, width_ft):
    return round(float(length_ft) * float(width_ft), 2)


def room_area_category(area):

    if area < 80:
        return "Compact"

    if area < 150:
        return "Small"

    if area < 250:
        return "Medium"

    if area < 400:
        return "Large"

    return "Very Large"


def budget_limit(budget):

    return {
        "Low Budget": 10000,
        "Medium Budget": 30000,
        "Premium Budget": 75000,
        "Luxury Budget": 200000,
    }.get(budget, 30000)


def normalise_text(value):

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip().lower()


def parse_price(value):

    if value is None:
        return float("nan")

    text = str(value)

    match = re.search(
        r"\d+(?:\.\d+)?",
        text.replace(",", "")
    )

    return float(match.group()) if match else float("nan")

# ==========================================================
# 8. FUSED DATASET RETRIEVAL
# ==========================================================

def retrieve_dataset_records(
    df,
    room,
    style,
    area,
    budget,
    requirements,
    top_k=8,
):

    if df is None or df.empty:
        return pd.DataFrame()

    work = df.copy()

    text_cols = list(
        work.select_dtypes(
            include=["object", "string"]
        ).columns
    )

    if not text_cols:
        return work.head(top_k)

    query_terms = [
        room.lower(),
        style.lower(),
    ]

    if area < 100:
        query_terms += ["small", "compact"]

    elif area < 200:
        query_terms += ["medium", "small"]

    else:
        query_terms += ["large", "spacious"]

    if requirements:
        query_terms += [
            word.lower()
            for word in requirements.split()
            if len(word) >= 4
        ]

    scores = []

    for _, row in work.iterrows():

        row_text = " ".join(
            normalise_text(row[col])
            for col in text_cols
        )

        score = 0

        if (
            ROOM_COL
            and ROOM_COL in work.columns
            and room.lower() in normalise_text(row[ROOM_COL])
        ):
            score += 8

        if (
            STYLE_COL
            and STYLE_COL in work.columns
            and style.lower() in normalise_text(row[STYLE_COL])
        ):
            score += 7

        if (
            CATEGORY_COL
            and CATEGORY_COL in work.columns
            and room.lower() in normalise_text(row[CATEGORY_COL])
        ):
            score += 2

        for term in query_terms:
            if term and term in row_text:
                score += 1

        if PRICE_COL and PRICE_COL in work.columns:

            price = parse_price(row[PRICE_COL])

            if pd.notna(price):
                if price <= budget_limit(budget):
                    score += 1.5
                else:
                    score -= 0.5

        if RATING_COL and RATING_COL in work.columns:

            try:
                if float(row[RATING_COL]) >= 4:
                    score += 0.8
            except Exception:
                pass

        scores.append(score)

    work["_match_score"] = scores

    selected = work.sort_values(
        "_match_score",
        ascending=False
    ).head(top_k)

    return selected.drop(
        columns=["_match_score"],
        errors="ignore"
    )


def dataset_context_text(records, max_chars=7000):

    if records is None or records.empty:
        return "No matching fused dataset records found."

    lines = []

    for idx, (_, row) in enumerate(records.iterrows(), 1):

        parts = []

        for col in records.columns:

            value = row[col]

            if pd.isna(value):
                continue

            if "image" in str(col).lower():
                continue

            value = str(value).strip()

            if not value:
                continue

            if len(value) > 450:
                value = value[:450] + "..."

            parts.append(f"{col}: {value}")

        lines.append(
            f"Record {idx}: " + " | ".join(parts)
        )

    return "\n".join(lines)[:max_chars]

# ==========================================================
# 9. DATASET IMAGE HELPERS
# ==========================================================

def split_image_values(value):

    if value is None:
        return []

    try:
        if pd.isna(value):
            return []
    except Exception:
        pass

    text = str(value).strip()

    if text.lower() in {"", "nan", "none", "null"}:
        return []

    return [
        item.strip().strip("'\"")
        for item in text.replace("\n", "|").split("|")
        if item.strip().startswith(("http://", "https://"))
    ]


@st.cache_data(ttl=3600, show_spinner=False)
def validate_image_url(url):

    try:
        response = requests.get(
            url,
            timeout=5,
            stream=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        content_type = response.headers.get(
            "content-type", ""
        ).lower()

        valid = (
            response.status_code == 200
            and "image/" in content_type
        )

        response.close()

        return valid

    except Exception:
        return False


def dataset_inspiration_images(
    df,
    room,
    style,
    max_images=6,
):

    if df is None or df.empty:
        return []

    records = retrieve_dataset_records(
        df,
        room,
        style,
        150,
        "Medium Budget",
        "interior decor",
        top_k=20,
    )

    found = []
    seen = set()

    for _, row in records.iterrows():

        for col in IMAGE_COLS:

            for url in split_image_values(row.get(col)):

                if url in seen:
                    continue

                seen.add(url)

                if validate_image_url(url):

                    found.append({
                        "url": url,
                        "source": "Fused Dataset",
                    })

                    if len(found) >= max_images:
                        return found

    return found

# ==========================================================
# 10. UNSPLASH API
# ==========================================================

def search_unsplash_live(
    room,
    style,
    requirements="",
    count=6,
):

    if not UNSPLASH_ACCESS_KEY:
        return []

    query = f"{style} {room} interior design {requirements}"

    try:

        response = requests.get(
            "https://api.unsplash.com/search/photos",
            params={
                "client_id": UNSPLASH_ACCESS_KEY,
                "query": query,
                "per_page": min(count, 30),
                "orientation": "landscape",
            },
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get("results", []):

            image_url = (
                item.get("urls", {}).get("regular")
                or item.get("urls", {}).get("small")
            )

            if image_url:

                results.append({
                    "url": image_url,
                    "source": "Unsplash",
                    "author": item.get(
                        "user", {}
                    ).get("name", "Unsplash creator"),
                    "page": item.get(
                        "links", {}
                    ).get("html", ""),
                })

        return results

    except Exception as exc:
        print("Unsplash error:", exc)
        return []

# ==========================================================
# 11. PIXABAY API
# ==========================================================

def search_pixabay_live(
    room,
    style,
    requirements="",
    count=6,
):

    if not PIXABAY_API_KEY:
        return []

    query = f"{style} {room} interior design {requirements}"

    try:

        response = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": PIXABAY_API_KEY,
                "q": query,
                "image_type": "photo",
                "orientation": "horizontal",
                "per_page": max(3, min(count, 20)),
                "safesearch": "true",
            },
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get("hits", []):

            image_url = (
                item.get("largeImageURL")
                or item.get("webformatURL")
            )

            if image_url:

                results.append({
                    "url": image_url,
                    "source": "Pixabay",
                    "author": item.get("user", "Pixabay creator"),
                    "page": item.get("pageURL", ""),
                })

        return results

    except Exception as exc:
        print("Pixabay error:", exc)
        return []

# ==========================================================
# 12. COMBINE INSPIRATION IMAGES
# ==========================================================

def build_inspiration_gallery(
    room,
    style,
    requirements,
    df,
    target=6,
):

    gallery = []
    seen = set()

    sources = [
        dataset_inspiration_images(
            df, room, style, max_images=target
        ),
        search_unsplash_live(
            room, style, requirements, count=target
        ),
        search_pixabay_live(
            room, style, requirements, count=target
        ),
    ]

    for source_items in sources:

        for item in source_items:

            url = item.get("url")

            if not url or url in seen:
                continue

            seen.add(url)
            gallery.append(item)

            if len(gallery) >= target:
                return gallery

    return gallery

# ==========================================================
# 13. REAL MISTRAL API REVIEW
# ==========================================================

# ==========================================================
# GROQ DESIGN REVIEW
# ==========================================================

def call_mistral_live(prompt):
    """
    Backward-compatible function name.
    Uses Groq for the review because the Mistral API
    currently returns 402 Payment Required.
    """
    return review_design(prompt)

    try:

        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mistral-small-latest",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a professional interior design reviewer. "
                            "Review room layouts, furniture scale, circulation, "
                            "colour coordination and budget suitability. "
                            "Give practical suggestions."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "temperature": 0.3,
                "max_tokens": 900,
            },
            timeout=90,
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception as exc:
        return f"Mistral review error: {exc}"

# ==========================================================
# 14. GEOAPIFY LOCATION AND NEARBY SHOPS
# ==========================================================

def search_nearby_places(location, radius=5000):

    result = {
        "center": None,
        "places": [],
        "resolved_address": "",
        "error": None,
        "maps_search_url": "",
    }

    location = (location or "").strip()

    if not location:
        result["error"] = "Please enter a City / Area."
        return result

    encoded = urllib.parse.quote_plus(
        f"furniture stores and interior designers near {location}"
    )

    result["maps_search_url"] = (
        "https://www.google.com/maps/search/?api=1&query="
        + encoded
    )

    if not GEOAPIFY_API_KEY:
        result["error"] = "GEOAPIFY_API_KEY is missing."
        return result

    try:

        geo_response = requests.get(
            "https://api.geoapify.com/v1/geocode/search",
            params={
                "text": location,
                "apiKey": GEOAPIFY_API_KEY,
                "limit": 1,
            },
            timeout=15,
        )

        geo_response.raise_for_status()

        geo_data = geo_response.json()

        features = geo_data.get("features", [])

        if not features:
            result["error"] = "Location not found."
            return result

        first = features[0]

        coordinates = first.get(
            "geometry", {}
        ).get("coordinates", [])

        if len(coordinates) < 2:
            result["error"] = "No valid coordinates returned."
            return result

        longitude = float(coordinates[0])
        latitude = float(coordinates[1])

        result["center"] = {
            "lat": latitude,
            "lng": longitude,
        }

        result["resolved_address"] = (
            first.get("properties", {}).get(
                "formatted", location
            )
        )

        categories = [
            "commercial.furniture",
            "commercial.home_goods",
            "commercial.houseware_and_hardware",
            "commercial.lighting",
            "service.interior_design",
        ]

        unique_places = {}

        for category in categories:

            try:

                places_response = requests.get(
                    "https://api.geoapify.com/v2/places",
                    params={
                        "categories": category,
                        "filter": (
                            f"circle:{longitude},{latitude},{radius}"
                        ),
                        "limit": 20,
                        "apiKey": GEOAPIFY_API_KEY,
                    },
                    timeout=15,
                )

                if places_response.status_code != 200:
                    continue

                places_data = places_response.json()

            except Exception:
                continue

            for feature in places_data.get("features", []):

                props = feature.get("properties", {})

                coords = feature.get(
                    "geometry", {}
                ).get("coordinates", [])

                if len(coords) < 2:
                    continue

                name = (
                    props.get("name")
                    or props.get("address_line1")
                )

                if not name:
                    continue

                lat = props.get("lat", coords[1])
                lon = props.get("lon", coords[0])

                try:
                    lat = float(lat)
                    lon = float(lon)
                except (TypeError, ValueError):
                    continue

                place_id = props.get("place_id") or (
                    f"{name}|{lat:.6f}|{lon:.6f}"
                )

                if place_id in unique_places:
                    continue

                address = (
                    props.get("formatted")
                    or props.get("address_line2")
                    or "Address unavailable"
                )

                maps_query = urllib.parse.quote_plus(
                    f"{name}, {address}"
                )

                unique_places[place_id] = {
                    "name": str(name),
                    "address": str(address),
                    "lat": lat,
                    "lng": lon,
                    "rating": props.get("rating"),
                    "reviews": props.get("reviews"),
                    "maps_url": (
                        "https://www.google.com/maps/search/?api=1&query="
                        + maps_query
                    ),
                }

        result["places"] = list(
            unique_places.values()
        )[:50]

        if not result["places"]:
            result["error"] = (
                "Location found, but no matching nearby shops "
                "were returned by the available map data."
            )

        return result

    except Exception as exc:
        result["error"] = f"Geoapify error: {exc}"
        return result

# ==========================================================
# 15. ROOM LAYOUT
# ==========================================================

def render_room_layout(room, length_ft, width_ft):

    room_lower = room.lower()

    if "living" in room_lower:
        items = [
            "Sofa", "TV Unit", "Coffee Table", "Plant / Decor"
        ]

    elif "bedroom" in room_lower:
        items = [
            "Bed", "Wardrobe", "Side Tables", "Dresser"
        ]

    elif "kitchen" in room_lower:
        items = [
            "Counter", "Sink", "Cooktop", "Storage"
        ]

    elif "dining" in room_lower:
        items = [
            "Dining Table", "Chairs", "Storage", "Pendant Light"
        ]

    elif "study" in room_lower or "office" in room_lower:
        items = [
            "Work Desk", "Chair", "Shelves", "Task Light"
        ]

    elif "kids" in room_lower:
        items = [
            "Bed", "Study Desk", "Storage", "Play Area"
        ]

    else:
        items = [
            "Main Furniture", "Storage", "Decor", "Lighting"
        ]

    cells = "".join(
        f"""
        <div style="
            background:#F4EFE8;
            border:1px solid #DDD2C5;
            border-radius:10px;
            min-height:70px;
            display:flex;
            align-items:center;
            justify-content:center;
            text-align:center;
            font-weight:700;
            color:#4D443D;">
            {item}
        </div>
        """
        for item in items
    )

    st.markdown(
        f"""
        <div class="card">
            <div style="font-weight:800;font-size:1.15rem;">
                Suggested Top-View Arrangement
            </div>

            <div class="small-note">
                {length_ft:g} ft × {width_ft:g} ft ·
                {calculate_room_area(length_ft, width_ft):g} sq.ft
            </div>

            <div style="
                display:grid;
                grid-template-columns:1fr 1fr;
                gap:10px;
                margin-top:14px;
                padding:12px;
                background:#FBF9F5;
                border-radius:12px;">
                {cells}
            </div>

            <div class="small-note" style="text-align:center;margin-top:10px;">
                Conceptual planning view — not an architectural drawing.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==========================================================
# 16. DATASET PRODUCT CARDS
# ==========================================================

def display_dataset_matches(records):

    st.markdown(
        '<div class="section">📦 Products from Your Dataset</div>',
        unsafe_allow_html=True,
    )

    if records is None or records.empty:
        st.info("No matching dataset products were found.")
        return

    cards = records.head(6)
    cols = st.columns(min(3, len(cards)))

    for i, (_, row) in enumerate(cards.iterrows()):

        with cols[i % len(cols)]:

            product_name = (
                str(row.get(PRODUCT_COL, "Dataset Product"))
                if PRODUCT_COL else "Dataset Product"
            )

            category = (
                str(row.get(CATEGORY_COL, ""))
                if CATEGORY_COL else ""
            )

            price = (
                row.get(PRICE_COL)
                if PRICE_COL else None
            )

            rating = (
                row.get(RATING_COL)
                if RATING_COL else None
            )

            price_text = ""

            if price is not None and pd.notna(price):

                parsed = parse_price(price)

                price_text = (
                    f"₹{parsed:,.0f}"
                    if pd.notna(parsed)
                    else str(price)
                )

            rating_text = ""

            if rating is not None and pd.notna(rating):
                rating_text = f"⭐ {rating}"

            st.markdown(
                f"""
                <div class="dataset-card">
                    <div class="dataset-name">
                        {product_name[:100]}
                    </div>
                    <div class="dataset-meta">{category}</div>
                    <div style="margin-top:8px;font-weight:700;color:#8C4D38;">
                        {price_text} {rating_text}
                    </div>
                    <span class="source-badge">Fused Dataset</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ==========================================================
# 17. SESSION STATE
# ==========================================================

defaults = {
    "design_result": None,
    "generated_image": None,
    "image_error": None,
    "dataset_matches": pd.DataFrame(),
    "inspiration_gallery": [],
    "nearby_places": {
        "center": None,
        "places": [],
        "error": None,
    },
    "mistral_result": None,
    "last_query": None,
    "image_history": [],
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================================
# 18. HEADER
# ==========================================================

st.markdown(
    '<div class="brand">AI <span>Interior</span> Designer</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="tagline">
        Design your dream space with AI, real datasets,
        personalized recommendations and visual inspiration.
    </div>
    """,
    unsafe_allow_html=True,
)

if not RAG_AVAILABLE:

    st.error("RAG module could not be loaded.")
    st.code(RAG_IMPORT_ERROR)
    st.info("Keep rag_groq.py in the same folder as app.py.")
    st.stop()

if fused_df is None:

    st.warning(
        "Fused dataset not found. Dataset retrieval "
        "and product recommendations will be unavailable."
    )

# ==========================================================
# 19. TABS
# ==========================================================

tab_designer, tab_dataset, tab_ml = st.tabs(
    [
        "🏠 Design Studio",
        "📊 Dataset Explorer",
        "🧠 ML Model Lab",
    ]
)

# ==========================================================
# 20. DESIGN STUDIO
# ==========================================================

with tab_designer:

    # ------------------------------------------------------
    # SIDEBAR INPUTS
    # ------------------------------------------------------

    with st.sidebar:

        st.markdown("## Design Inputs")
        st.caption(
            "Customize your room and generate a personalized design."
        )

        room = st.selectbox(
            "Room Type",
            [
                "Living Room",
                "Bedroom",
                "Kitchen",
                "Dining Room",
                "Study Room",
                "Kids Room",
                "Home Office",
                "Bathroom",
                "Balcony",
            ],
        )

        style = st.selectbox(
            "Interior Style",
            [
                "Modern",
                "Minimalist",
                "Contemporary",
                "Traditional",
                "Scandinavian",
                "Industrial",
                "Bohemian",
                "Luxury",
                "Rustic",
                "Indian Traditional",
            ],
        )

        st.markdown("### Room Dimensions")

        d1, d2 = st.columns(2)

        with d1:
            length_ft = st.number_input(
                "Length (ft)",
                min_value=3.0,
                max_value=100.0,
                value=12.0,
                step=0.5,
            )

        with d2:
            width_ft = st.number_input(
                "Width (ft)",
                min_value=3.0,
                max_value=100.0,
                value=10.0,
                step=0.5,
            )

        height_ft = st.number_input(
            "Ceiling Height (ft)",
            min_value=7.0,
            max_value=30.0,
            value=10.0,
            step=0.5,
        )

        area_sqft = calculate_room_area(
            length_ft, width_ft
        )

        st.markdown(
            f"""
            <div class="area-card">
                <div class="area-number">{area_sqft:g} sq.ft</div>
                <div class="area-label">
                    Calculated Floor Area · {room_area_category(area_sqft)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        budget = st.selectbox(
            "Budget",
            [
                "Low Budget",
                "Medium Budget",
                "Premium Budget",
                "Luxury Budget",
            ],
        )

        lighting = st.selectbox(
            "Lighting",
            [
                "Natural Light",
                "Warm Lighting",
                "Cool Lighting",
                "Mixed Lighting",
                "Low Light",
            ],
        )

        # NEW COLOUR PREFERENCE

        st.markdown("### 🎨 Visual Preferences")

        color_palette = st.selectbox(
            "Colour Palette",
            [
                "Beige, Cream and Walnut Brown",
                "White and Light Grey",
                "Sage Green and Beige",
                "Terracotta and Cream",
                "Navy Blue and Gold",
                "Pastel Pink and White",
                "Earthy Brown and Olive",
                "Black, White and Grey",
                "Custom / Let AI Decide",
            ],
        )

        # NEW FURNITURE PREFERENCE

        furniture_preference = st.selectbox(
            "Furniture Preference",
            [
                "Minimal Wooden Furniture",
                "Modern Modular Furniture",
                "Luxury Upholstered Furniture",
                "Space-Saving Multifunctional Furniture",
                "Traditional Indian Furniture",
                "Rattan and Natural Furniture",
                "Custom / Let AI Decide",
            ],
        )

        location = st.text_input(
            "City / Area",
            value="Mumbai, Maharashtra",
            placeholder="Example: Mumbai, Maharashtra",
        )

        requirements = st.text_area(
            "Additional Requirements",
            placeholder=(
                "Example: 3-seater sofa, TV unit, plants, "
                "storage and warm lighting."
            ),
            height=100,
        )

        uploaded_file = st.file_uploader(
            "Reference Image (Optional)",
            type=["png", "jpg", "jpeg"],
        )

        if uploaded_file is not None:

            st.image(
                uploaded_file,
                caption="Your reference image",
                use_container_width=True,
            )

        # API CONNECTIONS

        st.markdown("### 🔌 API Connections")

        api_items = [
            (
                "Groq",
                bool(GROQ_API_KEY),
                "LLM design generation",
            ),
            (
                "Mistral",
                bool(MISTRAL_API_KEY),
                "Design review",
            ),
            (
                "Cloudflare Workers AI",
                bool(CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN),
                "FLUX AI image generation",
            ),
            (
                "Unsplash",
                bool(UNSPLASH_ACCESS_KEY),
                "Interior inspiration",
            ),
            (
                "Pixabay",
                bool(PIXABAY_API_KEY),
                "Image inspiration",
            ),
            (
                "Geoapify",
                bool(GEOAPIFY_API_KEY),
                "Nearby furniture and interior shops",
            ),
        ]

        for api_name, connected, purpose in api_items:

            status = (
                "🟢 Connected"
                if connected
                else "🔴 Not configured"
            )

            st.markdown(
                f"**{api_name}** — {status}"
                f"<br><span class='small-note'>{purpose}</span>",
                unsafe_allow_html=True,
            )

        st.divider()

        generate_button = st.button(
            "✨ Generate My Design",
            type="primary",
            use_container_width=True,
        )

        regenerate_image_button = st.button(
            "🎨 Generate New Image",
            use_container_width=True,
        )

    # ------------------------------------------------------
    # USER SUMMARY
    # ------------------------------------------------------

    left, right = st.columns([2.3, 1])

    with left:

        st.markdown(
            f"""
            <div class="card">
                <div style="font-size:1.45rem;font-weight:800;">
                    {room} · {style}
                </div>
                <div class="small-note">
                    {length_ft:g} ft × {width_ft:g} ft ·
                    {area_sqft:g} sq.ft · {budget} · {lighting}
                </div>
                <div class="small-note">
                    Colours: {color_palette} · Furniture: {furniture_preference}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:

        st.markdown(
            f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:1.7rem;font-weight:800;color:#8C4D38;">
                    {area_sqft:g}
                </div>
                <div class="small-note">Square Feet</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ------------------------------------------------------
    # GENERATE COMPLETE DESIGN
    # ------------------------------------------------------

    if generate_button:

        if not GROQ_API_KEY:
            st.error("GROQ_API_KEY is missing in your .env file.")

        else:

            # 1. DATASET RETRIEVAL

            with st.spinner(
                "🔎 Retrieving matching fused dataset records..."
            ):

                dataset_matches = retrieve_dataset_records(
                    fused_df,
                    room,
                    style,
                    area_sqft,
                    budget,
                    requirements,
                    top_k=8,
                )

                st.session_state.dataset_matches = dataset_matches

            dataset_context = dataset_context_text(
                dataset_matches
            )

            # 2. BUILD DESIGN PROMPT

            query = f"""
You are a professional AI interior designer.

USER ROOM DETAILS

Room: {room}
Style: {style}
Length: {length_ft:g} ft
Width: {width_ft:g} ft
Ceiling height: {height_ft:g} ft
Floor area: {area_sqft:g} sq.ft
Area category: {room_area_category(area_sqft)}
Budget: {budget}
Lighting: {lighting}
Colour palette: {color_palette}
Furniture preference: {furniture_preference}
Location: {location}
Requirements: {requirements}

FUSED DATASET RECORDS

{dataset_context}

INSTRUCTIONS

1. Create a practical room design.
2. Respect the exact room dimensions.
3. Suggest suitable furniture and materials.
4. Use relevant retrieved dataset products.
5. Do not invent product prices.
6. Consider walking and circulation space.
7. Follow the user's colour palette and furniture preferences.
8. Provide budget guidance.
9. Explain why the design suits the room.

RETURN THESE SECTIONS

1. Design Concept
2. Space Planning and Furniture Placement
3. Recommended Furniture and Decor
4. Colour and Material Palette
5. Lighting Plan
6. Storage and Space-Saving Ideas
7. Budget Guidance
8. Why This Design Fits the Room
"""

            st.session_state.last_query = query

            # 3. GROQ DESIGN GENERATION

            with st.spinner(
                "🤖 Groq is generating your interior design..."
            ):

                try:

                    st.session_state.design_result = (
                        generate_design(query=query)
                    )

                except Exception as exc:

                    st.session_state.design_result = None
                    st.error(f"Groq generation error: {exc}")

            # 4. MISTRAL REVIEW

            if st.session_state.design_result:

                with st.spinner(
                    "🧠 Groq is reviewing your design..."
                ):

                    review_prompt = f"""
Review this interior design.

Room: {room}
Dimensions: {length_ft:g} × {width_ft:g} ft
Area: {area_sqft:g} sq.ft
Style: {style}
Budget: {budget}

PROPOSED DESIGN:

{st.session_state.design_result}

Review:
- Space utilization
- Furniture scale
- Circulation
- Style consistency
- Budget suitability

Give practical improvements.
"""

                    st.session_state.mistral_result = (
                        call_mistral_live(review_prompt)
                    )

                # 5. CLOUDFLARE IMAGE GENERATION

                with st.spinner(
                    "🎨 Cloudflare is creating your interior image..."
                ):

                    try:

                        image, image_error = (
                            generate_interior_image(
                                room=room,
                                style=style,
                                room_size=(
                                    f"{length_ft:g} ft x "
                                    f"{width_ft:g} ft, "
                                    f"{area_sqft:g} sq.ft, "
                                    f"{height_ft:g} ft ceiling"
                                ),
                                lighting=lighting,
                                description=(
                                    f"Requirements: {requirements}. "
                                    f"Colour palette: {color_palette}. "
                                    f"Furniture preference: "
                                    f"{furniture_preference}."
                                ),
                                budget=budget,
                                design_answer=(
                                    st.session_state.design_result
                                ),
                                color_palette=color_palette,
                                furniture_preference=(
                                    furniture_preference
                                ),
                            )
                        )

                        st.session_state.generated_image = image
                        st.session_state.image_error = image_error

                        if image:
                            st.session_state.image_history.append({
                                "image": image,
                                "style": style,
                                "room": room,
                                "palette": color_palette,
                            })

                    except Exception as exc:

                        st.session_state.generated_image = None
                        st.session_state.image_error = str(exc)

                # 6. INSPIRATION GALLERY

                with st.spinner(
                    "🖼️ Finding matching inspiration images..."
                ):

                    st.session_state.inspiration_gallery = (
                        build_inspiration_gallery(
                            room,
                            style,
                            requirements,
                            fused_df,
                            target=6,
                        )
                    )

                # 7. NEARBY SHOPS

                if location.strip():

                    with st.spinner(
                        "📍 Finding nearby furniture and interior shops..."
                    ):

                        st.session_state.nearby_places = (
                            search_nearby_places(location)
                        )

    # ------------------------------------------------------
    # REGENERATE IMAGE ONLY
    # ------------------------------------------------------

    if regenerate_image_button:

        if not st.session_state.design_result:

            st.warning(
                "Please generate your design first."
            )

        else:

            with st.spinner(
                "🎨 Generating a new image using your selected preferences..."
            ):

                try:

                    new_image, new_error = (
                        generate_interior_image(
                            room=room,
                            style=style,
                            room_size=(
                                f"{length_ft:g} ft x "
                                f"{width_ft:g} ft, "
                                f"{area_sqft:g} sq.ft"
                            ),
                            lighting=lighting,
                            description=(
                                f"Requirements: {requirements}. "
                                f"Colour palette: {color_palette}. "
                                f"Furniture preference: "
                                f"{furniture_preference}."
                            ),
                            budget=budget,
                            design_answer=(
                                st.session_state.design_result
                            ),
                            color_palette=color_palette,
                            furniture_preference=(
                                furniture_preference
                            ),
                        )
                    )

                    st.session_state.generated_image = new_image
                    st.session_state.image_error = new_error

                    if new_image:

                        st.session_state.image_history.append({
                            "image": new_image,
                            "style": style,
                            "room": room,
                            "palette": color_palette,
                        })

                        st.success(
                            "Your new interior image is ready!"
                        )

                    else:

                        st.error(
                            new_error or "Image generation failed."
                        )

                except Exception as exc:

                    st.session_state.image_error = str(exc)

                    st.error(
                        f"Image generation error: {exc}"
                    )

    # ------------------------------------------------------
    # DESIGN RESULTS
    # ------------------------------------------------------

    if st.session_state.design_result:

        st.markdown(
            '<div class="section">✨ AI Design Recommendation</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True,
        )

        st.write(st.session_state.design_result)

        st.markdown("</div>", unsafe_allow_html=True)

        # DATASET PRODUCTS

        display_dataset_matches(
            st.session_state.dataset_matches
        )

        # ROOM LAYOUT

        st.markdown(
            '<div class="section">📐 Room Layout</div>',
            unsafe_allow_html=True,
        )

        render_room_layout(
            room,
            length_ft,
            width_ft,
        )

        # MISTRAL REVIEW

        if st.session_state.mistral_result:

            st.markdown(
                '<div class="section">🧠 Groq Design Review"</div>',
                unsafe_allow_html=True,
            )

            st.write(st.session_state.mistral_result)

        # AI GENERATED IMAGE

        st.markdown(
            '<div class="section">🎨 AI Generated Interior Preview</div>',
            unsafe_allow_html=True,
        )

        if st.session_state.generated_image is not None:

            st.image(
                st.session_state.generated_image,
                caption=(
                    f"{style} {room} · {area_sqft:g} sq.ft"
                ),
                use_container_width=True,
            )

            st.caption(
                f"Colour palette: {color_palette} · "
                f"Furniture: {furniture_preference}"
            )

        elif st.session_state.image_error:

            st.warning(
                "AI image generation was not available."
            )

            with st.expander("Image generation details"):
                st.write(st.session_state.image_error)

        # IMAGE HISTORY

        if st.session_state.image_history:

            st.markdown(
                '<div class="section">🖼️ Previous Generated Designs</div>',
                unsafe_allow_html=True,
            )

            history = st.session_state.image_history[-4:]

            history_cols = st.columns(
                min(2, len(history))
            )

            for i, item in enumerate(reversed(history)):

                with history_cols[i % len(history_cols)]:

                    st.image(
                        item["image"],
                        use_container_width=True,
                    )

                    st.caption(
                        f"{item['style']} · {item['palette']}"
                    )

        # INSPIRATION GALLERY

        st.markdown(
            '<div class="section">🌿 Interior Inspiration Gallery</div>',
            unsafe_allow_html=True,
        )

        gallery = st.session_state.inspiration_gallery

        if gallery:

            cols = st.columns(3)

            for i, item in enumerate(gallery):

                with cols[i % 3]:

                    try:

                        st.image(
                            item["url"],
                            use_container_width=True,
                        )

                        caption = item.get(
                            "source", "Image"
                        )

                        if item.get("author"):
                            caption += (
                                " · " + item["author"]
                            )

                        st.caption(caption)

                        if item.get("page"):
                            st.link_button(
                                "View Source",
                                item["page"],
                                use_container_width=True,
                            )

                    except Exception as exc:

                        st.caption(
                            f"Image could not be displayed: {exc}"
                        )

        else:

            st.info(
                "No inspiration images were returned. "
                "Check your Unsplash and Pixabay API configuration."
            )

        # NEARBY SHOPS

        places_data = st.session_state.nearby_places

        if places_data.get("places"):

            st.markdown(
                '<div class="section">📍 Nearby Furniture & Interior Stores</div>',
                unsafe_allow_html=True,
            )

            center = places_data.get("center")

            map_rows = [
                {
                    "lat": place["lat"],
                    "lon": place["lng"],
                }
                for place in places_data["places"]
                if place.get("lat") is not None
                and place.get("lng") is not None
            ]

            if map_rows:

                st.map(
                    pd.DataFrame(map_rows),
                    zoom=13,
                )

            cols = st.columns(2)

            for i, place in enumerate(
                places_data["places"][:8]
            ):

                with cols[i % 2]:

                    rating = place.get("rating")
                    reviews = place.get("reviews")

                    rating_text = (
                        f"⭐ {rating} ({reviews} reviews)"
                        if rating is not None
                        else "Rating unavailable"
                    )

                    st.markdown(
                        f"""
                        <div class="card">
                            <div style="font-weight:800;">
                                {place['name']}
                            </div>
                            <div class="small-note">
                                {place['address']}
                            </div>
                            <div style="margin-top:7px;">
                                {rating_text}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if place.get("maps_url"):

                        st.link_button(
                            "Open in Google Maps",
                            place["maps_url"],
                            use_container_width=True,
                        )

        elif places_data.get("error"):

            st.warning(
                "Nearby shops could not be retrieved: "
                + str(places_data["error"])
            )

            if places_data.get("maps_search_url"):

                st.link_button(
                    "Search this area in Google Maps",
                    places_data["maps_search_url"],
                )

    else:

        st.markdown(
            """
            <div class="card">
                <div style="font-size:1.4rem;font-weight:800;">
                    Start Designing Your Room
                </div>

                <div class="small-note" style="margin-top:8px;">
                    Select your room dimensions, interior style,
                    colour palette, furniture preference and budget.
                    Your AI designer will retrieve matching dataset
                    records, generate a design recommendation and
                    create a visual interior preview.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==========================================================
# 21. DATASET EXPLORER
# ==========================================================

with tab_dataset:

    st.markdown(
        '<div class="section">📊 Fused Dataset Explorer</div>',
        unsafe_allow_html=True,
    )

    if fused_df is None:

        st.error(
            f"Dataset not found: {FUSED_DATASET}"
        )

    else:

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Records",
            f"{len(fused_df):,}",
        )

        c2.metric(
            "Columns",
            f"{len(fused_df.columns):,}",
        )

        if "api_fusion_status" in fused_df.columns:

            complete = (
                fused_df["api_fusion_status"]
                .astype(str)
                .str.lower()
                .eq("complete")
                .sum()
            )

            c3.metric(
                "Complete API Records",
                int(complete),
            )

        else:

            c3.metric(
                "Complete API Records",
                "N/A",
            )

        st.markdown("### Dataset Filters")

        f1, f2 = st.columns(2)

        with f1:

            if CATEGORY_COL:

                categories = sorted(
                    fused_df[CATEGORY_COL]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                selected_category = st.selectbox(
                    "Category",
                    ["All"] + categories[:200],
                )

            else:

                selected_category = "All"

        with f2:

            search_text = st.text_input(
                "Search Dataset",
                placeholder="Search product, style or category...",
            )

        explorer = fused_df.copy()

        if (
            CATEGORY_COL
            and selected_category != "All"
        ):

            explorer = explorer[
                explorer[CATEGORY_COL]
                .astype(str)
                .eq(selected_category)
            ]

        if search_text.strip():

            mask = explorer.astype(str).apply(
                lambda col: col.str.contains(
                    search_text,
                    case=False,
                    na=False,
                    regex=False,
                )
            ).any(axis=1)

            explorer = explorer[mask]

        st.caption(
            f"Showing {len(explorer):,} records"
        )

        st.dataframe(
            explorer,
            use_container_width=True,
            height=500,
        )

        st.download_button(
            "⬇️ Download Filtered Dataset",
            data=explorer.to_csv(index=False),
            file_name="filtered_interior_dataset.csv",
            mime="text/csv",
        )

# ==========================================================
# 22. MACHINE LEARNING MODEL LAB
# ==========================================================

with tab_ml:

    st.markdown(
        '<div class="section">🧠 Machine Learning Model Lab</div>',
        unsafe_allow_html=True,
    )

    st.write(
        "Train and compare eight classical machine-learning "
        "algorithms using your fused interior-design dataset."
    )

    if not os.path.exists(ML_DATASET):

        st.error(
            f"ML training dataset not found: {ML_DATASET}"
        )

    else:

        try:

            ml_preview = pd.read_csv(ML_DATASET)

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Training Records",
                f"{len(ml_preview):,}",
            )

            c2.metric(
                "Available Features",
                len(ml_preview.columns),
            )

            c3.metric(
                "Algorithms",
                8,
            )

            st.markdown("### Algorithms Included")

            model_names = [
                ("Naive Bayes", "Classification"),
                ("SVM", "Classification"),
                ("Decision Tree", "Classification"),
                ("Random Forest", "Classification"),
                ("Logistic Regression", "Classification"),
                ("Linear Regression", "Regression"),
                ("Multiple Regression", "Regression"),
                ("Polynomial Regression", "Regression"),
            ]

            model_cols = st.columns(4)

            for idx, (name, task) in enumerate(model_names):

                with model_cols[idx % 4]:

                    st.markdown(
                        f"""
                        <div class="dataset-card">
                            <div class="dataset-name">
                                {idx + 1:02d} · {name}
                            </div>
                            <div class="dataset-meta">
                                {task}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown("### Model Evaluation")

            st.caption(
                "Classification models predict design style. "
                "Regression models estimate the dataset match score. "
                "Evaluation depends on the training data and test split."
            )

            if st.button(
                "🚀 Train and Evaluate All 8 Models",
                type="primary",
                use_container_width=True,
            ):

                with st.spinner(
                    "Preparing features and training models..."
                ):

                    try:

                        from ml_models import train_evaluate

                        ml_results, _, ml_info = (
                            train_evaluate(ML_DATASET)
                        )

                        st.session_state["ml_model_results"] = (
                            ml_results
                        )

                        st.session_state["ml_model_info"] = (
                            ml_info
                        )

                    except Exception as exc:

                        st.error(
                            f"Model training failed: {exc}"
                        )

                        st.info(
                            "Check ml_models.py and install "
                            "the required packages from requirements.txt."
                        )

            if "ml_model_results" in st.session_state:

                result_df = st.session_state[
                    "ml_model_results"
                ]

                st.success(
                    f"Evaluation complete · {len(result_df)} models"
                )

                st.dataframe(
                    result_df,
                    use_container_width=True,
                    hide_index=True,
                )

                if "Task" in result_df.columns:

                    class_results = result_df[
                        result_df["Task"].astype(str).str.startswith(
                            "Classification"
                        )
                    ]

                    reg_results = result_df[
                        result_df["Task"].astype(str).str.startswith(
                            "Regression"
                        )
                    ]

                    if (
                        not class_results.empty
                        and "F1" in class_results.columns
                    ):

                        st.markdown(
                            "#### Classification Comparison · F1 Score"
                        )

                        st.bar_chart(
                            class_results.set_index("Model")[["F1"]]
                        )

                    if (
                        not reg_results.empty
                        and "RMSE" in reg_results.columns
                    ):

                        st.markdown(
                            "#### Regression Comparison · RMSE"
                        )

                        st.bar_chart(
                            reg_results.set_index("Model")[["RMSE"]]
                        )

                st.download_button(
                    "⬇️ Download Model Evaluation",
                    data=result_df.to_csv(index=False),
                    file_name="ml_model_evaluation.csv",
                    mime="text/csv",
                )

                st.caption(
                    "Metrics depend on the dataset, target variables "
                    "and train/test split. They do not guarantee "
                    "real-world performance."
                )

        except Exception as exc:

            st.error(
                f"Could not read ML training dataset: {exc}"
            )

# ==========================================================
# 23. FOOTER
# ==========================================================

st.divider()

st.caption(
    "AI Interior Designer · Fused Dataset + Keyword RAG + "
    "Groq Design Generation + Groq Design Review + "
    "Cloudflare FLUX + Unsplash + Pixabay + Geoapify"
)
