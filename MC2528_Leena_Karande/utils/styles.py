import streamlit as st


def load_css():
    """Injects the FinDoc Insight AI custom theme."""
    st.markdown(
        """
        <style>
        /* ---------- Global ---------- */
        .stApp {
            background:
                radial-gradient(circle at 8% 0%, rgba(190, 76, 255, .22), transparent 28%),
                radial-gradient(circle at 95% 16%, rgba(29, 219, 202, .14), transparent 24%),
                #090A1B;
            color: #E2E8F0;
        }

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {
            background-color: #111827;
            border-right: 1px solid #1E293B;
        }

        /* ---------- Headings ---------- */
        h1, h2, h3, h4 {
            color: #F8FAFC;
            font-family: 'Segoe UI', sans-serif;
        }

        /* ---------- Metric / KPI cards ---------- */
        .kpi-card {
            background: linear-gradient(145deg, #1E293B, #172033);
            border: 1px solid #2C3B57;
            border-radius: 14px;
            padding: 22px 20px;
            text-align: left;
        }
        .kpi-value {
            font-size: 28px;
            font-weight: 700;
            color: #FACC15;
        }
        .kpi-label {
            font-size: 13px;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* ---------- Generic content card ---------- */
        .fd-card {
            background: linear-gradient(135deg, rgba(36, 38, 82, .78), rgba(19, 21, 51, .86));
            border: 1px solid rgba(255,255,255,.13);
            border-radius: 22px;
            padding: 24px;
            margin-bottom: 18px;
            box-shadow: 0 18px 50px rgba(0,0,0,.18);
        }

        /* ---------- Badges ---------- */
        .badge-phase1 {
            background-color: #14532D;
            color: #86EFAC;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-upcoming {
            background-color: #78350F;
            color: #FCD34D;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }

        /* ---------- Buttons ---------- */
        .stButton>button {
            background: linear-gradient(100deg, #D75BFF, #6E77FF 58%, #32DACB);
            color: white;
            font-weight: 600;
            border-radius: 14px;
            border: none;
            min-height: 42px;
            transition: transform .18s ease, box-shadow .18s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(100deg, #E775FF, #8088FF 58%, #4DEBDD);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 10px 28px rgba(124, 58, 237, .35);
        }

        .ai-hero {
            padding: 46px 38px; margin: 5px 0 18px; border-radius: 28px;
            background: linear-gradient(120deg, rgba(167, 72, 255, .34), rgba(59, 74, 220, .42), rgba(16, 184, 176, .26));
            border: 1px solid rgba(255,255,255,.16); overflow: hidden;
        }
        .ai-hero h1 { font-size: clamp(2rem, 4vw, 3.7rem); margin: 5px 0 10px; letter-spacing: -.055em; }
        .ai-hero p { color: #D9D9FF; font-size: 1.08rem; margin: 0; }
        .eyebrow { color: #83F6E9 !important; font-size: .73rem !important; font-weight: 800; letter-spacing: .17em; }
        .prompt-label { color:#B9B6D9; margin: 22px 0 8px; font-weight: 600; }
        [data-testid="stChatInput"] {
            border-radius: 26px;
            border: 1px solid rgba(176,123,255,.5);
            background: rgba(21,23,56,.85);
            box-shadow: 0 8px 28px rgba(124,58,237,.18);
            padding: 4px 6px;
        }
        [data-testid="stChatInput"] textarea { padding: 10px 6px; }
        [data-testid="stChatInputSubmitButton"] button {
            border-radius: 50%;
            background: linear-gradient(135deg, #D75BFF, #6E77FF 60%, #32DACB) !important;
            border: none !important;
        }

        /* ---------- Chat bubbles (AI Dance Guide) ---------- */
        /* User and assistant messages alternate strictly in this app, so
           nth-of-type(odd/even) reliably tracks role without needing JS.
           stChatMessage is itself the flex row (avatar + content side by
           side); we reverse that row for the user so the avatar lands on
           the right, then push the whole bubble to the right edge with
           margin-left:auto and cap its width so it reads as a bubble
           instead of a full-width strip. */
        [data-testid="stChatMessage"] {
            display: flex !important;
            align-items: flex-start;
            border-radius: 18px;
            padding: 10px 16px;
            margin-bottom: 12px;
            border: 1px solid transparent;
            max-width: 76%;
            width: fit-content;
        }
        [data-testid="stChatMessage"]:nth-of-type(odd) {
            flex-direction: row-reverse;
            margin-left: auto;
            margin-right: 0;
            background: linear-gradient(100deg, rgba(215,91,255,.22), rgba(110,119,255,.22) 58%, rgba(50,218,203,.16));
            border-color: rgba(180,140,255,.35);
            border-radius: 18px 18px 4px 18px;
        }
        [data-testid="stChatMessage"]:nth-of-type(even) {
            margin-right: auto;
            margin-left: 0;
            background: linear-gradient(135deg, rgba(36,38,82,.82), rgba(19,21,51,.9));
            border-color: rgba(255,255,255,.12);
            border-radius: 18px 18px 18px 4px;
        }
        [data-testid="stChatMessageContent"] { text-align: left; }
        [data-testid="stChatMessage"] h3 { color: #83F6E9; font-size: 1.05rem; margin: 10px 0 4px; }
        [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
            box-shadow: 0 0 0 2px rgba(255,255,255,.08);
            flex-shrink: 0;
        }

        /* ---------- Self-contained chat "window" panel ---------- */
        /* Applies only to the bordered container immediately following
           a .chat-window-anchor marker div, so it doesn't affect the
           bordered chart cards used elsewhere (e.g. Dataset Insights). */
        .chat-window-anchor + div[data-testid="stVerticalBlockBorderWrapper"] {
            background: radial-gradient(120% 90% at 50% -12%, rgba(167,72,255,.28), rgba(9,10,27,0) 62%),
                        linear-gradient(165deg, rgba(21,23,56,.94), rgba(11,12,32,.97));
            border: 1px solid rgba(180,140,255,.3) !important;
            border-radius: 26px !important;
            box-shadow: 0 30px 80px rgba(90,40,200,.28);
            padding: 4px 14px 0 !important;
        }
        .chat-window-titlebar {
            display: flex; align-items: center; gap: 8px;
            padding: 14px 4px 12px; margin-bottom: 6px;
            border-bottom: 1px solid rgba(255,255,255,.08);
        }
        .chat-window-titlebar .dot { width: 11px; height: 11px; border-radius: 50%; }
        .chat-window-titlebar .dot.red { background: #FF5F57; }
        .chat-window-titlebar .dot.yellow { background: #FEBC2E; }
        .chat-window-titlebar .dot.green { background: #28C840; }
        .chat-window-titlebar .title {
            margin-left: 10px; color: #D9D9FF; font-size: .85rem; font-weight: 700; letter-spacing: .02em;
        }
        .chat-window-titlebar .status {
            margin-left: auto; color: #83F6E9; font-size: .72rem; font-weight: 700; letter-spacing: .08em;
            display: flex; align-items: center; gap: 6px;
        }
        .chat-window-titlebar .status .pulse {
            width: 7px; height: 7px; border-radius: 50%; background: #34D399;
            box-shadow: 0 0 0 0 rgba(52,211,153,.6); animation: chatpulse 2s infinite;
        }
        @keyframes chatpulse {
            0% { box-shadow: 0 0 0 0 rgba(52,211,153,.55); }
            70% { box-shadow: 0 0 0 7px rgba(52,211,153,0); }
            100% { box-shadow: 0 0 0 0 rgba(52,211,153,0); }
        }
        /* Inside the windowed panel, chat_input renders "inline" (docked
           to this container's own bottom, not the page) -- style it to
           blend into the panel rather than float as a separate pill. */
        .chat-window-anchor + div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stChatInput"] {
            margin: 10px 0 14px;
        }
        .home-hero { display:flex; justify-content:space-between; align-items:center; gap:30px; padding:48px 52px; border-radius:30px; background:linear-gradient(130deg,rgba(120,74,224,.45),rgba(23,102,185,.33),rgba(9,10,27,.2)); border:1px solid rgba(255,255,255,.15); }
        .home-hero h1 { font-size:clamp(2.5rem,5vw,4.8rem); line-height:.95; letter-spacing:-.07em; margin:.2em 0; }
        .home-hero p { color:#D5D1F5; font-size:1.08rem; max-width:560px; }
        .hero-orb { display:grid; place-items:center; flex:0 0 150px; width:150px; height:150px; border-radius:50%; font-size:70px; background:radial-gradient(circle at 30% 20%,#ffe079,#dd68ff 35%,#3c49db 80%); box-shadow:0 0 70px rgba(191,91,255,.55); transform:rotate(-8deg); }
        .featured-card { min-height:210px; } .featured-card h3 { font-size:1.55rem; margin:.15rem 0; } .card-place { color:#83F6E9; }.tag { display:inline-block; margin:.4rem .25rem 0 0; padding:5px 9px; border-radius:999px; font-size:.75rem; background:rgba(126,120,255,.19); border:1px solid rgba(180,175,255,.28); }.action-card { min-height:145px; transition:transform .2s ease; }.action-card:hover { transform:translateY(-5px); }

        /* ---------- Footer ---------- */
        .fd-footer {
            text-align: center;
            color: #64748B;
            font-size: 12px;
            margin-top: 40px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
