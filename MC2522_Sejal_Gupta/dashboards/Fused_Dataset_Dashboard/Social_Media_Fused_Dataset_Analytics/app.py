import streamlit as st
import pandas as pd
from modules.data import load_fused_data, filter_dataframe
from modules.charts import (
    toxicity_distribution_donut,
    gemini_risk_donut,
    toxicity_categories_bar,
    sentiment_vs_toxic_scatter,
    safesearch_summary_bar
)
from modules.ui import inject_custom_css, metric_card

st.set_page_config(
    page_title="Social Media Fused Dataset Analytics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_custom_css()

# Header
st.title("🛡️ Social Media Fused Dataset Analytics Dashboard")
st.markdown("""
**AI Social Media Moderator – Multimodal API Fused Dataset Intelligence**  
*Project by Sejal Gupta (MC2522) · SNDT Women's University · MCA Sem III*
""")
st.divider()

# Load Data
df = load_fused_data()

# Sidebar Filters
with st.sidebar:
    st.header("🔍 Global Filters")
    all_langs = sorted(df["detected_language"].dropna().unique().tolist())
    selected_langs = st.multiselect("Language", all_langs, default=all_langs)

    all_risks = sorted(df["gemini_risk_level"].dropna().unique().tolist())
    selected_risks = st.multiselect("Gemini Risk Level", all_risks, default=all_risks)

    all_decisions = sorted(df["gemini_decision"].dropna().unique().tolist())
    selected_decisions = st.multiselect("Gemini Decision", all_decisions, default=all_decisions)

    toxic_opt = st.radio("Toxicity Status", ["All", "Toxic Only", "Non-Toxic Only"], horizontal=True)

    if st.button("Reset Filters"):
        st.rerun()

filtered_df = filter_dataframe(df, selected_langs, selected_risks, selected_decisions, toxic_opt)

# Top KPIs
total_records = len(filtered_df)
toxic_count = int(filtered_df["toxic"].sum()) if "toxic" in filtered_df.columns else 0
toxic_pct = round((toxic_count / total_records * 100), 1) if total_records > 0 else 0
safe_count = total_records - toxic_count
high_risk_count = len(filtered_df[filtered_df["gemini_risk_level"] == "High"]) if "gemini_risk_level" in filtered_df.columns else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    metric_card("Total Samples", f"{total_records:,}", "Fused social comments", "#3b82f6")
with kpi2:
    metric_card("Toxic Comments", f"{toxic_count} ({toxic_pct}%)", "Identified toxic text", "#ef4444")
with kpi3:
    metric_card("Safe Comments", f"{safe_count}", "Compliant & clean text", "#10b981")
with kpi4:
    metric_card("High Risk Level", f"{high_risk_count}", "Flagged by Gemini LLM", "#f59e0b")

# Row 1: Charts
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(toxicity_distribution_donut(filtered_df), use_container_width=True)
with c2:
    st.plotly_chart(gemini_risk_donut(filtered_df), use_container_width=True)

# Row 2: Subcategories and Scatter
c3, c4 = st.columns(2)
with c3:
    st.plotly_chart(toxicity_categories_bar(filtered_df), use_container_width=True)
with c4:
    st.plotly_chart(sentiment_vs_toxic_scatter(filtered_df), use_container_width=True)

# Row 3: Multimodal Vision SafeSearch
st.plotly_chart(safesearch_summary_bar(filtered_df), use_container_width=True)

st.divider()

# Selected Sample Explorer
st.subheader("🔎 Interactive Sample Inspector")
sample_id = st.selectbox(
    "Select Comment Record ID to inspect full analysis pipeline:",
    filtered_df["id"].tolist(),
    format_func=lambda x: f"Record #{x}: {filtered_df[filtered_df['id'] == x]['comment_text'].values[0][:75]}..."
)

if sample_id:
    row = filtered_df[filtered_df["id"] == sample_id].iloc[0]
    col_a, col_b = st.columns([1.5, 1])
    
    with col_a:
        st.markdown(f"**💬 Comment Text:**")
        st.info(row.get("comment_text", "N/A"))
        if row.get("translated_text") and str(row.get("translated_text")) != str(row.get("comment_text")):
            st.markdown(f"**🌐 Translated Text ({row.get('detected_language')}):**")
            st.code(row.get("translated_text"))
        st.markdown(f"**🤖 Gemini LLM Moderation Explanation:**")
        st.warning(row.get("gemini_explanation", "No explanation available."))
        
    with col_b:
        st.markdown("#### Decision Metadata")
        decision = row.get("gemini_decision", "Unknown")
        risk = row.get("gemini_risk_level", "Unknown")
        cat = row.get("gemini_moderation_category", "Unknown")
        st.write(f"• **Decision:** `{decision}`")
        st.write(f"• **Risk Level:** `{risk}`")
        st.write(f"• **Category:** `{cat}`")
        st.write(f"• **HF Sentiment:** `{row.get('hf_sentiment_label', 'N/A')}` ({row.get('hf_sentiment_score', 0):.2f})")
        st.write(f"• **HF Toxicity:** `{row.get('hf_toxic_label', 'N/A')}` ({row.get('hf_toxic_score', 0):.2f})")
        st.write(f"• **Vision Adult / Violence:** `{row.get('adult_content', 'N/A')}` / `{row.get('violence_content', 'N/A')}`")
