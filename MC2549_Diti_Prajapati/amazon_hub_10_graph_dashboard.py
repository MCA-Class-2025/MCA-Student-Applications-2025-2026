import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# AMAZON HUB — 10-CHART ANALYTICS DASHBOARD
# Dataset: amazon_5api_fused_dataset.csv
# ------------------------------------------------------------

st.set_page_config(
    page_title="Amazon Hub | Sales & Product Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark dashboard styling inspired by the reference screenshot.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"], .stApp { font-family: Inter, sans-serif; }
    .stApp { background: #0b1220; color: #e5edf8; }
    [data-testid="stSidebar"] { background: #111c2e; border-right: 1px solid #26364e; }
    h1, h2, h3 { color: #f8fafc !important; font-family: Outfit, sans-serif !important; }
    .dashboard-title { font-family: Outfit, sans-serif; font-size: 2rem; font-weight: 800; color: #f8fafc; }
    .dashboard-subtitle { color: #a9b8ce; margin-bottom: 1.1rem; }
    .metric-card { background: linear-gradient(145deg,#17263b,#111c2e); border: 1px solid #2a3b54;
                   border-radius: 12px; padding: 16px 18px; min-height: 94px; }
    .metric-value { font-family: Outfit,sans-serif; font-size: 1.65rem; font-weight: 800; color: #ffb703; }
    .metric-label { font-size: .78rem; font-weight: 700; color: #b8c5d8; text-transform: uppercase; letter-spacing: .5px; }
    .chart-card { background: #111c2e; border: 1px solid #26364e; border-radius: 12px; padding: 10px 12px 4px 12px; }
    div[data-testid="stMetric"] { background: #111c2e; border: 1px solid #26364e; padding: 12px; border-radius: 10px; }
    div[data-testid="stMetricLabel"] { color: #b8c5d8 !important; }
    div[data-testid="stMetricValue"] { color: #ffb703 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

CHART_TEMPLATE = "plotly_dark"
PLOT_BG = "#111c2e"
PAPER_BG = "#111c2e"
ACCENT = "#ffb703"


@st.cache_data
def load_csv(uploaded_file, path):
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)
    return pd.read_csv(path)


def clean_numeric(data, columns):
    for col in columns:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    return data


def style_fig(fig, height=330):
    fig.update_layout(
        template=CHART_TEMPLATE,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color="#e5edf8", family="Inter"),
        title_font=dict(size=15, color="#f8fafc"),
        height=height,
        margin=dict(l=20, r=20, t=55, b=35),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


st.sidebar.markdown(
    """
    <div style="text-align:center;padding:14px 0 8px;">
      <div style="font-size:2rem;">🛒</div>
      <div style="font-family:Outfit,sans-serif;font-size:1.5rem;font-weight:800;color:#ffb703;">Amazon Hub</div>
      <div style="font-size:.8rem;color:#9fb0c8;">Retail Intelligence Dashboard</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Dashboard Controls")
uploaded = st.sidebar.file_uploader(
    "Upload fused CSV (optional)",
    type=["csv"],
    help="If the CSV is in the same folder as this script, you can leave this empty.",
)
default_path = "amazon_5api_fused_dataset.csv"
if not os.path.exists(default_path):
    default_path = "df16531a-efb2-449a-aa0d-c4f3e25488cb.csv"

try:
    df = load_csv(uploaded, default_path)
except Exception:
    st.error(
        "Could not load the fused dataset. Put `amazon_5api_fused_dataset.csv` "
        "in the same folder as this script, or upload the fused CSV in the sidebar."
    )
    st.stop()

required_original = ["product_id", "product_name", "main_category"]
missing = [c for c in required_original if c not in df.columns]
if missing:
    st.error(f"The uploaded file is missing required columns: {', '.join(missing)}")
    st.stop()

numeric_cols = [
    "discounted_price_clean", "actual_price_clean", "discount_percentage_clean",
    "rating_clean", "rating_count_clean", "api_price_usd", "api_price_inr",
    "api_rating", "api_rating_count", "api_stock",
]
df = clean_numeric(df.copy(), numeric_cols)

# Original Amazon data: deduplicate because the fused join repeats a base product
# for each linked API record. API data: deduplicate on API product ID.
original = df.drop_duplicates(subset=["product_id"]).copy()
if "api_product_name" in df.columns:
    api = df.dropna(subset=["api_product_name"]).copy()
    if "api_product_id" in api.columns:
        api = api.drop_duplicates(subset=["api_product_id"])
else:
    api = pd.DataFrame()

# Sidebar filters apply to original-product charts.
categories = sorted(original["main_category"].dropna().astype(str).unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Original product categories",
    categories,
    default=categories[:min(8, len(categories))],
)
if selected_categories:
    original_view = original[original["main_category"].astype(str).isin(selected_categories)].copy()
else:
    original_view = original.copy()

if not api.empty and "api_source" in api.columns:
    sources = sorted(api["api_source"].dropna().astype(str).unique().tolist())
    selected_sources = st.sidebar.multiselect("API sources", sources, default=sources)
    if selected_sources:
        api_view = api[api["api_source"].astype(str).isin(selected_sources)].copy()
    else:
        api_view = api.copy()
else:
    api_view = api

st.markdown('<div class="dashboard-title">📊 Amazon Hub — Product Analytics</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="dashboard-subtitle">Interactive dashboard with 10 charts using the original Amazon catalog and the five-API fused dataset.</div>',
    unsafe_allow_html=True,
)

# KPI row
k1, k2, k3, k4, k5 = st.columns(5)
kpis = [
    (f"{len(original):,}", "Unique Amazon Products"),
    (f"{len(api):,}", "Unique API Records"),
    (f"{original['discounted_price_clean'].mean():,.0f}" if "discounted_price_clean" in original else "N/A", "Avg Discounted Price (₹)"),
    (f"{original['rating_clean'].mean():.2f}/5" if "rating_clean" in original else "N/A", "Avg Amazon Rating"),
    (f"{api['api_source'].nunique()}" if not api.empty and "api_source" in api else "0", "API Sources"),
]
for col, (value, label) in zip([k1, k2, k3, k4, k5], kpis):
    with col:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("")

# Layout helpers
def show_chart(title, fig):
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.plotly_chart(style_fig(fig), use_container_width=True)


left, right = st.columns(2)

# GRAPH 1: Number of unique products by category
with left:
    if not original_view.empty:
        cat = original_view.groupby("main_category")["product_id"].nunique().sort_values(ascending=False).head(10).reset_index()
        cat.columns = ["Category", "Product Count"]
        fig = px.bar(cat.sort_values("Product Count"), x="Product Count", y="Category", orientation="h",
                     text="Product Count", color="Product Count", color_continuous_scale="Blues",
                     title="1. Top Categories by Product Count")
        show_chart("1. Top Categories by Product Count", fig)

# GRAPH 2: Average discounted price by category
with right:
    if "discounted_price_clean" in original_view:
        cat_price = original_view.groupby("main_category")["discounted_price_clean"].mean().sort_values(ascending=False).head(10).reset_index()
        cat_price.columns = ["Category", "Average Discounted Price (₹)"]
        fig = px.bar(cat_price.sort_values("Average Discounted Price (₹)"), x="Average Discounted Price (₹)",
                     y="Category", orientation="h", color="Average Discounted Price (₹)",
                     color_continuous_scale="Oranges", title="2. Average Discounted Price by Category")
        show_chart("2. Average Discounted Price by Category", fig)

left, right = st.columns(2)

# GRAPH 3: Original Amazon rating distribution
with left:
    if "rating_clean" in original_view:
        fig = px.histogram(original_view.dropna(subset=["rating_clean"]), x="rating_clean", nbins=18,
                           color_discrete_sequence=[ACCENT], title="3. Amazon Rating Distribution",
                           labels={"rating_clean": "Rating (out of 5)"})
        show_chart("3. Amazon Rating Distribution", fig)

# GRAPH 4: Discount percentage distribution
with right:
    if "discount_percentage_clean" in original_view:
        fig = px.histogram(original_view.dropna(subset=["discount_percentage_clean"]),
                           x="discount_percentage_clean", nbins=20, color_discrete_sequence=["#38bdf8"],
                           title="4. Discount Percentage Distribution",
                           labels={"discount_percentage_clean": "Discount (%)"})
        show_chart("4. Discount Percentage Distribution", fig)

left, right = st.columns(2)

# GRAPH 5: Top products by rating count
with left:
    if "rating_count_clean" in original_view:
        top_reviews = original_view.nlargest(10, "rating_count_clean")[["product_name", "rating_count_clean"]].copy()
        top_reviews["Short Name"] = top_reviews["product_name"].astype(str).str.slice(0, 34)
        fig = px.bar(top_reviews.sort_values("rating_count_clean"), x="rating_count_clean", y="Short Name",
                     orientation="h", color="rating_count_clean", color_continuous_scale="Viridis",
                     title="5. Top 10 Products by Rating Count",
                     labels={"rating_count_clean": "Rating Count", "Short Name": "Product"})
        show_chart("5. Top 10 Products by Rating Count", fig)

# GRAPH 6: API source record count
with right:
    if not api_view.empty and "api_source" in api_view:
        source_counts = api_view["api_source"].value_counts().rename_axis("API Source").reset_index(name="Records")
        fig = px.bar(source_counts, x="API Source", y="Records", text="Records", color="API Source",
                     title="6. API Records by Source")
        show_chart("6. API Records by Source", fig)

left, right = st.columns(2)

# GRAPH 7: API price distribution in INR
with left:
    if not api_view.empty and "api_price_inr" in api_view:
        price_data = api_view.dropna(subset=["api_price_inr"]).copy()
        if not price_data.empty:
            # Limit visual range at 99th percentile so extreme values do not hide the main distribution.
            cap = price_data["api_price_inr"].quantile(0.99)
            plot_data = price_data[price_data["api_price_inr"] <= cap]
            fig = px.histogram(plot_data, x="api_price_inr", nbins=25,
                               color_discrete_sequence=["#a78bfa"],
                               title="7. API Price Distribution (INR, up to 99th percentile)",
                               labels={"api_price_inr": "API Price (₹)"})
            show_chart("7. API Price Distribution (INR)", fig)

# GRAPH 8: API rating spread by source
with right:
    if not api_view.empty and {"api_source", "api_rating"}.issubset(api_view.columns):
        fig = px.box(api_view.dropna(subset=["api_rating"]), x="api_source", y="api_rating",
                     color="api_source", points="outliers", title="8. API Rating by Source",
                     labels={"api_source": "API Source", "api_rating": "API Rating"})
        show_chart("8. API Rating by Source", fig)

left, right = st.columns(2)

# GRAPH 9: API rating vs rating count
with left:
    if not api_view.empty and {"api_rating", "api_rating_count"}.issubset(api_view.columns):
        scatter = api_view.dropna(subset=["api_rating", "api_rating_count"])
        if not scatter.empty:
            fig = px.scatter(scatter, x="api_rating_count", y="api_rating", color="api_source",
                             hover_name="api_product_name", title="9. API Rating vs Rating Count",
                             labels={"api_rating_count": "Number of Ratings", "api_rating": "API Rating"})
            show_chart("9. API Rating vs Rating Count", fig)
        else:
            st.info("This chart needs API records with both rating and rating-count values.")
    else:
        st.info("This chart needs `api_rating` and `api_rating_count` columns.")

# GRAPH 10: Correlation heatmap across original and API variables
with right:
    heat_cols = [c for c in [
        "discounted_price_clean", "actual_price_clean", "discount_percentage_clean",
        "rating_clean", "rating_count_clean", "api_price_inr", "api_rating",
        "api_rating_count", "api_stock"
    ] if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
    if len(heat_cols) >= 2:
        corr = df[heat_cols].corr(numeric_only=True)
        fig = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1, aspect="auto",
                        color_continuous_scale="RdBu_r", title="10. Correlation Heatmap: Original + API Variables")
        show_chart("10. Correlation Heatmap", fig)

st.markdown("---")
st.caption(
    "Data note: Original-product charts use one row per product_id to avoid double-counting caused by the relational join. "
    "API charts use unique api_product_id records. API price values are displayed in INR where available."
)

with st.expander("Preview the fused dataset"):
    st.write(f"Rows: {len(df):,} | Columns: {df.shape[1]}")
    st.dataframe(df.head(100), use_container_width=True)

with st.expander("View statistical summary"):
    cols = [c for c in numeric_cols if c in df.columns]
    st.dataframe(df[cols].describe().T.round(2), use_container_width=True)
