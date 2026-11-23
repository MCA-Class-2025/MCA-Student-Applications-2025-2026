import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st
from modules.dashboard_layout import page_setup, card, kpi, show, explain
from modules.calculations import kpis, counts, unit_subset, available_units
from modules import chart_visualization as cv, map_visualization as mv
from config.settings import NOT_RECORDED, DEFAULT_UNIT

ctx = page_setup(0)
df, dfnc, F = ctx["dff"], ctx["dfnc"], ctx["F"]
k = kpis(df)

c = st.columns(4)
kpi(c[0], "Microplastic Samples", f"{k['samples']:,}", "valid sampling records")
kpi(c[1], "Countries Surveyed", f"{k['countries']:,}", f"{k['countries_missing_pct']}% of records have no country")
kpi(c[2], "Oceans Covered", f"{k['oceans']:,}", "oceans with recorded samples")
kpi(c[3], "Highest Sampling Coverage", k["top_ocean"], f"{k['top_ocean_pct']}% of all samples")

# ---------------- row 1: map | donut + bar
m, t = st.columns([3, 2])
with m:
    with card("Global sampling map", "Each dot is one sample, coloured by ocean · click a country to filter · hover a dot for details"):
        proj = st.radio("Map view", ["Flat map", "Globe"], horizontal=True, key="ov_proj", label_visibility="collapsed")
        zoom = bool(F["country"])
        ver = st.session_state.get("map_ver", 0)
        ev = show(mv.overview_map(df, dfnc, zoom=zoom, height=519,
                                  projection="orthographic" if proj == "Globe" else "natural earth"), f"ovmap_{ver}", select=True)
        pts = []
        try:
            pts = ev["selection"]["points"] if ev else []
        except Exception:
            pass
        sig = str(pts)
        if pts and st.session_state.get("sel_sig") != sig:
            st.session_state["sel_sig"] = sig
            p = pts[0]
            cd = p.get("customdata")
            if p.get("curve_number") == 0:
                name = cd[0] if isinstance(cd, (list, tuple)) else (cd or p.get("location"))
                if name:
                    F["country"] = [name]
                    st.rerun()
            elif cd:
                st.session_state["sel_point"] = cd[0]
        n_no = int((df.ocean == NOT_RECORDED).sum())
        if n_no:
            st.caption(f"{n_no:,} records with no ocean listed are not drawn on this map.")
        sp = st.session_state.get("sel_point")
        if sp is not None:
            rec = ctx["df"][ctx["df"].id == sp]
            if len(rec):
                r = rec.iloc[0].dropna()
                st.caption(f"Selected sample **{sp}**: " + " · ".join(f"{a}: {r[a]}" for a in
                           ["date", "country", "ocean", "region", "setting", "method", "value", "unit", "conc_class", "reference"] if a in r.index))
with t:
    with card("Share of samples by ocean", "How the records split between oceans"):
        show(cv.donut(df[df.ocean != NOT_RECORDED], "ocean", height=240), "ov_donut")
    with card("Top 8 countries", "Countries with the most sampling records"):
        cc = counts(df, "country", exclude_nr=True, top=8)
        if cc.empty:
            st.info("No country information in the current selection.")
        else:
            show(cv.bar(cc, "samples", "country", height=270), "ov_country")

# ---------------- row 2: treemap | donut (concentration class)
a, b = st.columns([3, 2])
with a:
    with card("Where samples come from", "Ocean → country · bigger tile = more records · small countries are grouped as 'Other'"):
        tm = df[(df.country != NOT_RECORDED) & (df.ocean != NOT_RECORDED)]
        if tm.empty:
            st.info("No country information in the current selection.")
        else:
            show(cv.treemap(tm, ["ocean", "country"], height=300, top_children=5), "ov_tree")
with b:
    with card("How contaminated are the samples?", "Share of records in each concentration class (green = low, red = high)"):
        cl = df.dropna(subset=["conc_class"]).assign(conc_class=lambda d: d.conc_class.astype(str))
        if cl.empty:
            st.info("No concentration classes in the current selection.")
        else:
            show(cv.donut(cl, "conc_class", height=300), "ov_class")

# ---------------- row 3: time-series line | scatter
units = available_units(df)
a, b = st.columns(2)
with a:
    with card("Sampling over time", "Records collected each year, one line per ocean"):
        ts = df[(df.ocean != NOT_RECORDED)].dropna(subset=["year"]).assign(year=lambda d: d.year.astype(int))
        if ts.empty:
            st.info("No dated records in the current selection.")
        else:
            show(cv.line_ts(ts, "year", "ocean", height=330), "ov_line")
with b:
    with card("Plastic found vs latitude", "Each dot is one measurement (log scale) · coloured by ocean · one unit at a time"):
        if not units:
            st.info("No measurements in the current selection.")
        else:
            u = st.selectbox("Unit", units, index=units.index(DEFAULT_UNIT) if DEFAULT_UNIT in units else 0,
                             key="ov_unit", label_visibility="collapsed")
            du = unit_subset(df, u)
            du = du[(du.log_value.notna()) & (du.ocean != NOT_RECORDED)]
            if len(du) < 5:
                st.info("Too few positive values for this unit.")
            else:
                du = du.sample(min(len(du), 3000), random_state=1)
                f = cv.scatter(du, "lat", "log_value", height=285, color="ocean")
                f.update_xaxes(title="Latitude (°)")
                f.update_yaxes(title=f"log10({u})")
                show(f, "ov_scatter")

# ---------------- heat map
with card("Sampling timeline heat map", "Number of records per ocean and decade · brighter = more samples"):
    hm = df[(df.ocean != NOT_RECORDED)].dropna(subset=["year"]).assign(decade=lambda d: (d.year // 10 * 10).astype(int).astype(str) + "s")
    if hm.empty:
        st.info("No dated records in the current selection.")
    else:
        show(cv.heatmap(hm, "ocean", "decade", height=270, col_label="Decade"), "ov_heat")
st.caption("Records without a country/ocean/region value are left out of those specific charts only.")

explain("Each dot is one place where scientists collected water, sand or sediment and counted microplastics. "
        "Dot colour = ocean. Click a country on the map to filter the whole dashboard.",
        "Counts show sampling EFFORT (where people looked), not pollution level. Units are never mixed.")
