import os
import pandas as pd
import streamlit as st

@st.cache_data
def load_fused_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, "..", "data", "Final_fused_dataset.csv")
    if not os.path.exists(data_path):
        data_path = os.path.join(os.path.dirname(current_dir), "data", "Final_fused_dataset.csv")
    df = pd.read_csv(data_path)
    
    # Ensure numeric columns
    numeric_cols = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate", "hf_sentiment_score", "hf_toxic_score"]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    
    # Ensure string cleanups
    str_cols = ["gemini_decision", "gemini_risk_level", "detected_language", "gemini_moderation_category", "hf_sentiment_label", "hf_toxic_label"]
    for c in str_cols:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()
            
    return df

def filter_dataframe(df, languages=None, risk_levels=None, decisions=None, toxic_filter=None):
    filtered = df.copy()
    if languages:
        filtered = filtered[filtered["detected_language"].isin(languages)]
    if risk_levels:
        filtered = filtered[filtered["gemini_risk_level"].isin(risk_levels)]
    if decisions:
        filtered = filtered[filtered["gemini_decision"].isin(decisions)]
    if toxic_filter is not None and toxic_filter != "All":
        if toxic_filter == "Toxic Only":
            filtered = filtered[filtered["toxic"] == 1]
        elif toxic_filter == "Non-Toxic Only":
            filtered = filtered[filtered["toxic"] == 0]
    return filtered
