from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# InterviewAce AI | Interactive Analytics Dashboard
# Designed with a Power BI-inspired widescreen layout.
# ============================================================

st.set_page_config(
    page_title="InterviewAce AI | Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Resolve paths safely:
# - Works when dashboard.py is in the project root.
# - Also works after moving it into a folder named "dashboard".
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent if SCRIPT_DIR.name.lower() == "dashboard" else SCRIPT_DIR
DATA_DIR = PROJECT_DIR / "data"
API_DIR = DATA_DIR / "api_data"
ML_DIR = DATA_DIR / "ml_results"

# ---------- Visual theme ----------
NAVY = "#14213D"
BLUE = "#2563EB"
TEAL = "#0F9D8A"
PURPLE = "#8067D8"
CORAL = "#F28C6B"
GOLD = "#E7B44A"
PALE = "#F3F6FB"
TEXT = "#263449"
MUTED = "#6B7890"
PALETTE = [BLUE, TEAL, PURPLE, CORAL, GOLD]

st.markdown(
    f"""
    <style>
      .stApp {{
          background: {PALE};
          color: {TEXT};
      }}
      [data-testid="stHeader"] {{ background: rgba(243,246,251,0.92); }}
      [data-testid="stSidebar"] {{
          background: #FFFFFF;
          border-right: 1px solid #E4EAF3;
      }}
      .block-container {{
          max-width: 1600px;
          padding-top: 1.25rem;
          padding-bottom: 2rem;
      }}
      .hero {{
          background: linear-gradient(115deg, {NAVY} 0%, #203B67 58%, {TEAL} 125%);
          padding: 25px 30px;
          border-radius: 18px;
          color: white;
          margin-bottom: 18px;
          box-shadow: 0 8px 24px rgba(20,33,61,.13);
      }}
      .hero h1 {{ color: white; font-size: 2rem; margin: 0 0 5px 0; }}
      .hero p {{ color: #DCE7F6; margin: 0; font-size: .98rem; }}
      .section-label {{
          color: {NAVY};
          font-size: 1.12rem;
          font-weight: 700;
          margin: 14px 0 8px 0;
      }}
      div[data-testid="stMetric"] {{
          background: #FFFFFF;
          border: 1px solid #E7ECF4;
          padding: 15px 17px;
          border-radius: 14px;
          box-shadow: 0 3px 12px rgba(20,33,61,.045);
      }}
      div[data-testid="stMetricLabel"] p {{
          color: {MUTED};
          font-weight: 600;
          font-size: .83rem;
      }}
      div[data-testid="stMetricValue"] {{
          color: {NAVY};
          font-weight: 750;
      }}
      div[data-testid="stPlotlyChart"] {{
          background: #FFFFFF;
          border: 1px solid #E7ECF4;
          border-radius: 14px;
          padding: 7px;
          box-shadow: 0 3px 12px rgba(20,33,61,.035);
      }}
      .insight {{
          background: #FFFFFF;
          border-left: 4px solid {TEAL};
          padding: 12px 15px;
          border-radius: 9px;
          color: {TEXT};
          margin: 6px 0 12px 0;
      }}
      .footnote {{ color: {MUTED}; font-size: .82rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Helpers ----------
@st.cache_data(show_spinner=False)
def load_csv(path_string):
    path = Path(path_string)
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def numeric_column(df, column):
    if df.empty or column not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[column], errors="coerce")


def unique_job_count(df):
    if df.empty:
        return 0
    for col in ("id", "url"):
        if col in df.columns:
            return int(df[col].dropna().astype(str).nunique())
    return int(len(df.drop_duplicates()))


def chart_layout(fig, height=340, show_legend=False):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Arial, sans-serif", color=TEXT, size=12),
        title=dict(font=dict(size=15, color=NAVY), x=0.02, xanchor="left"),
        margin=dict(l=18, r=18, t=55, b=25),
        showlegend=show_legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor=NAVY, font_color="white"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#EDF1F6", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#EDF1F6", zeroline=False)
    return fig


def show_empty(message):
    st.info(message)


# ---------- Load datasets ----------
github = load_csv(str(API_DIR / "github_python.csv"))
stack = load_csv(str(API_DIR / "stackexchange_python.csv"))
books = load_csv(str(API_DIR / "openlibrary_books.csv"))
hackernews = load_csv(str(API_DIR / "hackernews_technology.csv"))
remotive = load_csv(str(API_DIR / "remotive_software_dev.csv"))

model_results = load_csv(str(ML_DIR / "model_evaluation.csv"))
classification_results = load_csv(str(ML_DIR / "classification_evaluation.csv"))

fused_path = DATA_DIR / "InterviewAce_Data_Fusion.xlsx"
fused = pd.DataFrame()
if fused_path.exists():
    try:
        fused = pd.read_excel(fused_path, sheet_name="Fused_Data")
    except Exception:
        pass

source_data = {
    "GitHub": github,
    "Stack Exchange": stack,
    "Open Library": books,
    "Hacker News": hackernews,
}
source_data = {name: df for name, df in source_data.items() if not df.empty}
if not remotive.empty:
    source_data["Remotive Jobs"] = remotive

# ---------- Header ----------
st.markdown(
    """
    <div class="hero">
      <h1>InterviewAce AI</h1>
      <p>Data intelligence overview · API collection · data fusion · exploratory analysis · ML experiment</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Sidebar filters ----------
st.sidebar.markdown("## Dashboard controls")
st.sidebar.caption("Use these filters to explore the collected project data.")

available_sources = list(source_data.keys())
selected_sources = st.sidebar.multiselect(
    "API sources",
    options=available_sources,
    default=available_sources,
)
st.sidebar.markdown("---")
st.sidebar.caption("The dashboard reads the CSV and Excel files stored in the project's data folder.")
if st.sidebar.button("Refresh dashboard data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

selected_data = {name: df for name, df in source_data.items() if name in selected_sources}
selected_counts = {name: len(df) for name, df in selected_data.items()}
selected_total = sum(selected_counts.values())
jobs_unique = unique_job_count(remotive) if "Remotive Jobs" in selected_sources else 0
fused_count = len(fused) if not fused.empty else 0

# ---------- KPI cards ----------
st.markdown('<div class="section-label">Project at a glance</div>', unsafe_allow_html=True)
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Selected API records", f"{selected_total:,}")
k2.metric("Active data sources", f"{len(selected_data)} / 5")
k3.metric("GitHub repositories", f"{len(github):,}")
k4.metric("Stack Exchange questions", f"{len(stack):,}")
k5.metric("Unique job listings", f"{jobs_unique:,}")

st.caption(
    f"Fused dataset available: {fused_count:,} records"
    if fused_count
    else "Fused workbook not found at data/InterviewAce_Data_Fusion.xlsx."
)

# ---------- API overview ----------
st.markdown('<div class="section-label">01 · API data collection</div>', unsafe_allow_html=True)
left, right = st.columns([1.15, 1])

with left:
    if selected_counts:
        source_df = pd.DataFrame(
            {"API source": list(selected_counts.keys()), "Records": list(selected_counts.values())}
        ).sort_values("Records", ascending=True)
        fig = px.bar(
            source_df,
            x="Records",
            y="API source",
            orientation="h",
            text="Records",
            color="API source",
            color_discrete_sequence=PALETTE,
            title="Records collected from each selected source",
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig = chart_layout(fig, 330)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        show_empty("Select at least one available API source in the sidebar.")

with right:
    if selected_counts:
        source_df = pd.DataFrame(
            {"API source": list(selected_counts.keys()), "Records": list(selected_counts.values())}
        )
        fig = px.pie(
            source_df,
            names="API source",
            values="Records",
            hole=0.62,
            color_discrete_sequence=PALETTE,
            title="Share of selected API records",
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig = chart_layout(fig, 330, True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        show_empty("No source data selected.")

# ---------- GitHub ----------
st.markdown('<div class="section-label">02 · GitHub repository insights</div>', unsafe_allow_html=True)
g1, g2 = st.columns(2)

with g1:
    if not github.empty and {"repository", "stars"}.issubset(github.columns):
        gh = github.copy()
        gh["stars"] = pd.to_numeric(gh["stars"], errors="coerce")
        gh = gh.dropna(subset=["stars"]).nlargest(10, "stars").sort_values("stars")
        fig = px.bar(
            gh, x="stars", y="repository", orientation="h",
            color="stars", color_continuous_scale=["#B9D8F5", BLUE],
            hover_data=[c for c in ["forks", "language"] if c in gh.columns],
            title="Top repositories by GitHub stars",
            labels={"stars": "Stars", "repository": "Repository"},
        )
        fig = chart_layout(fig, 350)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        show_empty("GitHub chart needs 'repository' and 'stars' columns.")

with g2:
    if not github.empty and {"stars", "forks"}.issubset(github.columns):
        gh = github.copy()
        gh["stars"] = pd.to_numeric(gh["stars"], errors="coerce")
        gh["forks"] = pd.to_numeric(gh["forks"], errors="coerce")
        gh = gh.dropna(subset=["stars", "forks"])
        if not gh.empty:
            name_col = "repository" if "repository" in gh.columns else None
            fig = px.scatter(
                gh,
                x="stars",
                y="forks",
                size="stars",
                color="stars",
                hover_name=name_col,
                color_continuous_scale=["#B9D8F5", PURPLE],
                size_max=42,
                title="Repository engagement · stars vs forks",
                labels={"stars": "GitHub stars", "forks": "Forks"},
            )
            fig = chart_layout(fig, 350)
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            show_empty("No valid numeric stars/forks values are available.")
    else:
        show_empty("Bubble chart requires both 'stars' and 'forks' columns.")

# ---------- Stack Exchange ----------
st.markdown('<div class="section-label">03 · Stack Exchange question insights</div>', unsafe_allow_html=True)
s1, s2 = st.columns(2)

with s1:
    if not stack.empty and {"score", "answer_count"}.issubset(stack.columns):
        se = stack.copy()
        se["score"] = pd.to_numeric(se["score"], errors="coerce")
        se["answer_count"] = pd.to_numeric(se["answer_count"], errors="coerce")
        se = se.dropna(subset=["score", "answer_count"])
        fig = px.scatter(
            se, x="answer_count", y="score",
            hover_data=["title"] if "title" in se.columns else None,
            color="score", color_continuous_scale=["#F7C7B8", CORAL],
            title="Question score compared with answer count",
            labels={"answer_count": "Number of answers", "score": "Question score"},
        )
        fig = chart_layout(fig, 340)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        show_empty("Stack Exchange chart requires 'score' and 'answer_count' columns.")

with s2:
    if not stack.empty and "score" in stack.columns:
        scores = numeric_column(stack, "score").dropna()
        if not scores.empty:
            fig = px.histogram(
                x=scores, nbins=25, color_discrete_sequence=[TEAL],
                title="Distribution of question scores",
                labels={"x": "Question score", "y": "Number of questions"},
            )
            fig = chart_layout(fig, 340)
            st.plotly_chart(fig, use_container_width=True)
        else:
            show_empty("No numeric question scores found.")
    else:
        show_empty("Stack Exchange score column is unavailable.")

# ---------- Hacker News and books ----------
st.markdown('<div class="section-label">04 · Technology discussions and reading resources</div>', unsafe_allow_html=True)
h1, h2 = st.columns(2)

with h1:
    if not hackernews.empty and {"title", "score"}.issubset(hackernews.columns):
        hn = hackernews.copy()
        hn["score"] = pd.to_numeric(hn["score"], errors="coerce")
        hn = hn.dropna(subset=["score"]).nlargest(8, "score").sort_values("score")
        fig = px.bar(
            hn, x="score", y="title", orientation="h",
            color_discrete_sequence=[PURPLE],
            hover_data=["comments"] if "comments" in hn.columns else None,
            title="Most engaged technology stories",
            labels={"score": "Story score", "title": "Story"},
        )
        fig = chart_layout(fig, 340)
        st.plotly_chart(fig, use_container_width=True)
    else:
        show_empty("Hacker News data or expected columns are unavailable.")

with h2:
    if not books.empty:
        st.metric("Open Library book records", f"{len(books):,}")
        possible_cols = [c for c in ["subject", "category", "language", "author"] if c in books.columns]
        st.markdown(
            '<div class="insight">Open Library contributes book-related reference material to the knowledge collection.</div>',
            unsafe_allow_html=True,
        )
        if possible_cols:
            st.dataframe(books[possible_cols].head(8), use_container_width=True, hide_index=True)
        else:
            st.caption("Book records are available; no standard category/author columns were detected.")
    else:
        show_empty("Open Library dataset was not found or contains no rows.")

# ---------- ML experiment ----------
st.markdown('<div class="section-label">05 · Machine learning experiment</div>', unsafe_allow_html=True)
m1, m2 = st.columns(2)

with m1:
    if not model_results.empty and {"model", "MAE"}.issubset(model_results.columns):
        mr = model_results.copy()
        mr["MAE"] = pd.to_numeric(mr["MAE"], errors="coerce")
        mr = mr.dropna(subset=["MAE"]).sort_values("MAE")
        fig = px.bar(
            mr, x="model", y="MAE", text_auto=".3f",
            color_discrete_sequence=[BLUE],
            title="Regression model comparison · MAE",
            labels={"model": "Model", "MAE": "Mean Absolute Error"},
        )
        fig = chart_layout(fig, 330)
        st.plotly_chart(fig, use_container_width=True)
    else:
        show_empty("Regression results unavailable. Expected data/ml_results/model_evaluation.csv with model and MAE columns.")

with m2:
    if not model_results.empty and {"model", "R2"}.issubset(model_results.columns):
        mr = model_results.copy()
        mr["R2"] = pd.to_numeric(mr["R2"], errors="coerce")
        mr = mr.dropna(subset=["R2"]).sort_values("R2")
        fig = px.bar(
            mr, x="model", y="R2", text_auto=".3f",
            color_discrete_sequence=[TEAL],
            title="Regression model comparison · R²",
            labels={"model": "Model", "R2": "R² score"},
        )
        fig = chart_layout(fig, 330)
        fig.add_hline(y=0, line_dash="dash", line_color=CORAL)
        st.plotly_chart(fig, use_container_width=True)
    else:
        show_empty("R² results unavailable. Expected an R2 column in the regression results file.")

if not classification_results.empty:
    metric_columns = [
        c for c in ["Accuracy", "Precision", "Recall", "F1"]
        if c in classification_results.columns
    ]
    if metric_columns:
        cl = classification_results.copy()
        for col in metric_columns:
            cl[col] = pd.to_numeric(cl[col], errors="coerce")
        id_cols = ["model"] if "model" in cl.columns else []
        plot_data = cl.melt(
            id_vars=id_cols, value_vars=metric_columns,
            var_name="Metric", value_name="Score",
        ).dropna(subset=["Score"])
        if not plot_data.empty:
            fig = px.bar(
                plot_data, x="Metric", y="Score",
                color="model" if id_cols else "Metric",
                barmode="group", text_auto=".3f",
                color_discrete_sequence=PALETTE,
                title="Classification evaluation metrics",
                labels={"Score": "Score"},
            )
            fig.update_yaxes(range=[0, 1])
            fig = chart_layout(fig, 340, bool(id_cols))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Classification file found, but Accuracy/Precision/Recall/F1 columns were not detected.")
else:
    st.info("Classification evaluation file not found. ML charts are shown only when result files are available.")

# ---------- Fused dataset ----------
st.markdown('<div class="section-label">06 · Data fusion overview</div>', unsafe_allow_html=True)
if not fused.empty:
    f1, f2 = st.columns([1, 1.5])
    with f1:
        st.metric("Fused records", f"{len(fused):,}")
        if "source" in fused.columns:
            source_summary = fused["source"].fillna("Unknown").value_counts().rename_axis("Source").reset_index(name="Records")
            fig = px.pie(
                source_summary, names="Source", values="Records", hole=0.58,
                color_discrete_sequence=PALETTE, title="Fused records by source",
            )
            fig = chart_layout(fig, 310, True)
            st.plotly_chart(fig, use_container_width=True)
    with f2:
        st.markdown("**Preview of the fused dataset**")
        st.dataframe(fused.head(12), use_container_width=True, hide_index=True)
    st.download_button(
        "Download fused dataset preview (first 100 rows)",
        data=fused.head(100).to_csv(index=False).encode("utf-8"),
        file_name="InterviewAce_fused_data_preview.csv",
        mime="text/csv",
    )
else:
    st.info("Fused workbook preview is unavailable. Expected data/InterviewAce_Data_Fusion.xlsx, sheet Fused_Data.")

# ---------- Footer ----------
st.divider()
st.markdown(
    """
    <p class="footnote">
    InterviewAce AI · Academic project analytics dashboard. Counts reflect the available local data files.
    API records may overlap. Experimental ML metrics describe the stored experiment and should not be
    interpreted as proof of real-world interview success or causal relationships.
    </p>
    """,
    unsafe_allow_html=True,
)
