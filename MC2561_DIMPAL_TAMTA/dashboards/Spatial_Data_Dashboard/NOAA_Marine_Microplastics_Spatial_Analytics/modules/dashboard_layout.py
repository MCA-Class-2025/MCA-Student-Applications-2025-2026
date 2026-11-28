"""Shared page chrome: header, horizontal navigation, filter bar, cards, KPI tiles."""
import streamlit as st
from config.settings import APP_TITLE, APP_SUBTITLE, PAGES
from config import theme_manager as tm
from modules.data_loader import load_data
from modules import filters

PLOT_CFG = {"displaylogo": False, "scrollZoom": True, "toImageButtonOptions": {"format": "png", "scale": 2}}


def show(fig, key, select=False, config=None):
    """Render a Plotly figure; returns the selection event when select=True."""
    kw = dict(key=key, theme=None, config=config or PLOT_CFG)
    if select:
        kw.update(on_select="rerun", selection_mode="points")
    try:
        return st.plotly_chart(fig, width="stretch", **kw)
    except TypeError:
        return st.plotly_chart(fig, use_container_width=True, **kw)


def card(title=None, note=None):
    n = st.session_state.get("_cardn", 0) + 1
    st.session_state["_cardn"] = n
    c = st.container(border=True, key=f"card_{n}")
    if title:
        c.markdown(f"<div class='ctitle'>{title}</div>", unsafe_allow_html=True)
    if note:
        c.markdown(f"<div class='note'>{note}</div>", unsafe_allow_html=True)
    return c


def kpi(col, label, value, sub=""):
    col.markdown(f"<div class='kpi'><div class='l'>{label}</div><div class='v'>{value}</div>"
                 f"<div class='s'>{sub}&nbsp;</div></div>", unsafe_allow_html=True)


def explain(simple, technical=None):
    """Short box: plain-language reading guide + one technical line."""
    t = f"<div class='tech'><b>Technical:</b> {technical}</div>" if technical else ""
    st.markdown(f"<div class='explain'><b>In simple words:</b> {simple}{t}</div>", unsafe_allow_html=True)


def message(text, kind="info"):
    getattr(st, kind)(text)


def page_setup(idx, advanced=True):
    st.set_page_config(page_title=f"{APP_TITLE} - {PAGES[idx][2]}", page_icon="🌊",
                       layout="wide", initial_sidebar_state="collapsed")
    st.session_state["_cardn"] = 0
    h = st.columns([5, 1.2, 1.5])
    with h[1].popover("🎨 Theme", use_container_width=True):
        tm.theme_gallery()
    white = h[2].toggle("White chart background", value=st.session_state.get("chart_white", False), key="w_chart_white",
                        help="Keeps the panels behind charts and maps white while the page colours follow the theme")
    st.session_state["chart_white"] = white
    th = tm.get_theme()
    st.markdown(tm.css(tm.get_base_theme(), th), unsafe_allow_html=True)
    h[0].markdown(f"<div class='hdr'><h1>{APP_TITLE}</h1><div class='sub'>{APP_SUBTITLE} &nbsp;·&nbsp; {PAGES[idx][2]}</div></div>",
                  unsafe_allow_html=True)

    nav = st.columns(len(PAGES))
    for n, (c, (path, label, _)) in enumerate(zip(nav, PAGES), 1):
        c.page_link(path, label=f"{n}  {label}")

    df, quality = load_data()
    dff, dfnc, F = filters.filter_bar(df, advanced)
    if dff.empty:
        st.warning("No records match the current filters. Press **Reset** to restore the global view.")
        st.stop()
    return dict(df=df, dff=dff, dfnc=dfnc, F=F, quality=quality, th=th)
