"""Page 3 · Food Quality & Processing Analysis"""
import pandas as pd
import streamlit as st
from modules import charts as ch, pagecharts as pc, shell
from modules.data import NUTR

ctx = shell.setup()
T, d = ctx.T, ctx.d
x1, x2 = st.columns(2)
with x1, shell.card("q1", "Nutri-Score Distribution", "pie · grades A–E (and '-' = not scored)"):
    shell.plot(ch.donut(d, "Nutri-Score Grade", ch.NUTRI, T, 420), "q1")
with x2, shell.card("q2", "NOVA Group Distribution", "treemap · groups 1–4"):
    shell.plot(ch.treemap(d, T, 420), "q2")
with shell.card("q3", "Nutri-Score vs NOVA Group", "heatmap · number of foods"):
    shell.plot(pc.nutri_nova_heat(d, T, 440), "q3")
with shell.card("q4", "Food Quality Comparison Table", "counts and % of filtered foods"):
    x = pd.crosstab(d["Nutri-Score Grade"], d["NOVA Group"], margins=True, margins_name="Total")
    st.dataframe(x, **shell.stretch())
    st.dataframe((pd.crosstab(d["Nutri-Score Grade"], d["NOVA Group"], normalize="all") * 100).round(2).astype(str) + " %", **shell.stretch())
    g = d.groupby("Nutri-Score Grade")[["Calories (kcal)", "Protein (g)", "Fiber (g)", "Sodium (mg)"]].mean().round(2)
    g["Foods"] = d["Nutri-Score Grade"].value_counts(); g["% of foods"] = (g["Foods"] / len(d) * 100).round(1)
    st.markdown("**Average nutrients by Nutri-Score**"); st.dataframe(g, **shell.stretch())
