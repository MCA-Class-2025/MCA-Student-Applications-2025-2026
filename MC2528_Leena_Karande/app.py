"""DanceCompass AI application entry point."""

import os
import streamlit as st
from streamlit_option_menu import option_menu

from modules import about, analytics, assistant, compare, dashboard, discover, explore, image_guide, quiz, recommender, upload
from utils.dance_data import build_enriched_corpus_with_metadata
from utils.styles import load_css
from utils.translate import LANGUAGES

st.set_page_config(page_title="DanceCompass AI", page_icon="💃", layout="wide", initial_sidebar_state="expanded")
load_css()

if "doc_index" not in st.session_state:
    # Enriched corpus: curated dance_forms.json profiles + API-sourced facts
    # (Wikipedia/Wikidata/Nominatim/Open Library/MusicBrainz) from the fused
    # dataset, so the AI Guide can answer from both. Metadata travels
    # alongside each chunk so retrieved context can be cited by dance name.
    corpus_texts, corpus_metadata = build_enriched_corpus_with_metadata()
    st.session_state["corpus_full_text"] = "\n\n".join(corpus_texts)
    st.session_state["corpus_metadata"] = corpus_metadata
    try:
        from utils.rag_pipeline import build_index_from_texts
        with st.spinner("Preparing the cultural knowledge library..."):
            st.session_state["doc_index"] = build_index_from_texts(corpus_texts, metadata=corpus_metadata)
    except ImportError:
        st.session_state["doc_index"] = None

with st.sidebar:
    st.markdown("<h2 style='text-align:center;margin-bottom:0;'>💃 DanceCompass</h2><p style='text-align:center;color:#B9B6D9;'>Cultural Heritage, Reimagined</p>", unsafe_allow_html=True)
    selected = option_menu(
        menu_title=None,
        options=["Home", "Explore Dance Forms", "Dataset Insights", "AI Dance Guide", "Dance Recommender", "Dance Recognition", "Upload Knowledge", "Quiz", "About"],
        icons=["house-heart", "globe2", "bar-chart-line", "chat-dots", "compass", "camera", "cloud-arrow-up", "patch-question", "info-circle"],
        default_index=0,
        styles={"container": {"padding": "0", "background-color": "transparent"}, "icon": {"color": "#83F6E9", "font-size": "16px"}, "nav-link": {"font-size": "14px", "border-radius": "12px", "margin": "4px", "color": "#E2E8F0"}, "nav-link-selected": {"background": "linear-gradient(90deg,#7149d8,#327fdc)", "font-weight": "700"}},
    )
    st.markdown("---")
    st.selectbox("🌐 Answer language", options=list(LANGUAGES), key="target_language")

    
    DEFAULT_GEMINI_KEY = (
    st.secrets.get("GEMINI_API_KEY")
    or os.getenv("GEMINI_API_KEY")
    or ""
)

    st.caption("AI features use Gemini securely. API keys are never stored in the application.")

    with st.expander("✨ Gemini API Key"):
        gemini_key = st.text_input(
            "GEMINI_API_KEY",
            type="password",
            value=st.session_state.get(
                "gemini_api_key",
                DEFAULT_GEMINI_KEY,
            ),
            help="Used for AI answers, translation, and image descriptions.",
        )

        if gemini_key:
            st.session_state["gemini_api_key"] = gemini_key

        st.caption(
        "The API key is loaded automatically from your local environment or Streamlit Cloud secrets. You can also enter a temporary key here."
        )

PAGES = {
    "Home": dashboard, "Explore Dance Forms": explore, "Dataset Insights": analytics,
    "AI Dance Guide": assistant, "Dance Recommender": recommender, "Dance Recognition": image_guide,
    "Upload Knowledge": upload, "Quiz": quiz, "About": about,
}
PAGES[selected].render()
