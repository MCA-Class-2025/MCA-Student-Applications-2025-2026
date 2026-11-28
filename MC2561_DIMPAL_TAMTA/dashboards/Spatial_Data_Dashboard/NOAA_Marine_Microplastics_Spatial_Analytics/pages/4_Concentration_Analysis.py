import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st
from modules.dashboard_layout import page_setup, card, show, explain
from modules.calculations import unit_subset, available_units, group_stats
from modules import chart_visualization as cv, map_visualization as mv
from modules.spatial_analysis import grid_cells
from config.settings import DEFAULT_UNIT, CLASS_ORDER

ctx = page_setup(3)
df = ctx["dff"]
units = available_units(df)
if not units:
    st.info("No measurements in the current selection.")
    st.stop()
u = st.radio("Measurement unit (each unit is analysed separately - units are not comparable)", units,
             index=units.index(DEFAULT_UNIT) if DEFAULT_UNIT in units else 0, horizontal=True, key="c_unit")
d = unit_subset(df, u)
pos = d[d.value > 0]
c = st.columns(5)
for col, (lab, val) in zip(c, [("Records", f"{len(d):,}"), ("Median", f"{d.value.median():.4g}"),
                               ("Mean", f"{d.value.mean():.4g}"), ("Maximum", f"{d.value.max():.4g}"),
                               ("Zero values", f"{int((d.value == 0).sum()):,}")]):
    col.metric(lab, val)

if len(pos) < 10:
    st.info("Fewer than 10 positive values - charts cannot be drawn.")
    st.stop()

a, b = st.columns(2)
with a:
    with card("1 · How much plastic was found", "Number of records at each concentration level (log10 scale)"):
        show(cv.hist(pos, "log_value", nbins=50, height=330, xlabel=f"log10({u})"), "c_hist")
with b:
    with card("2 · Contamination classes", "How many records fall in each class, Very Low to Very High"):
        cls = d.conc_class.value_counts().reindex(CLASS_ORDER).dropna().rename_axis("class").reset_index(name="records")
        cls["class"] = cls["class"].astype(str)
        show(cv.bar(cls, "records", "class", horizontal=False, height=330), "c_class")

a, b = st.columns(2)
with a:
    with card("3 · Plastic by marine setting", "Box = middle 50% of values, line = median (log scale)"):
        show(cv.box(pos, "setting", "value", height=350, log_y=True), "c_box")
with b:
    with card("4 · Median by sampling method", "Top 10 methods by record count · median is robust to extreme values"):
        gs = group_stats(pos, "method", 10)
        show(cv.bar(gs, "median", "method", height=350), "c_meth")

a, b = st.columns([2, 1])
with a:
    with card("5 · Concentration map", f"Each dot is a 2° grid cell · bigger and darker = higher average log10 {u}"):
        cells = grid_cells(pos, 2.0, "log_value")
        if cells.empty:
            st.info("No positive values to map.")
        else:
            cells["size_v"] = cells["log_value_mean"] - cells["log_value_mean"].min() + 0.1
            show(mv.bubble_map(cells, "size_v", color_col="log_value_mean", label="mean log10", height=430), "c_map")
with b:
    with card("6 · Median by marine setting", "Typical amount found in each setting"):
        gs = group_stats(pos, "setting", 6)
        show(cv.bar(gs, "median", "setting", height=430), "c_set")

explain("How much plastic was actually found. A few places have extremely high counts, so we use a log scale: each step to the right is 10 times more plastic.",
        f"Unit: {u}. Distributions use log10 of positive values because the data span many orders of magnitude. Median is more reliable than mean here.")
