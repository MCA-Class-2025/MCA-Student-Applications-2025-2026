"""GeoTime Analytics - Commodity Temporal Analytics: main dashboard."""
import streamlit as st

from modules import charts as ch, pagecharts as pc, shell, ui
from modules.data import agg, fmt_price, performance_table, pick_interval, summarize

ctx = shell.setup(main=True)
T, sel, d, d_all, focus = ctx.T, ctx.sel, ctx.d, ctx.d_all, ctx.focus
interval, metric, cmap = ctx.interval, ctx.metric, ctx.cmap

# ── KPIs ─────────────────────────────────────────────────────────────────────────────────────
fs = summarize(d[d["name"] == focus]) if focus else None
with ctx.kpi_box:
    k = st.columns(4)
    k[0].markdown(ui.kpi("", "Total Records", f"{len(d):,}", "in current filters", ("rgba(31,111,235,.10)", "rgba(31,111,235,.18)")), unsafe_allow_html=True)
    k[1].markdown(ui.kpi("", "Commodities", f"{d['name'].nunique()}", "selected" if sel else "all in dataset", ("rgba(18,161,80,.10)", "rgba(18,161,80,.18)")), unsafe_allow_html=True)
    cov = f"{d['date'].min():%Y-%m-%d} → {d['date'].max():%Y-%m-%d}" if len(d) else "—"
    k[2].markdown(ui.kpi("", "Date Coverage", cov, "first → last trading date", ("rgba(124,77,255,.10)", "rgba(124,77,255,.18)"), small=True), unsafe_allow_html=True)
    if fs:
        k[3].markdown(ui.kpi("", "Latest Close", fmt_price(fs["latest"]), f"{focus} · {fs['latest_date']:%d %b %Y}",
                             ("rgba(242,142,43,.10)", "rgba(242,142,43,.20)")), unsafe_allow_html=True)
    else:
        pt = performance_table(d_all)
        k[3].markdown(ui.kpi("", "Average Change", f"{pt['change_pct'].mean():+.1f}%" if len(pt) else "—",
                             "all commodities over range", ("rgba(242,142,43,.10)", "rgba(242,142,43,.20)")), unsafe_allow_html=True)

H1, H2, H3, H4 = 395, 310, 280, 320

# ── row 1 · line (2 cols) + commodity panel ──────────────────────────────────────────────────
with ctx.line_col:
    with shell.card("line", "Historical Price Trend", f"{metric} · {interval}" + (" · indexed to 100" if len(sel) != 1 else "")):
        shell.plot(ch.line_fig(d, sel, interval, metric, T, cmap, H1), "line")
if True:
    with ctx.panel_box:
        if not sel:
            st.markdown(ui.panel_none(performance_table(d_all), ctx.dark), unsafe_allow_html=True)
        elif len(sel) == 1:
            one = d[d["name"] == sel[0]]
            s = summarize(one)
            st.markdown(ui.panel_single(sel[0], one["symbol"].iloc[0], s, ctx.dark) if s else
                        "<div class='hint'>No records for this commodity in the chosen range.</div>", unsafe_allow_html=True)
        else:
            rows = [(n, g["symbol"].iloc[0], summarize(g)) for n in sel for g in [d[d["name"] == n]] if len(g)]
            st.markdown(ui.panel_multi(rows, focus, ctx.dark), unsafe_allow_html=True)

# ── row 2 · three charts ─────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    with shell.card("donut", "Commodity Composition", "share of records"):
        shell.plot(ch.donut_fig(d_all, sel, T, cmap, H2), "donut")
with c2:
    with shell.card("ribbon", "Performance Ranking", "ribbon · price index by period"):
        shell.plot(ch.ribbon_fig(d_all if len(sel) < 2 else d, sel, interval, metric, T, cmap, H2), "ribbon")
with c3:
    with shell.card("waterfall", "Price Change Analysis", f"waterfall · {focus or 'Market Index'}"):
        shell.plot(ch.waterfall_fig(d, focus, interval, metric, T, H2), "waterfall")

# ── row 3 · two charts ───────────────────────────────────────────────────────────────────────
e1, e2 = st.columns(2)
with e1:
    with shell.card("volume", "Trading Activity", f"volume bars · {focus or 'all commodities'}"):
        shell.plot(ch.volume_fig(d, focus, interval, T, H3), "volume")
with e2:
    with shell.card("combo", "Price & Volume Analysis", f"{metric} line + volume bars · {focus or 'all commodities'}"):
        shell.plot(ch.combo_fig(d, focus, interval, metric, T, H3), "combo")

# ── row 4 · two extra visuals: candlestick (OHLC) + market movers ────────────────────────────
f1, f2 = st.columns(2)
with f1:
    iv = pick_interval(d["date"].min(), d["date"].max(), interval, 160) if (focus and len(d)) else interval
    with shell.card("candle", "OHLC Candlestick", f"{focus or 'pick a commodity'} · {iv}"):
        if focus and len(d):
            shell.plot(ch.candle_fig(agg(d[d["name"] == focus], iv), focus, T, H4), "candle")
        else:
            shell.plot(ch.empty_fig(T, H4, 'Pick a commodity for candles'), "candle")
with f2:
    with shell.card("movers", "Market Movers", "% change over range · all commodities"):
        shell.plot(pc.movers(d_all, sel, T, H4), "movers")

st.markdown("<div class='foot'>Source: commodity-prices.csv · prices as reported (units/currency not stated in the file) · "
            "volumes are contract-specific and not comparable across commodities · use the tabs at the top for the detailed pages</div>", unsafe_allow_html=True)
