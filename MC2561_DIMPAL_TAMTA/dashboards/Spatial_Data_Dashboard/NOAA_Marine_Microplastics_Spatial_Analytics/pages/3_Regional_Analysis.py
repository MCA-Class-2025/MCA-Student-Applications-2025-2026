import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st
from modules.dashboard_layout import page_setup, card, show, explain
from modules.calculations import counts, unit_subset, available_units
from modules import chart_visualization as cv, map_visualization as mv
from config.settings import NOT_RECORDED, DEFAULT_UNIT

ctx = page_setup(2)
df = ctx["dff"]
rec = df[df.region != NOT_RECORDED]
cty = df[df.country != NOT_RECORDED]

a, b = st.columns([3, 2])
with a:
    with card("1 · Country map", "Darker country = more sampling records (log scale)"):
        cc = counts(df, "country", exclude_nr=True)
        if cc.empty:
            st.info("No country information in the current selection.")
        else:
            show(mv.choropleth(cc, "records", height=400), "r_choro")
with b:
    with card("2 · Samples per ocean", "Each ocean has its own colour everywhere in the dashboard"):
        show(cv.bar(counts(df, "ocean", exclude_nr=True), "samples", "ocean", height=400), "r_ocean")

a, b = st.columns(2)
with a:
    with card("3 · Country ranking", "Top 15 countries by number of records"):
        if cty.empty:
            st.info("No country information.")
        else:
            show(cv.bar(counts(df, "country", exclude_nr=True, top=15), "samples", "country", height=420), "r_rank")
with b:
    with card("4 · Regions inside each ocean", "Ocean → region · bigger tile = more records"):
        rr = rec[rec.ocean != NOT_RECORDED]
        if rr.empty:
            st.info("No region information.")
        else:
            show(cv.treemap(rr, ["ocean", "region"], height=420, top_children=8), "r_tree")

units = available_units(df)
u = st.selectbox("Measurement unit for the next two charts (units are never mixed)", units,
                 index=units.index(DEFAULT_UNIT) if DEFAULT_UNIT in units else 0, key="r_unit")
du = unit_subset(rec, u)
a, b = st.columns(2)
with a:
    with card("5 · Amount of plastic by region", f"{u} · log scale · the box is the middle 50% of values, the line is the median"):
        if du.empty:
            st.info("No regional measurements for this unit.")
        else:
            top = du.region.value_counts().head(8).index
            show(cv.box(du[du.region.isin(top)], "region", "value", height=380, log_y=True), "r_box")
with b:
    with card("6 · Contamination levels by region", "Share of records in each class, from Very Low (green) to Very High (red)"):
        if rec.empty:
            st.info("No region information.")
        else:
            top = rec.region.value_counts().head(8).index
            show(cv.stacked_bar(rec[rec.region.isin(top)], "region", "conc_class", height=380, normalize=True), "r_stack")

explain("Compares oceans, countries and regions: who has the most samples, and how contaminated each region looks.",
        f"{len(df):,} records · {len(cty):,} with a country · {len(rec):,} with a region. Missing values are left out of that chart only.")
