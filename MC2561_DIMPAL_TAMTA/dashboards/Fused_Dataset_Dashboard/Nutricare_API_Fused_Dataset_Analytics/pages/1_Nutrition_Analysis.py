"""Page 2 · Nutrition Analysis"""
import streamlit as st
from modules import charts as ch, pagecharts as pc, shell, stats
from modules.data import MACROS, MICROS, NUTR, SUPPORT, export_view, filter_df

ctx = shell.setup()
T, d = ctx.T, ctx.d
c1, c2 = st.columns([1, 2])
with c1: r = shell.food_picker(d, "food_p2", "Selected food")
cmp_ = c2.multiselect("Compare with (up to 4 foods)", sorted(d["Food Name"]), max_selections=4, key="cmp")
by = st.selectbox("Group nutrient charts by", ["Nutri-Score Grade", "NOVA Group", "Risk Group", SUPPORT], key="p2_by")
x1, x2 = st.columns(2)
with x1, shell.card("n1", "Macronutrient Comparison", f"mean per 100 g by {by} · Protein, Carbs, Fat, Fiber"):
    shell.plot(pc.compare(d, by, MACROS[1:], False, T, 420), "n1")
with x2, shell.card("n2", "Micronutrient Comparison", f"mean per 100 g by {by} · log scale"):
    shell.plot(pc.compare(d, by, MICROS, True, T, 420), "n2")
with shell.card("n3", "Calories vs Protein", "point size = fiber · stars = selected and comparison foods"):
    shell.plot(ch.scatter(d, r, T, 520, cmp_), "n3")
if cmp_:
    with shell.card("n4", "Food Comparison", "per 100 g"):
        st.dataframe(d[d["Food Name"].isin([r["Food Name"]] + cmp_)][["Food Name"] + NUTR].set_index("Food Name").T, **shell.stretch())
with shell.card("n5", "Nutritional Statistics & Searchable Food Table"):
    nut = st.multiselect("Nutrients to describe", NUTR, default=MACROS, key="p2_nut")
    if nut: st.dataframe(d[nut].describe().T.round(2), **shell.stretch())
    q = st.text_input("Search food", key="p2_search")
    st.dataframe(filter_df(d, text=q)[["Food Name", "Hindi Name", "Marathi Name"] + NUTR + ["Nutri-Score Grade", "nova_group"]], height=420, hide_index=True, **shell.stretch())
