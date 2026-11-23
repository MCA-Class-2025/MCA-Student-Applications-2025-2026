"""Page 5 · Global & Indian Production Analysis"""
import pandas as pd
import streamlit as st
from modules import charts as ch, pagecharts as pc, shell
from modules.data import GLOB, IND, SHARE, counts, loc_info

ctx = shell.setup()
T, d = ctx.T, ctx.d
c1, c2 = st.columns([1, 2])
with c1: r = shell.food_picker(d, "food_p5", "Selected food")
mode = c2.radio("Map shows", ["Selected food (zoom to producers)", "All filtered foods (food count per place)"], horizontal=True, key="p5_mode")
food = r["Food Name"]
m = st.columns(5)
for col, (l, v) in zip(m, [("Global production", f"{r[GLOB]:,.0f} t"), ("India production", f"{r[IND]:,.0f} t"), ("India's share", f"{r[SHARE]:g} %"),
                           ("Top country", r["Top Producing Country"]), ("Top Indian state", r["Top Producing Indian State"])]):
    col.metric(l, v)
st.markdown(f"**Top 3 countries:** {r['Top 3 Producing Countries']} · **Top 3 Indian states:** {r['Top 3 Producing Indian States']} · **Source crop (Assumption):** {r['Assumption']}")
single = mode.startswith("Selected")
if single:
    vc, vs = ch.rank_dict(r, "Top 3 Producing Countries"), ch.rank_dict(r, "Top 3 Producing Indian States")
    hc = {k: f"<b>{k}</b><br>Rank #{i} producer of {food}" for k, i in vc.items()}
    hs = {k: f"<b>{k}</b><br>Rank #{i} state for {food}" for k, i in vs.items()}
else:
    ic, is_ = loc_info(d, "Top 3 Producing Countries"), loc_info(d, "Top 3 Producing Indian States")
    vc, vs = {k: v[0] for k, v in ic.items()}, {k: v[0] for k, v in is_.items()}
    hc = {k: f"<b>{k}</b><br>{v[0]} foods<br>{v[1]}" for k, v in ic.items()}
    hs = {k: f"<b>{k}</b><br>{v[0]} foods<br>{v[1]}" for k, v in is_.items()}
x1, x2 = st.columns(2)
with x1, shell.card("g1", "Interactive World Map", "producing countries · names shown on map"):
    shell.plot(ch.geo_map(vc, T, 520, False, single, hc), "g1")
with x2, shell.card("g2", "Interactive India Map", "producing states · names shown on map"):
    shell.plot(ch.geo_map(vs, T, 520, True, single, hs), "g2")
st.caption("Locations are highlighted by rank or food count because the dataset has no per-country/state tonnage. The boundary file predates Telangana (drawn inside Andhra Pradesh).")
n = st.slider("Top N", 5, 25, 12, key="p5_n")
x1, x2 = st.columns(2)
with x1, shell.card("g3", "Top Producing Countries", "foods listing the country in their top 3"):
    shell.plot(ch.top_names(pd.Series(counts(d["Top 3 Producing Countries"])), T, 480, n), "g3a")
with x2, shell.card("g4", "Top Producing Indian States", "foods listing the state in their top 3"):
    shell.plot(ch.top_names(pd.Series(counts(d["Top 3 Producing Indian States"])), T, 480, n), "g3b")
x1, x2 = st.columns(2)
with x1, shell.card("g5", "Global vs Indian Production", "tonnes · log scale"):
    shell.plot(pc.glob_vs_india(d, n, T, 440), "g5")
with x2, shell.card("g6", "India's Share in Global Production", "% · highest shares"):
    shell.plot(pc.share_bar(d, n, T, 440), "g6")
with shell.card("g7", "Production Table"):
    st.dataframe(d[["Food Name", "Assumption", "Top 3 Producing Countries", "Top 3 Producing Indian States", GLOB, IND, SHARE]].sort_values(GLOB, ascending=False), height=380, hide_index=True, **shell.stretch())
