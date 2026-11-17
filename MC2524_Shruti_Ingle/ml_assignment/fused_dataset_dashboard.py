from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# =====================================================
# 1. PAGE SETTINGS
# =====================================================

st.set_page_config(
    page_title="DocuMind AI - Dataset Dashboard",
    page_icon="📊",
    layout="wide"
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "datasets"

st.title("📊 DocuMind AI")
st.subheader("Dataset Dashboard")
st.caption("Phase 2 | Exploratory Data Analysis and Visualization")

# =====================================================
# 2. SELECT DATASET
# =====================================================

dataset_choice = st.sidebar.selectbox(
    "Choose dataset",
    ["Real Dataset", "Synthetic Demo Dataset (500 records)"]
)

if dataset_choice == "Synthetic Demo Dataset (500 records)":
    DATA_PATH = DATA_DIR / "synthetic_demo_dataset.csv"
    st.warning(
        "DEMO DATA ONLY: These 500 records are synthetic test examples, "
        "not real documents or verified factual evidence."
    )
else:
    DATA_PATH = DATA_DIR / "fused_knowledge_dataset.csv"
    st.info(
        "Real dataset selected. This dashboard reads the existing fused CSV "
        "without modifying it. Some rows may contain metadata rather than "
        "extracted document text."
    )

# =====================================================
# 3. LOAD DATASET
# =====================================================

@st.cache_data
def load_dataset(path, modified_time):
    return pd.read_csv(path)

if not DATA_PATH.exists():
    st.error(f"Dataset not found: {DATA_PATH}")
    st.stop()

try:
    df = load_dataset(str(DATA_PATH), DATA_PATH.stat().st_mtime)
except Exception as error:
    st.error(f"Could not read the CSV file: {error}")
    st.stop()

if df.empty:
    st.error("The selected dataset contains no records.")
    st.stop()

# Work on a copy; original CSV is not modified.
df.columns = [str(column).strip() for column in df.columns]
df = df.replace(r"^\s*$", np.nan, regex=True)

# =====================================================
# 4. DATASET SUMMARY
# =====================================================

col1, col2, col3 = st.columns(3)
col1.metric("Total Records", len(df))
col2.metric("Total Columns", len(df.columns))
col3.metric(
    "Unique Titles",
    df["title"].nunique() if "title" in df.columns else "N/A"
)

st.subheader("Dataset Preview")
st.dataframe(df.head(20), use_container_width=True)

# =====================================================
# 5. BASIC DATA QUALITY
# =====================================================

st.subheader("Data Quality")
quality_df = pd.DataFrame({
    "Column": df.columns,
    "Missing Values": [int(df[column].isna().sum()) for column in df.columns],
    "Unique Values": [int(df[column].nunique()) for column in df.columns]
})
st.dataframe(quality_df, use_container_width=True)

# =====================================================
# 6. SOURCE DISTRIBUTION
# =====================================================

source_col = next(
    (column for column in ["source_type", "source", "data_source", "platform"]
     if column in df.columns),
    None
)

if source_col:
    st.subheader("Records by Source")
    source_counts = (
        df[source_col].fillna("Unknown").astype(str)
        .value_counts().rename_axis("Source").reset_index(name="Records")
    )
    fig = px.bar(
        source_counts,
        x="Source",
        y="Records",
        title="Number of Records by Source"
    )
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 7. SEARCH RECORDS
# =====================================================

st.subheader("Search Dataset")
search_text = st.text_input("Search titles and content")

if search_text:
    searchable_cols = [
        column for column in ["title", "content", "source_type"]
        if column in df.columns
    ]
    mask = pd.Series(False, index=df.index)
    for column in searchable_cols:
        mask |= df[column].fillna("").astype(str).str.contains(
            search_text, case=False, regex=False
        )
    results = df[mask]
    st.write(f"Matching records: {len(results)}")
    st.dataframe(results, use_container_width=True)
