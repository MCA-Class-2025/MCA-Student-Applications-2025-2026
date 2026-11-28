"""Shared page shell: header, navigation, global slicers, calendar filters, filtering.

Every page calls `ctx = shell.setup()` first, so slicer values (session_state keys) survive page changes.
"""
import calendar
from types import SimpleNamespace

import pandas as pd
import streamlit as st

from . import charts as ch, ui
from .data import METRICS, ORDER, RANGES, filter_df, load_data, preset_range, to_csv_bytes
from .theme import DEFAULT_THEME, THEMES

Z = "​"  # label for icon-only buttons
NAV = [("app.py", "Dashboard"), ("pages/1_Historical_Price_Trends.py", "Price Trends"),
       ("pages/2_Commodity_Comparison.py", "Comparison"), ("pages/3_Trading_Volume.py", "Volume"),
       ("pages/4_Volatility_Risk.py", "Volatility & Risk"), ("pages/5_Seasonal_Analysis.py", "Seasonality"),
       ("pages/6_Statistical_Analysis.py", "Statistics & Data")]
DEFAULTS = {"sel": [], "range": "All Time", "interval": "Monthly", "metric": "Close",
            "f_year": [], "f_month": [], "f_quarter": []}


def _ver():
    try:
        return tuple(int(x) for x in st.__version__.split(".")[:2])
    except Exception:
        return (1, 40)


def stretch(fn=None):
    """Full-width kwarg: width="stretch" on newer Streamlit (>=1.50), use_container_width on older ones."""
    return {"width": "stretch"} if _ver() >= (1, 50) else {"use_container_width": True}


def reset_filters():
    for k, v in DEFAULTS.items():
        st.session_state[k] = list(v) if isinstance(v, list) else v
    st.session_state.pop("custom_range", None)


def card(key, title, sub=""):
    c = st.container(key=f"card_{key}")
    c.markdown(ui.title(title, sub), unsafe_allow_html=True)
    return c


def plot(fig, key):
    st.plotly_chart(fig, key=f"pc_{key}", config={"displaylogo": False, "displayModeBar": "hover"}, **stretch(st.plotly_chart))


def setup(main=False):
    st.set_page_config(page_title="Commodity Market Temporal Analysis", layout="wide",
                       initial_sidebar_state="collapsed")
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, list(v) if isinstance(v, list) else v)

    df, q = load_data()
    names_all = sorted(df["name"].unique())
    dmin, dmax = q["date_min"], q["date_max"]
    T = THEMES[st.session_state.get("theme_name", DEFAULT_THEME)]
    dark = T["mode"] == "dark"
    st.markdown(ui.css(T), unsafe_allow_html=True)

    # header: banner + labelled toolbar
    hb, h1, h2, h3, h4, h5 = st.columns([9, 1.1, 1.1, 1.0, 1.1, 1.0], vertical_alignment="center")
    hb.markdown(ui.banner(), unsafe_allow_html=True)
    with h1.popover("Theme", **stretch(st.popover)):
        st.radio("Theme", list(THEMES), key="theme_name")
        st.markdown(ui.swatches(THEMES), unsafe_allow_html=True)
    with h2.popover("Filters", **stretch(st.popover)):
        st.markdown("**Filters** (applied on every page)")
        st.selectbox("Date range", RANGES, key="range")
        if st.session_state["range"] == "Custom":
            st.date_input("From – to", value=(dmin.date(), dmax.date()), min_value=dmin.date(),
                          max_value=dmax.date(), key="custom_range")
        st.multiselect("Year", sorted(df["year"].unique()), key="f_year")
        st.multiselect("Month", list(range(1, 13)), key="f_month", format_func=lambda m: calendar.month_abbr[m])
        st.multiselect("Quarter", [1, 2, 3, 4], key="f_quarter", format_func=lambda x: f"Q{x}")
    with h3.popover("Info", **stretch(st.popover)):
        st.markdown(
            f"**Data quality** (nothing hidden)\n\n"
            f"- {q['rows']:,} records · {q['commodities']} commodities · {dmin:%Y-%m-%d} → {dmax:%Y-%m-%d}\n"
            f"- {q['duplicate_keys_removed']} repeated date+symbol rows (kept the last one)\n"
            f"- {q['missing_volume']:,} rows ({q['missing_volume'] / q['rows']:.1%}) have no volume: gaps, never 0\n"
            f"- {q['high_below_low']} rows with High < Low and {q['close_outside_range']:,} with Close outside High/Low: kept as in the source\n"
            f"- {q['non_positive_close']} non-positive close (WTI crude, 2020-04-19, a real negative-price event): kept; "
            f"{q['returns_excluded']} daily returns around it are left blank because a % return is undefined across zero/negative prices\n\n"
            f"Prices are as reported in the file; contract units/currency are not given.")
    h5.button("Reset", help="Reset filters", on_click=reset_filters, **stretch(st.button))
    dl_slot = h4.container()

    # navigation
    cols = st.columns(len(NAV))
    for c, (path, label) in zip(cols, NAV):
        c.page_link(path, label=label, **stretch(st.page_link))

    st.markdown("<div style='height:.35rem'></div>", unsafe_allow_html=True)
    kpi_box = st.container()

    # global slicers
    sel_pre = st.session_state["sel"]          # value from this run's widget state (needed before the box is drawn)
    line_col = panel_box = None
    if main:
        s3, s4, s5 = st.columns([1.2, 1.2, 1.8])
    else:
        s1, s3, s4, s5 = st.columns([3.2, 1.2, 1.1, 1.7])
        sel_pre = s1.multiselect("Commodity", names_all, key="sel", max_selections=8,
                                 placeholder="Nothing selected: all commodities shown")
    rng = st.session_state["range"]
    interval = s3.selectbox("Time interval", ORDER, key="interval")
    metric = s4.selectbox("Price metric", list(METRICS), key="metric")
    cr = st.session_state.get("custom_range")
    if rng == "Custom" and cr is not None and len(cr) == 2:
        start, end = pd.Timestamp(cr[0]), pd.Timestamp(cr[1])
    else:
        start, end = preset_range(rng if rng != "Custom" else "All Time", dmin, dmax)
    pick = s5.selectbox("Focus commodity", sel_pre, index=0 if len(sel_pre) >= 2 else None, disabled=len(sel_pre) < 2,
                        placeholder="pick 2+ commodities",
                        help="Single-commodity charts use this one when several are selected.")
    if main:
        line_col, side_col = st.columns([2, 1])
        panel_box = side_col.container(key="card_panel")
        panel_box.markdown(ui.title("Commodity", f"{len(sel_pre)} selected" if sel_pre else "all commodities"), unsafe_allow_html=True)
        with panel_box:
            sel_pre = st.multiselect("Choose commodities (max 8)", names_all, key="sel", max_selections=8,
                                     placeholder="All commodities shown. Pick up to 8 to focus.")
    sel = sel_pre
    focus = pick if len(sel) >= 2 else (sel[0] if sel else None)

    fy, fm, fq = st.session_state["f_year"], st.session_state["f_month"], st.session_state["f_quarter"]

    def subset(names=None):
        """Rows inside the date range + calendar filters, for the given commodity names (None/[] = all)."""
        x = filter_df(df, names or [], start, end)
        if fy: x = x[x["year"].isin(fy)]
        if fm: x = x[x["month"].isin(fm)]
        if fq: x = x[x["quarter"].isin(fq)]
        return x

    d, d_all = subset(sel), subset([])
    dl_slot.download_button(Z, data=to_csv_bytes(d), file_name="commodity_filtered.csv", mime="text/csv",
                            icon=":material/download:", help="Download filtered records (CSV)", **stretch(st.download_button))

    def one(name, clip=True):
        """Full-history rows for one commodity (so rolling windows are warmed up), optionally clipped to the range."""
        x = df[df["name"] == name]
        return x[(x["date"] >= start) & (x["date"] <= end)] if clip else x

    def need_focus():
        if not focus:
            st.info("Select a commodity in the Commodity box to see this page.")
            st.stop()

    cal = " · ".join(filter(None, [f"years {fy}" if fy else "", f"months {[calendar.month_abbr[m] for m in fm]}" if fm else "",
                                   f"quarters {fq}" if fq else ""]))
    return SimpleNamespace(df=df, q=q, names_all=names_all, dmin=dmin, dmax=dmax, T=T, dark=dark, sel=sel, rng=rng,
                           interval=interval, metric=metric, focus=focus, start=start, end=end, d=d, d_all=d_all,
                           subset=subset, one=one, need_focus=need_focus, kpi_box=kpi_box, cal=cal,
                           cmap=ch.color_map(sel, T, names_all), line_col=line_col, panel_box=panel_box)
