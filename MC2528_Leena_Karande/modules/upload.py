import streamlit as st

from utils.text_utils import extract_pdf
from utils.dance_data import build_corpus_texts

try:
    from utils.rag_pipeline import build_index_from_texts, chunk_text
    _RAG_LIBS_AVAILABLE = True
except ImportError:
    _RAG_LIBS_AVAILABLE = False


def render():
    st.markdown("## ➕ Add More Dance Knowledge")
    st.markdown(
        "<div class='fd-card'>The AI Guide already knows the built-in "
        "20-dance-form dataset. Upload extra PDFs here (an article, a "
        "class handout, notes on a dance form not yet covered) to extend "
        "what it can answer, without touching the core dataset.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    if "extra_chunks" not in st.session_state:
        st.session_state["extra_chunks"] = []

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        with st.spinner("Extracting text..."):
            result = extract_pdf(uploaded_file.read())
        st.success(f"Parsed **{uploaded_file.name}** — {result['page_count']} pages, "
                   f"{result['word_count']:,} words.")

        if _RAG_LIBS_AVAILABLE:
            if st.button("➕ Add this to the AI Guide's knowledge"):
                new_chunks = chunk_text(result["full_text"])
                st.session_state["extra_chunks"].extend(new_chunks)
                with st.spinner("Rebuilding the search index with your addition..."):
                    all_texts = build_corpus_texts() + st.session_state["extra_chunks"]
                    st.session_state["doc_index"] = build_index_from_texts(all_texts)
                st.success(
                    f"Added {len(new_chunks)} chunks. The AI Guide can now "
                    "draw on this document too."
                )
        else:
            st.info(
                "Install `requirements-phase2.txt` (sentence-transformers, "
                "faiss-cpu) to add documents to the semantic index."
            )

    if st.session_state["extra_chunks"]:
        st.caption(
            f"Currently {len(st.session_state['extra_chunks'])} extra chunks "
            "added this session, on top of the 20-dance-form dataset."
        )
