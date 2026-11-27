"""Page 4 · Cancer-Related Classification Analysis"""
import pandas as pd
import streamlit as st
from modules import charts as ch, pagecharts as pc, shell
from modules.data import MACROS, RISK_TXT, SUPPORT

ctx = shell.setup()
T, d = ctx.T, ctx.d
st.info("These are the dataset's own classifications. They are not medically verified cancer prevention or treatment recommendations.")
x1, x2 = st.columns(2)
with x1, shell.card("c1", "Cancer Risk Classification", "top 15 categories (full dataset text)"):
    shell.plot(ch.top_names(d[RISK_TXT].value_counts(), T, 520, 15), "c1")
with x2, shell.card("c2", "Cancer Patient Support Category", "number of foods"):
    shell.plot(ch.donut(d, SUPPORT, {}, T, 520), "c2")
by = st.radio("Nutrition by", ["Risk Group", SUPPORT], horizontal=True, key="c_by")
with shell.card("c3", "Nutritional Composition Across Classifications", f"mean per 100 g by {by}"):
    shell.plot(pc.compare(d, by, MACROS[1:], False, T, 440), "c3")
with shell.card("c4", "Category-wise Food List"):
    a, b = st.columns(2)
    sc = a.selectbox("Support category", ["All"] + sorted(d[SUPPORT].unique()), key="c_sc")
    rg = b.selectbox("Risk group", ["All"] + sorted(d["Risk Group"].unique()), key="c_rg")
    t = d[(d[SUPPORT] == sc) | (sc == "All")]; t = t[(t["Risk Group"] == rg) | (rg == "All")]
    st.caption(f"{len(t):,} foods")
    st.dataframe(t[["Food Name", "Hindi Name", "Marathi Name", RISK_TXT, SUPPORT, "Calories (kcal)", "Protein (g)", "Nutri-Score Grade"]], height=420, hide_index=True, **shell.stretch())
