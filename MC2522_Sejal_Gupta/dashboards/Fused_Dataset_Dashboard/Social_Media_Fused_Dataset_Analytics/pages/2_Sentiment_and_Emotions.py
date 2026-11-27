import streamlit as st
import plotly.express as px
from modules.data import load_fused_data
from modules.ui import inject_custom_css

st.set_page_config(page_title="Sentiment & Emotion Analysis", page_icon="🎭", layout="wide")
inject_custom_css()

st.title("🎭 Sentiment & Emotion Dynamics")
st.markdown("Examining how comment sentiments correlate with online toxicity and language distribution.")

df = load_fused_data()

c1, c2 = st.columns(2)
with c1:
    sent_counts = df["hf_sentiment_label"].value_counts().reset_index()
    sent_counts.columns = ["Sentiment", "Count"]
    fig_sent = px.pie(
        sent_counts, values="Count", names="Sentiment",
        color="Sentiment",
        color_discrete_map={"Positive": "#10B981", "Negative": "#EF4444", "Neutral": "#6B7280"},
        hole=0.4,
        title="Overall Sentiment Distribution"
    )
    st.plotly_chart(fig_sent, use_container_width=True)

with c2:
    fig_hist = px.histogram(
        df,
        x="hf_sentiment_score",
        color="toxic",
        barmode="overlay",
        labels={"toxic": "Is Toxic"},
        title="Sentiment Score Distribution (Toxic vs Clean)"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# Sentiment vs Language
st.subheader("Language Distribution & Sentiment Cross-Tabulation")
fig_lang = px.histogram(
    df,
    x="detected_language",
    color="hf_sentiment_label",
    barmode="group",
    title="Sentiment Distribution across Detected Comment Languages"
)
st.plotly_chart(fig_lang, use_container_width=True)
