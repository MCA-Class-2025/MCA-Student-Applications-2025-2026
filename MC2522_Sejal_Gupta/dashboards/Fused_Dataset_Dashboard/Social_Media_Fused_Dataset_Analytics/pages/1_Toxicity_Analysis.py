import streamlit as st
import plotly.express as px
from modules.data import load_fused_data
from modules.ui import inject_custom_css

st.set_page_config(page_title="Toxicity Subcategory Analysis", page_icon="⚠️", layout="wide")
inject_custom_css()

st.title("⚠️ In-Depth Toxicity Subcategory Analysis")
st.markdown("Detailed breakdown of toxicity subcategories: Severe Toxic, Obscene, Threat, Insult, and Identity Hate.")

df = load_fused_data()

cols = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
existing_cols = [c for c in cols if c in df.columns]

# Correlation Heatmap
corr = df[existing_cols].corr()
fig_corr = px.imshow(
    corr,
    text_auto=True,
    aspect="auto",
    color_continuous_scale="RdBu_r",
    title="Toxicity Subcategory Correlation Matrix"
)
st.plotly_chart(fig_corr, use_container_width=True)

# Co-occurrence analysis
col1, col2 = st.columns(2)
with col1:
    multi_toxic = df[existing_cols].sum(axis=1)
    multi_df = multi_toxic.value_counts().reset_index()
    multi_df.columns = ["Number of Toxic Flags", "Comments Count"]
    fig_multi = px.bar(
        multi_df,
        x="Number of Toxic Flags",
        y="Comments Count",
        color="Comments Count",
        color_continuous_scale="Viridis",
        title="Number of Simultaneous Toxic Flags per Comment"
    )
    st.plotly_chart(fig_multi, use_container_width=True)

with col2:
    mean_scores = df.groupby("toxic")["hf_toxic_score"].mean().reset_index()
    mean_scores["toxic"] = mean_scores["toxic"].map({1: "Toxic (Benchmark)", 0: "Non-Toxic (Benchmark)"})
    fig_mean = px.bar(
        mean_scores,
        x="toxic",
        y="hf_toxic_score",
        color="toxic",
        color_discrete_map={"Toxic (Benchmark)": "#EF4444", "Non-Toxic (Benchmark)": "#10B981"},
        title="Average Hugging Face Model Confidence by Label"
    )
    st.plotly_chart(fig_mean, use_container_width=True)
