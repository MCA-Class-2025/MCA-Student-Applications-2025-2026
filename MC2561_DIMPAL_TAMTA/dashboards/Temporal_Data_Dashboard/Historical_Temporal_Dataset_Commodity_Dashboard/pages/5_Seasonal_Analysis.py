import streamlit as st
from modules import pagecharts as pc, shell

ctx = shell.setup()
T, f = ctx.T, ctx.focus
ctx.need_focus()
daily = ctx.subset([f])
full = ctx.one(f, clip=False)
if daily.empty:
    st.warning("No records with the current filters.")
    st.stop()
st.markdown(f"<div class='hint'><b>{f}</b> · {ctx.rng} · these charts describe historical calendar patterns, not proof of predictable seasonal behaviour.</div>", unsafe_allow_html=True)

a1, a2 = st.columns([1, 1.4])
with a1:
    with shell.card("p5a", "Monthly Average Price", f"{ctx.metric} · affected by long-term trend"):
        shell.plot(pc.season_month(daily, ctx.metric, T, 340), "p5a")
with a2:
    mode = st.radio("Heatmap value", ["Monthly return (%)", "Average close"], horizontal=True, key="p5_mode", label_visibility="collapsed")
    with shell.card("p5b", "Year × Month Heatmap", mode):
        shell.plot(pc.heat_year_month(full, ctx.start, ctx.end, mode, T, 340), "p5b")
b1, b2 = st.columns(2)
with b1:
    with shell.card("p5c", "Quarterly Average Price", "Q1–Q4 across years"):
        shell.plot(pc.quarter_avg(daily, ctx.metric, T, 300), "p5c")
with b2:
    with shell.card("p5d", "Yearly Price Trend", "average vs year-end close"):
        shell.plot(pc.yearly_trend(daily, ctx.metric, T, 300), "p5d")
c1, c2 = st.columns(2)
with c1:
    with shell.card("p5e", "Day-of-Week Average Return", "mean daily return"):
        shell.plot(pc.dow_returns(daily, T, 300), "p5e")
with c2:
    with shell.card("p5f", "Monthly Trading Volume", "average monthly total by calendar month"):
        shell.plot(pc.month_volume(daily, T, 300), "p5f")
