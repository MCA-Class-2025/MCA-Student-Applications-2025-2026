"""Page 1 · Main Dashboard: KPIs, selected-food profile, donut, treemap, producer bars, maps, nutrient chart, scatter, cancer chart, dataset explorer."""
import pandas as pd
import streamlit as st
from modules import charts as ch, shell, ui
from modules.data import GLOB, IND, MACROS, MICROS, counts, export_view, filter_df, loc_info, to_csv_bytes, to_excel_bytes

ctx = shell.setup(main=True)
T, d = ctx.T, ctx.d
nc, ns = counts(d["Top 3 Producing Countries"]), counts(d["Top 3 Producing Indian States"])

for col, (lb, v, sb, c) in zip(st.columns(4), [("Total Foods", f"{len(d):,}", "unique food records", T["palette"][0]),
                                               ("Countries", len(nc), "producing-country coverage", T["palette"][1]),
                                               ("Indian States", len(ns), "producing-state coverage", T["palette"][2]),
                                               ("NOVA Groups", d["nova_group"].nunique(), "processing classification", T["palette"][3])]):
    col.markdown(ui.kpi(lb, v, sb, c), unsafe_allow_html=True)

with shell.card("profile", "Selected Food Profile", "image comes from this food's Image URL"):
    r = shell.food_picker(d, "food_main")
    a, b, c = st.columns([1, 1.8, 1.3])
    a.markdown(ui.profile_left(r, ctx.dark), unsafe_allow_html=True)
    b.markdown(ui.profile_mid(r, ch.NUTRI.get(r["Nutri-Score Grade"], "#999"), ch.NOVA.get(str(r["nova_group"]), "#999")), unsafe_allow_html=True)
    c.markdown(ui.profile_right(r), unsafe_allow_html=True)
food = r["Food Name"]

x1, x2 = st.columns(2)
with x1, shell.card("m1", "Nutri-Score Distribution", "donut · count and %"):
    shell.plot(ch.donut(d, "Nutri-Score Grade", ch.NUTRI, T, 400), "m1")
with x2, shell.card("m2", "Food Distribution by NOVA Group", "treemap · size = number of foods"):
    shell.plot(ch.treemap(d, T, 400), "m2")
x1, x2 = st.columns(2)
with x1, shell.card("m3", "Top Producing Countries", "foods listing the country among top 3 producers"):
    shell.plot(ch.top_names(pd.Series(nc), T, 460, 12), "m3")
with x2, shell.card("m4", "Top Producing Indian States", "foods listing the state among top 3 producers"):
    shell.plot(ch.top_names(pd.Series(ns), T, 460, 12), "m4")

with shell.card("map", "Interactive Production Map", f"zooms to the top producers of {food}"):
    view = st.radio("Map", ["🌍 World", "🇮🇳 India"], horizontal=True, key="mapview", label_visibility="collapsed")
    if view.startswith("🌍"):
        v = ch.rank_dict(r, "Top 3 Producing Countries")
        st.markdown(f"**{food}** · " + (" · ".join(f"#{i} {k}" for k, i in v.items()) or "no producing country listed"))
        shell.plot(ch.geo_map(v, T, 520, False, True, {k: f"<b>{k}</b><br>Rank #{i} producer of {food}<br>Global production: {r[GLOB]:,.0f} t" for k, i in v.items()}), "map_w")
    else:
        v = ch.rank_dict(r, "Top 3 Producing Indian States")
        st.markdown(f"**{food}** · " + (" · ".join(f"#{i} {k}" for k, i in v.items()) or "not produced in India"))
        shell.plot(ch.geo_map(v, T, 560, True, True, {k: f"<b>{k}</b><br>Rank #{i} state for {food}<br>India production: {r[IND]:,.0f} t" for k, i in v.items()}), "map_i")
        st.caption("The bundled boundary file predates Telangana, so it is drawn inside Andhra Pradesh.")

x1, x2 = st.columns(2)
with x1, shell.card("m5", "Nutrient Composition", "choose a nutrient · top foods + selected food"):
    nut = st.selectbox("Nutrient", MACROS + MICROS, key="nutsel")
    shell.plot(ch.nutrient_top(d, nut, food, 12, T, 480), "m5")
with x2, shell.card("m6", "Calories vs Protein", "point size = fiber · ★ selected food"):
    shell.plot(ch.scatter(d, r, T, 535), "m6")

with shell.card("m7", "Cancer Classification", "Cancer Risk Classification × Cancer Patient Support Category"):
    c = d.groupby(["Cancer_Patient_Support_Category", "Risk Group"]).size().reset_index(name="Foods")
    import plotly.express as px
    f = px.bar(c, x="Foods", y="Cancer_Patient_Support_Category", color="Risk Group", orientation="h", text="Foods", color_discrete_sequence=T["palette"])
    f.update_yaxes(title="", tickfont_size=14)
    shell.plot(ch.layout(f, T, 460), "m7")
st.caption("Dataset classifications – not medical advice.")

n = st.slider("Foods shown in production comparisons", 5, 30, 12, key="topn")
x1, x2 = st.columns(2)
with x1, shell.card("m8", "Global Production", "tonnes · log scale · selected food in red"):
    shell.plot(ch.prod_compare(d, GLOB, food, n, T, 420), "m8")
with x2, shell.card("m9", "Indian Production", "tonnes · log scale · selected food in red"):
    shell.plot(ch.prod_compare(d, IND, food, n, T, 420), "m9")

with shell.card("explorer", "API Fused Dataset Explorer", "all columns · search · sort · filters above also apply"):
    q = st.text_input("Search food or any column", key="search", placeholder="food, Hindi/Marathi name, country, state, classification…")
    t = filter_df(d, text=q)
    st.caption(f"{len(t):,} rows × {export_view(t).shape[1]} columns")
    st.dataframe(export_view(t), height=520, hide_index=True, **shell.stretch(),
                 column_config={"Image URL": st.column_config.LinkColumn("Image URL", display_text="open")})
    e1, e2, _ = st.columns([1, 1, 4])
    e1.download_button("⬇ Download CSV", to_csv_bytes(t), "fused_dataset_filtered.csv", "text/csv", key="dl_csv", **shell.stretch())
    e2.download_button("⬇ Download Excel", to_excel_bytes(t), "fused_dataset_filtered.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_xlsx", **shell.stretch())
