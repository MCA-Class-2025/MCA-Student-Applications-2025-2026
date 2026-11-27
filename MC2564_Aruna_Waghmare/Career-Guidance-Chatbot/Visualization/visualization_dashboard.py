

import os
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ------------------------- PAGE CONFIG -------------------------
st.set_page_config(
    page_title="Career Data Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DARK_BG = "#080D1C"
PANEL_BG = "#111A31"
TEXT = "#E8EEFF"
MUTED = "#9EACCA"
ACCENT = "#20C7D9"

RESOURCE_COLUMNS = {
    "Resume Samples": "resume_samples",
    "Remote Jobs (Remotive)": "remotive_jobs",
    "YouTube Videos": "youtube_resources",
    "GitHub Projects": "github_projects",
    "Technical Books": "technical_books",
    "Research Papers (OpenAlex)": "research_papers",
}


# ------------------------- CSS / THEME -------------------------
st.markdown(
    f"""
    <style>
    .stApp {{ background: {DARK_BG}; color: {TEXT}; }}
    [data-testid="stSidebar"] {{ background: #0C1428; }}
    h1, h2, h3, p, label {{ color: {TEXT} !important; }}
    div[data-testid="stMetric"] {{
        background: {PANEL_BG}; border: 1px solid #243454;
        padding: 16px 18px; border-radius: 12px;
    }}
    div[data-testid="stMetricLabel"] p {{ color: {MUTED} !important; }}
    div[data-testid="stMetricValue"] {{ color: #FFFFFF !important; }}
    div[data-testid="stSelectbox"] > label {{ color: {MUTED} !important; }}
    .dashboard-subtitle {{ color: {MUTED}; margin-top: -12px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------- LOAD DATA -------------------------
@st.cache_data(show_spinner="Loading fused career dataset...")
def load_data(file_path: str) -> pd.DataFrame:
    frame = pd.read_csv(file_path, encoding="utf-8-sig")
    frame.columns = frame.columns.astype(str).str.strip()
    return frame


candidate_paths = [
    os.getenv("FUSED_DATASET", ""),
    "processed_data/career_fused_dataset.csv",
    "eda_output/career_fused_eda_copy.csv",
    "career_fused_dataset.csv",
]
DATA_FILE = next((p for p in candidate_paths if p and Path(p).is_file()), None)

st.title("📊 Career Guidance — Data Analysis Dashboard")
st.markdown(
    '<div class="dashboard-subtitle">Career roles • skills • API resources • learning material availability</div>',
    unsafe_allow_html=True,
)

if DATA_FILE is None:
    st.error(
        "Fused dataset CSV was not found. Run fusion.py first, or set "
        "FUSED_DATASET to the full CSV path."
    )
    st.code("python fusion.py\nstreamlit run visualization_dashboard.py")
    st.stop()

df = load_data(DATA_FILE)

if "career_role" not in df.columns:
    if "Job Title" in df.columns:
        df["career_role"] = df["Job Title"].fillna("Unknown")
    else:
        st.error("The CSV must contain 'career_role' or 'Job Title'.")
        st.stop()

# Ensure expected API columns exist even if a source/API was unavailable.
for col in RESOURCE_COLUMNS.values():
    if col not in df.columns:
        df[col] = ""


# ------------------------- TRANSFORM DATA -------------------------
def split_resource_values(value):
    """Fusion.py joins multiple API results into a cell with ||."""
    if pd.isna(value):
        return []
    raw = str(value).strip()
    if not raw or raw.lower() in {"nan", "none", "null"}:
        return []
    return [part.strip() for part in raw.split("||") if part.strip()]


work = df.copy()
work["career_role"] = work["career_role"].fillna("Unknown").astype(str).str.strip()
work.loc[work["career_role"].eq(""), "career_role"] = "Unknown"

count_columns = {}
for label, source_col in RESOURCE_COLUMNS.items():
    count_col = source_col + "_count"
    work[count_col] = work[source_col].apply(lambda x: len(split_resource_values(x)))
    count_columns[label] = count_col

resource_summary = pd.DataFrame(
    [
        {
            "Resource": label,
            "Available Records": int(work[col].gt(0).sum()),
            "Total Items": int(work[col].sum()),
        }
        for label, col in count_columns.items()
    ]
)

total_records = len(work)
total_roles = work["career_role"].nunique()
total_items = int(sum(work[col].sum() for col in count_columns.values()))
avg_items = total_items / total_records if total_records else 0


# ------------------------- FILTERS -------------------------
with st.sidebar:
    st.header("Dashboard Filters")
    role_options = ["All"] + sorted(work["career_role"].dropna().unique().tolist())
    selected_role = st.selectbox("Career Role", role_options)
    resource_options = ["All"] + list(RESOURCE_COLUMNS.keys())
    selected_resource = st.selectbox("Resource Type", resource_options)
    st.caption(f"Source file: {DATA_FILE}")
    st.caption(f"Rows loaded: {total_records:,}")

filtered = work.copy()
if selected_role != "All":
    filtered = filtered[filtered["career_role"] == selected_role]

if selected_resource != "All":
    chosen_col = RESOURCE_COLUMNS[selected_resource]
    filtered = filtered[filtered[chosen_col].apply(lambda x: len(split_resource_values(x)) > 0)]

filtered_items = int(
    sum(filtered[col].sum() for col in count_columns.values())
)
filtered_avg = filtered_items / len(filtered) if len(filtered) else 0


# ------------------------- KPI CARDS -------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Records", f"{len(filtered):,}")
k2.metric("Career Roles", f"{filtered['career_role'].nunique():,}")
k3.metric("Resource Items", f"{filtered_items:,}")
k4.metric("Avg. Resources / Record", f"{filtered_avg:.2f}")

st.divider()


# ------------------------- CHART DATA -------------------------
# Resource availability should follow selected role filter, but should not
# remove other resource types just because a resource-type filter is selected.
avail = pd.DataFrame(
    [
        {
            "Resource": label,
            "Available Records": int(filtered[col].gt(0).sum()),
            "Total Items": int(filtered[col].sum()),
        }
        for label, col in count_columns.items()
    ]
)

role_counts = (
    filtered["career_role"].value_counts().head(15)
    .rename_axis("Career Role").reset_index(name="Records")
)

# Long-format data for resource-by-role visualizations.
long_rows = []
for role, group in filtered.groupby("career_role"):
    for label, col in count_columns.items():
        long_rows.append({
            "Career Role": role,
            "Resource": label,
            "Resource Items": int(group[col].sum()),
        })
role_resource = pd.DataFrame(long_rows)


# ------------------------- FIRST ROW -------------------------
left, right = st.columns([1.35, 1])
with left:
    st.subheader("Top Career Roles")
    if role_counts.empty:
        st.info("No records match the current filters.")
    else:
        fig = px.bar(
            role_counts.sort_values("Records"),
            x="Records", y="Career Role", orientation="h",
            text="Records",
        )
        fig.update_traces(marker_color="#20C7D9", textposition="outside")
        fig.update_layout(
            template="plotly_dark", paper_bgcolor=PANEL_BG,
            plot_bgcolor=PANEL_BG, font_color=TEXT,
            margin=dict(l=10, r=25, t=15, b=10),
            yaxis_title="", xaxis_title="Number of Records",
        )
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("API / Resource Availability")
    fig = px.bar(
        avail.sort_values("Available Records"),
        x="Available Records", y="Resource", orientation="h",
        text="Available Records",
    )
    fig.update_traces(marker_color="#32D6A0", textposition="outside")
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=PANEL_BG,
        plot_bgcolor=PANEL_BG, font_color=TEXT,
        margin=dict(l=10, r=25, t=15, b=10),
        xaxis_title="Records with Data", yaxis_title="",
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------- SECOND ROW -------------------------
left, right = st.columns([1, 1.35])
with left:
    st.subheader("Share of Resource Items")
    pie_data = avail[avail["Total Items"] > 0]
    if pie_data.empty:
        st.info("No resource items are available for this filter.")
    else:
        fig = px.pie(
            pie_data, names="Resource", values="Total Items",
            hole=0.55,
        )
        fig.update_layout(
            template="plotly_dark", paper_bgcolor=PANEL_BG,
            font_color=TEXT, margin=dict(l=10, r=10, t=15, b=10),
            legend_title_text="Resource Type",
        )
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Resources by Career Role")
    if role_resource.empty:
        st.info("No data available.")
    else:
        top_role_names = (
            filtered["career_role"].value_counts().head(10).index.tolist()
        )
        chart_data = role_resource[role_resource["Career Role"].isin(top_role_names)]
        fig = px.bar(
            chart_data, x="Career Role", y="Resource Items",
            color="Resource", barmode="stack",
        )
        fig.update_layout(
            template="plotly_dark", paper_bgcolor=PANEL_BG,
            plot_bgcolor=PANEL_BG, font_color=TEXT,
            margin=dict(l=10, r=10, t=15, b=65),
            xaxis_title="", yaxis_title="Number of Resource Items",
            xaxis_tickangle=-35, legend_title_text="Resource",
        )
        st.plotly_chart(fig, use_container_width=True)


# ------------------------- THIRD ROW: TREEMAP -------------------------
st.subheader("Career Role vs Resource Type — Treemap")
tree_data = role_resource[role_resource["Resource Items"] > 0].copy()
if tree_data.empty:
    st.info("No resource data is available to build the treemap.")
else:
    fig = px.treemap(
        tree_data,
        path=["Career Role", "Resource"],
        values="Resource Items",
        color="Resource Items",
        color_continuous_scale="Teal",
    )
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=PANEL_BG,
        font_color=TEXT, margin=dict(l=5, r=5, t=10, b=5),
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------- SKILLS ANALYSIS -------------------------
if "Skills" in filtered.columns:
    st.subheader("Most Frequently Mentioned Skills")
    skill_series = filtered["Skills"].dropna().astype(str)
    skill_counts = {}
    for cell in skill_series:
        # The source skills column is free text; split common separators.
        for skill in re.split(r"[,;|\n]", cell):
            skill = skill.strip(" .:-").lower()
            if skill and skill not in {"nan", "none"}:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
    top_skills = (
        pd.Series(skill_counts, name="Mentions")
        .sort_values(ascending=False).head(15)
        .rename_axis("Skill").reset_index()
    )
    if not top_skills.empty:
        fig = px.bar(
            top_skills.sort_values("Mentions"),
            x="Mentions", y="Skill", orientation="h",
            text="Mentions",
        )
        fig.update_traces(marker_color="#A78BFA", textposition="outside")
        fig.update_layout(
            template="plotly_dark", paper_bgcolor=PANEL_BG,
            plot_bgcolor=PANEL_BG, font_color=TEXT,
            margin=dict(l=10, r=25, t=10, b=10),
            xaxis_title="Number of Mentions", yaxis_title="",
        )
        st.plotly_chart(fig, use_container_width=True)


# ------------------------- DETAIL TABLE -------------------------
with st.expander("View filtered fused dataset"):
    st.dataframe(filtered, use_container_width=True, height=350)

with st.expander("View resource summary"):
    st.dataframe(avail, use_container_width=True, hide_index=True)

st.caption(
    "Note: resource counts are calculated by splitting the ' || ' delimiter "
    "used by fusion.py. They indicate stored result entries, not unique users "
    "or API request counts. Empty OpenAlex data will appear as zero."
)
