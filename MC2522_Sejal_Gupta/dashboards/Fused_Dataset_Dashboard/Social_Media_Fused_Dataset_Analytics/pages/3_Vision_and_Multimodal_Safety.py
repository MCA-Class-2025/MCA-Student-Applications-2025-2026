import streamlit as st
import plotly.express as px
import pandas as pd
from modules.data import load_fused_data
from modules.ui import inject_custom_css

st.set_page_config(page_title="Vision & Multimodal Safety", page_icon="👁️", layout="wide")
inject_custom_css()

st.title("👁️ Multimodal Visual Safety & OCR Analytics")
st.markdown("Analysis of Google Cloud Vision SafeSearch categories and OCR text extraction confidence.")

df = load_fused_data()

c1, c2 = st.columns(2)
with c1:
    adult_counts = df["adult_content"].value_counts().reset_index()
    adult_counts.columns = ["Likelihood", "Count"]
    fig_adult = px.pie(
        adult_counts, values="Count", names="Likelihood",
        title="SafeSearch: Adult Content Likelihood"
    )
    st.plotly_chart(fig_adult, use_container_width=True)

with c2:
    violence_counts = df["violence_content"].value_counts().reset_index()
    violence_counts.columns = ["Likelihood", "Count"]
    fig_violence = px.pie(
        violence_counts, values="Count", names="Likelihood",
        title="SafeSearch: Violence Content Likelihood"
    )
    st.plotly_chart(fig_violence, use_container_width=True)

st.subheader("Multimodal Risk Profile Matrix")
risk_matrix = pd.crosstab(df["adult_content"], df["violence_content"])
fig_mat = px.imshow(
    risk_matrix,
    text_auto=True,
    title="Adult Likelihood vs Violence Likelihood Cross-Tabulation"
)
st.plotly_chart(fig_mat, use_container_width=True)
