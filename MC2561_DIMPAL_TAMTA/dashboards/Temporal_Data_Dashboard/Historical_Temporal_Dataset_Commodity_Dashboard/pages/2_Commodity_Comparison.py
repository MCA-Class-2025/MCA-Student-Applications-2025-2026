import streamlit as st
from modules import charts as ch, pagecharts as pc, shell
from modules.data import performance_table

ctx = shell.setup()
T = ctx.T
U = ctx.sel if len(ctx.sel) >= 2 else ctx.names_all
dU = ctx.subset(U)
cm = ch.color_map(U, T, ctx.names_all)
st.markdown(f"<div class='hint'>Comparing <b>{', '.join(U) if len(ctx.sel) >= 2 else 'all ' + str(len(U)) + ' commodities'}</b>"
            f"{'' if len(ctx.sel) >= 2 else ' (select 2–8 commodities above to focus the comparison)'} · {ctx.rng} {ctx.cal}</div>", unsafe_allow_html=True)
if dU.empty:
    st.warning("No records with the current filters.")
    st.stop()

p = performance_table(dU)
if len(p):
    st.markdown(f"<div class='hint'>Best over the range: <b>{p.iloc[0]['name']}</b> ({p.iloc[0]['change_pct']:+.1f}%) · "
                f"weakest: <b>{p.iloc[-1]['name']}</b> ({p.iloc[-1]['change_pct']:+.1f}%). "
                f"Each commodity is measured from its own first to last close inside the range.</div>", unsafe_allow_html=True)

a1, a2 = st.columns(2)
with a1:
    log = st.toggle("Log scale", value=True, key="p2_log")
    with shell.card("p2a", "Closing Price Comparison", f"{ctx.metric} · {ctx.interval} · own units"):
        shell.plot(pc.multi_price(dU, U, ctx.interval, ctx.metric, T, cm, 330, log), "p2a")
with a2:
    st.markdown("<div style='height:2.2rem'></div>", unsafe_allow_html=True)
    with shell.card("p2b", "Normalised Performance", "index = 100 at each commodity's first date in range"):
        shell.plot(ch.line_fig(dU, list(U), ctx.interval, ctx.metric, T, cm, 330), "p2b")
b1, b2 = st.columns(2)
with b1:
    with shell.card("p2c", "Average Price by Commodity", ctx.metric):
        shell.plot(pc.avg_bar(dU, U, ctx.metric, T, cm, 360), "p2c")
with b2:
    with shell.card("p2d", "Highest & Lowest Price", "range of each commodity"):
        shell.plot(pc.highlow_bar(dU, U, T, 360), "p2d")
c1, c2 = st.columns(2)
with c1:
    with shell.card("p2e", "Correlation of Daily Returns", "pairwise, overlapping dates only"):
        shell.plot(pc.corr_heatmap(dU.pivot_table(index="date", columns="name", values="ret"), T, 400), "p2e")
with c2:
    with shell.card("p2f", "Commodity Ranking", "% change in close over range"):
        shell.plot(pc.rank_bar(dU, T, 400), "p2f")
st.caption("Correlation shows how daily moves line up historically; it does not imply that one commodity drives another.")
