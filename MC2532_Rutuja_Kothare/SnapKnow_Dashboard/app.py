
from pathlib import Path
from io import BytesIO

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SnapKnow | Analytics",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

ROOT = Path(__file__).parent
DEFAULT_CSV = ROOT / "snapknow_ml_dataset.csv"
IMAGE_DIR = ROOT / "snapknow_images"


# ============================================================
# 2. PROFESSIONAL UI THEME
# ============================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@600;700;800&display=swap');

:root {
    --primary: #2563eb;
    --dark: #172554;
    --text: #25344d;
    --muted: #64748b;
    --border: #e2e8f0;
    --surface: #ffffff;
    --background: #f1f5f9;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
    font-size: 15px;
}

.stApp {
    background: var(--background);
}

.block-container {
    padding-top: 1.8rem;
    padding-bottom: 3rem;
    max-width: 1550px;
}

/* Main headings */

h1, h2, h3, h4 {
    font-family: 'Manrope', sans-serif !important;
    color: #172554 !important;
    font-weight: 800 !important;
}

p, label, li {
    color: #334155;
    line-height: 1.65;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    color: #334155;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #172554 !important;
}

/* Hero banner */

.hero {
    background: linear-gradient(
        120deg,
        #101d3a 0%,
        #1e40af 55%,
        #0e7490 100%
    );
    padding: 34px 36px;
    border-radius: 20px;
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 8px 25px rgba(30,64,175,.13);
}

.hero h1 {
    font-family: 'Manrope', sans-serif;
    font-size: 2.15rem;
    font-weight: 800;
    margin: 0 0 10px 0;
    color: white !important;
    letter-spacing: -0.7px;
}

.hero p {
    color: #e0ecff;
    margin: 0;
    font-size: 1rem;
    line-height: 1.7;
}

/* KPI cards */

.kpi {
    background: white;
    border: 1px solid #e2e8f0;
    padding: 21px 20px;
    border-radius: 16px;
    min-height: 112px;
    box-shadow: 0 4px 15px rgba(15,23,42,.045);
    transition: transform .2s ease, box-shadow .2s ease;
}

.kpi:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 22px rgba(15,23,42,.09);
}

.kpi-label {
    color: #64748b;
    font-size: .85rem;
    font-weight: 700;
    letter-spacing: .2px;
}

.kpi-value {
    color: #172554;
    font-family: 'Manrope', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    margin-top: 9px;
    line-height: 1.25;
    overflow-wrap: anywhere;
}

.kpi-note {
    color: #64748b;
    font-size: .77rem;
    margin-top: 6px;
}

/* Section headings */

.section-title {
    font-family: 'Manrope', sans-serif;
    color: #172554;
    font-weight: 800;
    font-size: 1.3rem;
    margin: 16px 0 5px;
}

.section-sub {
    color: #64748b;
    font-size: .9rem;
    margin-bottom: 18px;
    line-height: 1.6;
}

/* Tabs */

button[data-baseweb="tab"] {
    color: #475569;
    font-size: .95rem;
    font-weight: 700;
    padding: 13px 18px;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #1d4ed8 !important;
    border-bottom-color: #2563eb !important;
}

/* Input fields */

.stTextInput input,
.stNumberInput input {
    background: white;
    border-radius: 9px;
    border-color: #cbd5e1;
    color: #172554;
}

.stTextInput label,
.stSelectbox label,
.stMultiSelect label,
.stSlider label {
    color: #334155 !important;
    font-weight: 700;
}

/* Charts */

div[data-testid="stPlotlyChart"] {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 15px;
    padding: 10px;
    box-shadow: 0 3px 12px rgba(15,23,42,.035);
}

/* Tables */

div[data-testid="stDataFrame"] {
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
}

/* Download button */

.stDownloadButton button {
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 9px;
    padding: 10px 20px;
    font-weight: 700;
}

.stDownloadButton button:hover {
    background: #1d4ed8;
    color: white;
}

/* Alerts */

div[data-testid="stAlert"] {
    border-radius: 12px;
}

/* Divider and footer */

hr {
    border-color: #e2e8f0;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def clean_col(s):
    return str(s).strip()


@st.cache_data(show_spinner=False)
def load_data(file_bytes=None):

    if file_bytes is not None:
        df = pd.read_csv(BytesIO(file_bytes))

    else:
        if not DEFAULT_CSV.exists():
            raise FileNotFoundError(
                f"Dataset not found: {DEFAULT_CSV.name}"
            )

        df = pd.read_csv(DEFAULT_CSV)

    df.columns = [clean_col(c) for c in df.columns]

    return df


def find_col(df, options):

    low = {c.lower(): c for c in df.columns}

    for opt in options:
        if opt.lower() in low:
            return low[opt.lower()]

    return None


def num(df, col):

    if not col:
        return pd.Series(np.nan, index=df.index)

    return pd.to_numeric(df[col], errors="coerce")


def chart_layout(fig, height=370):

    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=65, b=30),

        paper_bgcolor="white",
        plot_bgcolor="white",

        font=dict(
            family="DM Sans",
            size=13,
            color="#334155"
        ),

        title_font=dict(
            family="Manrope",
            size=17,
            color="#172554"
        ),

        title_x=0.02,
        title_y=0.96,

        legend_title_text="",

        legend=dict(
            font=dict(
                size=12,
                color="#334155"
            ),
            bgcolor="rgba(255,255,255,0.8)"
        ),

        hoverlabel=dict(
            bgcolor="white",
            font=dict(
                color="#172554",
                size=13
            )
        )
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#e2e8f0",
        tickfont=dict(size=11, color="#475569"),
        title_font=dict(size=12, color="#334155")
    )

    fig.update_yaxes(
        gridcolor="#edf1f6",
        zeroline=False,
        tickfont=dict(size=11, color="#475569"),
        title_font=dict(size=12, color="#334155")
    )

    return fig


def section(title, subtitle=""):

    st.markdown(
        f"""
        <div class="section-title">{title}</div>
        <div class="section-sub">{subtitle}</div>
        """,
        unsafe_allow_html=True
    )


def kpi(label, value, note=""):

    st.markdown(
        f"""
        <div class="kpi">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# 4. SIDEBAR AND DATASET LOADING
# ============================================================

st.sidebar.markdown("## 📸 SnapKnow Analytics")

st.sidebar.caption(
    "Image Intelligence • API-ready Data • Visual Analytics"
)

st.sidebar.markdown("---")

uploaded = st.sidebar.file_uploader(
    "Upload Fused / ML Dataset (CSV)",
    type=["csv"]
)

try:

    df = load_data(
        uploaded.getvalue() if uploaded else None
    )

except Exception as e:

    st.error(f"Could not read the CSV: {e}")
    st.stop()


if df.empty:

    st.warning("The uploaded dataset is empty.")
    st.stop()


# ============================================================
# 5. IDENTIFY DATASET COLUMNS
# ============================================================

cat_col = find_col(df, ["category"])
name_col = find_col(df, ["name"])
true_col = find_col(df, ["true_label"])
conf_col = find_col(df, ["confidence"])
correct_col = find_col(df, ["ai_correct"])
source_col = find_col(df, ["source"])
image_col = find_col(df, ["image_filename"])
id_col = find_col(df, ["image_id"])

if cat_col is None:

    st.error(
        "The dataset needs a 'category' column to build the dashboard."
    )

    st.stop()


# ============================================================
# 6. SIDEBAR FILTERS
# ============================================================

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔎 Dashboard Filters")

cats = sorted(
    df[cat_col].dropna().astype(str).unique().tolist()
)

chosen_cats = st.sidebar.multiselect(
    "Predicted Category",
    cats,
    default=cats
)

f = df[
    df[cat_col].astype(str).isin(chosen_cats)
].copy()


# Confidence filter

if conf_col:

    conf_values = num(f, conf_col).dropna()

    if len(conf_values):

        lo = float(conf_values.min())
        hi = float(conf_values.max())

        if lo == hi:
            hi = lo + 1

        conf_range = st.sidebar.slider(
            "Confidence Range",
            min_value=float(np.floor(lo)),
            max_value=float(np.ceil(hi)),
            value=(
                float(np.floor(lo)),
                float(np.ceil(hi))
            )
        )

        f = f[
            num(f, conf_col).between(*conf_range)
        ]


# Source filter

if source_col:

    sources = sorted(
        f[source_col].dropna().astype(str).unique().tolist()
    )

    selected_sources = st.sidebar.multiselect(
        "Source Image",
        sources,
        default=sources
    )

    f = f[
        f[source_col].astype(str).isin(selected_sources)
    ]


st.sidebar.markdown("---")

st.sidebar.caption(
    f"Showing **{len(f):,}** of **{len(df):,}** records"
)

st.sidebar.caption(
    "All dashboard charts update automatically when filters change."
)


# ============================================================
# 7. MAIN DASHBOARD HEADER
# ============================================================


# ============================================================
# 7. MAIN DASHBOARD HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>📸 SnapKnow | Image Intelligence Dashboard</h1>
        <p>
            An interactive analytics platform to explore image
            classifications, AI model performance, image properties
            and dataset quality in one workspace.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)



# ============================================================
# 8. HANDLE EMPTY FILTER RESULTS
# ============================================================

if f.empty:

    st.warning(
        "No records match the selected filters. "
        "Please change your sidebar filters."
    )

    st.stop()


# ============================================================
# 9. KPI CARDS
# ============================================================

total = len(f)

avg_conf = (
    num(f, conf_col).mean()
    if conf_col else np.nan
)

acc = (
    num(f, correct_col).mean() * 100
    if correct_col else np.nan
)

n_categories = f[cat_col].nunique()

mp_col = find_col(f, ["img_megapixels"])

avg_mp = num(f, mp_col).mean()


st.markdown("### 📊 Dataset Summary")

c1, c2, c3, c4, c5 = st.columns(5)

with c1:

    kpi(
        "Images Analysed",
        f"{total:,}",
        "Records after filters"
    )

with c2:

    kpi(
        "Categories",
        f"{n_categories}",
        "Unique predicted classes"
    )

with c3:

    kpi(
        "Average Confidence",
        f"{avg_conf:.1f}%" if pd.notna(avg_conf) else "N/A",
        "Vision model confidence"
    )

with c4:

    kpi(
        "Label Agreement",
        f"{acc:.1f}%" if pd.notna(acc) else "N/A",
        "AI category vs true label"
    )

with c5:

    kpi(
        "Avg. Image Size",
        f"{avg_mp:.2f} MP" if pd.notna(avg_mp) else "N/A",
        "Megapixels"
    )


# ============================================================
# 10. DASHBOARD TABS
# ============================================================

st.markdown("")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "🧠 Model Performance",
    "🖼️ Image Analytics",
    "🔎 Record Explorer"
])


# ============================================================
# TAB 1: DATASET OVERVIEW
# ============================================================

with tab1:

    section(
        "Dataset Overview",
        "Understand category distribution, confidence scores "
        "and generated content characteristics."
    )

    a, b = st.columns(2)

    # Chart 1: Category distribution

    with a:

        counts = (
            f[cat_col]
            .astype(str)
            .value_counts()
            .rename_axis("Category")
            .reset_index(name="Images")
        )

        fig = px.pie(
            counts,
            names="Category",
            values="Images",
            hole=0.58,
            title="1. Image Category Distribution",
            color_discrete_sequence=px.colors.qualitative.Set2
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            textfont_size=12
        )

        st.plotly_chart(
            chart_layout(fig),
            use_container_width=True
        )

    # Chart 2: Confidence distribution

    with b:

        if conf_col:

            plot_df = f.copy()
            plot_df["_confidence"] = num(f, conf_col)
            plot_df = plot_df.dropna(subset=["_confidence"])

            fig = px.histogram(
                plot_df,
                x="_confidence",
                nbins=12,
                color=cat_col,
                barmode="overlay",
                opacity=0.82,
                title="2. Confidence Score Distribution",
                color_discrete_sequence=px.colors.qualitative.Safe
            )

            fig.update_layout(
                xaxis_title="Confidence (%)",
                yaxis_title="Number of Images"
            )

            st.plotly_chart(
                chart_layout(fig),
                use_container_width=True
            )

        else:

            st.info("Confidence field not found in the dataset.")

    a, b = st.columns(2)

    # Chart 3: Highest confidence

    with a:

        if name_col and conf_col:

            top = f[[name_col, conf_col]].copy()

            top[conf_col] = pd.to_numeric(
                top[conf_col], errors="coerce"
            )

            top = (
                top.dropna()
                .sort_values(conf_col, ascending=False)
                .head(12)
            )

            fig = px.bar(
                top.sort_values(conf_col),
                x=conf_col,
                y=name_col,
                orientation="h",
                title="3. Highest Confidence Identifications",
                color=conf_col,
                color_continuous_scale="Tealgrn"
            )

            fig.update_layout(
                xaxis_title="Confidence (%)",
                yaxis_title=""
            )

            st.plotly_chart(
                chart_layout(fig, 390),
                use_container_width=True
            )

        else:

            st.info(
                "Name or confidence field not found."
            )

    # Chart 4: Generated text length

    with b:

        text_cols = [
            c for c in [
                "name_word_count",
                "caption_word_count",
                "description_word_count",
                "details_word_count",
                "fun_fact_word_count"
            ]
            if c in f.columns
        ]

        if text_cols:

            means = (
                f[text_cols]
                .apply(pd.to_numeric, errors="coerce")
                .mean()
                .rename_axis("Text field")
                .reset_index(name="Average words")
            )

            means["Text field"] = (
                means["Text field"]
                .str.replace("_word_count", "", regex=False)
                .str.replace("_", " ", regex=False)
                .str.title()
            )

            fig = px.bar(
                means,
                x="Text field",
                y="Average words",
                title="4. Average Generated Text Length",
                color="Average words",
                color_continuous_scale="Blues"
            )

            fig.update_layout(
                xaxis_title="",
                yaxis_title="Average Word Count"
            )

            st.plotly_chart(
                chart_layout(fig, 390),
                use_container_width=True
            )

        else:

            st.info(
                "Text word-count fields not found."
            )


# ============================================================
# TAB 2: MODEL PERFORMANCE
# ============================================================

with tab2:

    section(
        "Model Performance & Quality",
        "Compare AI predictions with ground-truth labels "
        "and understand the reliability of model predictions."
    )

    a, b = st.columns(2)

    # Chart 5: Predicted vs true label

    if true_col:

        with a:

            comp = (
                f.groupby(
                    [true_col, cat_col],
                    dropna=False
                )
                .size()
                .reset_index(name="Images")
            )

            fig = px.density_heatmap(
                comp,
                x=cat_col,
                y=true_col,
                z="Images",
                histfunc="sum",
                title="5. Predicted Category vs True Label",
                color_continuous_scale="Blues",
                text_auto=True
            )

            fig.update_layout(
                xaxis_title="Predicted Category",
                yaxis_title="True Label"
            )

            st.plotly_chart(
                chart_layout(fig),
                use_container_width=True
            )

        # Chart 6: Label agreement

        with b:

            if correct_col:

                q = f.copy()
                q["_correct"] = num(q, correct_col)

                q = (
                    q.groupby(cat_col)["_correct"]
                    .mean()
                    .mul(100)
                    .reset_index(name="Agreement %")
                )

                fig = px.bar(
                    q,
                    x=cat_col,
                    y="Agreement %",
                    title="6. Label Agreement by Category",
                    color="Agreement %",
                    color_continuous_scale="Tealgrn",
                    range_y=[0, 100]
                )

                fig.update_layout(
                    xaxis_title="Predicted Category",
                    yaxis_title="Agreement (%)"
                )

                st.plotly_chart(
                    chart_layout(fig),
                    use_container_width=True
                )

            else:

                st.info(
                    "ai_correct field not found. "
                    "Add it to compare predictions with labels."
                )

    else:

        with a:

            st.info(
                "Ground-truth column not found. "
                "Prediction comparison is unavailable."
            )

        with b:

            st.info(
                "Ground-truth column not found. "
                "Category agreement is unavailable."
            )

    a, b = st.columns(2)

    # Chart 7: Confidence by correctness

    with a:

        if conf_col and correct_col:

            q = f.copy()

            q["_confidence"] = num(q, conf_col)

            q["_correct"] = num(
                q, correct_col
            ).map({
                1: "Correct",
                0: "Incorrect"
            })

            q = q.dropna(
                subset=["_confidence", "_correct"]
            )

            fig = px.box(
                q,
                x="_correct",
                y="_confidence",
                color="_correct",
                title="7. Confidence by Prediction Correctness",
                color_discrete_map={
                    "Correct": "#1f9d83",
                    "Incorrect": "#e58b55"
                }
            )

            fig.update_layout(
                xaxis_title="Prediction Result",
                yaxis_title="Confidence (%)"
            )

            st.plotly_chart(
                chart_layout(fig),
                use_container_width=True
            )

        else:

            st.info(
                "Confidence and ai_correct columns are required."
            )

    # Chart 8: Confidence vs correctness

    with b:

        if conf_col and correct_col:

            q = f.copy()

            q["_confidence"] = num(q, conf_col)
            q["_correct"] = num(q, correct_col)

            q = q.dropna(
                subset=["_confidence", "_correct"]
            )

            fig = px.scatter(
                q,
                x="_confidence",
                y="_correct",
                color=cat_col,
                hover_name=name_col if name_col else None,
                title="8. Confidence vs Correctness",
                color_discrete_sequence=px.colors.qualitative.Bold
            )

            fig.update_yaxes(
                tickmode="array",
                tickvals=[0, 1],
                ticktext=["Incorrect", "Correct"],
                range=[-0.15, 1.15]
            )

            fig.update_layout(
                xaxis_title="Confidence (%)",
                yaxis_title="Prediction Outcome"
            )

            st.plotly_chart(
                chart_layout(fig),
                use_container_width=True
            )

        else:

            st.info(
                "Confidence and ai_correct columns are required."
            )


# ============================================================
# TAB 3: IMAGE ANALYTICS
# ============================================================

with tab3:

    section(
        "Image Characteristics",
        "Understand image resolution, brightness, contrast, "
        "colour composition, saturation and visual complexity."
    )

    a, b = st.columns(2)

    # Chart 9: Image resolution

    if "img_width" in f.columns and "img_height" in f.columns:

        with a:

            plot_df = f.copy()

            plot_df["img_width"] = num(plot_df, "img_width")
            plot_df["img_height"] = num(plot_df, "img_height")

            if "img_megapixels" in f.columns:
                plot_df["img_megapixels"] = num(
                    plot_df, "img_megapixels"
                )

            fig = px.scatter(
                plot_df,
                x="img_width",
                y="img_height",
                color=cat_col,
                size=(
                    "img_megapixels"
                    if "img_megapixels" in f.columns
                    else None
                ),
                hover_name=name_col if name_col else None,
                title="9. Image Resolution Map",
                color_discrete_sequence=px.colors.qualitative.Safe
            )

            fig.update_layout(
                xaxis_title="Width (Pixels)",
                yaxis_title="Height (Pixels)"
            )

            st.plotly_chart(
                chart_layout(fig),
                use_container_width=True
            )

    else:

        with a:
            st.info(
                "Image width/height columns not found."
            )

    # Chart 10: Brightness vs contrast

    if "brightness" in f.columns and "contrast" in f.columns:

        with b:

            plot_df = f.copy()

            plot_df["brightness"] = num(plot_df, "brightness")
            plot_df["contrast"] = num(plot_df, "contrast")

            if "img_size_kb" in f.columns:
                plot_df["img_size_kb"] = num(
                    plot_df, "img_size_kb"
                )

            fig = px.scatter(
                plot_df,
                x="brightness",
                y="contrast",
                color=cat_col,
                size=(
                    "img_size_kb"
                    if "img_size_kb" in f.columns
                    else None
                ),
                hover_name=name_col if name_col else None,
                title="10. Brightness vs Contrast",
                color_discrete_sequence=px.colors.qualitative.Safe
            )

            fig.update_layout(
                xaxis_title="Brightness",
                yaxis_title="Contrast"
            )

            st.plotly_chart(
                chart_layout(fig),
                use_container_width=True
            )

    else:

        with b:
            st.info(
                "Brightness/contrast columns not found."
            )

    a, b = st.columns(2)

    # Chart 11: Saturation vs colourfulness

    if (
        "mean_saturation" in f.columns
        and "colorfulness" in f.columns
    ):

        with a:

            plot_df = f.copy()

            plot_df["mean_saturation"] = num(
                plot_df, "mean_saturation"
            )

            plot_df["colorfulness"] = num(
                plot_df, "colorfulness"
            )

            fig = px.scatter(
                plot_df,
                x="mean_saturation",
                y="colorfulness",
                color=cat_col,
                hover_name=name_col if name_col else None,
                title="11. Saturation vs Colourfulness",
                color_discrete_sequence=px.colors.qualitative.Safe
            )

            fig.update_layout(
                xaxis_title="Mean Saturation",
                yaxis_title="Colourfulness"
            )

            st.plotly_chart(
                chart_layout(fig),
                use_container_width=True
            )

    else:

        with a:
            st.info(
                "Saturation/colourfulness columns not found."
            )

    # Chart 12: RGB colour intensity

    rgb = [
        c for c in ["mean_r", "mean_g", "mean_b"]
        if c in f.columns
    ]

    if rgb:

        with b:

            rgb_df = f[[cat_col] + rgb].copy()

            for col in rgb:
                rgb_df[col] = num(rgb_df, col)

            means = (
                rgb_df.groupby(cat_col)[rgb]
                .mean()
                .reset_index()
                .melt(
                    id_vars=cat_col,
                    var_name="Channel",
                    value_name="Mean intensity"
                )
            )

            means["Channel"] = (
                means["Channel"]
                .str.replace("mean_", "", regex=False)
                .str.upper()
            )

            fig = px.bar(
                means,
                x=cat_col,
                y="Mean intensity",
                color="Channel",
                barmode="group",
                title="12. Average RGB Colour Intensity by Category",
                color_discrete_map={
                    "R": "#e76f6f",
                    "G": "#39a978",
                    "B": "#538bd5"
                }
            )

            fig.update_layout(
                xaxis_title="Category",
                yaxis_title="Average Pixel Intensity"
            )

            st.plotly_chart(
                chart_layout(fig),
                use_container_width=True
            )

    else:

        with b:
            st.info(
                "RGB feature columns not found."
            )

    # Chart 13: Hue composition

    hue_cols = [
        c for c in [
            "hue_red_share",
            "hue_yellow_share",
            "hue_green_share",
            "hue_cyan_share",
            "hue_blue_share",
            "hue_magenta_share"
        ]
        if c in f.columns
    ]

    if hue_cols:

        hue_df = f[hue_cols].apply(
            pd.to_numeric, errors="coerce"
        )

        hue = (
            hue_df.mean()
            .rename_axis("Hue")
            .reset_index(name="Average share")
        )

        hue["Hue"] = (
            hue["Hue"]
            .str.replace("hue_", "", regex=False)
            .str.replace("_share", "", regex=False)
            .str.title()
        )

        fig = px.bar(
            hue,
            x="Hue",
            y="Average share",
            title="13. Average Hue Composition",
            color="Average share",
            color_continuous_scale="Sunset"
        )

        fig.update_layout(
            xaxis_title="Colour Family",
            yaxis_title="Average Share"
        )

        st.plotly_chart(
            chart_layout(fig),
            use_container_width=True
        )

    # Chart 14: Correlation heatmap

    numeric = f.select_dtypes(
        include=np.number
    ).columns.tolist()

    if len(numeric) >= 2:

        corr = f[numeric].corr(
            numeric_only=True
        )

        fig = px.imshow(
            corr,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="14. Numeric Feature Correlation Heatmap"
        )

        st.plotly_chart(
            chart_layout(fig, 520),
            use_container_width=True
        )

    else:

        st.info(
            "At least two numeric fields are needed "
            "for a correlation heatmap."
        )


# ============================================================
# TAB 4: RECORD EXPLORER
# ============================================================

with tab4:

    section(
        "Record Explorer",
        "Search, explore and inspect individual image records "
        "and their AI-generated information."
    )

    # Search field

    search = st.text_input(
        "🔎 Search Image Records",
        placeholder="Enter image name, ID, caption or category..."
    )

    view = f.copy()

    if search:

        mask = pd.Series(
            False,
            index=view.index
        )

        for c in [
            name_col,
            id_col,
            cat_col,
            "caption",
            "image_filename"
        ]:

            if c and c in view.columns:

                mask |= view[c].astype(str).str.contains(
                    search,
                    case=False,
                    na=False,
                    regex=False
                )

        view = view[mask]

    st.caption(
        f"Showing {len(view):,} matching records"
    )

    # Display table

    display_cols = [
        c for c in [
            id_col,
            image_col,
            name_col,
            cat_col,
            true_col,
            conf_col,
            correct_col,
            "caption",
            "description",
            "fun_fact"
        ]
        if c and c in view.columns
    ]

    st.dataframe(
        view[display_cols] if display_cols else view,
        use_container_width=True,
        hide_index=True,
        height=350
    )

    # Individual record details

    if len(view):

        st.markdown("---")

        options = view.index.tolist()

        selected = st.selectbox(
            "Select an Image Record",
            options,
            format_func=lambda i: str(
                view.loc[i, name_col]
                if name_col
                else view.loc[i].get(id_col, i)
            )
        )

        record = view.loc[selected]

        left, right = st.columns([1, 2])

        # Image preview

        with left:

            st.markdown("### 🖼️ Image Preview")

            candidate = (
                record.get(image_col, "")
                if image_col
                else ""
            )

            if pd.notna(candidate) and str(candidate).strip():

                img_path = IMAGE_DIR / str(candidate)

                if img_path.is_file():

                    st.image(
                        str(img_path),
                        use_container_width=True
                    )

                else:

                    st.info(
                        "Image file is not available in the image folder."
                    )

            else:

                st.info(
                    "Image preview is not available for this record."
                )

        # Image information

        with right:

            st.markdown("### 📋 Image Information")

            image_name = (
                record.get(name_col, "N/A")
                if name_col
                else "N/A"
            )

            st.markdown(
                f"**Image Name:** {image_name}"
            )

            st.markdown(
                f"**Predicted Category:** {record.get(cat_col, 'N/A')}"
            )

            if true_col:

                st.markdown(
                    f"**Actual Label:** {record.get(true_col, 'N/A')}"
                )

            if conf_col:

                st.markdown(
                    f"**AI Confidence:** {record.get(conf_col, 'N/A')}%"
                )

            if correct_col:

                st.markdown(
                    f"**Prediction Correct:** {record.get(correct_col, 'N/A')}"
                )

            if id_col:

                st.markdown(
                    f"**Image ID:** {record.get(id_col, 'N/A')}"
                )

        # AI generated information

        st.markdown("---")

        st.markdown("### 🧠 AI-Generated Content")

        content_found = False

        for c in [
            "caption",
            "description",
            "details",
            "fun_fact"
        ]:

            if (
                c in record.index
                and pd.notna(record[c])
                and str(record[c]).strip()
            ):

                content_found = True

                with st.expander(
                    c.replace("_", " ").title(),
                    expanded=True
                ):

                    st.write(str(record[c]))

        if not content_found:

            st.info(
                "No AI-generated text information is available."
            )

    else:

        st.warning(
            "No matching image records found. "
            "Try another search keyword."
        )

    # Download filtered dataset

    st.markdown("---")

    st.download_button(
        "⬇️ Download Filtered Records (CSV)",
        data=view.to_csv(index=False).encode("utf-8"),
        file_name="snapknow_filtered_data.csv",
        mime="text/csv",
        use_container_width=False
    )


# ============================================================
# 11. FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align:center;
        padding:15px 5px;
        color:#64748b;
        font-size:13px;
        line-height:1.8;
    ">
        <strong style="color:#172554;">
            📸 SnapKnow Analytics
        </strong>
        <br>
        Built with Python • Streamlit • Pandas • NumPy • Plotly
        <br>
        Interactive Image Intelligence & Visual Analytics Platform
    </div>
    """,
    unsafe_allow_html=True
)
