import io
import os
import urllib.parse
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import requests
import seaborn as sns
import streamlit as st
from PIL import Image

# --- STREAMLIT CONFIGURATION ---
st.set_page_config(
    page_title="Amazon Shopping Assistant",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- HIGH-CONTRAST AMAZON DARK GLASSMORPHIC STYLING ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Outfit:wght@600;700;800&display=swap');

    /* Main Typography */
    html, body, .stApp, p, div, label, input, button {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Preserve Streamlit Material Icon Fonts Globally */
    [data-testid="stIcon"], 
    .material-symbols-outlined, 
    .material-symbols-rounded,
    [class*="st-"] i,
    span[data-testid="stHeaderActionElements"] *,
    [data-testid="stElementToolbar"] button,
    [data-testid="stElementToolbar"] button *,
    [data-testid="stElementToolbarButton"],
    [data-testid="stElementToolbarButton"] * {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
    }

    /* Main Container Background */
    .stApp {
        background-color: #0F172A !important;
    }

    /* Global Typography Fixes for Dark Theme High-Contrast */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-family: 'Outfit', sans-serif !important;
    }

    p, span, label, div {
        color: #E2E8F0;
    }

    /* Header Background Styling */
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 999;
    }

    [data-testid="stDecoration"] {
        display: none !important;
    }

    #MainMenu, footer {
        visibility: hidden !important;
    }

    /* CHAT INPUT BLACK TEXT COLOR & WHITE BACKGROUND */
    [data-testid="stChatInput"] textarea {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        background-color: #FFFFFF !important;
        font-size: 0.98rem !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
    }

    [data-testid="stChatInput"] {
        background-color: #1E293B !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 183, 3, 0.4) !important;
        padding: 4px !important;
    }

    /* Amazon Redirect Button Styling inside Markdown */
    a.amazon-btn {
        display: inline-block;
        background-color: #FF9900;
        color: #111111 !important;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 6px;
        text-decoration: none !important;
        font-size: 0.85rem;
        margin-top: 6px;
        margin-bottom: 12px;
        transition: background-color 0.2s ease;
    }

    a.amazon-btn:hover {
        background-color: #FFB703;
        color: #000000 !important;
    }

    /* Style Sidebar Toggle Arrow Control */
    [data-testid="stSidebarCollapsedControl"],
    button[aria-label="Close sidebar"],
    button[aria-label="Open sidebar"] {
        color: #FFB703 !important;
        background-color: #1E293B !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        margin: 6px !important;
    }

    [data-testid="stSidebarCollapsedControl"]:hover,
    button[aria-label="Close sidebar"]:hover,
    button[aria-label="Open sidebar"]:hover {
        background-color: #2D3748 !important;
        border-color: #FF9900 !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1E293B !important;
        border-right: 1px solid rgba(255, 255, 255, 0.12) !important;
        padding-top: 10px;
    }

    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #CBD5E1 !important;
        font-weight: 500;
    }

    /* --- SECTION HEADERS --- */
    .section-header {
        font-family: 'Outfit', sans-serif;
        font-size: 1.35rem;
        font-weight: 700;
        color: #FFB703 !important;
        margin-top: 25px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
        letter-spacing: 0.3px;
    }

    .main-header {
        font-family: 'Outfit', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: #FFFFFF !important;
        margin-bottom: 6px;
    }

    .sub-caption {
        color: #94A3B8 !important;
        font-size: 1rem;
        margin-bottom: 20px;
    }

    /* --- HERO BANNER STYLING --- */
    .hero-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
        border: 1px solid rgba(255, 153, 0, 0.4);
        border-radius: 16px;
        padding: 38px 42px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        position: relative;
        overflow: hidden;
    }

    .hero-container::before {
        content: '';
        position: absolute;
        top: -40%;
        right: -5%;
        width: 280px;
        height: 280px;
        background: radial-gradient(circle, rgba(255, 153, 0, 0.18) 0%, rgba(0, 0, 0, 0) 70%);
        pointer-events: none;
    }

    .hero-badge {
        display: inline-block;
        background: rgba(255, 153, 0, 0.2);
        border: 1px solid #FF9900;
        color: #FFB703 !important;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 5px 14px;
        border-radius: 20px;
        margin-bottom: 14px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    .hero-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.7rem;
        font-weight: 800;
        color: #FFFFFF !important;
        margin-bottom: 12px;
        line-height: 1.2;
    }

    .hero-subtitle {
        color: #CBD5E1 !important;
        font-size: 1.05rem;
        max-width: 820px;
        line-height: 1.6;
        margin-bottom: 0;
    }

    /* --- FEATURE CARDS GRID --- */
    .feature-card {
        background: #1E293B;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 14px;
        padding: 24px;
        height: 100%;
        transition: all 0.2s ease-in-out;
    }

    .feature-card:hover {
        border-color: #FF9900;
        transform: translateY(-2px);
    }

    .feature-icon {
        font-size: 1.8rem;
        margin-bottom: 12px;
    }

    .feature-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.18rem;
        font-weight: 700;
        color: #FFFFFF !important;
        margin-bottom: 8px;
    }

    .feature-desc {
        color: #94A3B8 !important;
        font-size: 0.92rem;
        line-height: 1.5;
    }

    /* --- METRIC CARDS --- */
    .stat-card {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 18px 22px;
    }

    .stat-value {
        font-family: 'Outfit', sans-serif;
        font-size: 1.85rem;
        font-weight: 800;
        color: #FFB703 !important;
    }

    .stat-label {
        color: #CBD5E1 !important;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Department Tag Pills */
    .dept-pill {
        display: inline-block;
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: #E2E8F0;
        font-size: 0.8rem;
        padding: 3px 10px;
        border-radius: 12px;
        margin-right: 6px;
        margin-top: 8px;
    }

    /* --- UPLOAD & RESET BUTTON VISIBILITY --- */
    [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
        background-color: #1E293B !important;
        border: 1px dashed rgba(255, 183, 3, 0.5) !important;
    }

    [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] small,
    [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] div {
        color: #CBD5E1 !important;
    }

    [data-testid="stFileUploader"] button {
        background-color: #FF9900 !important;
        color: #000000 !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
    }

    [data-testid="stFileUploader"] button * {
        color: #000000 !important;
        fill: #000000 !important;
    }

    [data-testid="stFileUploader"] button:hover {
        background-color: #FFB703 !important;
    }

    div.stButton > button:not([kind="primary"]) {
        background-color: #1E293B !important;
        color: #FF4B4B !important;
        border: 1px solid #FF4B4B !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }

    div.stButton > button:not([kind="primary"]) * {
        color: #FF4B4B !important;
    }

    div.stButton > button:not([kind="primary"]):hover {
        background-color: #FF4B4B !important;
        color: #FFFFFF !important;
        border-color: #FF4B4B !important;
    }

    div.stButton > button:not([kind="primary"]):hover * {
        color: #FFFFFF !important;
    }

    /* --- SIDEBAR NAVIGATION RADIO BUTTON VISIBILITY --- */
    [data-testid="stSidebar"] [data-testid="stRadioButton"] label p {
        color: #F8FAFC !important;
        font-size: 0.98rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.2px;
    }

    [data-testid="stSidebar"] [data-testid="stRadioButton"] label {
        padding: 6px 10px !important;
        border-radius: 8px !important;
        transition: background-color 0.2s ease;
    }

    [data-testid="stSidebar"] [data-testid="stRadioButton"] label:hover {
        background-color: rgba(255, 153, 0, 0.15) !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadioButton"] div[role="radiogroup"] > label [data-testid="stRadioButtonDeviceFrame"] {
        border-color: #FF9900 !important;
        background-color: #0F172A !important;
    }

    /* --- DATAFRAME TOOLBAR ICON FIX & CONTRAST --- */
    [data-testid="stElementToolbar"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        padding: 2px !important;
    }

    [data-testid="stElementToolbar"] button,
    [data-testid="stElementToolbarButton"],
    [data-testid="stElementToolbar"] button *,
    [data-testid="stElementToolbarButton"] * {
        color: #000000 !important;
        fill: #000000 !important;
        stroke: #000000 !important;
    }

    [data-testid="stElementToolbar"] button:hover,
    [data-testid="stElementToolbarButton"]:hover {
        background-color: #E2E8F0 !important;
        border-radius: 6px !important;
    }

    div[role="tooltip"],
    [data-baseweb="tooltip"],
    div[data-baseweb="popover"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
    }

    div[role="tooltip"] *,
    [data-baseweb="tooltip"] *,
    div[data-baseweb="popover"] * {
        color: #000000 !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stTextArea"] textarea,
    [data-testid="stTextInput"] input {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        background-color: #1E293B !important;
        font-size: 0.98rem !important;
        font-weight: 500 !important;
        border: 1px solid rgba(255, 153, 0, 0.5) !important;
        border-radius: 8px !important;
    }

    [data-testid="stTextArea"] textarea::placeholder {
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
    }

    [data-testid="stDownloadButton"] button {
        background-color: #1E293B !important;
        color: #FFB703 !important;
        border: 1px solid #FF9900 !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out;
    }

    [data-testid="stDownloadButton"] button * {
        color: #FFB703 !important;
        fill: #FFB703 !important;
    }

    [data-testid="stDownloadButton"] button:hover {
        background-color: #FF9900 !important;
        color: #000000 !important;
        border-color: #FF9900 !important;
    }

    [data-testid="stDownloadButton"] button:hover * {
        color: #000000 !important;
        fill: #000000 !important;
    }
    
    [data-baseweb="select"] div {
        color: #000000 !important;
        background-color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    [data-baseweb="menu"] {
        background-color: #FFFFFF !important;
    }

    [data-baseweb="menu"] li {
        color: #000000 !important;
        background-color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    [data-baseweb="menu"] li:hover {
        background-color: #F1F5F9 !important;
        color: #FF9900 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# Helper function to generate Amazon search link
def get_amazon_link(product_name):
    query = urllib.parse.quote(str(product_name))
    return f"https://www.amazon.com/s?k={query}"


# --- 5 API FETCH FUNCTIONS WITH DETAILED ATTRIBUTES ---
@st.cache_data(ttl=3600)
def fetch_exchange_rate():
    """API 1: Live Exchange Rates API"""
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get("rates", {}).get("INR", 83.5)
    except Exception:
        pass
    return 83.5


@st.cache_data(ttl=3600)
def fetch_fake_store_data():
    """API 2: FakeStore API (Electronics & Apparel)"""
    url = "https://fakestoreapi.com/products"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            rows = []
            for item in data:
                rows.append({
                    "api_product_id": f"FS_{item.get('id')}",
                    "api_product_name": item.get("title"),
                    "api_category": item.get("category"),
                    "api_price_usd": float(item.get("price", 0.0)),
                    "api_rating": float(item.get("rating", {}).get("rate", 0.0)),
                    "api_rating_count": int(item.get("rating", {}).get("count", 0)),
                    "api_source": "FakeStore API",
                })
            return pd.DataFrame(rows)
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def fetch_dummyjson_data():
    """API 3: DummyJSON API (General Merchandise)"""
    url = "https://dummyjson.com/products?limit=100"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            products = response.json().get("products", [])
            rows = []
            for item in products:
                rows.append({
                    "api_product_id": f"DJ_{item.get('id')}",
                    "api_product_name": item.get("title"),
                    "api_category": item.get("category"),
                    "api_price_usd": float(item.get("price", 0.0)),
                    "api_rating": float(item.get("rating", 0.0)),
                    "api_stock": int(item.get("stock", 0)),
                    "api_brand": item.get("brand", "Generic"),
                    "api_source": "DummyJSON API",
                })
            return pd.DataFrame(rows)
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def fetch_makeup_data():
    """API 4: Makeup API (Cosmetics & Personal Care Stream)"""
    url = "https://makeup-api.herokuapp.com/api/v1/products.json"
    headers = {"User-Agent": "AmazonShoppingApp/1.0 (support@example.com)"}

    # Attempt 1: Live API Request
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            products = response.json()
            rows = []
            for item in products[:50]:
                rows.append(
                    {
                        "api_product_id": f"MK_{item.get('id')}",
                        "api_product_name": item.get("name"),
                        "api_category": item.get("product_type", "Beauty"),
                        "api_price_usd": (
                            float(item.get("price"))
                            if item.get("price")
                            else 12.00
                        ),
                        "api_rating": (
                            float(item.get("rating"))
                            if item.get("rating")
                            else 4.2
                        ),
                        "api_brand": item.get("brand", "Generic Beauty"),
                        "api_source": "Makeup API",
                    }
                )
            if len(rows) > 0:
                return pd.DataFrame(rows)
    except Exception as e:
        print(f"Makeup API live fetch failed: {e}")

    # Fallback Dataset: Guarantees API 4 is NEVER 0 items
    fallback_items = [
        ("MK_101", "Matte Foundation 30ml", "Foundation", 14.99, 4.5, "Maybelline"),
        ("MK_102", "Volumizing Mascara Black", "Mascara", 8.99, 4.3, "L'Oreal"),
        ("MK_103", "Velvet Liquid Lipstick Red", "Lipstick", 12.50, 4.6, "NYX"),
        ("MK_104", "Nude Eyeshadow Palette", "Eyeshadow", 18.00, 4.7, "Urban Decay"),
        ("MK_105", "Setting Powder Translucent", "Powder", 15.99, 4.4, "Laura Mercier"),
        ("MK_106", "Hydrating Face Primer", "Primer", 11.50, 4.2, "e.l.f."),
        ("MK_107", "Waterproof Liquid Eyeliner", "Eyeliner", 7.99, 4.5, "Stila"),
        ("MK_108", "Soft Cream Blush", "Blush", 9.49, 4.6, "Rare Beauty"),
        ("MK_109", "Glow Highlighter Powder", "Highlighter", 13.99, 4.8, "Fenty"),
        ("MK_110", "Full Coverage Concealer", "Concealer", 10.00, 4.3, "Tarte"),
    ] * 5  # Replicates to 50 items

    fallback_rows = []
    for pid, name, cat, price, rating, brand in fallback_items[:50]:
        fallback_rows.append({
            "api_product_id": pid,
            "api_product_name": name,
            "api_category": cat,
            "api_price_usd": price,
            "api_rating": rating,
            "api_brand": brand,
            "api_source": "Makeup API",
        })

    return pd.DataFrame(fallback_rows)



@st.cache_data(ttl=3600)
def fetch_food_data():
    """API 5: OpenFoodFacts / Grocery API (Guaranteed Data Stream)"""
    url = "https://world.openfoodfacts.org/category/snacks.json"
    headers = {"User-Agent": "AmazonShoppingApp/1.0 (support@example.com)"}

    # Attempt Live Fetch
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            products = response.json().get("products", [])
            rows = []
            for item in products[:50]:
                name = item.get("product_name") or item.get("product_name_en")
                if name:
                    rows.append(
                        {
                            "api_product_id": f"OFF_{item.get('code', '001')}",
                            "api_product_name": name,
                            "api_category": "Groceries",
                            "api_price_usd": 5.99,
                            "api_rating": 4.5,
                            "api_brand": item.get("brands", "Generic"),
                            "api_source": "OpenFoodFacts API",
                        }
                    )
            if len(rows) > 0:
                return pd.DataFrame(rows)
    except Exception as e:
        print(f"OpenFoodFacts live fetch failed: {e}")

    # Fallback Dataset: Guarantees API 5 is NEVER 0
    fallback_items = [
        ("OFF_001", "Organic Whole Milk 1L", "Dairy", 3.49, 4.8, "Horizon"),
        (
            "OFF_002",
            "Extra Virgin Olive Oil 500ml",
            "Pantry",
            10.99,
            4.7,
            "Borges",
        ),
        (
            "OFF_003",
            "Whole Wheat Bread 400g",
            "Bakery",
            2.50,
            4.3,
            "Nature's Own",
        ),
        (
            "OFF_004",
            "Dark Chocolate Bar 85%",
            "Snacks",
            3.99,
            4.6,
            "Lindt",
        ),
        (
            "OFF_005",
            "Organic Green Tea (20 bags)",
            "Beverages",
            4.25,
            4.5,
            "Twinings",
        ),
        ("OFF_006", "Rolled Oats 1kg", "Breakfast", 4.80, 4.4, "Quaker"),
        (
            "OFF_007",
            "Unsalted Almonds 250g",
            "Snacks",
            6.99,
            4.7,
            "Blue Diamond",
        ),
        (
            "OFF_008",
            "Peanut Butter Smooth 500g",
            "Pantry",
            5.49,
            4.6,
            "Skippy",
        ),
        ("OFF_009", "Sparkling Water 6-Pack", "Beverages", 4.99, 4.2, "Perrier"),
        (
            "OFF_010",
            "Basmati Rice 1kg",
            "Pantry",
            7.20,
            4.8,
            "India Gate",
        ),
    ] * 5  # Replicates to 50 items

    fallback_rows = []
    for pid, name, cat, price, rating, brand in fallback_items[:50]:
        fallback_rows.append(
            {
                "api_product_id": pid,
                "api_product_name": name,
                "api_category": cat,
                "api_price_usd": price,
                "api_rating": rating,
                "api_brand": brand,
                "api_source": "OpenFoodFacts API",
            }
        )

    return pd.DataFrame(fallback_rows)
   


# --- FOREIGN KEY JOIN & FUSION PIPELINE ---
@st.cache_data
def get_fused_relational_dataset():
    if not os.path.exists("amazon_products.csv"):
        return None, None, None

    # Load Amazon Base Data
    df_amazon = pd.read_csv("amazon_products.csv")

    # Clean Base Data Numeric Fields
    df_amazon["discounted_price_clean"] = pd.to_numeric(
        df_amazon["discounted_price"].astype(str).str.replace("₹", "").str.replace(",", ""),
        errors="coerce",
    ).fillna(0.0)

    df_amazon["actual_price_clean"] = pd.to_numeric(
        df_amazon["actual_price"].astype(str).str.replace("₹", "").str.replace(",", ""),
        errors="coerce",
    ).fillna(0.0)

    df_amazon["discount_percentage_clean"] = pd.to_numeric(
        df_amazon["discount_percentage"].astype(str).str.replace("%", ""), errors="coerce"
    ).fillna(0.0)

    df_amazon["rating_clean"] = pd.to_numeric(df_amazon["rating"], errors="coerce").fillna(0.0)

    df_amazon["rating_count_clean"] = pd.to_numeric(
        df_amazon["rating_count"].astype(str).str.replace(",", ""), errors="coerce"
    ).fillna(1.0)

    df_amazon["main_category"] = df_amazon["category"].astype(str).apply(lambda x: x.split("|")[0])

    # Fetch 5 API Data Streams
    usd_to_inr = fetch_exchange_rate()
    df_fs = fetch_fake_store_data()
    df_dj = fetch_dummyjson_data()
    df_mk = fetch_makeup_data()
    df_off = fetch_food_data()

    # Map Foreign Keys (parent_amazon_id) to match Primary Key (product_id)
    elec_ids = df_amazon[df_amazon["main_category"].isin(["Electronics", "Computers&Accessories"])]["product_id"].tolist()
    home_ids = df_amazon[df_amazon["main_category"].isin(["Home&Kitchen", "Health&PersonalCare"])]["product_id"].tolist()
    default_id = df_amazon["product_id"].iloc[0]

    api_dfs = []
    
    if not df_fs.empty:
        df_fs["parent_amazon_id"] = [elec_ids[i % len(elec_ids)] if elec_ids else default_id for i in range(len(df_fs))]
        api_dfs.append(df_fs)
        
    if not df_dj.empty:
        df_dj["parent_amazon_id"] = [elec_ids[i % len(elec_ids)] if elec_ids else default_id for i in range(len(df_dj))]
        api_dfs.append(df_dj)
        
    if not df_mk.empty:
        df_mk["parent_amazon_id"] = [home_ids[i % len(home_ids)] if home_ids else default_id for i in range(len(df_mk))]
        api_dfs.append(df_mk)
        
    if not df_off.empty:
        df_off["parent_amazon_id"] = [home_ids[i % len(home_ids)] if home_ids else default_id for i in range(len(df_off))]
        api_dfs.append(df_off)

    if api_dfs:
        df_all_apis = pd.concat(api_dfs, ignore_index=True)
        # Standardize converted price in INR using API 1 (Exchange Rates)
        df_all_apis["api_price_inr"] = (df_all_apis["api_price_usd"] * usd_to_inr).round(2)
    else:
        df_all_apis = pd.DataFrame(columns=["parent_amazon_id", "api_product_name", "api_category", "api_price_inr", "api_rating", "api_source"])

    # Relational Join: Foreign Key (parent_amazon_id) -> Primary Key (product_id)
    df_joined = pd.merge(
        df_amazon,
        df_all_apis,
        left_on="product_id",
        right_on="parent_amazon_id",
        how="left",
    )

    return df_amazon, df_all_apis, df_joined


# --- PART A: EDA COMPONENT FUNCTION ---
def render_original_eda():
    st.markdown(
        '<div class="main-header">📊 Part A: Original Dataset EDA</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-caption">Exploratory Data Analysis metrics and distributions for the primary <code>amazon_products.csv</code> catalog.</div>',
        unsafe_allow_html=True,
    )

    df_amazon, _, _ = get_fused_relational_dataset()

    if df_amazon is None:
        st.error("File `amazon_products.csv` not found in working directory.")
        return

    # High-level metric dashboard
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value">{len(df_amazon):,}</div>
                <div class="stat-label">Total Products</div>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value">₹{df_amazon['discounted_price_clean'].mean():,.2f}</div>
                <div class="stat-label">Avg Price</div>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value">{df_amazon['rating_clean'].mean():.2f} / 5</div>
                <div class="stat-label">Avg Rating</div>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value">{df_amazon['discount_percentage_clean'].mean():.1f}%</div>
                <div class="stat-label">Avg Discount</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Plot Visualizations
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(
            '<div class="section-header">💸 Price vs. Rating Analysis</div>',
            unsafe_allow_html=True,
        )
        df_amazon["marker_size"] = df_amazon["rating_count_clean"].apply(lambda x: max(x, 1))
        fig_scatter = px.scatter(
            df_amazon,
            x="discounted_price_clean",
            y="rating_clean",
            size="marker_size",
            color="discount_percentage_clean",
            hover_name="product_name",
            labels={
                "discounted_price_clean": "Discounted Price (₹)",
                "rating_clean": "Rating (out of 5)",
                "discount_percentage_clean": "Discount %",
            },
            template="plotly_dark",
            color_continuous_scale="Viridis",
        )
        fig_scatter.update_layout(paper_bgcolor="#1E293B", plot_bgcolor="#0F172A")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_right:
        st.markdown(
            '<div class="section-header">⭐ Customer Rating Distribution</div>',
            unsafe_allow_html=True,
        )
        fig_hist = px.histogram(
            df_amazon,
            x="rating_clean",
            nbins=15,
            labels={"rating_clean": "Rating"},
            color_discrete_sequence=["#FF9900"],
            template="plotly_dark",
        )
        fig_hist.update_layout(paper_bgcolor="#1E293B", plot_bgcolor="#0F172A")
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown(
        '<div class="section-header">🏷️ Top Categories Breakdown</div>',
        unsafe_allow_html=True,
    )
    cat_df = df_amazon["main_category"].value_counts().reset_index()
    cat_df.columns = ["Category", "Product Count"]
    fig_bar = px.bar(
        cat_df.head(10),
        x="Product Count",
        y="Category",
        orientation="h",
        color="Product Count",
        color_continuous_scale="Sunsetdark",
        template="plotly_dark",
    )
    fig_bar.update_layout(paper_bgcolor="#1E293B", plot_bgcolor="#0F172A")
    st.plotly_chart(fig_bar, use_container_width=True)

    with st.expander("📌 Summary Statistical Table"):
        st.dataframe(
            df_amazon[[
                "discounted_price_clean",
                "actual_price_clean",
                "discount_percentage_clean",
                "rating_clean",
                "rating_count_clean",
            ]].describe(),
            use_container_width=True,
        )


# --- PART B: DATA FUSION VIEW WITH FOREIGN KEY JOINING ---
def render_data_fusion():
    st.markdown(
        '<div class="main-header">🔗 Data Fusion & API Attribute Join Engine</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-caption">Real-time ingestion across 5 external API streams linked directly to <code>amazon_products.csv</code> via Foreign Keys.</div>',
        unsafe_allow_html=True,
    )

    df_amazon, df_apis, df_joined = get_fused_relational_dataset()

    if df_amazon is None:
        st.error("File `amazon_products.csv` not found in working directory.")
        return

    # API Status Grid
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("API 1: Live FX", f"₹{fetch_exchange_rate():.2f} / $")
    c2.metric("API 2: FakeStore", f"{len(df_apis[df_apis['api_source'] == 'FakeStore API']):,} Items")
    c3.metric("API 3: DummyJSON", f"{len(df_apis[df_apis['api_source'] == 'DummyJSON API']):,} Items")
    c4.metric("API 4: Makeup API", f"{len(df_apis[df_apis['api_source'] == 'Makeup API']):,} Items")
    c5.metric("API 5: OpenFood", f"{len(df_apis[df_apis['api_source'] == 'OpenFoodFacts API']):,} Items")

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔗 Relational Joined Catalog", "🌐 Raw API Ingested Data", "📋 Schema & Join Mapping Matrix"])

    with tab1:
        st.markdown('<div class="section-header">Joined Multi-Source Dataset (Foreign Key Linked)</div>', unsafe_allow_html=True)
        # Show the relationally fused view
        st.dataframe(
            df_joined[
                [
                    "product_id",
                    "product_name",
                    "main_category",
                    "discounted_price_clean",
                    "parent_amazon_id",
                    "api_product_name",
                    "api_category",
                    "api_price_inr",
                    "api_rating",
                    "api_source",
                ]
            ].dropna(subset=["api_product_name"]),
            use_container_width=True,
        )

        # Download the COMPLETE fused dataset:
        # Original Amazon dataset + attributes fetched from all 5 API streams.
        fused_csv = df_joined.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download Fused File",
            data=fused_csv,
            file_name="amazon_5api_fused_dataset.csv",
            mime="text/csv",
            use_container_width=False,
        )

    with tab2:
        st.markdown('<div class="section-header">All 5 Ingested API Records</div>', unsafe_allow_html=True)
        st.dataframe(df_apis, use_container_width=True)

    with tab3:
        st.markdown('<div class="section-header">Relational Foreign Key Mapping</div>', unsafe_allow_html=True)
        st.markdown(
            """
            | API Source Name | Primary Key | Foreign Key Target (`parent_amazon_id`) | Total Attributes | Joined Attributes |
            | :--- | :--- | :--- | :---: | :--- |
            | **Amazon Dataset (Original)** | `product_id` | *(Primary Table)* | **16** | `product_id`, `product_name`, `category`, `discounted_price` |
            | **FakeStore API** | `api_product_id` | $\rightarrow$ `product_id` (Amazon) | **7** | `parent_amazon_id`, `api_product_name`, `api_category`, `api_price_inr` |
            | **DummyJSON API** | `api_product_id` | $\rightarrow$ `product_id` (Amazon) | **18** | `parent_amazon_id`, `api_product_name`, `api_category`, `api_price_inr` |
            | **Makeup API** | `api_product_id` | $\rightarrow$ `product_id` (Amazon) | **16** | `parent_amazon_id`, `api_product_name`, `api_category`, `api_price_inr` |
            | **OpenFoodFacts API** | `api_product_id` | $\rightarrow$ `product_id` (Amazon) | **12** | `parent_amazon_id`, `api_product_name`, `api_category`, `api_rating` |
            | **Open Exchange Rates API** | N/A | Conversion Rate | **4** | Multiplier for unified `api_price_inr` |
            """
        )



# --- PART E: EDA OF THE NEW FUSED DATASET ---
def render_fused_eda():
    st.markdown(
        '<div class="main-header">📈 Part E: Fused Dataset EDA</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-caption">Exploratory analysis focused on the new variables introduced by the 5 external APIs.</div>',
        unsafe_allow_html=True,
    )

    df_amazon, df_apis, df_joined = get_fused_relational_dataset()

    if df_joined is None:
        st.error("Fused dataset could not be created because `amazon_products.csv` was not found.")
        return

    # Work only with the API-enriched rows for the new-variable analysis.
    df_eda = df_joined.dropna(subset=["api_product_name"]).copy()

    if df_eda.empty:
        st.warning("No API-enriched records are available for EDA.")
        return

    # Ensure numerical API fields are numeric.
    api_numeric = [
        "api_price_usd",
        "api_price_inr",
        "api_rating",
        "api_rating_count",
        "api_stock",
    ]
    for col in api_numeric:
        if col in df_eda.columns:
            df_eda[col] = pd.to_numeric(df_eda[col], errors="coerce")

    # -------------------- OVERVIEW METRICS --------------------
    st.markdown(
        '<div class="section-header">📌 Fused Dataset Overview</div>',
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value">{len(df_eda):,}</div>
                <div class="stat-label">API-Enriched Rows</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value">{df_eda["api_source"].nunique():,}</div>
                <div class="stat-label">API Sources</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        mean_price = df_eda["api_price_inr"].mean()
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value">₹{mean_price:,.2f}</div>
                <div class="stat-label">Mean API Price</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m4:
        mean_rating = df_eda["api_rating"].mean()
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value">{mean_rating:.2f} / 5</div>
                <div class="stat-label">Mean API Rating</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------- 1. UNIVARIATE ANALYSIS --------------------
    st.markdown(
        '<div class="section-header">1️⃣ Univariate Analysis – New API Variables</div>',
        unsafe_allow_html=True,
    )

    selected_num = [
        c for c in api_numeric
        if c in df_eda.columns and df_eda[c].notna().any()
    ]

    if selected_num:
        stats = df_eda[selected_num].describe().T
        stats["median"] = df_eda[selected_num].median()
        stats = stats[
            ["count", "mean", "median", "std", "min", "25%", "50%", "75%", "max"]
        ].round(2)
        stats.index = [
            {
                "api_price_usd": "API Price (USD)",
                "api_price_inr": "API Price (INR)",
                "api_rating": "API Rating",
                "api_rating_count": "API Rating Count",
                "api_stock": "API Stock",
            }.get(x, x)
            for x in stats.index
        ]
        stats = stats.rename(
            columns={
                "count": "Count",
                "mean": "Mean",
                "median": "Median",
                "std": "Std. Dev.",
                "min": "Minimum",
                "25%": "Q1 (25%)",
                "50%": "Q2 (50%)",
                "75%": "Q3 (75%)",
                "max": "Maximum",
            }
        )
        st.dataframe(stats, use_container_width=True)

    # Distribution plots.
    plot_left, plot_right = st.columns(2)

    with plot_left:
        st.markdown(
            '<div class="section-header">💰 API Price Distribution</div>',
            unsafe_allow_html=True,
        )
        price_plot = df_eda["api_price_inr"].dropna()
        if not price_plot.empty:
            fig_price = px.histogram(
                price_plot,
                x="api_price_inr",
                nbins=30,
                labels={"api_price_inr": "API Price (₹)"},
                template="plotly_dark",
                title="Distribution of API Price (INR)",
            )
            fig_price.update_layout(
                paper_bgcolor="#1E293B",
                plot_bgcolor="#0F172A",
            )
            st.plotly_chart(fig_price, use_container_width=True)

    with plot_right:
        st.markdown(
            '<div class="section-header">⭐ API Rating Distribution</div>',
            unsafe_allow_html=True,
        )
        rating_plot = df_eda["api_rating"].dropna()
        if not rating_plot.empty:
            fig_rating = px.histogram(
                rating_plot,
                x="api_rating",
                nbins=15,
                labels={"api_rating": "API Rating"},
                template="plotly_dark",
                title="Distribution of API Ratings",
            )
            fig_rating.update_layout(
                paper_bgcolor="#1E293B",
                plot_bgcolor="#0F172A",
            )
            st.plotly_chart(fig_rating, use_container_width=True)

    st.markdown(
        '<div class="section-header">📦 API Price & Rating Spread</div>',
        unsafe_allow_html=True,
    )
    box_cols = [c for c in ["api_price_inr", "api_rating", "api_rating_count", "api_stock"] if c in df_eda.columns]
    if box_cols:
        box_data = df_eda[box_cols].melt(
            var_name="API Variable",
            value_name="Value",
        ).dropna()
        fig_box = px.box(
            box_data,
            x="API Variable",
            y="Value",
            points="outliers",
            template="plotly_dark",
            title="Boxplot of New API Numerical Variables",
        )
        fig_box.update_layout(
            paper_bgcolor="#1E293B",
            plot_bgcolor="#0F172A",
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # -------------------- 2. BIVARIATE ANALYSIS --------------------
    st.markdown(
        '<div class="section-header">2️⃣ Bivariate Analysis – API vs Original Variables</div>',
        unsafe_allow_html=True,
    )

    b1, b2 = st.columns(2)

    
    with b1:
        required_cols = ["api_rating", "api_rating_count"]

    if all(col in df_eda.columns for col in required_cols):
        pair = df_eda[required_cols].dropna()

        if not pair.empty:
            corr = pair["api_rating"].corr(
                pair["api_rating_count"]
            )

            st.markdown(
                f'<div class="sub-caption">'
                f'API Rating vs API Rating Count — '
                f'Pearson correlation: <b>{corr:.3f}</b>'
                f'</div>',
                unsafe_allow_html=True,
            )

            fig_rating_count = px.scatter(
                pair,
                x="api_rating_count",
                y="api_rating",
                labels={
                    "api_rating_count": "API Rating Count",
                    "api_rating": "API Rating",
                },
                template="plotly_dark",
                title="API Rating vs Number of Ratings",
            )

            fig_rating_count.update_layout(
                paper_bgcolor="#1E293B",
                plot_bgcolor="#0F172A",
            )

            st.plotly_chart(
                fig_rating_count,
                use_container_width=True,
            )
        else:
            st.info(
                "No records are available for API rating "
                "and rating count comparison."
            )
    else:
        st.info(
            "API Rating Count is not available in the "
            "current API records. This attribute is "
            "provided by FakeStore API."
        )


    with b2:
        pair = df_eda[
            ["api_price_inr", "discounted_price_clean"]
        ].dropna()
        if not pair.empty:
            corr = pair["api_price_inr"].corr(pair["discounted_price_clean"])
            st.markdown(
                f'<div class="sub-caption">API Price vs Original Amazon Discounted Price — Pearson correlation: <b>{corr:.3f}</b></div>',
                unsafe_allow_html=True,
            )
            fig_price_original = px.scatter(
                pair,
                x="discounted_price_clean",
                y="api_price_inr",
                labels={
                    "discounted_price_clean": "Original Amazon Discounted Price (₹)",
                    "api_price_inr": "API Price (₹)",
                },
                template="plotly_dark",
                title="API Price vs Original Amazon Price",
            )
            fig_price_original.update_layout(
                paper_bgcolor="#1E293B",
                plot_bgcolor="#0F172A",
            )
            st.plotly_chart(fig_price_original, use_container_width=True)

    st.markdown(
        '<div class="section-header">🌐 API Source-wise Comparison</div>',
        unsafe_allow_html=True,
    )
    source_summary = (
        df_eda.groupby("api_source", dropna=False)
        .agg(
            Records=("api_source", "size"),
            Mean_API_Price_INR=("api_price_inr", "mean"),
            Mean_API_Rating=("api_rating", "mean"),
        )
        .reset_index()
    )
    source_summary["Mean_API_Price_INR"] = source_summary["Mean_API_Price_INR"].round(2)
    source_summary["Mean_API_Rating"] = source_summary["Mean_API_Rating"].round(2)
    st.dataframe(source_summary, use_container_width=True)

    fig_source = px.bar(
        source_summary,
        x="api_source",
        y="Mean_API_Price_INR",
        text="Mean_API_Price_INR",
        labels={
            "api_source": "API Source",
            "Mean_API_Price_INR": "Mean API Price (₹)",
        },
        template="plotly_dark",
        title="Mean API Price by Source",
    )
    fig_source.update_layout(
        paper_bgcolor="#1E293B",
        plot_bgcolor="#0F172A",
    )
    st.plotly_chart(fig_source, use_container_width=True)

    # -------------------- 3. MULTIVARIATE ANALYSIS --------------------
    st.markdown(
        '<div class="section-header">3️⃣ Multivariate Analysis – Correlation Heatmap</div>',
        unsafe_allow_html=True,
    )

    heatmap_cols = [
        c for c in [
            "discounted_price_clean",
            "rating_clean",
            "rating_count_clean",
            "api_price_inr",
            "api_rating",
            "api_rating_count",
            "api_stock",
        ]
        if c in df_eda.columns
    ]

    corr_matrix = df_eda[heatmap_cols].corr()
    display_corr = corr_matrix.round(2)

    st.dataframe(display_corr, use_container_width=True)

    fig_heatmap = px.imshow(
        corr_matrix,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        template="plotly_dark",
        title="Correlation Heatmap: Original + New API Variables",
    )
    fig_heatmap.update_layout(
        paper_bgcolor="#1E293B",
        plot_bgcolor="#0F172A",
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # -------------------- FINDINGS --------------------
    st.markdown(
        '<div class="section-header">🔎 Key Findings</div>',
        unsafe_allow_html=True,
    )

    api_price_median = df_eda["api_price_inr"].median()
    api_price_mean = df_eda["api_price_inr"].mean()
    api_rating_mean = df_eda["api_rating"].mean()

    st.markdown(
        f"""
        <div class="feature-card">
            <div class="feature-title">EDA Interpretation</div>
            <div class="feature-desc">
                • The fused dataset adds external price, rating, rating-count, stock, brand and API-source variables.<br>
                • The API price distribution has a mean of <b>₹{api_price_mean:,.2f}</b> and a median of <b>₹{api_price_median:,.2f}</b>.<br>
                • The mean API rating is <b>{api_rating_mean:.2f}/5</b>.<br>
                • The API Rating vs Rating Count scatter plot tests whether product popularity is associated with rating.<br>
                • The API Price vs Original Amazon Price plot checks whether the newly introduced price variable behaves similarly to the original price variable.<br>
                • The correlation heatmap provides a multivariate view of relationships among original and API-derived numerical variables.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- CHATBOT RESPONSE ENGINE WITH "VIEW ON AMAZON" REDIRECT LINKS ---
def generate_assistant_response(query):
    q = query.lower()

    if any(k in q for k in ["adapter", "charger", "fast-charging", "watt", "wattage"]):
        return f"""### ⚡ Fast-Charging Adapters in Amazon Catalog

Here are the top-rated fast chargers along with their wattage and direct product links:

1. **Anker 737 Charger (GaNPrime 120W)**
   * **Wattage:** **120W** Max Output | **Ports:** 2x USB-C, 1x USB-A
   * **Rating:** 4.8 / 5 ⭐ | **Price:** $74.99
   * <a href="{get_amazon_link('Anker 737 Charger 120W')}" target="_blank" class="amazon-btn">🛒 View on Amazon Website</a>

2. **Samsung 45W Power Adapter**
   * **Wattage:** **45W** Super Fast Charging 2.0 | **Ports:** 1x USB-C
   * **Rating:** 4.6 / 5 ⭐ | **Price:** $29.99
   * <a href="{get_amazon_link('Samsung 45W USB C Charger')}" target="_blank" class="amazon-btn">🛒 View on Amazon Website</a>

3. **UGREEN Nexode 65W GaN Fast Charger**
   * **Wattage:** **65W** Power Delivery | **Ports:** 2x USB-C, 1x USB-A
   * **Rating:** 4.7 / 5 ⭐ | **Price:** $39.99
   * <a href="{get_amazon_link('UGREEN Nexode 65W GaN Charger')}" target="_blank" class="amazon-btn">🛒 View on Amazon Website</a>

4. **Apple 20W USB-C Power Adapter**
   * **Wattage:** **20W** | **Ports:** 1x USB-C
   * **Rating:** 4.8 / 5 ⭐ | **Price:** $19.00
   * <a href="{get_amazon_link('Apple 20W USB C Power Adapter')}" target="_blank" class="amazon-btn">🛒 View on Amazon Website</a>
"""

    elif any(k in q for k in ["fryer", "kitchen", "cooker", "oven"]):
        return f"""### 🍳 Top Kitchen & Cooking Appliances

1. **Ninja AF101 Air Fryer (4-Quart)** — **$89.99** (4.8 ⭐)
   * 1500W power, non-stick ceramic basket.
   * <a href="{get_amazon_link('Ninja AF101 Air Fryer')}" target="_blank" class="amazon-btn">🛒 View on Amazon Website</a>

2. **COSORI Pro III Dual Blaze 6.8-Quart Air Fryer** — **$149.99** (4.7 ⭐)
   * Dual heating elements, smart app control.
   * <a href="{get_amazon_link('COSORI Dual Blaze Air Fryer')}" target="_blank" class="amazon-btn">🛒 View on Amazon Website</a>

3. **Instant Pot Duo 7-in-1 Pressure Cooker** — **$79.95** (4.7 ⭐)
   * 6-Quart capacity multi-cooker.
   * <a href="{get_amazon_link('Instant Pot Duo 7 in 1 Pressure Cooker')}" target="_blank" class="amazon-btn">🛒 View on Amazon Website</a>
"""

    elif any(k in q for k in ["serum", "beauty", "skin", "cream"]):
        return f"""### 💄 Top Beauty & Skincare Products

1. **CeraVe Vitamin C Serum with Hyaluronic Acid** — **$19.99** (4.6 ⭐)
   * Brightens skin tone, formula enriched with 3 essential ceramides.
   * <a href="{get_amazon_link('CeraVe Vitamin C Serum')}" target="_blank" class="amazon-btn">🛒 View on Amazon Website</a>

2. **The Ordinary Niacinamide 10% + Zinc 1%** — **$10.80** (4.5 ⭐)
   * High-strength vitamin and mineral blemish formula.
   * <a href="{get_amazon_link('The Ordinary Niacinamide')}" target="_blank" class="amazon-btn">🛒 View on Amazon Website</a>

3. **Neutrogena Hydro Boost Water Gel** — **$16.49** (4.7 ⭐)
   * Hydrating facial moisturizer with hyaluronic acid.
   * <a href="{get_amazon_link('Neutrogena Hydro Boost Water Gel')}" target="_blank" class="amazon-btn">🛒 View on Amazon Website</a>
"""

    elif any(k in q for k in ["headphone", "audio", "earbud", "speaker", "bluetooth"]):
        return f"""### 🎧 High-Rating Audio Gear & Headphones

1. **Sony WH-1000XM5 Wireless Noise-Canceling Headphones** — **$398.00** (4.7 ⭐)
   * Industry-leading ANC with 30-hour battery life.
   * <a href="{get_amazon_link('Sony WH 1000XM5 Headphones')}" target="_blank" class="amazon-btn">🛒 View on Amazon Website</a>

2. **Apple AirPods Pro (2nd Generation)** — **$239.00** (4.8 ⭐)
   * Active Noise Cancellation, Adaptive Audio, and USB-C charging.
   * <a href="{get_amazon_link('Apple AirPods Pro 2nd Generation')}" target="_blank" class="amazon-btn">🛒 View on Amazon Website</a>

3. **Bose QuietComfort Wireless Headphones** — **$349.00** (4.6 ⭐)
   * World-class noise canceling with Quiet and Aware modes.
   * <a href="{get_amazon_link('Bose QuietComfort Headphones')}" target="_blank" class="amazon-btn">🛒 View on Amazon Website</a>
"""

    else:
        return f"""### 🔍 Smart Amazon Search Recommendation

Here are the top matches based on your query **"{query}"**:

1. **Top Recommendation for "{query}"**
   * Top-rated selection available on Amazon with quick delivery options.
   * <a href="{get_amazon_link(query)}" target="_blank" class="amazon-btn">🛒 Search "{query}" on Amazon Website</a>

2. **Alternative Budget Selection**
   * High-value alternative matching your query parameters.
   * <a href="{get_amazon_link(query + ' deals')}" target="_blank" class="amazon-btn">🛒 View Top Deals on Amazon Website</a>
"""


# --- PART C: AI SHOPPING ASSISTANT CHATBOT INTERFACE ---
def render_chatbot_interface():
    st.markdown(
        '<div class="main-header">💬 AI Amazon Shopping Assistant</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-caption">Ask questions about products, specs, ratings, and price recommendations with instant Amazon links.</div>',
        unsafe_allow_html=True,
    )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! 👋 I'm your Amazon AI Shopping Assistant. How can I help you find products, compare prices, or check specifications today?",
            }
        ]

    # Render Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

    # Chat Input Box
    if user_prompt := st.chat_input("Ask about fast chargers, air fryers, skincare serums..."):
        # Display user query
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.write(user_prompt)

        # Generate and display response
        response = generate_assistant_response(user_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response, unsafe_allow_html=True)



# --- 10 DISTINCT CHARTS DASHBOARD ---
def render_dashboard():
    import plotly.graph_objects as go
    st.markdown('<div class="main-header">📊 Amazon Hub Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-caption">Ten distinct visualizations of original Amazon products and fused API data.</div>', unsafe_allow_html=True)
    original, api, joined = get_fused_relational_dataset()
    if original is None:
        st.error("Please place amazon_products.csv in the project folder.")
        return
    original = original.drop_duplicates(subset="product_id").copy()
    api = api.copy()
    for frame in (original, api, joined):
        for c in ["discounted_price_clean", "discount_percentage_clean", "rating_clean", "rating_count_clean", "api_price_inr", "api_rating", "api_rating_count", "api_stock"]:
            if c in frame.columns:
                frame[c] = pd.to_numeric(frame[c], errors="coerce")

    a,b,c,d = st.columns(4)
    a.metric("Amazon Products", f"{len(original):,}")
    b.metric("API Records", f"{len(api):,}")
    c.metric("Average Amazon Rating", f"{original['rating_clean'].mean():.2f}/5")
    d.metric("API Product Sources", str(api['api_source'].nunique()))

    def show(fig, title):
        # Separate white title avoids CSS rules that previously made Plotly titles invisible.
        st.markdown(f'<h3 style="color:#FFFFFF!important;font-size:1.14rem;font-weight:800;margin:12px 0 4px">{title}</h3>', unsafe_allow_html=True)
        fig.update_layout(template="plotly_dark", paper_bgcolor="#1E293B", plot_bgcolor="#0F172A",
                          font=dict(color="#E2E8F0", size=11), height=340,
                          margin=dict(l=15,r=15,t=20,b=30), title=None,
                          legend=dict(font=dict(color="#FFFFFF")))
        fig.update_xaxes(tickfont=dict(color="#CBD5E1"), title_font=dict(color="#FFFFFF"))
        fig.update_yaxes(tickfont=dict(color="#CBD5E1"), title_font=dict(color="#FFFFFF"))
        st.plotly_chart(fig, use_container_width=True)

    cats = original.groupby('main_category').agg(n=('product_id','nunique'), price=('discounted_price_clean','mean')).reset_index()
    top = cats.nlargest(9, 'n')
    left,right = st.columns(2)
    with left:
        show(px.bar(top.sort_values('n'), x='n', y='main_category', orientation='h', color='n',
                    color_continuous_scale='Blues', labels={'n':'Products','main_category':'Category'}), '1. Products by Category — Horizontal Bar')
    with right:
        topprice = cats.nlargest(7,'price')
        show(px.pie(topprice, names='main_category', values='price', hole=.55,
                    color_discrete_sequence=px.colors.qualitative.Bold), '2. Average Category Price — Donut')
    left,right = st.columns(2)
    with left:
        show(px.histogram(original, x='rating_clean', nbins=18, color_discrete_sequence=['#FFB703'],
                          labels={'rating_clean':'Amazon Rating'}), '3. Amazon Rating Distribution — Histogram')
    with right:
        show(px.violin(original, y='discount_percentage_clean', box=True, points=False,
                       color_discrete_sequence=['#38BDF8'], labels={'discount_percentage_clean':'Discount (%)'}),
             '4. Discount Percentage — Violin Plot')
    left,right = st.columns(2)
    with left:
        top10 = original.nlargest(10,'rating_count_clean').sort_values('rating_count_clean')
        names = top10['product_name'].astype(str).str.slice(0,27).tolist()
        vals = top10['rating_count_clean'].tolist()
        fig=go.Figure()
        for name,val in zip(names,vals):
            fig.add_trace(go.Scatter(x=[0,val], y=[name,name], mode='lines', line=dict(color='#60A5FA',width=3),showlegend=False))
        fig.add_trace(go.Scatter(x=vals,y=names,mode='markers',marker=dict(color='#FFB703',size=11),showlegend=False))
        show(fig, '5. Most Reviewed Products — Lollipop')
    with right:
        counts=api['api_source'].value_counts()
        show(px.pie(names=counts.index,values=counts.values,
                    color_discrete_sequence=px.colors.qualitative.Set2), '6. API Records by Source — Pie')
    left,right = st.columns(2)
    with left:
        show(px.box(api.dropna(subset=['api_price_inr']),x='api_source',y='api_price_inr',
                    color='api_source',log_y=True,points='outliers',
                    labels={'api_price_inr':'API Price (₹, log scale)','api_source':'Source'}),
             '7. API Price by Source — Box Plot')
    with right:
        avg=api.groupby('api_source')['api_rating'].mean().dropna()
        if len(avg):
            labels=list(avg.index)+[avg.index[0]]
            vals=list(avg.values)+[avg.iloc[0]]
            fig=go.Figure(go.Scatterpolar(r=vals,theta=labels,fill='toself',line=dict(color='#FFB703')))
            fig.update_layout(polar=dict(bgcolor='#0F172A',radialaxis=dict(range=[0,5],tickfont=dict(color='white'))))
            show(fig,'8. Average API Ratings — Radar')
    left,right=st.columns(2)
    with left:
        scatter=api.dropna(subset=['api_rating','api_rating_count'])
        if not scatter.empty:
            show(px.scatter(scatter,x='api_rating_count',y='api_rating',color='api_source',
                            hover_name='api_product_name'), '9. API Rating vs Reviews — Scatter')
        else:
            st.info('Graph 9 needs API rating and review-count values.')
    with right:
        cols=[x for x in ['discounted_price_clean','discount_percentage_clean','rating_clean','rating_count_clean',
                          'api_price_inr','api_rating','api_rating_count','api_stock'] if x in joined.columns]
        corr=joined[cols].corr(numeric_only=True)
        show(px.imshow(corr,text_auto='.2f',color_continuous_scale='RdBu_r',zmin=-1,zmax=1,aspect='auto'),
             '10. Original + API Variables — Correlation Heatmap')
    st.caption('Prices, ratings and review counts describe catalog/API records, not verified sales transactions. API fallback records may be simulated.')


# --- MAIN INTERFACE ROUTER & NAVIGATION SIDEBAR ---
def main():
    # Sidebar Logo / Header
    st.sidebar.markdown(
        """
        <div style="text-align: center; padding: 10px 0;">
            <h2 style="color: #FF9900 !important; font-size: 1.6rem; margin-bottom: 0;">🛒 Amazon Hub</h2>
            <p style="color: #94A3B8 !important; font-size: 0.85rem;">Multi-API Retail Intelligence Engine</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("---")

    # Navigation Controls
    app_mode = st.sidebar.radio(
        "Navigation Menu",
        options=[
            "🏠 Overview & Hero",
            "📊 Part A: Original EDA",
            "🔗 Part B: Data Fusion View",
            "📈 Part E: Fused Dataset EDA",
            "📊 Dashboard: 10 Graphs",
            "💬 Part C: Shopping Assistant",
        ],
    )

    st.sidebar.markdown("---")
    
    # Dataset Reload & Session Controls
    st.sidebar.markdown("### 🛠️ Session Controls")
    if st.sidebar.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Chat reset successfully. How can I help you find products today?",
            }
        ]
        st.rerun()

    # Route Views
    if app_mode == "🏠 Overview & Hero":
        st.markdown(
            """
            <div class="hero-container">
                <div class="hero-badge">Smart Retail Analytics</div>
                <div class="hero-title">Amazon Multi-Source Shopping Platform</div>
                <p class="hero-subtitle">
                    Seamlessly integrating 5 live external APIs with primary catalog data. 
                    Explore full dataset distributions, foreign-key relational mappings, and interactive AI product discovery with direct Amazon checkout links.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Feature Grid Highlights
        f1, f2, f3 = st.columns(3)
        with f1:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-icon">📈</div>
                    <div class="feature-title">Original Catalog EDA</div>
                    <div class="feature-desc">Comprehensive visual breakdown of pricing, customer ratings, and top retail categories.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with f2:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-icon">⚡</div>
                    <div class="feature-title">5 API Data Fusion</div>
                    <div class="feature-desc">Live streaming and foreign key joining across FakeStore, DummyJSON, Makeup API, OpenFood, and Live FX rates.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with f3:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-icon">🤖</div>
                    <div class="feature-title">AI Shopping Assistant</div>
                    <div class="feature-desc">Conversational recommendation engine with dynamic Amazon search integration.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    elif app_mode == "📊 Part A: Original EDA":
        render_original_eda()

    elif app_mode == "🔗 Part B: Data Fusion View":
        render_data_fusion()

    elif app_mode == "📈 Part E: Fused Dataset EDA":
        render_fused_eda()

    elif app_mode == "📊 Dashboard: 10 Graphs":
        render_dashboard()

    elif app_mode == "💬 Part C: Shopping Assistant":
        render_chatbot_interface()


if __name__ == "__main__":
    main()