import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st
from datetime import datetime
from modules.dashboard_layout import page_setup, card, kpi, explain
from modules.calculations import kpis, available_units
from modules.insights_generator import run_spatial, build_insights
from modules.report_generator import build_pdf, CHARTS
from modules.filters import describe
from config.settings import DEFAULT_UNIT, EXPORT_DIR

ctx = page_setup(7)
df, F, q, th = ctx["dff"], ctx["F"], ctx["quality"], ctx["th"]
units = available_units(df)

@st.cache_data(show_spinner="Computing spatial statistics for the insights…")
def _spatial(d, unit):
    return run_spatial(d, unit)

u = st.selectbox("Measurement unit used for concentration statistics & Moran / Gi*", units,
                 index=units.index(DEFAULT_UNIT) if DEFAULT_UNIT in units else 0, key="i_unit") if units else None
sp = _spatial(df, u) if u else None
k = kpis(df)
ins = build_insights(df, q, sp)

c = st.columns(4)
kpi(c[0], "Microplastic Samples", f"{k['samples']:,}")
kpi(c[1], "Countries Surveyed", k["countries"])
kpi(c[2], "Oceans Covered", k["oceans"])
kpi(c[3], "Highest Sampling Coverage", k["top_ocean"], f"{k['top_ocean_pct']}% of all samples")

left, right = st.columns([3, 1])
with left:
    for i, (sec, items) in enumerate(ins.items(), 1):
        with card(f"{i}. {sec}"):
            for s in items:
                st.markdown(f"- {s}")
with right:
    with card("PDF report"):
        picks = st.multiselect("Charts to include", list(CHARTS), default=list(CHARTS), key="i_charts")
        if st.button("Generate PDF Report", use_container_width=True):
            with st.spinner("Building PDF…"):
                note = "Statistics in this report were computed for the unit: " + u if u else ""
                st.session_state["pdf"] = build_pdf(df, k, ins, q, describe(F), th, [CHARTS[p] for p in picks], u or DEFAULT_UNIT, note)
                st.session_state["pdf_name"] = f"NOAA_Microplastics_Report_{datetime.now():%Y%m%d_%H%M}.pdf"
                try:
                    (EXPORT_DIR / "reports").mkdir(parents=True, exist_ok=True)
                    (EXPORT_DIR / "reports" / st.session_state["pdf_name"]).write_bytes(st.session_state["pdf"])
                except Exception:
                    pass
        if "pdf" in st.session_state:
            st.download_button("⬇ Download PDF", st.session_state["pdf"], st.session_state["pdf_name"], "application/pdf", use_container_width=True)
            st.caption("Report reflects the filters active when it was generated.")
