import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import streamlit as st
from modules.dashboard_layout import page_setup, card, show, explain
from modules.calculations import unit_subset, available_units
from modules import chart_visualization as cv, map_visualization as mv
from modules import spatial_analysis as sa, spatial_statistics as ss
from config.settings import DEFAULT_UNIT

ctx = page_setup(4)
df = ctx["dff"]

with st.container(border=True, key="card_params5"):
    p = st.columns(5)
    units = available_units(df)
    u = p[0].selectbox("Measurement unit", units, index=units.index(DEFAULT_UNIT) if DEFAULT_UNIT in units else 0, key="h_unit")
    bw = p[1].slider("KDE bandwidth (km)", 50, 1000, 200, 50, key="h_bw")
    eps = p[2].slider("DBSCAN radius (km)", 10, 500, 100, 10, key="h_eps")
    ms = p[3].slider("DBSCAN min. samples", 3, 50, 10, key="h_ms")
    pct = p[4].slider("Hotspot threshold (percentile of cell mean)", 70, 99, 90, key="h_pct")

@st.cache_data(show_spinner="Computing density…")
def _kde(d, bw, w=False):
    return sa.kde_grid(d, bw, weights=(d.log_value - d.log_value.min() + 0.1).values if w else None)

@st.cache_data(show_spinner="Clustering…")
def _db(d, eps, ms):
    return sa.dbscan_clusters(d, eps, ms)

a, b = st.columns(2)
with a:
    with card("1 · Sampling-density KDE map", "Darker = more samples taken nearby (effort, not contamination)"):
        k = _kde(df, bw)
        if k is None:
            st.info("Need at least 10 records.")
        else:
            show(mv.cells_map(k, "density", "Relative density", height=360, size=6), "h_kde")
with b:
    with card("2 · DBSCAN geographic clusters", "Groups of samples that are close together; each cluster has its own colour, grey = isolated points"):
        db = _db(df, eps, ms)
        if db is None or (db.cluster >= 0).sum() == 0:
            st.info("No clusters found with these parameters - increase the radius or lower the minimum samples.")
        else:
            db["cl"] = np.where(db.cluster < 0, "Noise", "Cluster " + db.cluster.astype(str))
            top = db[db.cluster >= 0].cluster.value_counts().head(8).index
            db["cl"] = np.where(db.cluster.isin(top), db.cl, "Noise")
            th = ctx["th"]
            colors = {f"Cluster {c}": th["palette"][i % 8] for i, c in enumerate(top)}
            colors["Noise"] = "#999999"
            show(mv.category_map(db, "cl", colors, height=360, size=5), "h_db")
            st.caption(f"{db.cluster.nunique() - (1 if (db.cluster < 0).any() else 0)} clusters; map shows the 8 largest. Noise records: {(db.cluster < 0).sum():,}.")

d = unit_subset(df, u)
cells = ss.cell_table(d, 2.0)
with card("3 · Potential hotspot map (descriptive)", f"2° cells with mean log10 {u} above the {pct}th percentile"):
        if len(cells) < 10:
            st.info("Too few grid cells for this unit.")
        else:
            thr = np.percentile(cells.x, pct)
            cells["cls"] = np.where(cells.x >= thr, "Potential hotspot", "Non-hotspot")
            show(mv.category_map(cells, "cls", {"Potential hotspot": ctx["th"]["palette"][6], "Non-hotspot": "#999999"}, height=360, size=7), "h_hot")
            st.caption("Descriptive threshold only - see the Gi* map below for statistical support.")

with card("4 · Statistically supported hotspots / coldspots (Getis-Ord Gi*)", "Red = significantly high neighbourhood, blue = significantly low, grey = no clear pattern (95% confidence)"):
    g = ss.getis_ord(cells, 8)
    if not g["ok"]:
        st.info(g["reason"])
    else:
        gc = g["cells"]
        show(mv.category_map(gc, "class", {"Hotspot": "#D62728", "Coldspot": "#1F77B4", "Not significant": "#999999"}, height=380, size=7), "h_gi")

with card("5 · Size of the biggest clusters", "Number of samples in each of the 10 largest DBSCAN clusters"):
    if True:
        if db is None or (db.cluster >= 0).sum() == 0:
            st.info("No clusters to compare.")
        else:
            cl = db[db.cluster >= 0]
            top = cl.cluster.value_counts().head(10).index
            t = cl[cl.cluster.isin(top)].groupby("cluster").agg(samples=("lat", "size")).reset_index()
            t["cluster"] = "Cluster " + t.cluster.astype(str)
            show(cv.bar(t, "samples", "cluster", height=300), "h_cc")

explain("Hotspot = a place where many samples are taken (density) or where the plastic amount is unusually high. Use the sliders to change how strict the search is.",
        "Sampling effort (where people looked) and contamination (what they found) are analysed separately. Many records in a place do NOT make it a pollution hotspot.")
