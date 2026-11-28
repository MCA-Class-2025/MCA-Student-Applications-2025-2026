"""Shared desktop-web visual system and the FemCare home dashboard."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from Dashboard.utils.menocare import entries_frame, events_frame


def inject_ui_shell() -> None:
    """Apply the responsive blush-and-plum design system across Streamlit."""
    st.markdown(
        """
        <style>
        :root {
            --fc-plum: #56334f;
            --fc-plum-deep: #40243b;
            --fc-lilac: #ad71d8;
            --fc-pink: #dc6eaa;
            --fc-peach: #f3b6a6;
            --fc-blush: #f8eff2;
            --fc-surface: rgba(255, 252, 253, 0.90);
            --fc-border: rgba(111, 74, 103, 0.15);
            --fc-ink: #322731;
            --fc-muted: #746773;
            --fc-shadow: 0 18px 50px rgba(82, 48, 75, 0.09);
        }

        html, body, [class*="css"] {
            font-family: Inter, "Segoe UI", system-ui, sans-serif;
        }
        .stApp, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 78% 4%, rgba(218, 151, 220, .18), transparent 27rem),
                radial-gradient(circle at 10% 88%, rgba(246, 189, 167, .17), transparent 28rem),
                #f8f3f5;
            color: var(--fc-ink);
        }
        [data-testid="stHeader"] {
            background: rgba(248, 243, 245, .78);
            backdrop-filter: blur(16px);
        }
        .block-container {
            max-width: 1480px;
            padding: 2.2rem 2.8rem 4rem;
        }

        /* Desktop navigation */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #fffafd 0%, #f5e9ef 100%);
            border-right: 1px solid rgba(86, 51, 79, .11);
            box-shadow: 12px 0 35px rgba(91, 55, 84, .045);
        }
        [data-testid="stSidebar"] > div:first-child { padding: 1.6rem 1rem; }
        [data-testid="stSidebar"] [role="radiogroup"] { gap: .28rem; }
        [data-testid="stSidebar"] [data-testid="stRadioOption"] {
            width: 100%;
            min-height: 44px;
            padding: .63rem .78rem;
            border-radius: 13px;
            transition: all .18s ease;
            border: 1px solid transparent;
        }
        [data-testid="stSidebar"] [data-testid="stRadioOption"]:hover {
            background: rgba(255,255,255,.72);
            border-color: rgba(86,51,79,.10);
            transform: translateX(2px);
        }
        [data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] {
            background: linear-gradient(135deg, var(--fc-plum) 0%, #76506e 100%);
            box-shadow: 0 9px 22px rgba(86, 51, 79, .20);
        }
        [data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] p,
        [data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] span {
            color: #fff !important;
            font-weight: 650;
        }
        [data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div > div:first-child {
            display:none !important;
        }
        .fc-brand {
            display:flex; align-items:center; gap:.75rem; margin:.2rem .2rem 1.1rem;
            padding:.45rem .35rem;
        }
        .fc-brand-mark {
            width:44px; height:44px; display:grid; place-items:center; border-radius:15px;
            color:#fff; font-size:1.35rem;
            background:linear-gradient(145deg,#6a4161,#9b5e8d);
            box-shadow:0 10px 24px rgba(86,51,79,.22);
        }
        .fc-brand-name {font-size:1.15rem;font-weight:800;color:var(--fc-plum-deep);letter-spacing:-.02em}
        .fc-brand-sub {font-size:.72rem;color:var(--fc-muted);margin-top:.08rem}
        .fc-side-label {font-size:.67rem;font-weight:800;letter-spacing:.13em;color:#9a8794;text-transform:uppercase;margin:.5rem .65rem .35rem}

        /* Page surfaces */
        .hero-container {
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, rgba(255,250,252,.96) 0%, rgba(244,225,238,.96) 100%);
            border: 1px solid rgba(112, 70, 102, .13);
            border-radius: 26px;
            padding: 2rem 2.2rem;
            margin-bottom: 1.5rem;
            box-shadow: var(--fc-shadow);
        }
        .hero-container::after {
            content:""; position:absolute; width:220px;height:220px;border-radius:50%;
            right:-75px;top:-100px;background:radial-gradient(circle,rgba(190,121,211,.23),transparent 67%);
        }
        .hero-title {color:var(--fc-plum-deep);font-weight:800;margin:0 0 .35rem;font-size:2rem;letter-spacing:-.035em}
        .hero-subtitle {color:var(--fc-muted);font-size:1rem;margin:0;max-width:760px}
        .card-box, [data-testid="stForm"], [data-testid="stExpander"] {
            background: var(--fc-surface);
            border: 1px solid var(--fc-border) !important;
            border-radius: 20px !important;
            box-shadow: 0 12px 35px rgba(80, 45, 73, .055);
        }
        [data-testid="stForm"] { padding: 1.25rem 1.35rem; }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--fc-border) !important;
            border-radius: 20px !important;
        }

        /* Metrics and controls */
        [data-testid="stMetric"] {
            background: var(--fc-surface);
            border: 1px solid var(--fc-border);
            border-radius: 18px;
            padding: 1rem 1.05rem;
            box-shadow: 0 10px 26px rgba(80,45,73,.05);
        }
        [data-testid="stMetricLabel"] p {color:var(--fc-muted);font-weight:650}
        [data-testid="stMetricValue"] {color:var(--fc-plum-deep);font-weight:800}
        .metric-card {
            background:var(--fc-surface);border:1px solid var(--fc-border);border-radius:18px;
            padding:1rem;box-shadow:0 10px 26px rgba(80,45,73,.05);text-align:left;
        }
        .metric-card-label {font-size:.72rem;color:var(--fc-muted);font-weight:750;text-transform:uppercase;letter-spacing:.08em}
        .metric-card-value {font-size:1.55rem;font-weight:800;color:var(--fc-plum);margin-top:.3rem}
        .status-badge {
            display:block;background:rgba(255,255,255,.68);color:#66465f;border:1px solid rgba(90,55,82,.11);
            padding:.55rem .7rem;border-radius:12px;font-size:.72rem;font-weight:650;margin-bottom:.4rem;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius:14px !important;border:1px solid rgba(86,51,79,.18) !important;
            min-height:42px;font-weight:700;transition:transform .15s ease, box-shadow .15s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            transform:translateY(-1px);box-shadow:0 9px 22px rgba(86,51,79,.12);
        }
        .stButton > button[kind="primary"], button[kind="primary"] {
            background:linear-gradient(135deg,var(--fc-plum),#754b6d) !important;
            color:#fff !important;border-color:transparent !important;
        }
        [data-baseweb="input"] > div, [data-baseweb="select"] > div,
        [data-baseweb="textarea"] > div, textarea, input {
            border-radius:13px !important;background:rgba(255,252,253,.88) !important;
        }
        [data-baseweb="tab-list"] {
            background:rgba(255,255,255,.58);padding:.3rem;border-radius:15px;gap:.2rem;
            border:1px solid var(--fc-border);
        }
        [data-baseweb="tab"] {border-radius:11px;padding:.55rem .85rem}
        [aria-selected="true"][data-baseweb="tab"] {background:#fff;box-shadow:0 5px 16px rgba(80,45,73,.08)}
        [data-testid="stDataFrame"] {border-radius:18px;overflow:hidden;border:1px solid var(--fc-border)}
        [data-testid="stChatMessage"] {
            background:rgba(255,255,255,.72);border:1px solid var(--fc-border);border-radius:18px;
            padding:.65rem .8rem;margin:.5rem 0;
        }
        [data-testid="stChatInput"] {background:rgba(255,255,255,.82);border-radius:18px}
        hr {border-color:rgba(86,51,79,.10)!important}

        /* Home dashboard */
        .fc-welcome {font-size:.78rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#9a748f;margin-bottom:.4rem}
        .fc-home-title {font-size:2.4rem;line-height:1.05;font-weight:850;color:var(--fc-plum-deep);letter-spacing:-.045em;margin:0}
        .fc-home-sub {font-size:1rem;color:var(--fc-muted);margin:.7rem 0 0;max-width:660px}
        .fc-hero-grid {display:grid;grid-template-columns:minmax(0,1.5fr) minmax(280px,.7fr);gap:1.2rem;margin:1.4rem 0}
        .fc-home-panel {background:var(--fc-surface);border:1px solid var(--fc-border);border-radius:24px;padding:1.5rem;box-shadow:var(--fc-shadow)}
        .fc-home-panel.primary {background:linear-gradient(145deg,#fffafd 0%,#f0dce8 100%);position:relative;overflow:hidden}
        .fc-home-panel.primary::after {content:"";position:absolute;right:-90px;bottom:-120px;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(176,102,203,.23),transparent 68%)}
        .fc-kicker {font-size:.72rem;font-weight:800;letter-spacing:.11em;text-transform:uppercase;color:#9a748f}
        .fc-panel-title {font-size:1.5rem;font-weight:800;color:var(--fc-plum-deep);margin:.35rem 0 .4rem;letter-spacing:-.025em}
        .fc-panel-copy {color:var(--fc-muted);font-size:.92rem;max-width:600px;position:relative;z-index:1}
        .fc-ring {--p:0;width:146px;height:146px;border-radius:50%;display:grid;place-items:center;margin:.7rem auto;background:conic-gradient(var(--fc-lilac) calc(var(--p)*1%),#ecdee7 0);position:relative}
        .fc-ring::before {content:"";position:absolute;width:112px;height:112px;border-radius:50%;background:#fffafd}
        .fc-ring-content {position:relative;text-align:center}.fc-ring-big{font-size:1.7rem;font-weight:850;color:var(--fc-plum)}.fc-ring-small{font-size:.7rem;color:var(--fc-muted)}
        .fc-feature-card {min-height:132px;padding:1.15rem;border-radius:19px;background:rgba(255,255,255,.76);border:1px solid var(--fc-border);box-shadow:0 9px 26px rgba(80,45,73,.045)}
        .fc-feature-icon {font-size:1.35rem}.fc-feature-title {font-weight:800;color:var(--fc-plum-deep);margin:.55rem 0 .2rem}.fc-feature-copy{font-size:.8rem;color:var(--fc-muted);line-height:1.4}
        .fc-section-title {font-size:1.25rem;font-weight:800;color:var(--fc-plum-deep);margin:1.5rem 0 .85rem}

        @media (max-width: 900px) {
            .block-container {padding:1.25rem 1rem 3rem}
            .fc-hero-grid {grid-template-columns:1fr}
            .fc-home-title {font-size:1.9rem}
            .hero-container {padding:1.4rem;border-radius:20px}
            .hero-title {font-size:1.65rem}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    st.markdown(
        """
        <div class="fc-brand">
            <div class="fc-brand-mark">✦</div>
            <div><div class="fc-brand-name">FemCare</div><div class="fc-brand-sub">Your health, thoughtfully supported</div></div>
        </div>
        <div class="fc-side-label">Workspace</div>
        """,
        unsafe_allow_html=True,
    )


def _navigate(page: str) -> None:
    st.session_state["main_navigation"] = page


def render_home(metrics: dict) -> None:
    """Render a desktop dashboard inspired by the supplied mobile reference."""
    check_ins = entries_frame(st.session_state.get("menocare_entries", []))
    events = events_frame(st.session_state.get("menocare_events", []))
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    recent_check_ins = int((check_ins["entry_date"].dt.date >= week_start).sum()) if not check_ins.empty else 0
    recent_events = int((events["event_date"].dt.date >= week_start).sum()) if not events.empty else 0
    weekly_activity = recent_check_ins + recent_events
    ring_percent = min(100, round(weekly_activity / 7 * 100))

    st.markdown(
        f"""
        <div class="fc-welcome">FemCare wellness workspace · {today:%A, %d %B}</div>
        <h1 class="fc-home-title">Ready for a more informed day?</h1>
        <p class="fc-home-sub">Track patterns, ask health questions and keep your wellbeing tools together in one calm, private workspace.</p>
        <div class="fc-hero-grid">
            <div class="fc-home-panel primary">
                <div class="fc-kicker">MenoCare · This week</div>
                <div class="fc-panel-title">Notice patterns without pressure</div>
                <div class="fc-panel-copy">Use a quick check-in for the overall day or log a specific symptom, bleeding episode or medication change when it matters.</div>
            </div>
            <div class="fc-home-panel">
                <div class="fc-ring" style="--p:{ring_percent}">
                    <div class="fc-ring-content"><div class="fc-ring-big">{weekly_activity}</div><div class="fc-ring-small">logs this week</div></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cta_left, cta_right = st.columns([1.25, 1])
    with cta_left:
        st.button(
            "🌙 Open MenoCare",
            type="primary",
            width="stretch",
            on_click=_navigate,
            args=("🌙 MenoCare",),
        )
    with cta_right:
        st.button(
            "💬 Ask FemCare AI",
            width="stretch",
            on_click=_navigate,
            args=("💬 Chat",),
        )

    st.markdown('<div class="fc-section-title">Your FemCare toolkit</div>', unsafe_allow_html=True)
    features = [
        ("🌙", "MenoCare", "Quick check-ins, event tracking and appointment-ready summaries.", "🌙 MenoCare"),
        ("✦", "AI Copilot", "Ask evidence-grounded menstrual-health questions in plain language.", "💬 Chat"),
        ("🥗", "Nutrition", "Explore food guidance and generate recipe ideas from your ingredients.", "🍎 Nutrition Guide"),
        ("⌖", "Care Finder", "Find nearby healthcare services using the accessibility finder.", "🏥 Healthcare Finder"),
    ]
    columns = st.columns(4)
    for column, (icon, title, copy, target) in zip(columns, features):
        with column:
            st.markdown(
                f'<div class="fc-feature-card"><div class="fc-feature-icon">{icon}</div><div class="fc-feature-title">{title}</div><div class="fc-feature-copy">{copy}</div></div>',
                unsafe_allow_html=True,
            )
            st.button(
                f"Open {title}", key=f"home_{title}", width="stretch",
                on_click=_navigate, args=(target,),
            )

    st.markdown('<div class="fc-section-title">Research workspace</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Fused records", f"{metrics.get('Total Records', 0):,}")
    m2.metric("Dataset users", f"{metrics.get('Unique Users', 0):,}")
    m3.metric("MenoCare check-ins", len(check_ins))
    m4.metric("MenoCare events", len(events))
