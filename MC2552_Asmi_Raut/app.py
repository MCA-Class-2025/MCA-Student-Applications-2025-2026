import streamlit as st
import pandas as pd

from app_pages import dashboard
from app_pages import threat_detection
from app_pages import threat_analysis
from app_pages import knowledge_base
from app_pages import research_assistant
from app_pages import threat_intelligence
from app_pages import about


# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="SecureSense AI",
    page_icon="🛡️",
    layout="wide"
)

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("🛡️ SecureSense AI")
st.sidebar.markdown("---")

feature = st.sidebar.radio(
    "Select Module",
    [
        "🏠 Dashboard",
        "🚨 Threat Detection",
        "🌐 Threat Intelligence",
        "🤖 Threat Analysis Assistant",
        "📚 Knowledge Base",
        "ℹ️ About"
    ]
)

if feature == "🏠 Dashboard":
    dashboard.show()

elif feature == "🚨 Threat Detection":
    threat_detection.show()

elif feature == "🌐 Threat Intelligence":
    threat_intelligence.show()

elif feature == "🤖 Threat Analysis Assistant":
    threat_analysis.show()

elif feature == "📚 Knowledge Base":
    knowledge_base.show()

elif feature == "ℹ️ About":
    about.show()