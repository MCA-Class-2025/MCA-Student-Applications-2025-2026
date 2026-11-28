"""
ui.py
-----
Streamlit UI components for BugAssist AI: custom dark/gradient theme,
sidebar content (project info, upload instructions, tech stack), and
reusable render helpers for the main page sections (response, sources,
confidence, missing-evidence warning, severity distribution, and
source-page highlighting).
"""

import streamlit as st


def inject_custom_css():
    """Injects custom CSS for a modern dark, gradient-themed UI."""
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: #f0f0f5;
        }

        h1, h2, h3, h4 {
            color: #ffffff !important;
        }

        .main-title {
            font-size: 2.6rem;
            font-weight: 800;
            background: linear-gradient(90deg, #ff6a00, #ee0979);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0;
        }

        .subtitle {
            color: #c9c9e0;
            font-size: 1.05rem;
            margin-top: 0;
            margin-bottom: 1.5rem;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        div.stButton > button {
            background: linear-gradient(90deg, #ff6a00, #ee0979);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.4rem;
            font-weight: 600;
            transition: transform 0.15s ease-in-out;
        }

        div.stButton > button:hover {
            transform: scale(1.03);
            opacity: 0.95;
        }

        .response-box {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            margin-top: 1rem;
            white-space: pre-wrap;
            line-height: 1.6;
        }

        .source-card {
            background: rgba(255,255,255,0.04);
            border-left: 3px solid #ee0979;
            border-radius: 6px;
            padding: 0.8rem 1rem;
            margin-bottom: 0.6rem;
        }

        .severity-badge {
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 700;
            margin-left: 0.5rem;
        }
        .severity-Critical { background: #ff3b3b; color: #fff; }
        .severity-High     { background: #ff8a00; color: #1a1a1a; }
        .severity-Medium   { background: #ffd23f; color: #1a1a1a; }
        .severity-Low      { background: #4cd964; color: #1a1a1a; }

        .confidence-banner {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 10px;
            padding: 0.9rem 1.2rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .evidence-warning {
            background: rgba(255, 138, 0, 0.12);
            border: 1px solid #ff8a00;
            border-radius: 10px;
            padding: 0.9rem 1.2rem;
            margin-bottom: 1rem;
            color: #ffd8a8;
        }

        .stTextInput > div > div > input,
        .stTextArea textarea {
            background-color: rgba(255,255,255,0.07);
            color: #f0f0f5;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    """Renders the main application header/title."""
    st.markdown('<p class="main-title">🐞 BugAssist AI</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">AI-powered bug report analysis using Retrieval '
        'Augmented Generation (RAG)</p>',
        unsafe_allow_html=True,
    )


def render_sidebar():
    """Renders the sidebar with project info, upload instructions, and tech stack."""
    with st.sidebar:
        st.markdown("## 📌 About BugAssist AI")
        st.write(
            "BugAssist AI is a RAG-based assistant that analyzes software bug "
            "reports, logs, and technical documentation to help engineers "
            "quickly understand issues and find fixes."
        )

        st.markdown("---")
        st.markdown("## 📤 Upload Instructions")
        st.write(
            "1. Upload one or more PDF files (bug reports, logs, manuals).\n"
            "2. Click **Create Knowledge Base** to process and index them.\n"
            "3. Ask a question in the query box below.\n"
            "4. Click **Search** to get an AI-generated bug analysis."
        )

        st.markdown("---")
        st.markdown("## 🛠️ Technology Stack")
        st.write(
            "- **Frontend:** Streamlit\n"
            "- **Embeddings:** Sentence-Transformers (all-MiniLM-L6-v2)\n"
            "- **LLM:** Qwen2.5-1.5B-Instruct\n"
            "- **Vector DB:** FAISS\n"
            "- **PDF Parsing:** PyMuPDF\n"
            "- **Core:** Python, NumPy"
        )

        st.markdown("---")
        st.caption("MCA Final Year Project · RAG Architecture")


def render_response(response_text: str):
    """Renders the AI-generated response inside a styled box."""
    st.markdown("### 🤖 AI Bug Analysis")
    st.markdown(f'<div class="response-box">{response_text}</div>', unsafe_allow_html=True)


def render_confidence_badge(confidence: float):
    """Renders an overall answer-confidence badge above the AI response."""
    if confidence >= 70:
        color = "#4cd964"
        label = "High"
    elif confidence >= 40:
        color = "#ffd23f"
        label = "Moderate"
    else:
        color = "#ff8a00"
        label = "Low"

    st.markdown(
        f"""
        <div class="confidence-banner">
            <span>🎯 <b>Answer Confidence</b></span>
            <span style="font-size:1.3rem; font-weight:800; color:{color};">
                {confidence:.1f}% &nbsp;<span style="font-size:0.85rem; font-weight:600;">({label})</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_low_evidence_warning():
    """Renders a warning banner when retrieved evidence is weak ("missing evidence detection")."""
    st.markdown(
        """
        <div class="evidence-warning">
            ⚠️ <b>Limited evidence found.</b> The knowledge base doesn't contain
            strongly matching content for this question — the answer below may
            be incomplete or only partially relevant. Consider uploading more
            relevant documents or rephrasing your question.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_severity_chart(distribution: dict):
    """Renders a bar chart of severity distribution across the knowledge base."""
    st.markdown("### 📊 Severity Distribution (Knowledge Base)")
    if not distribution or sum(distribution.values()) == 0:
        st.info("No severity data available yet.")
        return
    st.bar_chart(distribution)
    st.caption(
        "Severity is estimated per chunk using keyword-based classification "
        "(Critical > High > Medium > Low)."
    )


def render_sources(retrieved_chunks, show_highlights: bool = True):
    """
    Renders the retrieved source document chunks used for the response,
    including severity badges and (optionally) a highlighted source-page
    image for each chunk.
    """
    st.markdown("### 📚 Retrieved Source Documents")
    if not retrieved_chunks:
        st.info("No source documents to display.")
        return

    # Local import avoids a hard dependency for callers that only need
    # the text-based source cards (e.g. if PyMuPDF page rendering fails).
    from src.highlight import get_highlighted_page_image, HighlightError

    for i, chunk in enumerate(retrieved_chunks, start=1):
        source = chunk.get("source", "unknown")
        chunk_id = chunk.get("chunk_id", "?")
        page = chunk.get("page")
        severity = chunk.get("severity", "Low")
        score = chunk.get("score", 0.0)
        text_preview = chunk.get("text", "")
        if len(text_preview) > 500:
            text_preview = text_preview[:500] + "..."

        page_label = f"Page {page}" if page else "Page unknown"

        st.markdown(
            f"""
            <div class="source-card">
                <b>Source {i}:</b> {source} &nbsp;|&nbsp;
                <b>{page_label}</b> &nbsp;|&nbsp;
                <b>Chunk:</b> #{chunk_id} &nbsp;|&nbsp;
                <b>Relevance:</b> {score:.3f}
                <span class="severity-badge severity-{severity}">{severity}</span>
                <p style="margin-top:0.5rem; color:#d8d8e8;">{text_preview}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if show_highlights and page:
            try:
                image_bytes, found = get_highlighted_page_image(source, page, chunk.get("text", ""))
                caption = (
                    f"Highlighted match on page {page} of {source}"
                    if found else
                    f"Page {page} of {source} (exact highlight not located — showing full page)"
                )
                with st.expander(f"🖼️ View source page — {source} (page {page})"):
                    st.image(image_bytes, caption=caption, use_container_width=True)
            except HighlightError as exc:
                st.caption(f"ℹ️ Source page preview unavailable: {exc}")