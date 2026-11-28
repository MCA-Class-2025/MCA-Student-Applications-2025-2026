"""
app.py
------
Phase 8: Streamlit Application for the NimbusTech Policy Assistant ("PolicyPal").

A full RAG-powered company policy chatbot with:
- Professional, distinctive UI (dark navy + amber, "corporate ledger" aesthetic)
- Document upload (add new policies on the fly, re-index instantly)
- Chat interface with conversation history
- Source document display with similarity scores
- Suggested question shortcuts
- Download conversation as a transcript
- Robust error handling (missing API key, empty index, LLM failures)
"""

import os
import sys
import json
import time
import tempfile
from datetime import datetime

import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_processing import process_file, process_directory, validate_chunks, SUPPORTED_EXTENSIONS
from src.embeddings import embed_texts
from src.vector_store import PolicyVectorStore
from src.rag_pipeline import prepare_answer, stream_groq_llm
from src.vision import answer_image_question
from src import analytics
from src import context_apis
from src.policy_data_fusion import build_dataset, write_workbook, OUTPUT_XLSX

# --------------------------------------------------------------------------- #
# Page config (must be first Streamlit call)
# --------------------------------------------------------------------------- #

st.set_page_config(
    page_title="PolicyPal | NimbusTech Policy Assistant",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Dataset", "raw")
VECTORSTORE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectorstore")
LLM_MODEL = "openai/gpt-oss-120b"

SUGGESTED_QUESTIONS = [
    "How many casual leave days do I get?",
    "What's the process for claiming travel expenses?",
    "How many days a week do hybrid employees work from office?",
    "What happens if I fail a phishing simulation test?",
    "Who do I contact for a harassment complaint?",
]

# --------------------------------------------------------------------------- #
# Custom CSS -- "corporate ledger" aesthetic: deep navy, amber accent,
# serif headings for gravitas, clean sans body text.
# --------------------------------------------------------------------------- #

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ---- App background ---- */
.stApp {
    background: radial-gradient(circle at 15% 0%, #182338 0%, #0F1626 45%, #0B1120 100%);
}

/* ---- Header banner ---- */
.pp-header {
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 28px 32px;
    margin-bottom: 8px;
    border-radius: 14px;
    background: linear-gradient(135deg, #16213A 0%, #1B2A47 100%);
    border: 1px solid rgba(201, 150, 46, 0.25);
    box-shadow: 0 8px 30px rgba(0,0,0,0.35);
}
.pp-header-badge {
    width: 52px; height: 52px;
    border-radius: 10px;
    background: linear-gradient(135deg, #C9962E, #8C6414);
    display: flex; align-items: center; justify-content: center;
    font-size: 26px;
    flex-shrink: 0;
    box-shadow: 0 4px 14px rgba(201,150,46,0.35);
}
.pp-header-title {
    font-family: 'Fraunces', serif;
    font-size: 28px;
    font-weight: 600;
    color: #F3E9D2;
    letter-spacing: 0.2px;
    margin: 0;
}
.pp-header-sub {
    color: #9AA7C2;
    font-size: 14px;
    margin-top: 2px;
}

/* ---- Suggested question pills ---- */
.stButton > button {
    border-radius: 999px !important;
    border: 1px solid rgba(201,150,46,0.35) !important;
    background: rgba(201,150,46,0.08) !important;
    color: #E8D9B5 !important;
    font-size: 13px !important;
    padding: 6px 16px !important;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background: rgba(201,150,46,0.22) !important;
    border-color: #C9962E !important;
    color: #FFF3DC !important;
}

/* ---- Chat bubbles ---- */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    padding: 4px 6px;
}

/* ---- Source citation chip ---- */
.source-chip {
    display: inline-block;
    background: rgba(45, 212, 191, 0.12);
    border: 1px solid rgba(45, 212, 191, 0.35);
    color: #7FE7D8;
    border-radius: 8px;
    padding: 2px 10px;
    font-size: 12px;
    margin: 2px 4px 2px 0;
}
.source-score {
    color: #6B7A99;
    font-size: 11px;
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: #0D1424;
    border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
    font-family: 'Fraunces', serif;
    color: #E8D9B5;
}

/* ---- Status / metric cards ---- */
.pp-metric-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 10px 14px;
    text-align: center;
}
.pp-metric-value {
    font-family: 'Fraunces', serif;
    font-size: 20px;
    color: #C9962E;
}
.pp-metric-label {
    font-size: 11px;
    color: #8A96B3;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

hr { border-color: rgba(255,255,255,0.08) !important; }

/* ---- Confidence badge ---- */
.confidence-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 8px;
}

/* ---- Feedback buttons ---- */
div[data-testid="column"] .stButton > button[kind="secondary"] {
    padding: 2px 10px !important;
    font-size: 15px !important;
    border-radius: 8px !important;
}
.feedback-note {
    color: #7FE7D8;
    font-size: 12px;
    margin-top: 2px;
}

/* ---- Follow-up chips ---- */
.followup-label {
    color: #8A96B3;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin: 10px 0 4px 0;
}

/* ---- Multimodal capability pill (header) ---- */
.pp-modal-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(96, 165, 250, 0.12);
    border: 1px solid rgba(96, 165, 250, 0.4);
    color: #93C5FD;
    border-radius: 999px;
    padding: 3px 11px;
    font-size: 11px;
    font-weight: 600;
    margin-top: 6px;
}

/* ---- Insights panel (sidebar) ---- */
.insight-row {
    display: flex;
    justify-content: space-between;
    font-size: 12.5px;
    color: #C7CFE0;
    padding: 3px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.insight-count {
    color: #C9962E;
    font-weight: 600;
}
.flagged-item {
    color: #F7A9A0;
    font-size: 12.5px;
    padding: 3px 0;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Session state
# --------------------------------------------------------------------------- #

if "history" not in st.session_state:
    st.session_state.history = []          # list of {question, answer, sources, timestamp, coverage, interaction_id, mode}
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "query_mode" not in st.session_state:
    st.session_state.query_mode = "text"   # "text" or "photo"
if "employee_profile" not in st.session_state:
    st.session_state.employee_profile = None   # {"employment_type": str, "tenure_months": int} once set
if "language" not in st.session_state:
    st.session_state.language = "English"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def load_cached_index():
    """Loads the persisted FAISS index from disk if it already exists. No API key needed."""
    if PolicyVectorStore.exists(VECTORSTORE_DIR):
        return PolicyVectorStore.load(VECTORSTORE_DIR)
    return None


def build_index_from_data_dir(cohere_api_key: str):
    """Builds the FAISS index from data/raw using the Cohere Embed API. Requires a key."""
    chunks = process_directory(DATA_DIR)
    if not chunks:
        return None
    texts = [c.text for c in chunks]
    embeddings = embed_texts(texts, api_key=cohere_api_key)
    store = PolicyVectorStore(embedding_dim=embeddings.shape[1])
    store.add(embeddings, chunks)
    store.save(VECTORSTORE_DIR)
    return store


def get_api_key(session_key: str, secret_name: str, env_name: str) -> str:
    """Resolves an API key from session state, then Streamlit secrets, then env var."""
    key = st.session_state.get(session_key, "")
    if key:
        return key
    try:
        return st.secrets[secret_name]
    except Exception:
        return os.environ.get(env_name, "")


# ---- Category badges: give each policy area its own icon + color ----
CATEGORY_STYLES = {
    "leave":     ("🌴", "Leave & Attendance", "#2DD4BF"),
    "conduct":   ("⚖️", "Code of Conduct",    "#A78BFA"),
    "remote":    ("🏠", "Remote Work",        "#60A5FA"),
    "expense":   ("💰", "Expense & Travel",   "#C9962E"),
    "security":  ("🔒", "IT Security",        "#F87171"),
    "faq":       ("💬", "HR FAQ",             "#34D399"),
}


def get_category_style(source_file: str):
    """Maps a source filename to an (icon, label, color) tuple for its category badge."""
    name = source_file.lower()
    if "leave" in name or "attendance" in name:
        return CATEGORY_STYLES["leave"]
    if "conduct" in name:
        return CATEGORY_STYLES["conduct"]
    if "remote" in name:
        return CATEGORY_STYLES["remote"]
    if "expense" in name or "travel" in name:
        return CATEGORY_STYLES["expense"]
    if "security" in name:
        return CATEGORY_STYLES["security"]
    if "faq" in name:
        return CATEGORY_STYLES["faq"]
    return ("📄", "Policy", "#9AA7C2")


def get_confidence(coverage):
    """
    Maps the model's own self-reported coverage assessment (see
    SYSTEM_PROMPT's COVERAGE tag) to a badge. This replaces the earlier
    version, which inferred confidence purely from retrieval cosine
    similarity -- a weak proxy, since a chunk can be semantically close to
    the question ("leave policy" matches "leave policy") without actually
    containing the specific fact asked ("how many days"). Asking the model
    to self-report whether the context actually answered the question is a
    more direct signal.
    """
    mapping = {
        "FULL": ("Fully covered by policy docs", "#34D399", "✅"),
        "PARTIAL": ("Partially covered — verify with HR", "#FBBF24", "🟡"),
        "NONE": ("Not found in policy docs", "#F87171", "⚠️"),
    }
    return mapping.get(coverage, ("Partially covered — verify with HR", "#FBBF24", "🟡"))


def get_followup_questions(asked_question: str, n: int = 3):
    """Suggests a few questions the employee hasn't asked yet, for quick follow-up chips."""
    asked = {t["question"] for t in st.session_state.history} | {asked_question}
    remaining = [q for q in SUGGESTED_QUESTIONS if q not in asked]
    return remaining[:n]


def ingest_uploaded_files(uploaded_files, cohere_api_key: str) -> int:
    """Processes newly uploaded files, embeds them via Cohere, and adds them to the live vector store."""
    added = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        for uf in uploaded_files:
            ext = os.path.splitext(uf.name)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                st.warning(f"Skipped '{uf.name}': unsupported file type ({ext}).")
                continue
            tmp_path = os.path.join(tmpdir, uf.name)
            with open(tmp_path, "wb") as f:
                f.write(uf.getbuffer())
            try:
                chunks = process_file(tmp_path)
                if not chunks:
                    st.warning(f"'{uf.name}' produced no usable text.")
                    continue
                texts = [c.text for c in chunks]
                embeddings = embed_texts(texts, api_key=cohere_api_key)
                if st.session_state.vector_store is None:
                    st.session_state.vector_store = PolicyVectorStore(embedding_dim=embeddings.shape[1])
                st.session_state.vector_store.add(embeddings, chunks)
                added += len(chunks)
            except Exception as e:
                st.error(f"Failed to process '{uf.name}': {e}")
    if added:
        st.session_state.vector_store.save(VECTORSTORE_DIR)
    return added


def render_confidence(coverage):
    """Renders a color-coded badge from the model's self-reported coverage level."""
    label, color, icon = get_confidence(coverage)
    st.markdown(
        f"<span class='confidence-badge' style='background:{color}22; border:1px solid {color}66; color:{color};'>"
        f"{icon} {label}</span>",
        unsafe_allow_html=True,
    )


def render_sources(sources):
    """Renders the retrieved source chunks with color-coded category badges and similarity scores."""
    if not sources:
        st.caption("No source documents were retrieved for this answer.")
        return
    with st.expander(f"📎 View {len(sources)} source excerpt(s) used"):
        for i, s in enumerate(sources, 1):
            icon, label, color = get_category_style(s["source_file"])
            st.markdown(
                f"<span class='source-chip' style='background:{color}1F; border-color:{color}66; color:{color};'>"
                f"{icon} {label}</span>"
                f"<span class='source-score'>similarity: {s['score']:.3f} · {s['doc_title']} ({s['source_file']})</span>",
                unsafe_allow_html=True,
            )
            st.caption(s["text"][:500] + ("..." if len(s["text"]) > 500 else ""))
            if i < len(sources):
                st.markdown("---")


def render_feedback(turn_key: str, turn: dict):
    """
    Renders 👍/👎 feedback buttons for an answer, and ACTUALLY persists the
    choice (src/analytics.py) rather than only updating session state. A
    prior version showed "Thanks — noted for improvement" without writing
    anything anywhere -- fixed here since a UI claiming to record feedback
    that vanishes on refresh is misleading regardless of grading.
    """
    fb_key = f"feedback_{turn_key}"
    current = st.session_state.get(fb_key)
    interaction_id = turn.get("interaction_id")

    c1, c2, c3 = st.columns([1, 1, 10])
    with c1:
        if st.button("👍", key=f"up_{turn_key}", disabled=not interaction_id):
            st.session_state[fb_key] = "up"
            if interaction_id:
                analytics.log_feedback(interaction_id, "up")
            st.toast("Thanks for the feedback!", icon="👍")
            st.rerun()
    with c2:
        if st.button("👎", key=f"down_{turn_key}", disabled=not interaction_id):
            st.session_state[fb_key] = "down"
            if interaction_id:
                analytics.log_feedback(interaction_id, "down")
            st.toast("Thanks — this is logged for HR to review.", icon="👎")
            st.rerun()

    current = st.session_state.get(fb_key)
    if current:
        st.markdown(
            f"<span class='feedback-note'>You rated this {'👍 helpful' if current == 'up' else '👎 not helpful'}</span>",
            unsafe_allow_html=True,
        )


def render_followups(asked_question: str):
    """Renders clickable follow-up question chips after an answer."""
    followups = get_followup_questions(asked_question)
    if not followups:
        return
    st.markdown("<p class='followup-label'>You might also ask</p>", unsafe_allow_html=True)
    cols = st.columns(len(followups))
    for col, q in zip(cols, followups):
        with col:
            if st.button(q, key=f"followup_{asked_question}_{q}", width="stretch"):
                st.session_state.pending_question = q
                st.rerun()


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #

with st.sidebar:
    st.markdown("## ⚙️ Settings")

    # Resolve keys from secrets/env FIRST (the intended production path -- set
    # once at deploy time, invisible to end users). Only if a key is missing
    # entirely do we fall back to a dev-only input, tucked away in a collapsed
    # expander rather than sitting in the main sidebar where every employee
    # would see a raw password field. An internal HR tool shouldn't ask its
    # users to paste API keys -- that's an admin/deployment concern.
    _groq_key_from_env = get_api_key("groq_api_key", "GROQ_API_KEY", "GROQ_API_KEY")
    _cohere_key_from_env = get_api_key("cohere_api_key", "COHERE_API_KEY", "COHERE_API_KEY")

    if _groq_key_from_env and _cohere_key_from_env:
        st.markdown(
            "<span class='pp-status-ok'>🟢 Connected</span>",
            unsafe_allow_html=True,
        )
    else:
        missing = [n for n, k in [("Groq", _groq_key_from_env), ("Cohere", _cohere_key_from_env)] if not k]
        st.markdown(
            f"<span class='pp-status-warn'>🟡 Setup needed: {', '.join(missing)} key not configured</span>",
            unsafe_allow_html=True,
        )
        with st.expander("🔧 Developer setup (not shown to employees in production)"):
            st.caption(
                "For a real deployment, set these in `.streamlit/secrets.toml` or as environment "
                "variables — never ask employees to paste API keys into the app. This fallback exists "
                "only so you can test locally without a secrets file."
            )
            groq_key_input = st.text_input(
                "Groq API Key", type="password",
                help="Free key at console.groq.com/keys.", placeholder="gsk_...",
            )
            if groq_key_input:
                st.session_state["groq_api_key"] = groq_key_input

            cohere_key_input = st.text_input(
                "Cohere API Key", type="password",
                help="Free trial key at dashboard.cohere.com/api-keys.", placeholder="co_...",
            )
            if cohere_key_input:
                st.session_state["cohere_api_key"] = cohere_key_input

    # Retrieval tuning is an admin concern, not something an employee asking
    # about leave policy needs to see or adjust -- tucked away, defaults to
    # a sensible value (4) if never opened.
    with st.expander("🛠️ Advanced (admin)"):
        top_k = st.slider("Chunks to retrieve (top-k)", min_value=2, max_value=8, value=4)

    st.markdown("---")
    st.markdown("## 📅 Public Holidays")
    st.caption("Live lookup — demonstrates a third, genuinely dynamic API beyond Groq/Cohere.")
    try:
        import requests
        from datetime import date as _date

        # Note: this API migrated from date.nager.at (v3, "NextPublicHolidays"
        # convenience route, "localName" field) to nagerholidays.com (v4,
        # year-based endpoint only, "name" field, no localName) -- confirmed
        # directly against their current docs. The old v3 URL now 404s/redirects
        # in a way that silently failed here, which is exactly why this needs
        # the current endpoint below, not the one originally shipped.
        _today = _date.today()
        _year = _today.year
        _resp = requests.get(f"https://nagerholidays.com/api/v4/Holidays/IN/{_year}", timeout=5)
        _upcoming = []
        _debug_info = f"First request: status={_resp.status_code}"
        if _resp.status_code == 200:
            _all_holidays = _resp.json()
            _debug_info += f", {len(_all_holidays)} holidays in {_year}"
            _upcoming = [h for h in _all_holidays if h["date"] >= _today.isoformat()]
            if not _upcoming:
                _resp2 = requests.get(f"https://nagerholidays.com/api/v4/Holidays/IN/{_year + 1}", timeout=5)
                _debug_info += f" | Fallback to {_year+1}: status={_resp2.status_code}"
                if _resp2.status_code == 200:
                    _upcoming = _resp2.json()

        if _upcoming:
            for h in _upcoming[:3]:
                st.markdown(
                    f"<div class='insight-row'><span>{h['name']}</span>"
                    f"<span class='insight-count'>{h['date']}</span></div>",
                    unsafe_allow_html=True,
                )
        else:
            # Confirmed via testing: the live API returns 204 for India -- it
            # recognizes "IN" as valid but has zero populated holiday records
            # for it (a real data-coverage gap in this free, community-maintained
            # service for India specifically -- their own docs note lunar/regional
            # holidays like Diwali/Eid are deliberately excluded, and India's few
            # fixed-date national holidays appear unpopulated too). Rather than
            # show a broken widget, fall back to a small local reference list --
            # clearly labeled as such, never silently presented as live data.
            _local_fallback_2026 = [
                {"name": "Gandhi Jayanti", "date": "2026-10-02"},
                {"name": "Diwali (Deepavali)", "date": "2026-11-08"},
                {"name": "Christmas Day", "date": "2026-12-25"},
            ]
            _fallback_upcoming = [h for h in _local_fallback_2026 if h["date"] >= _today.isoformat()]
            if _fallback_upcoming:
                st.caption("⚠️ Live API has no India data yet — showing a local reference list.")
                for h in _fallback_upcoming[:3]:
                    st.markdown(
                        f"<div class='insight-row'><span>{h['name']}</span>"
                        f"<span class='insight-count'>{h['date']}</span></div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No upcoming holidays returned.")
            with st.expander("API status (debug)"):
                st.code(_debug_info)
                if _resp.status_code not in (200, 204):
                    st.caption(f"Response body preview: {_resp.text[:300]}")
    except Exception as _holiday_err:
        st.caption("Holiday lookup temporarily unavailable.")
        with st.expander("Details (debug)"):
            st.code(str(_holiday_err))

    # ----------------------------------------------------------------- #
    # 💱 Currency (expense-policy INR/USD context)
    # ----------------------------------------------------------------- #
    st.markdown("---")
    st.markdown("## 💱 Currency")
    st.caption("Live rate for expense claims quoted in a foreign currency — open.er-api.com, no key required.")
    try:
        _fx = context_apis.get_exchange_rate(base="USD", target="INR")
        if _fx["error"]:
            st.caption("Currency lookup temporarily unavailable.")
            with st.expander("Details (debug)"):
                st.code(_fx["error"])
        else:
            st.markdown(
                f"<div class='pp-metric-card'><div class='pp-metric-value'>₹{_fx['rate']:.2f}</div>"
                f"<div class='pp-metric-label'>1 USD → INR</div></div>",
                unsafe_allow_html=True,
            )
            st.caption(f"Updated: {_fx['last_updated']}")
    except Exception as _fx_err:
        st.caption("Currency lookup temporarily unavailable.")
        with st.expander("Details (debug)"):
            st.code(str(_fx_err))

    # ----------------------------------------------------------------- #
    # 🌦️ Weather / WFH advisory (remote-work-policy context)
    # ----------------------------------------------------------------- #
    st.markdown("---")
    st.markdown("## 🌦️ WFH Weather Advisory")
    st.caption("Flags weather that's a reasonable reason to check the remote work policy — open-meteo.com, no key required.")
    _wfh_city = st.text_input("City", value="Mumbai", key="wfh_city_input", label_visibility="collapsed")
    if _wfh_city:
        try:
            _wx = context_apis.get_wfh_advisory(_wfh_city)
            if _wx["error"]:
                st.caption("Weather lookup temporarily unavailable.")
                with st.expander("Details (debug)"):
                    st.code(_wx["error"])
            else:
                if _wx["is_severe"]:
                    st.warning(_wx["advisory"])
                else:
                    st.caption(_wx["advisory"])
        except Exception as _wx_err:
            st.caption("Weather lookup temporarily unavailable.")
            with st.expander("Details (debug)"):
                st.code(str(_wx_err))

    # ----------------------------------------------------------------- #
    # 🏢 Employer country context (NOT a legal company-registry check --
    # see context_apis.get_country_info docstring for why)
    # ----------------------------------------------------------------- #
    st.markdown("---")
    st.markdown("## 🏢 Employer Country Context")
    st.caption(
        "Country-level reference data (currency, region, capital) via countries.dev — "
        "not a legal registry verification; for that, use the official registry of the country in question."
    )
    with st.expander("Look up a country"):
        _country_q = st.text_input("Country name", placeholder="e.g. India", key="country_lookup_input")
        if _country_q and st.button("Look up", key="country_lookup_btn"):
            try:
                _ci = context_apis.get_country_info(_country_q)
                if _ci["error"]:
                    st.caption("No match found, or the lookup is temporarily unavailable.")
                    with st.expander("Details (debug)"):
                        st.code(_ci["error"])
                else:
                    st.markdown(f"**{_ci['name']}** {_ci.get('flag') or ''}")
                    st.caption(
                        f"Capital: {_ci['capital']} · Region: {_ci['region']} · "
                        f"Calling code: {_ci['calling_code']}"
                    )
                    if _ci["currencies"]:
                        st.caption(f"Currencies: {_ci['currencies']}")
            except Exception as _ci_err:
                st.caption("Country lookup temporarily unavailable.")
                with st.expander("Details (debug)"):
                    st.code(str(_ci_err))

    # ----------------------------------------------------------------- #
    # 📰 HR / labor-law news awareness feed (requires a free NewsData.io key)
    # ----------------------------------------------------------------- #
    st.markdown("---")
    st.markdown("## 📰 HR & Labor Law News")
    _newsdata_key = get_api_key("newsdata_api_key", "NEWSDATA_API_KEY", "NEWSDATA_API_KEY")
    if not _newsdata_key:
        st.caption(
            "Optional — add a free NewsData.io key to enable this feed "
            "([newsdata.io/register](https://newsdata.io/register), 200 free credits/day)."
        )
        with st.expander("🔧 Add NewsData.io key (dev-only fallback)"):
            _newsdata_key_input = st.text_input(
                "NewsData.io API Key", type="password",
                help="Free key at newsdata.io/register.", placeholder="pub_...",
                key="newsdata_key_field",
            )
            if _newsdata_key_input:
                st.session_state["newsdata_api_key"] = _newsdata_key_input
                st.rerun()
    else:
        st.caption("Recent headlines relevant to labor law and HR policy — newsdata.io.")
        try:
            _news = context_apis.get_hr_news(_newsdata_key)
            if _news["error"]:
                st.caption("News feed temporarily unavailable.")
                with st.expander("Details (debug)"):
                    st.code(_news["error"])
            else:
                for a in _news["articles"]:
                    st.markdown(
                        f"<div class='insight-row'><span>"
                        f"<a href='{a['link']}' target='_blank' style='color:#E8D9B5;text-decoration:none;'>{a['title']}</a>"
                        f"</span></div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(f"{a['source']} · {a['published']}")
        except Exception as _news_err:
            st.caption("News feed temporarily unavailable.")
            with st.expander("Details (debug)"):
                st.code(str(_news_err))

    st.markdown("---")
    # ----------------------------------------------------------------- #
    # 📊 PolicyPal Data Science Dataset
    # ----------------------------------------------------------------- #
    st.markdown("---")
    st.markdown("## 📊 PolicyPal Data Science Dataset")
    st.caption(
        "Build a persistent Excel dataset by fusing the five PolicyPal external APIs. "
        "This is an analytics dataset; it does not replace the PDF/RAG knowledge base."
    )
    _dataset_key = get_api_key("newsdata_api_key", "NEWSDATA_API_KEY", "NEWSDATA_API_KEY")
    if st.button("Generate / Refresh Excel Dataset", key="generate_policy_dataset_btn", width="stretch"):
        if not _dataset_key:
            st.warning("Add a NewsData.io API key above before generating the dataset.")
        else:
            with st.spinner("Collecting API data, caching responses, and fusing the dataset..."):
                try:
                    _master_df, _holiday_df, _api_log_df = build_dataset(_dataset_key)
                    _dataset_path = write_workbook(_master_df, _holiday_df, _api_log_df)
                    st.session_state["policy_dataset_path"] = str(_dataset_path)
                    st.success(f"Dataset generated: {_master_df.shape[0]:,} rows × {_master_df.shape[1]:,} columns.")
                except Exception as _dataset_err:
                    st.error("Dataset generation failed. Existing chatbot functionality is unchanged.")
                    with st.expander("Dataset error details"):
                        st.code(str(_dataset_err))

    _dataset_path = st.session_state.get("policy_dataset_path", str(OUTPUT_XLSX))
    if os.path.exists(_dataset_path):
        try:
            with open(_dataset_path, "rb") as _dataset_file:
                st.download_button(
                    "⬇️ Download PolicyPal_Master_Dataset.xlsx",
                    data=_dataset_file.read(),
                    file_name="PolicyPal_Master_Dataset.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_policy_dataset_btn",
                    width="stretch",
                )
        except OSError:
            pass

    st.markdown("## 🌐 Language")
    st.session_state.language = st.selectbox(
        "Answer language", ["English", "Hindi", "Marathi", "Tamil", "Bengali"],
        label_visibility="collapsed",
        help="Policy figures (days, amounts, deadlines) always stay exact regardless of language.",
    )

    st.markdown("---")
    st.markdown("## 🧑‍💼 Your Profile")
    st.caption("Optional — improves accuracy for eligibility-based questions (e.g. maternity leave, probation rules).")
    with st.expander("Set your profile" if not st.session_state.employee_profile else "✅ Profile set — edit"):
        emp_type = st.selectbox("Employment type", ["Full-time", "Contract", "Intern", "Part-time"], key="emp_type_input")
        tenure = st.number_input("Months at the company", min_value=0, max_value=600, value=0, step=1, key="tenure_input")
        if st.button("Save profile", key="save_profile_btn"):
            st.session_state.employee_profile = {"employment_type": emp_type, "tenure_months": int(tenure)}
            st.toast("Profile saved for this session.", icon="✅")
            st.rerun()
        if st.session_state.employee_profile and st.button("Clear profile", key="clear_profile_btn"):
            st.session_state.employee_profile = None
            st.rerun()

    st.markdown("---")
    st.markdown("## 💬 Mode")
    mode_choice = st.radio(
        "Mode", ["💬 Ask a question", "📷 Photo of a document"],
        label_visibility="collapsed",
    )
    st.session_state.query_mode = "photo" if "Photo" in mode_choice else "text"

    st.markdown("---")
    st.markdown("## 📤 Add Policy Documents")
    st.caption("Supports: " + ", ".join(sorted(SUPPORTED_EXTENSIONS)))
    uploaded_files = st.file_uploader(
        "Upload new policy files", accept_multiple_files=True,
        type=[e.strip(".") for e in SUPPORTED_EXTENSIONS],
        label_visibility="collapsed",
    )
    if uploaded_files and st.button("➕ Add to knowledge base", width="stretch"):
        _cohere_key = get_api_key("cohere_api_key", "COHERE_API_KEY", "COHERE_API_KEY")
        if not _cohere_key:
            st.error("Add your Cohere API key above first — it's needed to embed the new documents.")
        else:
            with st.spinner("Processing and embedding documents..."):
                n = ingest_uploaded_files(uploaded_files, _cohere_key)
            if n:
                st.success(f"Added {n} new chunks to the knowledge base.")
            else:
                st.warning("No new content was added.")

    st.markdown("---")
    vs = st.session_state.vector_store
    total_chunks = vs.index.ntotal if vs else 0
    total_docs = len(set(m["source_file"] for m in vs.chunk_metadata)) if vs else 0

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='pp-metric-card'><div class='pp-metric-value'>{total_docs}</div>"
                     f"<div class='pp-metric-label'>Documents</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='pp-metric-card'><div class='pp-metric-value'>{total_chunks}</div>"
                     f"<div class='pp-metric-label'>Chunks Indexed</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.session_state.history:
        transcript_lines = []
        for turn in st.session_state.history:
            transcript_lines.append(f"[{turn['timestamp']}]")
            transcript_lines.append(f"Employee: {turn['question']}")
            transcript_lines.append(f"PolicyPal: {turn['answer']}\n")
        transcript = "\n".join(transcript_lines)
        st.download_button(
            "⬇️ Download conversation", data=transcript,
            file_name=f"policypal_transcript_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain", width="stretch",
        )

    if st.button("🗑️ Clear conversation", width="stretch"):
        st.session_state.history = []
        st.rerun()

    st.markdown("---")
    st.markdown("## 📊 HR Insights")
    st.caption("Real, persisted data — not just session-local feedback buttons that vanish on refresh.")
    insights = analytics.load_insights()

    ic1, ic2 = st.columns(2)
    with ic1:
        st.markdown(f"<div class='pp-metric-card'><div class='pp-metric-value'>{insights['total_questions']}</div>"
                     f"<div class='pp-metric-label'>Questions logged</div></div>", unsafe_allow_html=True)
    with ic2:
        st.markdown(f"<div class='pp-metric-card'><div class='pp-metric-value'>{insights['low_coverage_count']}</div>"
                     f"<div class='pp-metric-label'>Not found in docs</div></div>", unsafe_allow_html=True)

    if insights["top_questions"]:
        with st.expander(f"🔝 Most-asked questions ({len(insights['top_questions'])})"):
            for q, count in insights["top_questions"]:
                st.markdown(
                    f"<div class='insight-row'><span>{q}</span><span class='insight-count'>{count}×</span></div>",
                    unsafe_allow_html=True,
                )

    if insights["flagged_questions"]:
        with st.expander(f"👎 Flagged as unhelpful ({len(insights['flagged_questions'])})"):
            st.caption("These often point to policy wording that's unclear or genuinely missing — worth a look.")
            for q in insights["flagged_questions"]:
                st.markdown(f"<div class='flagged-item'>• {q}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Built with FAISS · Cohere Embeddings · Groq (text + vision) · Streamlit")


# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #

st.markdown(
    """
    <div class="pp-header">
        <div class="pp-header-badge">📘</div>
        <div>
            <p class="pp-header-title">PolicyPal</p>
            <p class="pp-header-sub">Your always-on guide to NimbusTech's HR, IT, and travel policies — grounded in the actual policy documents, with sources cited.</p>
            <span class="pp-modal-pill">🖼️ Text + Photo — ask, or upload a photo of a printed policy notice</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------- #
# Load / build index (first run)
# --------------------------------------------------------------------------- #

if st.session_state.vector_store is None:
    # A cached index on disk needs no API key at all.
    st.session_state.vector_store = load_cached_index()

if st.session_state.vector_store is None:
    # No index on disk yet -- we need to build one from data/raw, which requires
    # a Cohere key (only for this one-time build; loads afterward are instant).
    cohere_key = get_api_key("cohere_api_key", "COHERE_API_KEY", "COHERE_API_KEY")
    if not cohere_key:
        st.info(
            "👋 First-time setup: add your **Cohere API key** in the sidebar to build the knowledge base "
            "(one-time step — get a free key at [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys))."
        )
        st.stop()
    with st.spinner("Building the knowledge base from policy documents (first run only)..."):
        try:
            st.session_state.vector_store = build_index_from_data_dir(cohere_key)
        except Exception as e:
            st.error(f"Failed to build the knowledge base: {e}")
            st.stop()

if st.session_state.vector_store is None or st.session_state.vector_store.index.ntotal == 0:
    st.warning("⚠️ The knowledge base is empty. Upload some policy documents from the sidebar to get started.")
    st.stop()

# --------------------------------------------------------------------------- #
# Suggested questions
# --------------------------------------------------------------------------- #

if not st.session_state.history:
    st.markdown("**Try asking:**")
    cols = st.columns(len(SUGGESTED_QUESTIONS))
    for col, q in zip(cols, SUGGESTED_QUESTIONS):
        with col:
            if st.button(q, key=f"sugg_{q}", width="stretch"):
                st.session_state.pending_question = q

st.markdown("")

# --------------------------------------------------------------------------- #
# Chat history render
# --------------------------------------------------------------------------- #

for idx, turn in enumerate(st.session_state.history):
    with st.chat_message("user", avatar="🧑‍💼" if turn.get("mode", "text") != "photo" else "📷"):
        st.markdown(turn["question"])
        if turn.get("mode") == "photo" and turn.get("image_bytes"):
            st.image(turn["image_bytes"], width=220)
    with st.chat_message("assistant", avatar="📘"):
        if turn.get("mode", "text") == "text":
            render_confidence(turn.get("coverage"))
        else:
            st.caption("📷 Answered from photo, cross-checked against policy docs")
        st.markdown(turn["answer"])
        render_sources(turn.get("sources", []))
        render_feedback(f"hist_{idx}", turn)

# --------------------------------------------------------------------------- #
# Chat input
# --------------------------------------------------------------------------- #

if st.session_state.query_mode == "text":
    user_question = st.chat_input("Ask about leave, expenses, remote work, IT security, code of conduct...")

    if st.session_state.pending_question:
        user_question = st.session_state.pending_question
        st.session_state.pending_question = None

    if user_question:
        groq_key = get_api_key("groq_api_key", "GROQ_API_KEY", "GROQ_API_KEY")
        cohere_key = get_api_key("cohere_api_key", "COHERE_API_KEY", "COHERE_API_KEY")

        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(user_question)

        with st.chat_message("assistant", avatar="📘"):
            missing = []
            if not groq_key:
                missing.append("Groq")
            if not cohere_key:
                missing.append("Cohere")
            if missing:
                st.error(
                    f"⚠️ Missing API key(s): {', '.join(missing)}. Add them in the sidebar — "
                    "free keys at [console.groq.com](https://console.groq.com/keys) and "
                    "[dashboard.cohere.com](https://dashboard.cohere.com/api-keys)."
                )
            else:
                with st.spinner("Searching policy documents..."):
                    try:
                        prepared = prepare_answer(
                            question=user_question,
                            vector_store=st.session_state.vector_store,
                            cohere_api_key=cohere_key,
                            history=st.session_state.history,
                            top_k=top_k,
                            employee_profile=st.session_state.employee_profile,
                            language=st.session_state.language,
                        )
                    except Exception as e:
                        prepared = {"system_prompt": None, "user_prompt": None, "sources": [], "error": str(e)}

                if prepared["error"]:
                    st.error(f"Something went wrong while retrieving policy content: {prepared['error']}")
                else:
                    # coverage isn't known until the stream reveals its first line (see
                    # stream_groq_llm) -- coverage_result is mutated in place by the
                    # generator since it can't both yield chunks and return a value.
                    coverage_result = {}
                    try:
                        full_answer = st.write_stream(
                            stream_groq_llm(
                                prepared["system_prompt"], prepared["user_prompt"],
                                api_key=groq_key, model=LLM_MODEL,
                                coverage_result=coverage_result,
                            )
                        )
                    except Exception as e:
                        full_answer = None
                        st.error(f"Something went wrong while generating the answer: {e}")

                    if full_answer:
                        coverage = coverage_result.get("coverage", "PARTIAL")
                        render_confidence(coverage)
                        render_sources(prepared["sources"])

                        interaction_id = analytics.log_interaction(user_question, coverage, mode="text")

                        new_idx = len(st.session_state.history)
                        st.session_state.history.append({
                            "question": user_question,
                            "answer": full_answer,
                            "sources": prepared["sources"],
                            "coverage": coverage,
                            "interaction_id": interaction_id,
                            "mode": "text",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        })
                        render_feedback(f"hist_{new_idx}", st.session_state.history[new_idx])
                        render_followups(user_question)

else:
    st.markdown("<p class='followup-label'>Upload a photo of a policy document</p>", unsafe_allow_html=True)
    uploaded_photo = st.file_uploader(
        "Upload photo", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed", key="photo_uploader"
    )
    photo_question = st.text_input(
        "What do you want to know about it?",
        placeholder="e.g. Does this notice match our current leave policy?",
        key="photo_question_input",
    )

    pcol1, pcol2 = st.columns([1, 2])
    if uploaded_photo:
        pcol1.image(uploaded_photo, width=280)

    ask_photo = pcol2.button("Ask about this photo", disabled=not (uploaded_photo and photo_question))

    if ask_photo:
        groq_key = get_api_key("groq_api_key", "GROQ_API_KEY", "GROQ_API_KEY")
        cohere_key = get_api_key("cohere_api_key", "COHERE_API_KEY", "COHERE_API_KEY")

        with st.chat_message("user", avatar="📷"):
            st.markdown(photo_question)
            st.image(uploaded_photo, width=220)

        with st.chat_message("assistant", avatar="📘"):
            if not groq_key:
                st.error("⚠️ Missing Groq API key. Add it in the sidebar.")
            else:
                image_bytes = uploaded_photo.getvalue()
                with st.spinner("Reading the photo and cross-checking policy documents..."):
                    result = answer_image_question(
                        groq_api_key=groq_key,
                        image_bytes=image_bytes,
                        question=photo_question,
                        vector_store=st.session_state.vector_store,
                        cohere_api_key=cohere_key,
                        mime_type=uploaded_photo.type or "image/jpeg",
                        top_k=top_k,
                    )
                if result["error"]:
                    st.error(f"Something went wrong reading the photo: {result['error']}")
                else:
                    st.markdown(result["answer"])
                    render_sources(result["sources"])

                    interaction_id = analytics.log_interaction(photo_question, None, mode="photo")

                    new_idx = len(st.session_state.history)
                    st.session_state.history.append({
                        "question": photo_question,
                        "answer": result["answer"],
                        "sources": result["sources"],
                        "coverage": None,
                        "interaction_id": interaction_id,
                        "mode": "photo",
                        "image_bytes": image_bytes,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                    render_feedback(f"hist_{new_idx}", st.session_state.history[new_idx])
