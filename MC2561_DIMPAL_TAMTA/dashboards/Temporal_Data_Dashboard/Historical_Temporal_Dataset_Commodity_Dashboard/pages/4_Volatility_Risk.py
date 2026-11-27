import streamlit as st
from modules import charts as ch, pagecharts as pc, shell, ui

ctx = shell.setup()
T, f = ctx.T, ctx.focus
ctx.need_focus()
S = ctx.sel if len(ctx.sel) >= 2 else [f]
U = ctx.sel if len(ctx.sel) >= 2 else ctx.names_all
daily, dS, dU = ctx.subset([f]), ctx.subset(S), ctx.subset(U)
cm = ch.color_map(S, T, ctx.names_all)
cu = ch.color_map(U, T, ctx.names_all)

c1, c2, c3 = st.columns([2, 1.5, 3])
win = c1.slider("Rolling window (observations)", 5, 120, 20, key="p4_win")
ann = c2.toggle("Annualise (×√252)", value=False, key="p4_ann")
c3.markdown(f"<div class='hint'>Daily return = (Close − previous Close) / previous Close × 100, computed per commodity. "
            f"Returns across zero/negative prices are left blank.</div>", unsafe_allow_html=True)

r = pc.risk_metrics(daily)
if r:
    tint = ("rgba(229,72,77,.10)", "rgba(229,72,77,.18)")
    k = st.columns(5)
    k[0].markdown(ui.kpi("🌪️", "Annualised volatility", f"{r['vol_ann']:.1f}%", f, tint), unsafe_allow_html=True)
    k[1].markdown(ui.kpi("📉", "Max drawdown", f"{r['maxdd']:.1f}%", "within range", tint), unsafe_allow_html=True)
    k[2].markdown(ui.kpi("🛡️", "Daily VaR 95%", f"{r['var95']:.2f}%", "5th percentile return", tint), unsafe_allow_html=True)
    k[3].markdown(ui.kpi("⬇️", "Worst day", f"{r['worst']:.2f}%", "", tint), unsafe_allow_html=True)
    k[4].markdown(ui.kpi("⬆️", "Best day", f"{r['best']:+.2f}%", "", tint), unsafe_allow_html=True)

a1, a2 = st.columns(2)
with a1:
    with shell.card("p4a", "Daily Percentage Return", ", ".join(S)):
        shell.plot(pc.returns_line(dS, S, T, cm, 300), "p4a")
with a2:
    with shell.card("p4b", "Rolling Volatility", f"{win}-observation window"):
        shell.plot(pc.rolling_vol(ctx.df, S, ctx.start, ctx.end, win, ann, T, cm, 300), "p4b")
b1, b2 = st.columns(2)
with b1:
    with shell.card("p4c", "Distribution of Daily Returns", f"{f} · vs normal curve"):
        shell.plot(pc.hist_returns(daily, T, 300), "p4c")
with b2:
    with shell.card("p4d", "Drawdown", f"{f} · distance below running peak"):
        shell.plot(pc.drawdown(daily, T, 300), "p4d")
c1, c2 = st.columns(2)
with c1:
    with shell.card("p4e", "Volatility by Commodity", "annualised" if ann else "daily"):
        shell.plot(pc.vol_bar(dU, U, ann, T, cu, 360), "p4e")
with c2:
    with shell.card("p4f", "Volatility Comparison", "distribution of daily returns"):
        shell.plot(pc.box_vol(dU, U, T, cu, 360), "p4f")
with shell.card("p4g", "Daily Price Range", f"{f} · (High − Low) / Open"):
    shell.plot(pc.range_chart(daily, T, 280), "p4g")
st.caption("Historical risk measures describe the past in the selected range; they are not forecasts.")
