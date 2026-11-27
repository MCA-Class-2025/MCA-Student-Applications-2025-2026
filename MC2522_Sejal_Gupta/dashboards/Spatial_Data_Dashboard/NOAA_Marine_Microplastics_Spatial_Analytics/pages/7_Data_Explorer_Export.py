import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd
import streamlit as st
from modules.dashboard_layout import page_setup, card, show, explain
from modules import map_visualization as mv
from modules.data_validation import missing_table
from modules.export import csv_bytes, chart_downloads

ctx = page_setup(6)
df, full, q = ctx["dff"], ctx["df"], ctx["quality"]

HIDE = ["log_value", "loc_key", "duplicate_flag", "doi", "organization"]
cols_all = [c for c in df.columns if c not in HIDE]
default_cols = ["id", "date", "lat", "lon", "ocean", "region", "country", "setting", "method", "value", "unit", "conc_class", "reference"]

with st.container(border=True, key="card_params7"):
    a = st.columns([2, 3, 1.3, 1.3])
    qtext = a[0].text_input("Search text (any text column)", key="x_search")
    cols = a[1].multiselect("Columns", cols_all, default=[c for c in default_cols if c in cols_all], key="x_cols")
    vmin = a[2].number_input("Min. measurement", value=0.0, key="x_vmin")
    vmax = a[3].number_input("Max. measurement (0 = no limit)", value=0.0, key="x_vmax")

d = df
if qtext:
    txt = d.select_dtypes(include=["object", "string", "category"]).astype(str)
    m = txt.apply(lambda s: s.str.contains(qtext, case=False, na=False, regex=False)).any(axis=1)
    d = d[m]
if vmin > 0:
    d = d[d.value >= vmin]
if vmax > 0:
    d = d[d.value <= vmax]
st.caption(f"{len(d):,} of {len(full):,} records match. Measurement limits apply to values of any unit - combine with the unit filter for meaningful ranges.")
if d.empty:
    st.warning("No records match.")
    st.stop()

tabs = st.tabs(["Table", "Record detail", "Map & charts", "Downloads", "Dataset information"])
with tabs[0]:
    st.dataframe(d[cols] if cols else d, height=480, use_container_width=True, hide_index=True)
with tabs[1]:
    ids = d.id.head(5000).tolist()
    sel = st.selectbox("Sample ID (first 5,000 matches)", ids, key="x_id")
    r = d[d.id == sel].iloc[0]
    st.dataframe(pd.DataFrame({"field": r.index, "value": r.astype(str).values}), height=460, hide_index=True, use_container_width=True)
    if pd.notna(r.get("doi")):
        st.markdown(f"Source: [{r['reference']}]({r['doi']})")
with tabs[2]:
    with card("Map of the selected records"):
        fig = mv.points_map(d, height=460, zoom=len(d) < len(full) and len(d) < 5000)
        show(fig, "x_map")
        chart_downloads(st, fig, "selected_records_map", "x")
with tabs[3]:
    c = st.columns(3)
    c[0].download_button("⬇ Filtered records (all columns)", csv_bytes(d), "filtered_records.csv", "text/csv")
    c[1].download_button("⬇ Selected columns only", csv_bytes(d[cols] if cols else d), "selected_columns.csv", "text/csv")
    c[2].download_button("⬇ Currently selected record (CSV)", csv_bytes(d[d.id == st.session_state.get("x_id", d.id.iloc[0])]), "selected_record.csv", "text/csv")
    st.caption("Chart exports (HTML / PNG) are under the map. PNG export needs the optional `kaleido` package.")
with tabs[4]:
    a, b = st.columns([1, 2])
    with a:
        st.metric("Records (cleaned)", f"{q['rows']:,}")
        st.metric("Unique coordinates", f"{q['unique_locations']:,}")
        st.metric("Exact duplicates (flagged)", f"{q['duplicate_records']:,}")
        st.metric("Invalid coordinates removed", f"{q['invalid_coordinates_removed']:,}")
        st.write("**Units:**", ", ".join(f"{k} ({v:,})" for k, v in q["units"].items()))
    with b:
        st.write("**Missing values per column (cleaned data)**")
        st.dataframe(missing_table(full), height=420, hide_index=True, use_container_width=True)

explain("Search, filter and download the raw records behind every chart.")
