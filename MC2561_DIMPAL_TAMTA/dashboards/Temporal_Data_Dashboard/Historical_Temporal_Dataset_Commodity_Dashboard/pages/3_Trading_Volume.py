import streamlit as st
from modules import charts as ch, pagecharts as pc, shell, ui

ctx = shell.setup()
T, f = ctx.T, ctx.focus
ctx.need_focus()
daily = ctx.subset([f])
full = ctx.one(f, clip=False)
U = ctx.sel if len(ctx.sel) >= 2 else ctx.names_all
dU = ctx.subset(U)
cm = ch.color_map(U, T, ctx.names_all)
v = daily["volume"]
if v.notna().sum() == 0:
    st.warning(f"{f} has no reported volume in this range.")
    st.stop()

tint = ("rgba(31,111,235,.10)", "rgba(31,111,235,.18)")
k = st.columns(4)
k[0].markdown(ui.kpi("📦", "Average daily volume", f"{v.mean():,.0f}", f, tint), unsafe_allow_html=True)
k[1].markdown(ui.kpi("🔝", "Highest volume day", f"{v.max():,.0f}", f"{daily.loc[v.idxmax(), 'date']:%d %b %Y}", tint), unsafe_allow_html=True)
k[2].markdown(ui.kpi("🧾", "Total volume", f"{v.sum():,.0f}", "sum of reported days", tint), unsafe_allow_html=True)
k[3].markdown(ui.kpi("❔", "Days without volume", f"{v.isna().mean():.1%}", f"{int(v.isna().sum()):,} of {len(v):,} rows", tint), unsafe_allow_html=True)
st.markdown("<div class='hint'>Volume is contract volume as reported; missing values are shown as gaps, and volumes of different commodities are not directly comparable.</div>", unsafe_allow_html=True)

with shell.card("p3a", "Daily Trading Volume", f"{f} · with 20-day average"):
    shell.plot(pc.vol_daily(full, ctx.start, ctx.end, T, 340), "p3a")
b1, b2 = st.columns(2)
with b1:
    with shell.card("p3b", "Monthly Trading Volume", "total per month"):
        shell.plot(pc.vol_period(daily, "ME", T, 300), "p3b")
with b2:
    with shell.card("p3c", "Yearly Trading Volume", "total per year (partial years are lower)"):
        shell.plot(pc.vol_period(daily, "YE", T, 300), "p3c")
c1, c2 = st.columns(2)
with c1:
    with shell.card("p3d", "Commodity-wise Volume", "average daily volume"):
        shell.plot(pc.vol_compare(dU, U, T, cm, 380), "p3d")
with c2:
    with shell.card("p3e", "Price vs Volume", f"{f} · colour = year"):
        shell.plot(pc.price_volume_scatter(daily, ctx.metric, T, 380), "p3e")
with shell.card("p3f", "Rolling Average Volume & Unusual Days", "red = volume above 60-day mean + 3σ"):
    shell.plot(pc.vol_rolling(full, ctx.start, ctx.end, T, 320), "p3f")
with st.expander("Ten highest-volume days"):
    st.dataframe(pc.top_volume(daily), hide_index=True, **shell.stretch(st.dataframe))
