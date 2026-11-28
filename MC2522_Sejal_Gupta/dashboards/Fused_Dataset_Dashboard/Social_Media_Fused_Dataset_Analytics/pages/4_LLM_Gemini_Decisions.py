import streamlit as st
import plotly.express as px
import pandas as pd
from modules.data import load_fused_data
from modules.ui import inject_custom_css

st.set_page_config(page_title="LLM Gemini Decisions", page_icon="🤖", layout="wide")
inject_custom_css()

st.title("🤖 LLM Gemini Content Moderation Decisions")
st.markdown("Insights into Gemini's multi-class moderation classifications, explanations, and risk assessments.")

df = load_fused_data()

c1, c2 = st.columns(2)
with c1:
    cat_counts = df["gemini_moderation_category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]
    fig_cat = px.bar(
        cat_counts,
        x="Count",
        y="Category",
        orientation="h",
        color="Count",
        color_continuous_scale="Viridis",
        title="Gemini Moderation Category Distribution"
    )
    st.plotly_chart(fig_cat, use_container_width=True)

with c2:
    fig_sun = px.sunburst(
        df,
        path=["gemini_decision", "gemini_risk_level", "gemini_moderation_category"],
        title="Hierarchical Moderation Decisions: Decision -> Risk -> Category"
    )
    st.plotly_chart(fig_sun, use_container_width=True)

st.subheader("LLM Decision vs Benchmark Toxicity Label")
st.dataframe(
    pd.crosstab(df["toxic"].map({1: "Benchmark Toxic", 0: "Benchmark Clean"}), df["gemini_decision"]),
    use_container_width=True
)
