import streamlit as st
from modules import pagecharts as pc, shell, ui
from modules.data import agg, fmt_price, pick_interval, summarize

ctx = shell.setup()
T, f = ctx.T, ctx.focus
ctx.need_focus()
daily = ctx.subset([f])
if daily.empty:
    st.warning("No records for this commodity with the current filters.")
    st.stop()
full = ctx.one(f, clip=False)

c1, c2, c3 = st.columns([2.2, 2.2, 3])
ctype = c1.radio("Chart type", ["Line", "Area", "Candlestick", "OHLC"], horizontal=True, key="p1_type")
ma = c2.multiselect("Moving averages (periods)", [10, 20, 50, 100, 200], default=[20, 50], key="p1_ma")
iv = ctx.interval
if ctype in ("Candlestick", "OHLC"):
    iv = pick_interval(daily["date"].min(), daily["date"].max(), ctx.interval, 400)
c3.markdown(f"<div class='hint'>Showing <b>{f}</b> · {iv} candles/points" + (" (auto-coarsened so candles stay readable)" if iv != ctx.interval else "") + "</div>", unsafe_allow_html=True)

s = summarize(daily)
tint = [("rgba(31,111,235,.10)", "rgba(31,111,235,.18)"), ("rgba(18,161,80,.10)", "rgba(18,161,80,.18)"),
        ("rgba(124,77,255,.10)", "rgba(124,77,255,.18)"), ("rgba(242,142,43,.10)", "rgba(242,142,43,.20)")]
k = st.columns(5)
k[0].markdown(ui.kpi("📈", "Latest close", fmt_price(s["latest"]), f"{s['latest_date']:%d %b %Y}", tint[0]), unsafe_allow_html=True)
k[1].markdown(ui.kpi("↕️", "Change over range", f"{s['change_pct']:+.2f}%", f"{fmt_price(s['first'])} → {fmt_price(s['latest'])}", tint[1]), unsafe_allow_html=True)
k[2].markdown(ui.kpi("⬆️", "Period high", fmt_price(s["high"]), "highest High", tint[2]), unsafe_allow_html=True)
k[3].markdown(ui.kpi("⬇️", "Period low", fmt_price(s["low"]), "lowest Low", tint[3]), unsafe_allow_html=True)
k[4].markdown(ui.kpi("📏", "Avg daily range", f"{daily['range_pct'].mean():.2f}%", "(High−Low)/Open", tint[0]), unsafe_allow_html=True)

ma200 = full["close"].rolling(200).mean().iloc[-1] if len(full) >= 200 else None
txt = f"Over the selected range <b>{f}</b> moved <b>{s['change_pct']:+.1f}%</b> (first to last close)."
if ma200 and ctx.end >= ctx.dmax:
    txt += f" The latest close is {'above' if s['latest'] >= ma200 else 'below'} its 200-day average ({fmt_price(ma200)})."
st.markdown(f"<div class='hint'>{txt} {ctx.cal}</div>", unsafe_allow_html=True)

a = agg(daily, iv)
with shell.card("p1a", "Price History", f"{ctype} · {iv}"):
    shell.plot(pc.price_main(a, f, ctype, ctx.metric, T, 380, ma), "p1a")
x1, x2 = st.columns(2)
with x1:
    with shell.card("p1b", "Daily Open vs Close", "points above the dashed line closed higher"):
        shell.plot(pc.open_close(daily, T, 300), "p1b")
with x2:
    with shell.card("p1c", "Monthly Average Price", ctx.metric):
        shell.plot(pc.avg_series(daily, ctx.metric, "ME", T, 300), "p1c")
x3, x4 = st.columns(2)
with x3:
    with shell.card("p1d", "Yearly Average Price", ctx.metric):
        shell.plot(pc.avg_series(daily, ctx.metric, "YE", T, 300, bars=True), "p1d")
with x4:
    with shell.card("p1e", "High–Low Price Range", iv):
        shell.plot(pc.range_band(a, T, 300), "p1e")
with shell.card("p1f", "Rolling Average Trend", "close vs 20/50/200 trading-day averages (computed on full history)"):
    shell.plot(pc.ma_trend(full, ctx.start, ctx.end, T, 320), "p1f")
