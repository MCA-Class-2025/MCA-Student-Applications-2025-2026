"""
app.py — Medicine & Drug Safety Intelligence AI
Main Streamlit Application

Multi-source drug intelligence powered by Data Science, RAG, OCR and LLMs.
"""

import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import time
import json
import io
import re
from functools import lru_cache
from pathlib import Path

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="DURG Intel",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Local imports ─────────────────────────────────────────────────────────────
from pipeline import run_full_pipeline, build_rag_pipeline, get_chatbot
from ocr.extractor import process_uploaded_image
from ocr.preprocessing import resize_for_display
from visualization.safety_charts import (
    chart_top_adverse_reactions, chart_recall_timeline, chart_recall_classification,
    chart_safety_score_gauge, chart_safety_score_components, chart_ae_year_trend,
)
from visualization.research_charts import (
    chart_publications_by_year, chart_top_journals, chart_research_keywords, chart_pub_types,
)
from visualization.clinical_trial_charts import (
    chart_trials_by_status, chart_trials_by_phase, chart_trials_over_time,
    chart_enrollment_distribution, chart_top_sponsors,
)
from utils.validation import sanitize_drug_name, is_valid_drug_name
from utils.caching import clear_all_cache
from config.settings import OPENAI_API_KEY, GROQ_API_KEY

# ── Brand assets & SVG helpers ─────────────────────────────────────────────────
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_LOGO_HOME = ASSETS_DIR / "logo_in_the_home_page.svg"
_LOGO_SIDEBAR = ASSETS_DIR / "logo_in_the_sidebar.svg"
_LOGO_MED = ASSETS_DIR / "med_logo_on_the_homepage.svg"
_ICONS_STRIP = ASSETS_DIR / "Feature icons.svg"


@lru_cache(maxsize=8)
def _svg_inner(path_str: str) -> str:
    """Read an SVG file and return its inner markup (between the <svg> tags)."""
    raw = Path(path_str).read_text(encoding="utf-8")
    m = re.search(r"<svg\b[^>]*>", raw)
    inner = raw[m.end():] if m else raw
    if inner.rstrip().endswith("</svg>"):
        inner = inner.rstrip()[: -len("</svg>")]
    return inner.strip()


@lru_cache(maxsize=8)
def _svg_viewbox(path_str: str) -> str:
    """Read an SVG file and return its viewBox attribute ("" if none)."""
    raw = Path(path_str).read_text(encoding="utf-8")
    m = re.search(r'viewBox="([^"]+)"', raw)
    return m.group(1) if m else ""


def _svg_html(path, width=None, height=None, cls="", style=""):
    """Inline an SVG file as HTML with controllable size (assets are mixed sizes)."""
    inner = _svg_inner(str(path))
    vb = _svg_viewbox(str(path))
    attrs = " ".join(
        a for a in [
            f'viewBox="{vb}"' if vb else "",
            f'width="{width}"' if width else "",
            f'height="{height}"' if height else "",
            f'class="{cls}"' if cls else "",
            f'style="{style}"' if style else "",
        ] if a
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'preserveAspectRatio="xMidYMid meet" version="1.0" {attrs}>{inner}</svg>'
    )


# Feature icons.svg is a vertical strip of 6 icons in a 23.25 x 167.25 canvas.
# Y-slices (minY, height) for each icon, computed from the icon geometry.
_FEATURE_ICON_SLICES = [(0, 26), (26, 26), (52, 29), (81, 29), (110, 28), (138, 29)]


def _feature_icon_html(idx: int, size: int = 30, cls: str = "") -> str:
    """Return icon band `idx` of the feature-icons strip as inline SVG HTML."""
    y0, h = _FEATURE_ICON_SLICES[idx % len(_FEATURE_ICON_SLICES)]
    inner = _svg_inner(str(_ICONS_STRIP))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 {y0} 23.25 {h}" width="{size}" height="{size}" '
        f'preserveAspectRatio="xMidYMid meet" class="{cls}" '
        f'style="display:block;margin:0 auto 6px;">{inner}</svg>'
    )


# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --navy: #17377F;
    --navy-dark: #122D6B;
    --lime: #C6FF00;
    --pale-blue: #E3F2FC;
    --soft-blue: #DCEEFF;
    --ink: #202020;
}

/* ── App chrome ─────────────────────────────────────────────── */
.stApp { background: #FFFFFF; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1280px; }

/* Sidebar: light blue panel */
section[data-testid="stSidebar"] {
    background: var(--pale-blue);
    border-right: 1px solid rgba(23, 55, 127, 0.12);
}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.4rem; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] h4 { color: var(--navy); }
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label { color: var(--navy); }
section[data-testid="stSidebar"] hr { border-color: rgba(23,55,127,0.15); }

/* Buttons */
[data-testid="stBaseButton-primary"] {
    background: var(--navy); color: var(--lime); font-weight: 800;
    letter-spacing: 1px; border-radius: 12px; height: 44px;
    border: 1.5px solid var(--navy);
    transition: transform .15s ease, box-shadow .15s ease, background .15s ease;
}
[data-testid="stBaseButton-primary"]:hover {
    background: var(--navy-dark); color: var(--lime);
    box-shadow: 0 6px 16px rgba(23,55,127,0.35);
}
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background: #FFFFFF; color: var(--navy); border: 1.5px solid rgba(23,55,127,0.35);
    border-radius: 10px; font-weight: 600;
    transition: transform .12s ease, box-shadow .12s ease;
}
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
    transform: translateY(-1px); box-shadow: 0 4px 12px rgba(23,55,127,0.18);
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: #FFFFFF; border: 1.5px dashed rgba(23,55,127,0.4); border-radius: 14px;
}

/* Text inputs */
section[data-testid="stSidebar"] [data-testid="stTextInputRootElement"],
section[data-testid="stSidebar"] input {
    background: #FFFFFF; border-radius: 12px;
}
section[data-testid="stSidebar"] input { color: var(--ink); }

/* ── Brand pill (sidebar logo) ──────────────────────────────── */
.brand-pill {
    padding: 0rem;
    margin-bottom: 0.6rem;
    background: none;
    border: none;
    box-shadow: none;
    text-align: center;
}
.brand-pill a {
    display: block;
    text-decoration: none;
}
.brand-pill svg {
    display: inline-block;
    width: 200px;   /* fixed width */
    height: 100px;  /* fixed height */
}





/* ── Sidebar section titles ─────────────────────────────────── */
.side-head {
    font-size: 1.02rem; font-weight: 800; color: var(--navy);
    letter-spacing: 0.5px; margin: 0.25rem 0; display: flex; align-items: center; gap: 0.4rem;
}
.side-label { font-size: 0.75rem; color: #5B7BC0; font-weight: 600; margin: 0.25rem 0; }
.side-box {
    background: rgba(255,255,255,0.65); border: 1px solid rgba(23,55,127,0.12);
    border-radius: 14px; padding: 0.75rem; margin: 0.25rem 0;
}
.side-note { font-size: 0.72rem; color: #5B7BC0; margin-top: 0.25rem; }

/* ── Home hero banner ───────────────────────────────────────── */
.hero-banner {
    background: linear-gradient(135deg, #17377F 0%, #1d4bb0 55%, #2a5fd0 100%);
    border-radius: 25px; padding: 1.8rem 2.2rem; color: #FFFFFF;
    display: flex; align-items: center; justify-content: space-between; gap: 1.5rem;
    box-shadow: 0 12px 34px rgba(23,55,127,0.28); margin-bottom: 1.4rem;
}
.hero-tag {
    font-size: 1.05rem; letter-spacing: 5px; font-weight: 700;
    text-transform: uppercase; color: var(--lime); margin: 0.5rem 0 0.2rem;
}
.hero-sub { color: rgba(255,255,255,0.85); font-size: 0.92rem; margin: 0; max-width: 520px; }
.hero-med { flex-shrink: 0; }

/* ── Safety notice ──────────────────────────────────────────── */
.safety-note {
    background: var(--pale-blue); border: 1.5px solid var(--navy);
    border-radius: 14px; padding: 0.9rem 1.2rem; color: var(--navy);
    display: flex; gap: 0.8rem; align-items: flex-start;
    box-shadow: 0 4px 14px rgba(23,55,127,0.10); margin-bottom: 1.2rem;
}
.safety-note .safety-icon {
    background: var(--navy); color: var(--lime); border-radius: 50%;
    width: 34px; height: 34px; flex-shrink: 0; display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 1.1rem;
}
.safety-note b { color: var(--navy); }

/* ── Section headings with divider line ─────────────────────── */
.section-head { display: flex; align-items: center; gap: 1rem; margin: 1.6rem 0 1rem; }
.section-head h2 {
    color: var(--navy); font-weight: 800; letter-spacing: 4px;
    text-transform: uppercase; font-size: 1.15rem; margin: 0; white-space: nowrap;
}
.section-line { flex: 1; height: 2px; background: rgba(23,55,127,0.22); }

/* ── Feature launcher cards (lime) ──────────────────────────── */
.feature-card {
    display: block; text-decoration: none;
    background: var(--lime); color: var(--navy);
    border: 1.5px solid var(--navy); border-radius: 18px;
    padding: 1.1rem 0.6rem; text-align: center; min-height: 118px;
    box-shadow: 0 4px 14px rgba(23,55,127,0.18);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    transition: transform .15s ease, box-shadow .15s ease;
    cursor: pointer;
}
.feature-card:hover { transform: translateY(-4px) scale(1.02); box-shadow: 0 12px 26px rgba(23,55,127,0.30); }
.feature-card .fc-title { font-weight: 800; font-size: 1.02rem; color: var(--navy); line-height: 1.2; }
.feature-card .fc-sub { font-size: 0.72rem; color: rgba(23,55,127,0.7); margin-top: 4px; font-weight: 600; }

/* ── Source pills ───────────────────────────────────────────── */
.source-pill {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: var(--pale-blue); border: 1.5px solid var(--navy);
    color: var(--navy); border-radius: 999px; padding: 0.45rem 1.1rem;
    font-weight: 700; font-size: 0.9rem; margin: 0.25rem 0.4rem 0.25rem 0;
    text-decoration: none; transition: transform .12s ease, box-shadow .12s ease;
}
.source-pill:hover { transform: translateY(-2px); box-shadow: 0 6px 14px rgba(23,55,127,0.25); }

/* ── Legacy cards used by other pages ───────────────────────── */
.main-header {
    background: linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #01579b 100%);
    padding: 2rem; border-radius: 12px; color: white; margin-bottom: 1.5rem;
}
.source-badge {
    display: inline-block; padding: 0.2rem 0.6rem; border-radius: 20px;
    font-size: 0.78rem; font-weight: 600; margin: 0.1rem;
}
.badge-openfda { background: #e3f2fd; color: #1565c0; }
.badge-rxnorm { background: #e8f5e9; color: #2e7d32; }
.badge-dailymed { background: #f3e5f5; color: #6a1b9a; }
.badge-pubmed { background: #fff3e0; color: #e65100; }
.badge-ct { background: #fce4ec; color: #880e4f; }
.warning-box {
    background: #fff8e1; border-left: 4px solid #ffc107;
    padding: 0.8rem 1rem; border-radius: 4px; margin: 0.5rem 0;
}
.disclaimer-box {
    background: var(--pale-blue); border: 1px solid rgba(23,55,127,0.3);
    border-radius: 8px; padding: 0.8rem 1rem; font-size: 0.85rem;
    color: var(--navy); margin: 0.5rem 0;
}
.metric-card {
    background: white; border-radius: 10px; padding: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;
}
.source-ok { color: #2e7d32; font-weight: 600; }
.source-fail { color: #c62828; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "current_drug" not in st.session_state:
    st.session_state.current_drug = ""
if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chatbot" not in st.session_state:
    st.session_state.chatbot = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"""
        <div class="brand-pill">
            <a href="?page=Home">
                {_svg_html(_LOGO_SIDEBAR, width=200, height=100)}
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )



    # ── Analyze a Medicine ──────────────────────────────────────────────
    st.markdown('<div class="side-head">Analyze a Medicine</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-label">Enter medicine name</div>', unsafe_allow_html=True)
    drug_input = st.text_input(
        "Enter medicine name",
        placeholder="e.g., Amoxicillin",
        help="Enter a drug brand name, generic name, or active ingredient",
        label_visibility="collapsed",
    )

    analyze_btn = st.button("ANALYZE", type="primary", width="stretch")

    if analyze_btn and drug_input:
        if not is_valid_drug_name(drug_input):
            st.error("Please enter a valid medicine name (at least 2 characters)")
        else:
            cleaned = sanitize_drug_name(drug_input)
            st.session_state.current_drug = cleaned
            st.session_state.pipeline_result = None
            st.session_state.rag_pipeline = None
            st.session_state.chat_messages = []
            st.rerun()

    # ── Medicine Scanner (below the analyzer) ───────────────────────────
    st.markdown('<div class="side-head">Medicine Scanner</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-label">Upload medicine image</div>', unsafe_allow_html=True)
    scanner_file = st.file_uploader(
        "Upload medicine image",
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed",
        key="sidebar_scanner_upload",
    )
    scanner_btn = st.button("Analyze Image", width="stretch", key="sidebar_scanner_btn")
    if scanner_btn and scanner_file:
        st.session_state.pending_ocr_name = scanner_file.name
        st.session_state.pending_ocr_bytes = scanner_file.getvalue()
        st.session_state.nav_radio = "OCR Scanner"
        st.rerun()
    elif scanner_btn and not scanner_file:
        st.info("Please upload an image first (PNG/JPG, up to 10MB).")
    st.markdown('<div class="side-note">PNG · JPG · JPEG — max 10MB per file</div>', unsafe_allow_html=True)

    st.markdown("---")

    # LLM status
    if OPENAI_API_KEY or GROQ_API_KEY:
        st.success("LLM: Connected")
    else:
        st.warning("LLM: No API Key\nSet GROQ_API_KEY or OPENAI_API_KEY in .env")

    if st.session_state.current_drug:
        st.info(f"Current Drug:\n**{st.session_state.current_drug}**")

    # Quick drug examples
    st.markdown('<div class="side-head">Try These Examples</div>', unsafe_allow_html=True)
    example_drugs = ["Amoxicillin", "Metformin", "Lisinopril", "Atorvastatin", "Ibuprofen"]
    for drug in example_drugs:
        if st.button(f"{drug}", width="stretch", key=f"ex_{drug}"):
            st.session_state.current_drug = drug
            st.session_state.pipeline_result = None
            st.session_state.rag_pipeline = None
            st.session_state.chat_messages = []
            st.rerun()

    # Cache control
    if st.button("Clear Cache & Refresh", width="stretch"):
        clear_all_cache()
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.pipeline_result = None
        st.session_state.rag_pipeline = None
        st.success("Cache cleared!")
        time.sleep(1)
        st.rerun()

# ── Run pipeline if drug is set ────────────────────────────────────────────────
current_drug = st.session_state.current_drug

if current_drug and st.session_state.pipeline_result is None:
    with st.spinner(f"Collecting intelligence for **{current_drug}** from 5 APIs..."):
        try:
            result = run_full_pipeline(current_drug)
            st.session_state.pipeline_result = result
        except Exception as e:
            st.error(f"Pipeline error: {e}")

# Build RAG if pipeline done but RAG not built
if (st.session_state.pipeline_result is not None
        and st.session_state.rag_pipeline is None
        and st.session_state.pipeline_result.get("dataset")):
    with st.spinner("Building RAG knowledge base..."):
        try:
            dataset = st.session_state.pipeline_result["dataset"]
            rag = build_rag_pipeline(current_drug, dataset)
            st.session_state.rag_pipeline = rag
        except Exception as e:
            st.warning(f"RAG build error: {e}")

# ── Page navigation ────────────────────────────────────────────────────────────
pages = [
    "Home",
    "Medicine Analyzer",
    "OCR Scanner",
    "AI Intelligence",
    "Safety Analytics",
    "Research & Trials",
    "Data Explorer",
    "EDA Dashboard",
    "RAG Chatbot",
    "System Sources",
]

# Allow feature launcher cards / logo to navigate via ?page=<label> links
_qp_page = st.query_params.get("page")
if _qp_page:
    _clean = str(_qp_page).replace("+", " ")
    if _clean in pages:
        st.session_state["nav_radio"] = _clean
        st.query_params.pop("page", None)

with st.sidebar:
    st.markdown("---")
    st.markdown('<div class="side-head">Navigation</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigation",
        pages,
        label_visibility="collapsed",
        key="nav_radio",
    )

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: HOME
# ═══════════════════════════════════════════════════════════════════════════════
if page == "Home":
    # ── Hero banner ────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="hero-banner">
        <div>
            {_svg_html(_LOGO_HOME, width=500)}
            <p class="hero-tag">Multi-Source Drug Intelligence</p>
            <p class="hero-sub">Five official public APIs · Data Science · RAG · OCR · LLMs —
            everything about a medicine in one place.</p>
        </div>
        <div class="hero-med">
            {_svg_html(_LOGO_MED, height=170)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Medical safety notice ──────────────────────────────────────────
    st.markdown("""
    <div class="safety-note">
        <div class="safety-icon"><svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M12 2 4 5v6c0 5.2 3.4 9.6 8 11 4.6-1.4 8-5.8 8-11V5l-8-3Z"/></svg></div>
        <div>
            <b>Medical Safety Notice:</b> This platform provides informational analysis of
            publicly available drug data only. It is NOT a medical diagnosis system and does
            NOT provide clinical recommendations. Always consult a qualified healthcare
            professional for medical decisions.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Key Features launcher grid ─────────────────────────────────────
    st.markdown("""
    <div class="section-head"><h2>Key Features</h2><div class="section-line"></div></div>
    """, unsafe_allow_html=True)

    def _feature_card(page_target, title, sub, icon_idx):
        icon = _feature_icon_html(icon_idx, size=34)
        href = f"?page={page_target.replace(' ', '%20')}"
        return (f'<a class="feature-card" href="{href}">'
                f'{icon}<span class="fc-title">{title}</span>'
                f'<span class="fc-sub">{sub}</span></a>')

    # Row 1 — AI Intelligence Report card is intentionally wider
    row1 = st.columns([1, 2, 1, 1])
    with row1[0]:
        st.markdown(_feature_card("Medicine Analyzer", "Medicine Analysis",
                                  "Identity, ingredients & labels", 0),
                    unsafe_allow_html=True)
    with row1[1]:
        st.markdown(_feature_card("AI Intelligence", "AI Intelligence Report",
                                  "LLM-fused report from all 5 sources", 1),
                    unsafe_allow_html=True)
    with row1[2]:
        st.markdown(_feature_card("System Sources", "FDA Explorer",
                                  "openFDA labels, events & recalls", 2),
                    unsafe_allow_html=True)
    with row1[3]:
        st.markdown(_feature_card("Safety Analytics", "Safety Analytics",
                                  "Adverse events, recalls & score", 3),
                    unsafe_allow_html=True)

    # Row 2 — four equal cards
    row2 = st.columns(4)
    with row2[0]:
        st.markdown(_feature_card("Research & Trials", "Research & Trials",
                                  "PubMed literature & clinical trials", 4),
                    unsafe_allow_html=True)
    with row2[1]:
        st.markdown(_feature_card("Data Explorer", "Data Explorer",
                                  "Browse every dataset & record", 5),
                    unsafe_allow_html=True)
    with row2[2]:
        st.markdown(_feature_card("EDA Dashboard", "EDA Dashboard",
                                  "Statistics, trends & anomalies", 2),
                    unsafe_allow_html=True)
    with row2[3]:
        st.markdown(_feature_card("RAG Chatbot", "ChatBot",
                                  "Evidence-grounded Q&A with citations", 3),
                    unsafe_allow_html=True)

    # ── Sources ────────────────────────────────────────────────────────
    st.markdown("""
    <div class="section-head"><h2>Sources</h2><div class="section-line"></div></div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div>
        <a class="source-pill" href="?page=System%20Sources">openFDA</a>
        <a class="source-pill" href="?page=System%20Sources">RxNorm</a>
        <a class="source-pill" href="?page=System%20Sources">DailyMed</a>
        <a class="source-pill" href="?page=System%20Sources">PubMed</a>
        <a class="source-pill" href="?page=System%20Sources">ClinicalTrials.gov</a>
    </div>
    """, unsafe_allow_html=True)

    # ── Getting started (compact) ──────────────────────────────────────
    st.markdown("""
    <div class="section-head"><h2>Get Started</h2><div class="section-line"></div></div>
    """, unsafe_allow_html=True)
    st.markdown("""
    1. **Enter a medicine name** in the sidebar (e.g., *Amoxicillin*, *Metformin*, *Lisinopril*) and click **Analyze**.
    2. **Or scan a package** — upload a medicine image in the sidebar **Medicine Scanner**.
    3. Explore the reports: **AI Intelligence**, **Safety Analytics**, **Research & Trials**, and ask the **ChatBot** questions grounded in the retrieved evidence.
    """)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: MEDICINE ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Medicine Analyzer":
    st.markdown("# Medicine Analyzer")

    if not current_drug:
        st.info("Enter a medicine name in the sidebar to begin analysis.")
        st.stop()

    result = st.session_state.pipeline_result
    if result is None:
        st.info("Loading drug data...")
        st.stop()

    dataset = result.get("dataset", {})
    identity = dataset.get("identity", {})

    # Source status banner
    status = result.get("source_status", {})
    status_cols = st.columns(5)
    for col, (api_name, api_status) in zip(status_cols, status.items()):
        with col:
            icon = "✓" if api_status["ok"] else "✗"
            color = "source-ok" if api_status["ok"] else "source-fail"
            st.markdown(f'<span class="{color}">{icon} {api_name}</span>', unsafe_allow_html=True)
            if not api_status["ok"] and api_status.get("error"):
                st.caption(f"Error: {api_status['error'][:50]}")

    st.markdown("---")

    # Drug identity header
    norm_name = identity.get("normalized_drug_name") or current_drug
    rxcui = identity.get("rxcui", "N/A")
    rxnorm_status = identity.get("rxnorm_status", "")

    st.markdown(f"## {norm_name}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("RxCUI", rxcui or "N/A")
    with col2:
        st.metric("Drug Class", (identity.get("drug_class") or "N/A")[:30])
    with col3:
        summary = dataset.get("summary", {})
        st.metric("Adverse Events", f"{summary.get('total_adverse_events', 0):,}")
    with col4:
        st.metric("Recalls Found", summary.get("total_recalls", 0))

    # Active ingredients
    ingredients = identity.get("all_ingredients", [])
    if ingredients:
        st.markdown("### Active Ingredients")
        for ing in ingredients:
            st.markdown(f"- **{ing}**")

    # Brand names
    brands = identity.get("brand_names", [])
    if brands:
        st.markdown("### Known Brand Names")
        st.write(", ".join(brands[:10]))

    # DailyMed official labeling
    dfs = dataset.get("dataframes", {})
    dailymed_df = dfs.get("dailymed")

    if dailymed_df is not None and not dailymed_df.empty:
        dm_row = dailymed_df.iloc[0].to_dict()

        st.markdown("---")
        st.markdown("## Official Drug Labeling")
        st.caption("Source: DailyMed (National Library of Medicine)")

        tabs = st.tabs(["Warnings", "Contraindications", "Indications", "Dosage", "Storage", "Interactions", "Precautions"])

        with tabs[0]:
            warn = dm_row.get("warnings", "")
            if warn:
                st.markdown(f'<div class="warning-box">{warn[:2000]}</div>', unsafe_allow_html=True)
            else:
                st.info("No warnings retrieved from DailyMed. Check openFDA labels below.")

        with tabs[1]:
            contra = dm_row.get("contraindications", "")
            if contra:
                st.write(contra[:1500])
            else:
                st.info("No contraindications data retrieved.")

        with tabs[2]:
            ind = dm_row.get("indications", "")
            if ind:
                st.write(ind[:1500])
            else:
                st.info("No indications data retrieved.")

        with tabs[3]:
            dos = dm_row.get("dosage", "")
            if dos:
                st.write(dos[:1500])
            else:
                st.info("No dosage information retrieved.")

        with tabs[4]:
            stor = dm_row.get("storage", "")
            if stor:
                st.success(stor[:500])
            else:
                st.info("No storage information retrieved.")

        with tabs[5]:
            inter = dm_row.get("interactions", "")
            if inter:
                st.write(inter[:1500])
            else:
                st.info("No drug interactions retrieved.")

        with tabs[6]:
            prec = dm_row.get("precautions", "")
            if prec:
                st.write(prec[:1500])
            else:
                st.info("No precautions retrieved.")

    # openFDA Labels
    labels_df = dfs.get("labels")
    if labels_df is not None and not labels_df.empty:
        st.markdown("---")
        st.markdown("## FDA Label Data (openFDA)")
        st.caption("Source: openFDA Drug Label endpoint")

        first_label = labels_df.iloc[0].to_dict()
        lcol1, lcol2 = st.columns(2)
        with lcol1:
            st.markdown(f"**Brand Name:** {first_label.get('brand_name', 'N/A')}")
            st.markdown(f"**Generic Name:** {first_label.get('generic_name', 'N/A')}")
            st.markdown(f"**Manufacturer:** {first_label.get('manufacturer_name', 'N/A')}")
        with lcol2:
            routes = first_label.get("route", [])
            if isinstance(routes, list):
                st.markdown(f"**Routes:** {', '.join(routes)}")
            substances = first_label.get("substance_name", [])
            if isinstance(substances, list):
                st.markdown(f"**Substances:** {', '.join(substances[:5])}")

        if first_label.get("boxed_warning"):
            st.markdown("### FDA Boxed Warning")
            st.error(first_label["boxed_warning"][:1000])

    # Recall status
    recalls_df = dfs.get("recalls")
    st.markdown("---")
    st.markdown("## Recall Status")
    if recalls_df is not None and not recalls_df.empty:
        st.warning(f"**{len(recalls_df)} recall record(s) found** for {current_drug}")
        st.dataframe(
            recalls_df[["recall_number", "classification", "status", "reason_for_recall", "recalling_firm", "recall_initiation_date"]].head(10),
            width="stretch",
        )
    else:
        st.success(f"No recalls found in openFDA enforcement database for **{current_drug}**")
        st.caption("Absence of recall records does not guarantee absence of risk.")

    # Data lineage
    with st.expander("Data Collection Summary"):
        record_counts = dataset.get("record_counts", {})
        if record_counts:
            df_counts = pd.DataFrame(record_counts).T
            st.dataframe(df_counts, width="stretch")

        st.markdown(f"**Retrieval timestamp:** {dataset.get('retrieval_timestamp', 'N/A')}")
        st.markdown(f"**Pipeline time:** {result.get('elapsed_seconds', 0):.1f}s")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: OCR SCANNER
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "OCR Scanner":
    st.markdown("# OCR Medicine Scanner")
    st.markdown("Upload a medicine package, label, or prescription image to extract the drug name.")

    st.markdown("""
    <div class="disclaimer-box">
    OCR Pipeline: Upload Image → Preprocessing → Text Extraction → Medicine Detection → RxNorm → 5 APIs
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload medicine image",
        type=["png", "jpg", "jpeg"],
        help="Upload a clear photo of a medicine package, label, or prescription",
    )

    # An image uploaded from the sidebar "Medicine Scanner" section
    _pending_bytes = st.session_state.get("pending_ocr_bytes")
    _pending_name = st.session_state.get("pending_ocr_name")
    if uploaded is None and _pending_bytes:
        _buf = io.BytesIO(_pending_bytes)
        _buf.name = _pending_name
        uploaded = _buf
        st.caption(f"Loaded from sidebar scanner: **{_pending_name}**")

    if uploaded:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Uploaded Image")
            image = Image.open(uploaded)
            display_img = resize_for_display(image, max_width=500)
            st.image(display_img, caption=f"{uploaded.name}", width="stretch")

        with col2:
            st.markdown("### OCR Processing")

            with st.spinner("Running OCR..."):
                ocr_result = process_uploaded_image(image)

            detected_name = ""

            # OCR status
            if not ocr_result.get("available"):
                st.error("""
                **Tesseract OCR not installed.**

                To enable OCR:
                - macOS: `brew install tesseract`
                - Ubuntu: `sudo apt-get install tesseract-ocr`
                - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

                You can use the **AI Vision Detection** button below instead, or
                enter the medicine name manually.
                """)

                st.markdown("### AI Vision Detection (no Tesseract needed)")
                if st.button("AI Vision Detection", width="stretch",
                             help="Sends the image to the LLM (vision-capable) to read the medicine name directly"):
                    with st.spinner(" Asking the LLM to read the image..."):
                        from ocr.llm_ocr import detect_medicine_name_with_vision
                        vision = detect_medicine_name_with_vision(image)
                    if vision.get("detected_name"):
                        st.success(f"**AI Detected Medicine:** {vision['detected_name']}")
                        st.caption(f"AI confidence: {vision.get('confidence', 0):.0%} | {vision.get('reason', '')}")
                        ocr_result["detected_name"] = vision["detected_name"]
                    else:
                        st.warning(f"AI could not identify a medicine name. {vision.get('error', '')}")

            else:
                if ocr_result.get("ocr", {}).get("confidence"):
                    conf = ocr_result["ocr"]["confidence"]
                    st.metric("OCR Confidence", f"{conf:.1f}%")

                # Show extracted text
                extracted_text = ocr_result.get("ocr_text", "")
                if extracted_text:
                    with st.expander("Extracted OCR Text"):
                        st.text_area("Raw OCR Output", extracted_text[:3000], height=200, disabled=True)

                # Show detection result
                detection = ocr_result.get("detection", {})
                detected_name = detection.get("detected_name", "")
                method = detection.get("method", "none")
                confidence = detection.get("confidence", 0.0)

                if detected_name:
                    st.success(f"**Detected Medicine:** {detected_name}")
                    st.caption(f"Detection method: {method} | Confidence: {confidence:.0%}")

                    candidates = detection.get("candidates", [])
                    if len(candidates) > 1:
                        with st.expander("Other Candidates"):
                            for c in candidates[1:]:
                                st.markdown(f"- **{c['name']}** (method: {c['method']}, conf: {c['confidence']:.0%})")
                else:
                    st.warning("Could not automatically detect medicine name. Please enter it manually below.")

                # ── LLM layer on top of OCR ────────────────────────────
                st.markdown("---")
                st.markdown("### AI-Assisted Detection (LLM)")

                ai_col1, ai_col2 = st.columns(2)
                with ai_col1:
                    if st.button("AI Vision Detection", width="stretch",
                                 help="Sends the image to the LLM (vision-capable) to read the medicine name directly"):
                        with st.spinner(" Asking the LLM to read the image..."):
                            from ocr.llm_ocr import detect_medicine_name_with_vision
                            vision = detect_medicine_name_with_vision(image)
                        if vision.get("detected_name"):
                            st.success(f"**AI Detected Medicine:** {vision['detected_name']}")
                            st.caption(f"AI confidence: {vision.get('confidence', 0):.0%} | {vision.get('reason', '')}")
                            if not detected_name or vision.get("confidence", 0) >= confidence:
                                detected_name = vision["detected_name"]
                                method = "llm_vision"
                                confidence = vision.get("confidence", 0)
                        else:
                            st.warning(f"AI could not identify a medicine name. {vision.get('error', '')}")

                with ai_col2:
                    if detected_name:
                        if st.button("AI-Correct Detected Name", width="stretch",
                                     help="Uses the LLM to fix OCR character mistakes in the detected name"):
                            with st.spinner(" Correcting with the LLM..."):
                                from ocr.llm_ocr import correct_medicine_name_with_llm
                                correction = correct_medicine_name_with_llm(
                                    ocr_result.get("ocr_text", ""),
                                    detection.get("candidates", []),
                                )
                            if correction.get("detected_name"):
                                st.success(f"**AI Corrected Name:** {correction['detected_name']}")
                                st.caption(f"AI confidence: {correction.get('confidence', 0):.0%} | {correction.get('reason', '')}")
                                detected_name = correction["detected_name"]
                                method = "llm_corrected"
                                confidence = correction.get("confidence", 0)
                            else:
                                st.warning(f"AI correction unavailable. {correction.get('error', '')}")

        # Manual correction / confirmation
        st.markdown("---")
        st.markdown("### Confirm / Correct Medicine Name")
        st.info("You can edit the detected name before running the analysis pipeline.")

        default_name = detected_name or ocr_result.get("detected_name", "")
        confirmed_name = st.text_input(
            "Medicine name to analyze",
            value=default_name,
            placeholder="Enter or confirm the medicine name",
        )

        if st.button("Analyze This Medicine", type="primary") and confirmed_name:
            if is_valid_drug_name(confirmed_name):
                st.session_state.current_drug = sanitize_drug_name(confirmed_name)
                st.session_state.pipeline_result = None
                st.session_state.rag_pipeline = None
                st.session_state.chat_messages = []
                st.success(f"Set to analyze: **{confirmed_name}** — navigate to Medicine Analyzer")
                st.rerun()
            else:
                st.error("Please enter a valid medicine name.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: SAFETY ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Safety Analytics":
    st.markdown("# Safety Analytics")

    if not current_drug or st.session_state.pipeline_result is None:
        st.info(" Analyze a medicine first using the sidebar.")
        st.stop()

    result = st.session_state.pipeline_result
    dataset = result.get("dataset", {})
    features = result.get("features", {})
    analytics = result.get("analytics", {})
    eda = result.get("eda", {})

    st.markdown(f"### Drug: **{current_drug}**")

    st.markdown("""
    <div class="disclaimer-box">
     <strong>Analytical Indicators Only:</strong> All metrics on this page are derived from publicly available reporting databases.
    Higher scores reflect higher observed reporting activity — they do not constitute clinical risk assessments.
    </div>
    """, unsafe_allow_html=True)

    # Safety score
    safety_score = features.get("safety_intelligence_score", {}) if features else {}
    count_features = features.get("count_features", {}) if features else {}

    col1, col2 = st.columns([1, 1])
    with col1:
        if safety_score:
            fig = chart_safety_score_gauge(safety_score)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Safety score not computed.")

    with col2:
        if safety_score:
            fig = chart_safety_score_components(safety_score)
            st.plotly_chart(fig, width="stretch")

    # Key metrics
    st.markdown("---")
    st.markdown("### Key Safety Metrics")
    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        ae_count = count_features.get("adverse_event_count", 0)
        st.metric("Total AE Reports", f"{ae_count:,}")

    with m2:
        serious_ae = count_features.get("serious_ae_count", 0)
        st.metric("Serious AE Reports", f"{serious_ae:,}")

    with m3:
        recall_count = count_features.get("recall_count", 0)
        st.metric("Recall Records", recall_count)

    with m4:
        has_boxed = count_features.get("has_boxed_warning", False)
        st.metric("Boxed Warning", "YES" if has_boxed else "None Found")

    with m5:
        reporting_cls = analytics.get("reporting_classification", {})
        cat = reporting_cls.get("category", "Unknown")
        st.metric("Reporting Category", cat[:25])

    # Reporting classification
    if analytics.get("reporting_classification"):
        rc = analytics["reporting_classification"]
        color_map = {"green": "success", "orange": "warning", "red": "error"}
        getattr(st, color_map.get(rc.get("color", "info"), "info"))(
            f"**{rc['category']}**: {rc['description']}"
        )

    # Adverse reaction charts
    st.markdown("---")
    st.markdown("### Adverse Event Analysis")
    st.caption("Source: FDA FAERS Database (openFDA)")

    top_ae = dataset.get("top_adverse_reactions", [])
    ae_eda = eda.get("adverse_events", {}) if eda else {}

    acol1, acol2 = st.columns([3, 2])
    with acol1:
        fig = chart_top_adverse_reactions(top_ae, current_drug)
        st.plotly_chart(fig, width="stretch")

    with acol2:
        fig = chart_ae_year_trend(ae_eda, current_drug)
        st.plotly_chart(fig, width="stretch")

    # Anomaly detection
    ae_anomalies = analytics.get("ae_anomalies", {})
    if ae_anomalies.get("available"):
        with st.expander("Anomaly Detection — Unusual AE Counts"):
            st.caption("Isolation Forest identifies reactions with statistically unusual report counts.")
            st.caption(ae_anomalies.get("disclaimer", ""))
            anomaly_reactions = [r for r in ae_anomalies.get("reactions", []) if r.get("anomaly")]
            if anomaly_reactions:
                df_anom = pd.DataFrame(anomaly_reactions)
                st.dataframe(df_anom[["term", "count", "anomaly_label"]], width="stretch")
            else:
                st.info("No statistically unusual counts detected.")

    # Recall analysis
    st.markdown("---")
    st.markdown("### Recall Analysis")
    st.caption("Source: openFDA Enforcement Database")

    dfs = dataset.get("dataframes", {})
    recalls_df = dfs.get("recalls")

    rcol1, rcol2 = st.columns([2, 1])
    with rcol1:
        fig = chart_recall_timeline(recalls_df, current_drug)
        st.plotly_chart(fig, width="stretch")
    with rcol2:
        fig = chart_recall_classification(recalls_df, current_drug)
        st.plotly_chart(fig, width="stretch")

    # Recall trend
    recall_trend = analytics.get("recall_trend", {})
    if recall_trend.get("available"):
        trend_dir = recall_trend.get("trend", "")
        sig = recall_trend.get("statistically_significant", False)
        r2 = recall_trend.get("r_squared", 0)
        st.info(
            f"Recall trend: **{trend_dir.upper()}**"
            f"(R²={r2:.3f}, {'statistically significant' if sig else 'not significant at p<0.05'})"
        )

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5: RESEARCH & TRIALS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Research & Trials":
    st.markdown("# Research & Clinical Trials")

    if not current_drug or st.session_state.pipeline_result is None:
        st.info("Analyze a medicine first.")
        st.stop()

    result = st.session_state.pipeline_result
    dataset = result.get("dataset", {})
    eda = result.get("eda", {})
    analytics = result.get("analytics", {})
    dfs = dataset.get("dataframes", {})

    st.markdown(f"### Drug: **{current_drug}**")

    # Summary metrics
    summary = dataset.get("summary", {})
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("PubMed Articles", summary.get("research_articles", 0))
    with m2:
        st.metric("Clinical Trials", summary.get("clinical_trials", 0))
    with m3:
        st.metric("Active Trials", summary.get("active_trials", 0))
    with m4:
        ct_data = result["dataset"]["sources"].get("clinicaltrials", {}).get("data", {})
        total_trials = ct_data.get("total", 0)
        st.metric("Total Trials in Registry", total_trials)

    # Research tabs
    research_tab, trials_tab = st.tabs(["PubMed Research", "Clinical Trials"])

    with research_tab:
        research_eda = eda.get("research", {}) if eda else {}
        st.markdown("### PubMed Research Literature")
        st.caption("Source: PubMed / NCBI E-utilities")

        rcol1, rcol2 = st.columns([2, 1])
        with rcol1:
            fig = chart_publications_by_year(research_eda, current_drug)
            st.plotly_chart(fig, width="stretch")
        with rcol2:
            fig = chart_pub_types(research_eda, current_drug)
            st.plotly_chart(fig, width="stretch")

        # Research trend
        research_trend = analytics.get("research_trend", {})
        if research_trend.get("available"):
            trend = research_trend.get("trend", "")
            sig = research_trend.get("statistically_significant", False)
            r2 = research_trend.get("r_squared", 0)
            st.info(
                f"Publication trend: **{trend.upper()}**"
                f"(R²={r2:.3f}, {'significant' if sig else 'not significant'})"
            )

        jcol1, jcol2 = st.columns([1, 1])
        with jcol1:
            fig = chart_top_journals(research_eda, current_drug)
            st.plotly_chart(fig, width="stretch")
        with jcol2:
            keywords = analytics.get("research_keywords", [])
            fig = chart_research_keywords(keywords, current_drug)
            st.plotly_chart(fig, width="stretch")

        # Article table
        articles_df = dfs.get("articles")
        if articles_df is not None and not articles_df.empty:
            st.markdown("### Retrieved Articles")
            display_cols = [c for c in ["title", "authors", "journal", "pub_date", "source_url"] if c in articles_df.columns]
            display_df = articles_df[display_cols].copy()
            if "source_url" in display_df.columns:
                display_df = display_df.rename(columns={"source_url": "PubMed URL"})
            st.dataframe(display_df, width="stretch", height=300)

    with trials_tab:
        trial_eda = eda.get("clinical_trials", {}) if eda else {}
        trials_df = dfs.get("trials")
        st.markdown("### Clinical Trials")
        st.caption("Source: ClinicalTrials.gov API v2")

        tcol1, tcol2 = st.columns([1, 1])
        with tcol1:
            fig = chart_trials_by_status(trial_eda, current_drug)
            st.plotly_chart(fig, width="stretch")
        with tcol2:
            fig = chart_trials_by_phase(trial_eda, current_drug)
            st.plotly_chart(fig, width="stretch")

        t2col1, t2col2 = st.columns([1, 1])
        with t2col1:
            fig = chart_trials_over_time(trial_eda, current_drug)
            st.plotly_chart(fig, width="stretch")
        with t2col2:
            fig = chart_enrollment_distribution(trials_df, current_drug)
            st.plotly_chart(fig, width="stretch")

        fig = chart_top_sponsors(trial_eda, current_drug)
        st.plotly_chart(fig, width="stretch")

        # Trials table
        if trials_df is not None and not trials_df.empty:
            st.markdown("### Trial Records")
            display_cols = [c for c in ["nct_id", "title", "status_normalized", "phase_normalized",
                                          "lead_sponsor", "enrollment", "start_date", "completion_date"] if c in trials_df.columns]
            st.dataframe(trials_df[display_cols].head(20), width="stretch")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 6: DATA EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Data Explorer":
    st.markdown("# Data Explorer")

    if not current_drug or st.session_state.pipeline_result is None:
        st.info("Analyze a medicine first.")
        st.stop()

    result = st.session_state.pipeline_result
    dataset = result.get("dataset", {})
    dfs = dataset.get("dataframes", {})

    st.markdown(f"### Fused Dataset — **{current_drug}**")

    # Fusion statistics
    st.markdown("### Data Fusion Summary")
    record_counts = dataset.get("record_counts", {})
    if record_counts:
        fusion_data = []
        for source, counts in record_counts.items():
            fusion_data.append({
                "Source": source,
                "Raw Records": counts.get("raw", 0),
                "After Cleaning": counts.get("after_cleaning", 0),
            })
        fusion_df = pd.DataFrame(fusion_data)
        st.dataframe(fusion_df, width="stretch")

    # Dataset selector
    st.markdown("---")
    df_names = {
        "Drug Identity (RxNorm)": "identity",
        "FDA Labels (openFDA)": "labels",
        "Adverse Events (openFDA)": "adverse_events",
        "Recalls (openFDA)": "recalls",
        "Official Labeling (DailyMed)": "dailymed",
        "Research Articles (PubMed)": "articles",
        "Clinical Trials": "trials",
    }

    selected_ds = st.selectbox("Select dataset to explore", list(df_names.keys()))
    df_key = df_names[selected_ds]
    df = dfs.get(df_key)

    if df is not None and not df.empty:
        # Filter / search
        st.markdown(f"**{selected_ds}** — {len(df)} records × {len(df.columns)} columns")

        search_term = st.text_input("Filter rows (searches all text columns)", "")

        display_df = df.copy()
        if search_term:
            mask = pd.Series(False, index=display_df.index)
            for col in display_df.select_dtypes(include="object").columns:
                mask |= display_df[col].astype(str).str.contains(search_term, case=False, na=False)
            display_df = display_df[mask]

        st.dataframe(display_df, width="stretch", height=400)

        # Download
        csv = display_df.to_csv(index=False)
        st.download_button(
            f"Download {selected_ds} as CSV",
            data=csv,
            file_name=f"{current_drug.lower()}_{df_key}.csv",
            mime="text/csv",
        )

        # Column stats
        with st.expander("Column Statistics"):
            st.dataframe(display_df.describe(include="all"), width="stretch")
    else:
        st.info(f"No data available for {selected_ds}")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 7: AI INTELLIGENCE (LLM layer on top — fused into ONE CSV)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "AI Intelligence":
    st.markdown("# AI Intelligence Layer")
    st.markdown(
        "The LLM layer on top of the pipeline understands the medicine and all five "
        "API payloads, extracts structured drug intelligence, and fuses everything "
        "into **one CSV file**."
    )

    if not current_drug or st.session_state.pipeline_result is None:
        st.info("Analyze a medicine first.")
        st.stop()

    result = st.session_state.pipeline_result
    llm_intel = result.get("llm_intelligence") or {}

    if not llm_intel:
        st.warning("LLM intelligence layer did not run (pipeline may have failed).")
        st.stop()

    record = llm_intel.get("record", {})
    used_llm = llm_intel.get("used_llm", False)

    # Status banner
    if used_llm:
        st.success(f"LLM extraction: **successful** ({llm_intel.get('latency_ms', 0)} ms)")

    st.markdown("""
    <div class="disclaimer-box">
    All intelligence fields are extracted from the five retrieved public sources.
    They are informational only — not clinical recommendations.
    </div>
    """, unsafe_allow_html=True)

    # Identity metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Drug", record.get("drug_name") or current_drug)
    with col2:
        st.metric("Generic Name", record.get("generic_name") or "N/A")
    with col3:
        st.metric("Drug Class", (record.get("drug_class") or "N/A")[:28])
    with col4:
        srcs = record.get("sources_used", [])
        st.metric("Sources Used", len(srcs) if srcs else "N/A")

    # Brand names / uses / dosage forms
    brands = record.get("brand_names") or []
    uses = record.get("therapeutic_uses") or []
    dosage = record.get("dosage_forms") or []
    if brands:
        st.markdown("### Brand Names")
        st.write(", ".join(brands[:10]))
    if uses:
        st.markdown("### Therapeutic Uses")
        for u in uses[:8]:
            st.markdown(f"- {u}")
    if dosage:
        st.markdown("### Dosage Forms")
        st.write(", ".join(dosage[:8]))

    # Key text sections
    st.markdown("---")
    tabs = st.tabs([
        "Boxed Warning", "Warnings", "Contraindications",
        "Precautions", "Interactions", "Storage",
        "Research", "Trials", "Recalls",
    ])

    boxed = record.get("boxed_warning", "")
    warnings = record.get("warnings", "")
    contra = record.get("contraindications", "")
    prec = record.get("precautions", "")
    interactions = record.get("drug_interactions", "")
    storage = record.get("storage_instructions", "")
    research = record.get("research_highlights", "")
    trials = record.get("trial_highlights", "")
    recalls = record.get("recall_summary", "")

    with tabs[0]:
        if boxed:
            st.error(boxed[:2000])
        else:
            st.info("No boxed warning in retrieved data.")
    with tabs[1]:
        st.write(warnings[:2500] if warnings else "No warnings in retrieved data.")
    with tabs[2]:
        st.write(contra[:2500] if contra else "No contraindications in retrieved data.")
    with tabs[3]:
        st.write(prec[:2500] if prec else "No precautions in retrieved data.")
    with tabs[4]:
        st.write(interactions[:2500] if interactions else "No interactions in retrieved data.")
    with tabs[5]:
        st.success(storage[:800] if storage else "No storage instructions in retrieved data.")
    with tabs[6]:
        st.write(research[:2500] if research else "No research highlights.")
    with tabs[7]:
        st.write(trials[:2500] if trials else "No trial highlights.")
    with tabs[8]:
        st.warning(recalls[:2500] if recalls else "No recall records in retrieved data.")

    # Top adverse reactions table
    reactions = record.get("top_adverse_reactions") or []
    if reactions:
        st.markdown("---")
        st.markdown("### Top Adverse Reactions (FAERS-derived)")
        reaction_rows = []
        for r in reactions:
            if isinstance(r, dict):
                reaction_rows.append({
                    "Reaction": r.get("reaction", ""),
                    "Report Count": r.get("report_count", ""),
                    "Signal Strength": r.get("signal_strength", ""),
                    "Notes": r.get("notes", ""),
                })
            else:
                reaction_rows.append({"Reaction": str(r), "Report Count": "", "Signal Strength": "", "Notes": ""})
        st.dataframe(pd.DataFrame(reaction_rows), width="stretch")

    # Known risks & data gaps
    risks = record.get("known_risks") or []
    gaps = record.get("data_gaps") or []
    if risks:
        st.markdown("### Known Risks")
        for r in risks[:8]:
            st.markdown(f"- {r}")
    if gaps:
        with st.expander("Data Gaps"):
            for g in gaps[:8]:
                st.markdown(f"- {g}")

    # Safety summary
    if record.get("safety_summary"):
        st.markdown("---")
        st.markdown("### Safety Summary")
        st.info(record["safety_summary"][:2000])

    # ── The fused CSV outputs ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Fused CSV Outputs (all data in one file)")
    st.caption("Written to `data/fused/` during the pipeline run. Every column is source-attributed.")

    csv_path = llm_intel.get("csv_path", "")
    all_csv_path = llm_intel.get("all_sources_csv_path", "")
    column_sources = llm_intel.get("column_sources") or {}

    # Column → Source legend
    with st.expander("Column → Source Legend"):
        legend_rows = []
        for col, src in column_sources.items():
            legend_rows.append({"CSV Column": col, "Data Source": src})
        if legend_rows:
            st.markdown("** All-Sources CSV columns** — each column is prefixed with its source (`rxnorm_`, `openfda_labels_`, `openfda_adverse_events_`, `openfda_recalls_`, `dailymed_`, `pubmed_`, `clinicaltrials_`).")
            st.dataframe(pd.DataFrame(legend_rows), width="stretch", height=220)
        else:
            st.markdown("No column-level attribution available yet — run the pipeline first.")
        st.markdown("** LLM Intelligence CSV columns** — `llm_<field>` columns are curated from all sources; the `intelligence_field_sources` column maps each field to the APIs it was derived from.")

    col1, col2 = st.columns(2)
    with col1:
        if csv_path and Path(csv_path).exists():
            st.markdown(f"** LLM Intelligence Record** (1 row — all sources fused)")
            df_intel = pd.read_csv(csv_path)
            st.dataframe(df_intel, width="stretch", height=200)
            st.download_button(
                "Download LLM Intelligence CSV",
                data=df_intel.to_csv(index=False),
                file_name=Path(csv_path).name,
                mime="text/csv",
            )
        else:
            st.info("LLM intelligence CSV not available.")
    with col2:
        if all_csv_path and Path(all_csv_path).exists():
            st.markdown(f"** All-Sources Fused CSV** (clean, source-attributed rows)")
            df_all = pd.read_csv(all_csv_path)
            st.markdown(f"*{len(df_all)} rows × {len(df_all.columns)} cols*")
            st.dataframe(df_all, width="stretch", height=200)
            st.download_button(
                "Download All-Sources CSV",
                data=df_all.to_csv(index=False),
                file_name=Path(all_csv_path).name,
                mime="text/csv",
            )
        else:
            st.info("All-sources CSV not available.")

    # Raw record expander
    with st.expander("Raw Intelligence Record (JSON)"):
        st.json(record)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 8: EDA DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "EDA Dashboard":
    st.markdown("# Exploratory Data Analysis Dashboard")

    if not current_drug or st.session_state.pipeline_result is None:
        st.info("Analyze a medicine first.")
        st.stop()

    result = st.session_state.pipeline_result
    eda = result.get("eda", {})
    dataset = result.get("dataset", {})
    analytics = result.get("analytics", {})

    st.markdown(f"### EDA Report — **{current_drug}**")
    st.markdown("""
    <div class="disclaimer-box">
     This EDA is based on data retrieved from five public APIs. Counts reflect reported/registered data,
    not a complete picture of all occurrences. Statistical trends are exploratory, not confirmatory.
    </div>
    """, unsafe_allow_html=True)

    # Summary statistics table
    summary = dataset.get("summary", {})
    st.markdown("### Dataset Overview")
    ov_col1, ov_col2, ov_col3 = st.columns(3)
    with ov_col1:
        st.metric("AE Reports", f"{summary.get('total_adverse_events', 0):,}")
        st.metric("AE Records Retrieved", summary.get("ae_records_retrieved", 0))
    with ov_col2:
        st.metric("Recall Records", summary.get("recall_records", 0))
        st.metric("Research Articles", summary.get("research_articles", 0))
    with ov_col3:
        st.metric("Clinical Trials", summary.get("clinical_trials", 0))
        st.metric("Active Trials", summary.get("active_trials", 0))

    # AE EDA
    ae_eda = eda.get("adverse_events", {})
    if ae_eda.get("available"):
        st.markdown("---")
        st.markdown("### Adverse Events EDA")

        ecol1, ecol2, ecol3 = st.columns(3)
        with ecol1:
            st.metric("Records", ae_eda.get("total_records", 0))
        with ecol2:
            serious_rate = ae_eda.get("serious_rate", 0)
            st.metric("Serious Rate", f"{serious_rate:.1%}")
        with ecol3:
            unique_rx = ae_eda.get("unique_reactions", 0)
            st.metric("Unique Reactions", unique_rx)

        if ae_eda.get("date_range"):
            dr = ae_eda["date_range"]
            st.caption(f"Date range: {dr.get('min', 'N/A')} to {dr.get('max', 'N/A')}")

        # Country distribution
        if ae_eda.get("country_distribution"):
            import plotly.express as px
            country_df = pd.DataFrame(
                list(ae_eda["country_distribution"].items()),
                columns=["Country", "Reports"]
            )
            fig = px.bar(country_df, x="Country", y="Reports", title="AE Reports by Country")
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, width="stretch")

    # Recall EDA
    recall_eda = eda.get("recalls", {})
    if recall_eda.get("available"):
        st.markdown("---")
        st.markdown("### Recalls EDA")
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            st.metric("Recall Records", recall_eda.get("total_records", 0))
            if recall_eda.get("classification_distribution"):
                st.json(recall_eda["classification_distribution"])
        with rcol2:
            if recall_eda.get("date_range"):
                dr = recall_eda["date_range"]
                st.info(f"Recall date range: {dr.get('min', 'N/A')} to {dr.get('max', 'N/A')}")
            if recall_eda.get("top_reasons"):
                st.markdown("**Top recall reasons:**")
                for r in recall_eda["top_reasons"][:5]:
                    st.markdown(f"- {r[:100]}")

    # Research EDA
    research_eda = eda.get("research", {})
    if research_eda.get("available"):
        st.markdown("---")
        st.markdown("### Research Literature EDA")
        recol1, recol2, recol3 = st.columns(3)
        with recol1:
            st.metric("Articles Retrieved", research_eda.get("total_articles", 0))
        with recol2:
            yr = research_eda.get("year_range", {})
            if yr:
                st.metric("Year Range", f"{yr.get('min', 'N/A')} – {yr.get('max', 'N/A')}")
        with recol3:
            med_yr = research_eda.get("median_pub_year", None)
            if med_yr:
                st.metric("Median Pub Year", int(med_yr))

    # Trial EDA
    trial_eda = eda.get("clinical_trials", {})
    if trial_eda.get("available"):
        st.markdown("---")
        st.markdown("### Clinical Trials EDA")
        tcol1, tcol2, tcol3 = st.columns(3)
        with tcol1:
            st.metric("Total Trials", trial_eda.get("total_trials", 0))
        with tcol2:
            st.metric("Status Types", len(trial_eda.get("status_distribution", {})))
        with tcol3:
            enroll = trial_eda.get("enrollment_stats", {})
            if enroll:
                st.metric("Median Enrollment", int(enroll.get("median", 0)))

        if trial_eda.get("enrollment_stats"):
            enroll = trial_eda["enrollment_stats"]
            st.markdown(
                f"**Enrollment** — Mean: {enroll.get('mean', 0):.0f}, "
                f"Median: {enroll.get('median', 0):.0f}, "
                f"Max: {enroll.get('max', 0):.0f}, "
                f"Total: {enroll.get('total', 0):.0f}"
            )

    # Clustering
    ae_clustering = analytics.get("ae_clustering", {})
    if ae_clustering.get("available"):
        st.markdown("---")
        st.markdown("### ML — K-Means Clustering (Adverse Reactions)")
        st.caption(ae_clustering.get("disclaimer", ""))
        cluster_df = pd.DataFrame(ae_clustering.get("reactions", []))
        if not cluster_df.empty:
            import plotly.express as px
            fig = px.scatter(
                cluster_df, x="count", y="term", color="cluster_name",
                title="Adverse Reaction Clusters by Report Count",
                labels={"count": "Reports", "term": "Reaction", "cluster_name": "Cluster"},
                color_discrete_map={
                    "Low Frequency": "#4caf50",
                    "Medium Frequency": "#ff9800",
                    "High Frequency": "#f44336",
                },
            )
            fig.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, width="stretch")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 8: RAG CHATBOT
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "RAG Chatbot":
    st.markdown("# Drug Safety Intelligence Chatbot")

    if not current_drug or st.session_state.pipeline_result is None:
        st.info("Analyze a medicine first to enable the chatbot.")
        st.stop()

    rag = st.session_state.rag_pipeline
    if rag is None or not rag.is_ready:
        st.warning("RAG knowledge base is being built... Please wait and refresh.")
        st.stop()

    # Initialize chatbot
    if st.session_state.chatbot is None:
        st.session_state.chatbot = get_chatbot()

    chatbot = st.session_state.chatbot
    chatbot.set_drug_context(current_drug, rag)

    # RAG stats
    rag_stats = rag.get_stats()
    with st.expander("RAG Knowledge Base Info"):
        scol1, scol2, scol3, scol4 = st.columns(4)
        with scol1:
            st.metric("Documents", rag_stats.get("documents", 0))
        with scol2:
            st.metric("Chunks", rag_stats.get("chunks", 0))
        with scol3:
            st.metric("Vectors", rag_stats.get("vectors", 0))
        with scol4:
            st.metric("Build Time", f"{rag_stats.get('build_time_seconds', 0):.1f}s")

    st.markdown("""
    <div class="disclaimer-box">
     This chatbot answers using retrieved evidence from five official sources. It does NOT diagnose,
    prescribe, or provide clinical recommendations. Always consult a qualified healthcare professional.
    </div>
    """, unsafe_allow_html=True)

    # Chat interface
    st.markdown(f"### Chatting about: **{current_drug}**")

    # Suggested questions
    with st.expander("Suggested Questions"):
        suggested = [
            f"What are the main warnings for {current_drug}?",
            f"Has {current_drug} been recalled?",
            f"What adverse events are reported for {current_drug}?",
            f"What does the official label say about {current_drug}?",
            f"What recent research exists on {current_drug}?",
            f"Are there active clinical trials for {current_drug}?",
            f"What are the storage instructions for {current_drug}?",
            f"What contraindications are listed for {current_drug}?",
            f"Summarize the safety information for {current_drug}.",
        ]
        for q in suggested:
            if st.button(q, width="content", key=f"suggest_{q[:30]}"):
                st.session_state._suggested_question = q
                st.rerun()

    # Display chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Show sources for assistant messages
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander("Retrieved Sources"):
                    for src in msg["sources"]:
                        icon_map = {
                            "openFDA": "",
                            "DailyMed": "",
                            "PubMed": "",
                            "ClinicalTrials.gov": "",
                            "RxNorm": "",
                        }
                        icon = icon_map.get(src.get("source", ""), "")
                        st.markdown(
                            f"{icon} **{src['source']}** — {src['source_type']} "
                            f"(relevance: {src.get('relevance_score', 0):.3f})"
                        )
                        if src.get("url"):
                            st.markdown(f"→ [{src['url']}]({src['url']})")

    # Handle suggested question
    preset_q = st.session_state.pop("_suggested_question", None) if hasattr(st.session_state, '_suggested_question') else None

    # Chat input
    user_question = st.chat_input(f"Ask about {current_drug}...") or preset_q

    if user_question:
        # Add user message to UI
        with st.chat_message("user"):
            st.markdown(user_question)
        st.session_state.chat_messages.append({"role": "user", "content": user_question})

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner(" Retrieving evidence and generating answer..."):
                response = chatbot.ask(user_question)

            answer = response.get("answer", "")
            sources = response.get("sources", [])
            retrieved = response.get("retrieved_chunks", [])

            st.markdown(answer)

            # Sources
            if sources:
                with st.expander(f"Retrieved Sources ({len(sources)})"):
                    for src in sources:
                        icon_map = {"openFDA": "", "DailyMed": "", "PubMed": "",
                                    "ClinicalTrials.gov": "", "RxNorm": ""}
                        icon = icon_map.get(src.get("source", ""), "")
                        st.markdown(
                            f"{icon} **{src['source']}** — {src['source_type']} "
                            f"(relevance: {src.get('relevance_score', 0):.3f})"
                        )
                        if src.get("url"):
                            st.markdown(f"→ [{src['url']}]({src['url']})")

            # Retrieved context
            if retrieved:
                with st.expander(f"Retrieved Evidence ({len(retrieved)} chunks)"):
                    for i, chunk in enumerate(retrieved[:3], 1):
                        meta = chunk.get("metadata", {}).get("metadata", {})
                        source = meta.get("source", "Unknown")
                        st.markdown(f"**Chunk {i} — {source}**")
                        st.text(chunk.get("text", "")[:400])
                        st.markdown("---")

        # Store in history
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
        })

    # Clear history button
    if st.session_state.chat_messages:
        if st.button("Clear Conversation"):
            st.session_state.chat_messages = []
            chatbot.clear_history()
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 9: SYSTEM SOURCES
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "System Sources":
    st.markdown("# System Data Sources")
    st.markdown("The five official APIs powering this intelligence platform.")

    result = st.session_state.pipeline_result
    dataset = result.get("dataset", {}) if result else {}
    summary = dataset.get("summary", {}) if dataset else {}
    source_status = result.get("source_status", {}) if result else {}

    apis = [
        {
            "name": "openFDA",
            "icon": "",
            "badge": "badge-openfda",
            "purpose": "Drug adverse events (FAERS), drug recalls (enforcement), drug labels (SPL)",
            "url": "https://api.fda.gov",
            "doc_url": "https://open.fda.gov/apis/drug/",
            "key_required": False,
            "metrics": [
                ("AE Reports Retrieved", f"{summary.get('ae_records_retrieved', 0):,}"),
                ("AE Total in DB", f"{summary.get('total_adverse_events', 0):,}"),
                ("Recalls Found", str(summary.get("recall_records", 0))),
            ],
        },
        {
            "name": "RxNorm",
            "icon": "",
            "badge": "badge-rxnorm",
            "purpose": "Drug name normalization, RxCUI identifiers, brand/generic relationships, drug classes",
            "url": "https://rxnav.nlm.nih.gov/REST",
            "doc_url": "https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html",
            "key_required": False,
            "metrics": [
                ("Normalization", "RxCUI lookup"),
                ("Ingredients", "Active ingredient mapping"),
                ("Classes", "Drug class lookup"),
            ],
        },
        {
            "name": "DailyMed",
            "icon": "",
            "badge": "badge-dailymed",
            "purpose": "Official FDA-approved Structured Product Labels (SPL), dosage, warnings, contraindications",
            "url": "https://dailymed.nlm.nih.gov/dailymed/services/v2",
            "doc_url": "https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm",
            "key_required": False,
            "metrics": [
                ("Label Type", "Structured Product Label (SPL)"),
                ("Content", "Official FDA-approved labeling"),
                ("Authority", "National Library of Medicine"),
            ],
        },
        {
            "name": "PubMed",
            "icon": "",
            "badge": "badge-pubmed",
            "purpose": "Scientific literature, research articles, abstracts, publication metadata",
            "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            "doc_url": "https://www.ncbi.nlm.nih.gov/books/NBK25500/",
            "key_required": False,
            "metrics": [
                ("Articles Retrieved", str(summary.get("research_articles", 0))),
                ("Database", "NCBI PubMed"),
                ("Records", "20M+ indexed articles"),
            ],
        },
        {
            "name": "ClinicalTrials.gov",
            "icon": "",
            "badge": "badge-ct",
            "purpose": "Clinical trial data, study status, phases, interventions, trial summaries",
            "url": "https://clinicaltrials.gov/api/v2",
            "doc_url": "https://clinicaltrials.gov/data-api/api",
            "key_required": False,
            "metrics": [
                ("Trials Retrieved", str(summary.get("clinical_trials", 0))),
                ("Active Trials", str(summary.get("active_trials", 0))),
                ("Registry", "NIH ClinicalTrials.gov"),
            ],
        },
    ]

    for api in apis:
        name = api["name"]
        status = source_status.get(name, {})
        is_ok = status.get("ok", None) # None = not yet queried

        status_str = ""
        if is_ok is True:
            status_str = "**Online & Retrieved**"
        elif is_ok is False:
            error = status.get("error", "Unknown error")
            status_str = f"**Error:** {error}"
        else:
            status_str = "**Not yet queried** — analyze a medicine first"

        with st.expander(f"{api['icon']} {name} — {status_str}"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**Purpose:** {api['purpose']}")
                st.markdown(f"**API Base URL:** `{api['url']}`")
                st.markdown(f"**Documentation:** [{api['doc_url']}]({api['doc_url']})")
                st.markdown(f"**API Key Required:** {' No' if not api['key_required'] else ' Yes'}")
            with c2:
                st.markdown("**Retrieved Data:**")
                for label, value in api["metrics"]:
                    st.markdown(f"- **{label}:** {value}")

    # Architecture note
    st.markdown("---")
    st.markdown("### API Integration Architecture")
    st.markdown("""
    ```
    1. RxNorm → Normalize drug name → RxCUI + canonical name
    2. openFDA → Drug labels + adverse events + recalls
    3. DailyMed → Official SPL labeling (by RxCUI or name)
    4. PubMed → Research articles (by ingredient name)
    5. ClinicalTrials → Active/completed trials (by ingredient name)
    
    All 5 APIs → Data Fusion → Unified Dataset → RAG → LLM
    ```
    """)

    st.markdown("### Pipeline Performance")
    if result:
        elapsed = result.get("elapsed_seconds", 0)
        st.info(f"Last pipeline run: **{elapsed:.1f} seconds** for all 5 APIs + fusion + EDA")
    else:
        st.info("No pipeline run yet. Analyze a medicine to see performance metrics.")
