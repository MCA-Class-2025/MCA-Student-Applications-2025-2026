"""Application-wide visual, accessibility, and session-privacy settings."""

from __future__ import annotations

import streamlit as st


THEMES = ("Light", "Dark")
TEXT_SCALES = {"Compact": 0.94, "Standard": 1.0, "Large": 1.12}
SUMMARY_PERIODS = ("Weekly", "Monthly")


def settings_css(theme: str, text_scale: str, reduce_motion: bool) -> str:
    """Return validated CSS for the selected session preferences."""
    if theme not in THEMES:
        raise ValueError("Theme must be Light or Dark.")
    if text_scale not in TEXT_SCALES:
        raise ValueError("Choose a valid text size.")
    scale = TEXT_SCALES[text_scale]
    motion_css = """
    *, *::before, *::after {
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.001ms !important;
        scroll-behavior: auto !important;
    }
    """ if reduce_motion else ""

    if theme == "Dark":
        palette_css = """
        :root {
            color-scheme: dark;
            --fc-plum: #dba1c7;
            --fc-plum-deep: #f8eaf3;
            --fc-lilac: #c185e9;
            --fc-pink: #ee91c1;
            --fc-blush: #1d171e;
            --fc-surface: rgba(39, 29, 40, .94);
            --fc-border: rgba(235, 187, 218, .16);
            --fc-ink: #f8edf4;
            --fc-muted: #cfbdc8;
            --fc-shadow: 0 18px 50px rgba(0, 0, 0, .20);
        }
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background: #171219 !important;
            color: #f8edf4 !important;
        }
        [data-testid="stSidebar"] {
            background: #211921 !important;
            border-right-color: #463244 !important;
        }
        [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"],
        label, p, li, h1, h2, h3, h4, span {
            color: #f5eaf1;
        }
        .hero-container {
            background: linear-gradient(135deg, #3b1730 0%, #52203d 100%) !important;
            border-color: #7c355f !important;
        }
        .hero-title { color: #ff9dca !important; }
        .hero-subtitle { color: #f6d8e8 !important; }
        .card-box, .metric-card {
            background: #241c25 !important;
            border-color: #4b3749 !important;
        }
        .fc-home-panel, .fc-feature-card {
            background: #241c25 !important;
            border-color: #4b3749 !important;
        }
        .fc-home-panel.primary {
            background: linear-gradient(145deg, #2a2029 0%, #47283d 100%) !important;
        }
        .fc-ring { background: conic-gradient(#c185e9 calc(var(--p)*1%), #493744 0) !important; }
        .fc-ring::before { background: #241c25 !important; }
        .metric-card-value { color: #ff84bd !important; }
        .metric-card-label { color: #cfbdc8 !important; }
        .status-badge {
            background: #34202d !important;
            color: #ff9dca !important;
            border-color: #69405a !important;
        }
        [data-baseweb="input"] > div, [data-baseweb="select"] > div,
        [data-baseweb="textarea"] > div, [data-baseweb="base-input"],
        textarea, input {
            background: #2a202a !important;
            color: #fff6fb !important;
            border-color: #674a61 !important;
        }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            border-color: #4b3749 !important;
        }
        [data-testid="stMetric"] {
            background: #241c25;
            border: 1px solid #4b3749;
            border-radius: 12px;
            padding: 12px;
        }
        hr { border-color: #463244 !important; }
        """
    else:
        palette_css = ":root { color-scheme: light; }"

    return f"""
    <style>
    html, body, [class*="css"] {{ font-size: {scale}rem; }}
    {palette_css}
    {motion_css}
    </style>
    """


def apply_app_settings() -> None:
    """Initialize session defaults and apply preferences on every rerun."""
    st.session_state.setdefault("app_theme", "Light")
    st.session_state.setdefault("app_text_scale", "Standard")
    st.session_state.setdefault("app_reduce_motion", False)
    st.session_state.setdefault("menocare_summary_default", "Weekly")
    st.markdown(
        settings_css(
            st.session_state["app_theme"],
            st.session_state["app_text_scale"],
            st.session_state["app_reduce_motion"],
        ),
        unsafe_allow_html=True,
    )


def render_settings() -> None:
    """Render global settings and explicit controls for session health data."""
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">⚙️ Settings</div>
            <p class="hero-subtitle">Appearance, accessibility and session-data controls.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.pop("settings_notice", None):
        st.success("MenoCare session data was cleared from this running session.")

    appearance, preferences, privacy = st.tabs([
        "🎨 Appearance", "🌙 MenoCare preferences", "🔒 Privacy & session data"
    ])
    with appearance:
        st.radio(
            "Application theme", THEMES, horizontal=True,
            key="app_theme",
            help="Theme changes apply across the Streamlit application for this session.",
        )
        st.select_slider(
            "Text size", options=list(TEXT_SCALES),
            key="app_text_scale",
        )
        st.toggle(
            "Reduce animations and transitions",
            key="app_reduce_motion",
            help="Useful when motion is distracting or uncomfortable.",
        )
        st.caption("Settings currently last only for this Streamlit session. Account-based preferences will be added with authentication.")

    with preferences:
        st.radio(
            "Default trend summary", SUMMARY_PERIODS, horizontal=True,
            key="menocare_summary_default",
        )
        st.session_state["meno_summary_frequency"] = st.session_state["menocare_summary_default"]
        st.caption("This controls whether MenoCare initially opens weekly or monthly activity summaries.")

    with privacy:
        check_ins = len(st.session_state.get("menocare_entries", []))
        events = len(st.session_state.get("menocare_events", []))
        p1, p2 = st.columns(2)
        p1.metric("Check-ins in this session", check_ins)
        p2.metric("Events in this session", events)
        st.info(
            "This MVP keeps MenoCare entries in server session memory only. They disappear when the session resets and are not connected to an account or permanent database."
        )
        confirmed = st.checkbox(
            "I understand that clearing removes the current session's MenoCare entries and events.",
            key="confirm_clear_menocare",
        )
        if st.button(
            "Clear MenoCare session data",
            disabled=not confirmed or (check_ins == 0 and events == 0),
            type="secondary",
            width="stretch",
        ):
            st.session_state.pop("menocare_entries", None)
            st.session_state.pop("menocare_events", None)
            st.session_state["settings_notice"] = True
            st.rerun()
