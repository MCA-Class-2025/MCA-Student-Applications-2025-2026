"""Central theme manager: selection, persistence, CSS and Plotly styling."""
import json
import streamlit as st
from config.theme import THEMES
from config.settings import DEFAULT_THEME, PREFS_PATH


def _load_pref():
    try:
        k = json.loads(PREFS_PATH.read_text()).get("theme", DEFAULT_THEME)
        return k if k in THEMES else DEFAULT_THEME
    except Exception:
        return DEFAULT_THEME


def _save_pref(key):
    try:
        PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
        PREFS_PATH.write_text(json.dumps({"theme": key}))
    except Exception:
        pass


def get_base_theme():
    """The selected page theme (page background, header, navigation)."""
    if "theme" not in st.session_state:
        st.session_state["theme"] = _load_pref()
    return THEMES[st.session_state["theme"]]


def _mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def get_theme():
    """Theme used by charts/maps/cards. With the 'white chart background' option the panels behind the
    charts stay white (dark text) while the page, header and chart colours still follow the selected theme."""
    base = get_base_theme()
    if not st.session_state.get("chart_white") or base["mode"] == "light":
        return base
    p0 = base["palette"][0]
    return {**base, "mode": "light", "card": "#FFFFFF", "text": "#10243F", "muted": "#5B6F86", "border": "#D5E2EE",
            "grid": "rgba(128,128,128,0.18)", "land": "#DCE6EE", "ocean": "#FFFFFF", "coast": "#9FB6C9",
            "seq": ["#EAF2F8", _mix(p0, "#FFFFFF", .5), p0, _mix(p0, "#0B2545", .45), "#0B2545"]}


def set_theme(key):
    st.session_state["theme"] = key
    _save_pref(key)


CLASS_COLORS = {"Very Low": "#2F9E44", "Low": "#94C31D", "Medium": "#F2B705", "High": "#F76707", "Very High": "#C92A2A"}
_OCEANS = ["Atlantic Ocean", "Pacific Ocean", "Indian Ocean", "Arctic Ocean", "Southern Ocean"]


def ocean_colors(th=None):
    """Each ocean gets a fixed slot of the ACTIVE theme palette, so colours change with the theme."""
    th = th or get_theme()
    d = {o: th["palette"][i] for i, o in enumerate(_OCEANS)}
    d["Not recorded"] = "#8A94A3"
    return d


def color_map(names):
    """Stable colour per category from the active theme (oceans fixed, risk classes green->red)."""
    th = get_theme()
    oc, out, i = ocean_colors(th), {}, 0
    for n in names:
        if n in oc:
            out[n] = oc[n]
        elif n in CLASS_COLORS:
            out[n] = CLASS_COLORS[n]
        else:
            out[n] = th["palette"][i % len(th["palette"])]
            i += 1
    return out


def css(th, cth=None):
    cth = cth or th
    W = 'div[data-testid="stVerticalBlockBorderWrapper"]'
    K = 'div[class*="st-key-card_"]'

    def both(suffix=""):
        return ", ".join(f"{b} {suffix}".strip() for b in (W, K))
    return f"""
<style>
html {{font-size:17px;}}
.stApp {{background: {th['grad']}; background-attachment: fixed; color:{th['text']};}}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {{display:none !important;}}
header[data-testid="stHeader"] {{background:transparent; height:0;}}
.block-container {{padding-top:.7rem; padding-bottom:1.5rem; max-width:100%;}}
.stApp p, .stApp label, .stApp span, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp div[data-testid="stMarkdownContainer"] {{color:{th['text']};}}
.stCaption, [data-testid="stCaptionContainer"] * {{color:{th['muted']} !important;}}
{both()} {{background:{cth['card']} !important; border:1px solid {cth['border']}; border-radius:14px; box-shadow:0 2px 8px rgba(11,37,69,.07);}}
/* text INSIDE cards follows the card colours (matters for the white-chart option) */
{both("p")}, {both("span")}, {both("li")}, {both("label")}, {both('[data-testid="stWidgetLabel"] p')},
{both('[data-testid="stRadio"] label p')}, {both('[data-testid="stSlider"] *')}, {both('[data-testid="stSelectSlider"] *')},
{both('[data-testid="stMetricValue"]')}, {both('[data-testid="stMetricLabel"] *')} {{color:{cth['text']} !important;}}
{both('[data-testid="stCaptionContainer"] *')} {{color:{cth['muted']} !important;}}
.explain, .explain * {{color:{cth['text']};}}
/* navigation */
a[data-testid="stPageLink-NavLink"] {{background:{th['nav_bg']}; border-radius:10px; justify-content:center; padding:.5rem .3rem; min-height:2.6rem;}}
a[data-testid="stPageLink-NavLink"] *, a[data-testid="stPageLink-NavLink"] p {{color:{th['nav_text']} !important; font-weight:700; font-size:.9rem; white-space:normal !important; overflow:visible !important; text-overflow:clip !important; text-align:center;}}
a[data-testid="stPageLink-NavLink"][aria-current="page"] {{background:{th['primary']};}}
a[data-testid="stPageLink-NavLink"][aria-current="page"] *, a[data-testid="stPageLink-NavLink"][aria-current="page"] p {{color:#fff !important;}}
/* buttons: label text must always be readable */
.stButton>button, .stDownloadButton>button, div[data-testid="stPopover"]>button {{background:{th['primary']}; color:#fff !important; border:0; border-radius:10px; font-weight:700;}}
.stButton>button *, .stDownloadButton>button *, div[data-testid="stPopover"]>button * {{color:#fff !important; font-weight:700;}}
.stButton>button:hover, .stDownloadButton>button:hover, div[data-testid="stPopover"]>button:hover {{background:{th['accent']}; color:#fff !important;}}
.stButton>button:disabled {{opacity:.55;}}
/* filters / inputs */
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {{color:{th['text']} !important; font-weight:700; font-size:.88rem;}}
div[data-baseweb="select"]>div, .stTextInput input, .stDateInput input, .stNumberInput input {{background:#fff !important; color:#10243f !important; border-color:{th['border']};}}
div[data-baseweb="select"] *, .stDateInput input, .stTextInput input, .stNumberInput input {{color:#10243f !important;}}
div[data-baseweb="select"] svg {{fill:#10243f !important;}}
span[data-baseweb="tag"] {{background:{th['primary']} !important; border-radius:6px;}}
span[data-baseweb="tag"] * {{color:#fff !important; font-weight:600;}}
div[data-baseweb="popover"], div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li {{background:#fff !important;}}
div[data-baseweb="popover"] li *, div[data-baseweb="popover"] li {{color:#10243f !important;}}
div[data-baseweb="popover"] li:hover {{background:{th['nav_bg']} !important;}}
div[data-baseweb="calendar"] * {{color:#10243f !important;}}
div[data-testid="stRadio"] label p, div[data-testid="stSelectSlider"] *, div[data-testid="stSlider"] * {{color:{th['text']} !important;}}
div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] * {{color:{th['text']} !important;}}
button[data-baseweb="tab"] p {{color:{th['text']} !important; font-weight:700; font-size:.95rem;}}
[data-testid="stCheckbox"] p, label[data-baseweb="checkbox"] p {{color:{th['text']} !important; font-weight:700;}}
/* header */
.stApp .hdr {{background:linear-gradient(90deg,{th['primary']} 0%,{th['primary']} 45%,{th['accent']} 100%); border-radius:14px; padding:.9rem 1.3rem;}}
.stApp .hdr, .stApp .hdr * {{color:#ffffff !important;}}
.stApp .hdr h1 {{font-size:1.9rem; font-weight:800; margin:0; padding:0; letter-spacing:.05em; text-shadow:0 1px 3px rgba(0,0,0,.35);}}
.stApp .hdr .sub {{font-size:1rem; opacity:.95; font-weight:500;}}
/* kpi: Streamlit gives the markdown wrapper a -1rem bottom margin, which made the tile overflow into the row gap */
div[data-testid="stMarkdownContainer"]:has(> .kpi) {{margin-bottom:0 !important;}}
.kpi {{background:{cth['card']}; border:1px solid {cth['border']}; border-left:7px solid {th['accent']}; border-radius:14px; padding:.7rem 1rem; box-shadow:0 2px 8px rgba(11,37,69,.07);}}
.kpi .l {{font-size:.78rem; letter-spacing:.08em; text-transform:uppercase; color:{cth['muted']}; font-weight:700;}}
.kpi .v {{font-size:2rem; font-weight:800; color:{cth['text']}; line-height:1.15;}}
.kpi .s {{font-size:.8rem; color:{cth['muted']};}}
.ctitle {{font-weight:800; font-size:1.05rem; color:{cth['text']} !important; margin:.05rem 0 .1rem 0;}}
.note {{font-size:.85rem; color:{cth['muted']} !important; margin-bottom:.25rem;}}
/* explanation box */
.explain {{background:{cth['card']}; border:1px solid {cth['border']}; color:{cth['text']}; border-left:7px solid {th['primary']}; border-radius:14px; padding:.7rem 1.1rem; margin:.55rem 0; font-size:.95rem;}}
.explain b {{color:{cth['primary'] if cth['mode']=='dark' else '#0B2545'} !important;}}
.explain .tech {{color:{cth['muted']} !important; font-size:.85rem; margin-top:.25rem;}}
</style>"""


def style_fig(fig, th=None, height=280, title=None, legend=False):
    th = th or get_theme()
    txt = th["text"]
    fig.update_layout(
        height=height, margin=dict(l=8, r=12, t=34 if title else 10, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=txt, size=13, family="Source Sans Pro, Arial, sans-serif"), colorway=th["palette"], showlegend=legend,
        title=dict(text=f"<b>{title}</b>" if title else None, font=dict(size=15, color=txt), x=0.01) if title else None,
        legend=dict(orientation="h", y=-0.2, font=dict(size=12, color=txt)),
        hoverlabel=dict(bgcolor="#ffffff", font=dict(size=13, color="#10243f")),
    )
    ax = dict(gridcolor=th["grid"], zerolinecolor=th["grid"], tickfont=dict(size=12, color=txt),
              title_font=dict(size=13, color=txt), automargin=True)
    fig.update_xaxes(**ax)
    fig.update_yaxes(**ax)
    for f in (fig.for_each_xaxis, fig.for_each_yaxis):
        f(lambda a: a.update(title_text=f"<b>{a.title.text}</b>") if a.title.text and not str(a.title.text).startswith("<b>") else None)
    return fig


def theme_gallery():
    """Visual gallery of the eight themes (used inside the header popover)."""
    cur = st.session_state.get("theme")
    items = list(THEMES.values())
    for row in (items[:5], items[5:]):
        _gallery_row(row, cur)


def _gallery_row(items, cur):
    cols = st.columns(5)
    for c, t in zip(cols, items):
        sw = "".join(f"<span style='display:inline-block;width:10%;height:14px;background:{p}'></span>" for p in t["palette"])
        c.markdown(
            f"<div style='background:{t['grad']};border:3px solid "
            f"{t['accent'] if t['key']==cur else t['border']};border-radius:10px;padding:8px'>"
            f"<div style='background:{t['primary']};height:10px;border-radius:4px;margin-bottom:6px'></div>"
            f"<div style='background:{t['card']};border-radius:6px;padding:4px'>{sw}</div>"
            f"<div style='color:{t['text']} !important;font-weight:700;font-size:.85rem;margin-top:5px'>{t['name']}</div>"
            f"<div style='color:{t['muted']} !important;font-size:.7rem'>{t['desc']}</div></div>",
            unsafe_allow_html=True)
        c.button("Selected" if t["key"] == cur else "Use", key=f"th_{t['key']}",
                 on_click=set_theme, args=(t["key"],), disabled=t["key"] == cur, use_container_width=True)
