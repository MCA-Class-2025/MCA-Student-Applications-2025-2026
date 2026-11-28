import streamlit as st
import pandas as pd
from modules.data import load_fused_data
from modules.ui import inject_custom_css

st.set_page_config(page_title="Dataset Explorer & Statistics", page_icon="📊", layout="wide")
inject_custom_css()

st.title("📊 Complete Fused Dataset Explorer & Validation")
st.markdown("Inspect raw data records, export data slices, and review summary statistics.")

df = load_fused_data()

tab1, tab2, tab3 = st.tabs(["📋 Complete Dataset", "📈 Descriptive Statistics", "🔍 Missing Values & Quality"])

with tab1:
    search_query = st.text_input("Search comments or explanations:", placeholder="e.g. hurt, positive, idiot...")
    display_df = df
    if search_query:
        mask = (
            display_df["comment_text"].str.contains(search_query, case=False, na=False) |
            display_df["gemini_explanation"].str.contains(search_query, case=False, na=False)
        )
        display_df = display_df[mask]
    
    st.write(f"Showing **{len(display_df)}** records:")
    st.dataframe(display_df, use_container_width=True, height=450)
    
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download Filtered Data (CSV)",
        data=csv,
        file_name="social_media_fused_dataset_export.csv",
        mime="text/csv"
    )

with tab2:
    st.subheader("Numeric Summary")
    st.dataframe(df.describe().T, use_container_width=True)
    
    st.subheader("Categorical Value Counts")
    cat_cols = ["detected_language", "hf_sentiment_label", "gemini_decision", "gemini_risk_level"]
    c_col1, c_col2 = st.columns(2)
    for i, col in enumerate(cat_cols):
        target_col = c_col1 if i % 2 == 0 else c_col2
        with target_col:
            st.write(f"**{col}**")
            st.dataframe(df[col].value_counts(), use_container_width=True)

with tab3:
    st.subheader("Data Integrity & Completeness")
    null_counts = df.isnull().sum().reset_index()
    null_counts.columns = ["Column Name", "Missing Values Count"]
    null_counts["Missing %"] = (null_counts["Missing Values Count"] / len(df) * 100).round(2)
    st.dataframe(null_counts, use_container_width=True)
