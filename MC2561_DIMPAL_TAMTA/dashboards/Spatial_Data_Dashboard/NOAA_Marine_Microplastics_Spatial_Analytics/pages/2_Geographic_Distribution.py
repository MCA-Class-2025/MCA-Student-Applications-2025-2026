import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st
from modules.dashboard_layout import page_setup, card, show, explain
from modules.calculations import lat_zone, counts
from modules import chart_visualization as cv, map_visualization as mv
from modules.spatial_analysis import grid_cells
from modules.export import chart_downloads
from config.settings import NOT_RECORDED

ctx = page_setup(1)
df, F = ctx["dff"], ctx["F"]

with card("1 · Sampling point map", "Every dot = one record, coloured by ocean · hover for details · scroll to zoom"):
    fig = mv.points_map(df, color_col="ocean", height=520, zoom=bool(F["country"]))
    show(fig, "g_points")
    n_no = int((df.ocean == "Not recorded").sum())
    if n_no:
        st.caption(f"{n_no:,} records with no ocean listed are not drawn on this map.")
    chart_downloads(st, fig, "sampling_points_map", "g1")

with card("2 · Country explorer map", "Pick a country (and optionally an ocean) to zoom in · dot colour = marine setting (beach, water, sediment…)"):
    cdf = df[df.country != NOT_RECORDED]
    if cdf.empty:
        st.info("No country information in the current selection.")
    else:
        s1, s2 = st.columns([2, 2])
        names = counts(cdf, "country")["country"].tolist()
        pick = s1.selectbox("Country", names, key="g_country")
        sub = cdf[cdf.country == pick]
        oc = s2.multiselect("Ocean", sorted(sub.ocean.unique()), default=[], key=f"g_oc_{pick}", placeholder="All oceans")
        if oc:
            sub = sub[sub.ocean.isin(oc)]
        st.caption(f"{len(sub):,} records in {pick}")
        if sub.empty:
            st.info("No records for this choice.")
        else:
            show(mv.country_map(sub, height=480), "g_country_map")

a, b = st.columns(2)
with a:
    with card("3 · Sampling density grid", "Number of records in each grid square · darker = more samples"):
        cell = st.select_slider("Cell size (°)", [0.5, 1, 2, 5, 10], value=2, key="g_cell")
        show(mv.cells_map(grid_cells(df, float(cell)), "n", "Records", height=340, size=6 if cell <= 2 else 9), "g_grid")
with b:
    with card("4 · 3D sampling-density surface", "Height = how many samples per 10° block (log scale) · drag to rotate, scroll to zoom"):
        show(mv.surface3d(df, height=400), "g_3d")

a, b = st.columns(2)
with a:
    with card("5 · Latitude distribution", "How samples spread north–south"):
        show(cv.hist(df, "lat", nbins=45, height=300, xlabel="Latitude (°)"), "g_lat")
with b:
    with card("6 · Sampling reach arc map", "Arcs link the busiest country (star) to the next 14 · thicker arc = more records"):
        arc = mv.arc_map(df, height=330)
        if arc is None:
            st.info("Need at least two countries in the selection.")
        else:
            show(arc, "g_arc")

explain("This page shows WHERE the samples were taken. The first map colours every dot by ocean; the second map lets you pick one country and zoom in.",
        f"{len(df):,} records in the current selection. Use Advanced filters for latitude / longitude ranges.")
