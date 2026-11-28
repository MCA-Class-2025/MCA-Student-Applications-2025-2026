import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd
import streamlit as st
from modules.dashboard_layout import page_setup, card, show, explain
from modules.calculations import unit_subset, available_units
from modules import chart_visualization as cv, map_visualization as mv
from modules import spatial_statistics as ss
from config.settings import DEFAULT_UNIT

ctx = page_setup(5)
df, th = ctx["dff"], ctx["th"]
units = available_units(df)
with st.container(border=True, key="card_params6"):
    p = st.columns(4)
    u = p[0].selectbox("Measurement unit", units, index=units.index(DEFAULT_UNIT) if DEFAULT_UNIT in units else 0, key="s_unit")
    cell = p[1].select_slider("Grid cell size (°)", [1, 2, 3, 5], value=2, key="s_cell")
    k = p[2].slider("Spatial weights: k nearest neighbours", 4, 16, 8, key="s_k")
    perms = p[3].select_slider("Permutations", [199, 499, 999], value=499, key="s_perm")

d = unit_subset(df, u)
cells = ss.cell_table(d, float(cell))

@st.cache_data(show_spinner="Running spatial statistics…")
def _run(cells, k, perms):
    return ss.global_moran(cells, k, perms), ss.local_moran(cells, k, min(perms, 499)), ss.getis_ord(cells, k)

gm, lm, gi = _run(cells, k, perms)
st.info(f"{len(d):,} records of {u} → {len(cells):,} grid cells.")

tabs = st.tabs(["Global Moran's I", "LISA", "Getis-Ord Gi*", "Nearest neighbour", "Std. deviational ellipse"])
with tabs[0]:
    if not gm["ok"]:
        st.warning(gm["reason"])
    else:
        a, b = st.columns([1, 2])
        with a:
            with card("Result"):
                pv = f"< {1 / (gm['perms'] + 1):.3f}" if gm["p"] <= 1 / (gm["perms"] + 1) + 1e-12 else f"{gm['p']:.4f}"
                st.table(pd.DataFrame({"Statistic": ["Moran's I", "Expected I", "z-score (permutation)", "p-value", "Cells (n)", "Neighbours (k)", "Permutations"],
                                       "Value": [f"{gm['I']:.4f}", f"{gm['E_I']:.4f}", f"{gm['z']:.2f}", pv, str(gm["n"]), str(gm["k"]), str(gm["perms"])]}))
                sig = gm["p"] < 0.05
                st.write(f"**Interpretation:** {'Significant' if sig else 'No significant'} spatial autocorrelation "
                         f"({'positive: similar values cluster' if gm['I'] > 0 else 'negative: dissimilar values neighbour each other'}) at the 5% level." if sig
                         else "**Interpretation:** no significant spatial autocorrelation at the 5% level.")
        with b:
            with card("Moran scatter plot"):
                show(cv.moran_scatter(gm["zval"], np.asarray(gm["lag"])), "s_ms")
with tabs[1]:
    if not lm["ok"]:
        st.warning(lm["reason"])
    else:
        lc = lm["cells"]
        colors = {"High-High": "#D62728", "Low-Low": "#1F77B4", "High-Low": "#FF9896", "Low-High": "#9EC5E8", "Not significant": "#999999"}
        a, b = st.columns([3, 1])
        with a:
            with card("Local Moran's I (LISA) cluster map", "p < 0.05 (pseudo p-value, one-sided per sign)"):
                show(mv.category_map(lc, "cluster", colors, height=420, size=7), "s_lisa")
        with b:
            with card("Counts"):
                st.table(lc.cluster.value_counts().rename("cells"))
            st.caption("No multiple-testing correction is applied to LISA; treat isolated significant cells cautiously.")
with tabs[2]:
    if not gi["ok"]:
        st.warning(gi["reason"])
    else:
        gc = gi["cells"]
        a, b = st.columns([3, 1])
        with a:
            with card("Getis-Ord Gi* hotspot / coldspot map", "FDR-adjusted, 95% confidence"):
                show(mv.category_map(gc, "class", {"Hotspot": "#D62728", "Coldspot": "#1F77B4", "Not significant": "#999999"}, height=420, size=7), "s_gi")
        with b:
            with card("Counts"):
                st.table(gc["class"].value_counts().rename("cells (FDR)"))
                st.table(gc["class_raw"].value_counts().rename("cells (unadjusted)"))
with tabs[3]:
    nn = ss.nearest_neighbour(d)
    if not nn["ok"]:
        st.warning(nn["reason"])
    else:
        a, b = st.columns([1, 2])
        with a:
            with card("Clark-Evans result (unique locations)"):
                st.table(pd.DataFrame({"Statistic": ["Locations", "Mean NN distance (km)", "Median NN distance (km)", "Expected (random) km", "NN index R", "z-score", "p-value", "Study area (km²)"],
                                       "Value": [f"{nn['n']:,}", f"{nn['mean_nn_km']:.1f}", f"{nn['median_nn_km']:.1f}", f"{nn['expected_km']:.1f}",
                                                 f"{nn['R']:.3f}", f"{nn['z']:.1f}", "< 0.001" if nn["p"] < 0.001 else f"{nn['p']:.3f}", f"{nn['area_km2']:,.0f}"]}))
                st.write("**Interpretation:** R < 1 means sampling locations are more clustered than random." if nn["R"] < 1 else "**Interpretation:** R ≥ 1: dispersed or random.")
                st.caption("Caution: R depends on the study-area definition (convex hull of the sites). Sampling sites are chosen by researchers, so clustering reflects survey design, not pollution.")
        with b:
            with card("Nearest-neighbour distance distribution"):
                show(cv.hist(pd.DataFrame({"km": nn["nn"]}), "km", nbins=50, height=330, xlabel="Distance to nearest location (km)"), "s_nn")
with tabs[4]:
    e = ss.std_ellipse(d)
    if not e["ok"]:
        st.warning(e["reason"])
    else:
        a, b = st.columns([1, 3])
        with a:
            with card("Ellipse parameters"):
                st.table(pd.DataFrame({"Parameter": ["Mean centre (lat, lon)", "Major semi-axis (km)", "Minor semi-axis (km)", "Axis ratio", "Rotation (° from north)"],
                                       "Value": [f"{e['centre_lat']:.2f}, {e['centre_lon']:.2f}", f"{e['major_km']:,.0f}", f"{e['minor_km']:,.0f}", f"{e['ratio']:.2f}", f"{e['rotation_deg']:.0f}"]}))
                st.caption("Computed in a Lambert azimuthal equal-area projection centred on the data. For worldwide data the ellipse is a rough summary of directional spread.")
        with b:
            with card("Standard deviational ellipse (1 SD)"):
                show(mv.add_ellipse(mv.points_map(d, height=420, zoom=False), e), "s_sde")

with st.expander("Assumptions and limitations"):
    st.markdown("""
- Results describe **where measurements were taken** and are affected by sampling design, survey era, method and mesh size; they do not describe the whole ocean.
- Measurements from different units are never combined; change the unit above to re-run the tests.
- Cells are aggregated to reduce pseudo-replication; results depend on cell size and *k*.
- Permutation p-values cannot go below 1/(permutations+1).
- Gi* uses an analytic z-score; with strongly skewed data treat p-values as approximate (FDR shown for multiplicity).
- An analysis is skipped with a message when there are fewer than 30 valid grid cells.""")

explain("Tests whether high or low plastic amounts sit next to each other more than chance would predict (clusters), or are spread randomly.",
        "Variable: mean log10(measurement) per grid cell. Weights: k-nearest neighbours. Moran / LISA use permutation tests; Gi* uses z-scores with FDR correction.")
