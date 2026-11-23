"""Page 6 · Statistical Analysis & Data Explorer"""
import streamlit as st
from modules import pagecharts as pc, shell, stats
from modules.data import NUTR, export_view, filter_df, to_csv_bytes, to_excel_bytes

ctx = shell.setup()
T, d, q = ctx.T, ctx.d, ctx.q
a, b = st.columns(2)
with a, shell.card("s1", "Nutrient Correlation Heatmap"):
    shell.plot(pc.corr_heat(d, T, 460), "s1")
with b, shell.card("s2", "Nutritional Distribution", "standardised (z-score) box plot"):
    shell.plot(pc.box_z(d, T, 460), "s2")
with shell.card("s3", "Missing Values & Data Quality", "missing cells per column"):
    m = stats.missing_table(d)
    shell.plot(pc.missing_bar(m[m["Missing"] > 0], T, 320), "s3")
tabs = st.tabs(["Descriptive statistics", "Dataset summary", "Complete dataset", "Duplicate records", "Outliers", "Validation report", "Export"])
with tabs[0]: st.dataframe(stats.describe_table(d), hide_index=True, **shell.stretch())
with tabs[1]:
    st.dataframe(d.drop(columns=["NOVA Group", "Risk Group"]).dtypes.astype(str).rename("Type").reset_index().rename(columns={"index": "Column"}), hide_index=True, **shell.stretch())
with tabs[2]:
    text = st.text_input("Search any column", key="p6_search")
    t = filter_df(d, text=text); st.caption(f"{len(t):,} rows × {export_view(t).shape[1]} columns")
    st.dataframe(export_view(t), height=520, hide_index=True, **shell.stretch(), column_config={"Image URL": st.column_config.LinkColumn("Image URL", display_text="open")})
with tabs[3]:
    full, names = stats.duplicates(d)
    c1, c2 = st.columns(2); c1.metric("Fully duplicated rows", len(full)); c2.metric("Rows sharing a Food Name", len(names))
    if len(names): st.dataframe(names, hide_index=True, **shell.stretch())
    else: st.success("No duplicate records in the current filter.")
with tabs[4]:
    z = st.slider("|z| threshold", 2.0, 6.0, 3.0, .5, key="zthr"); st.dataframe(stats.outliers(d, z), hide_index=True, **shell.stretch())
with tabs[5]:
    st.dataframe(stats.quality_report(q, len(d)), hide_index=True, **shell.stretch()); st.dataframe(stats.missing_table(d), hide_index=True, **shell.stretch())
with tabs[6]:
    c1, c2, c3 = st.columns(3)
    c1.download_button("⬇ CSV", to_csv_bytes(d), "fused_dataset_filtered.csv", "text/csv", key="p6c", **shell.stretch())
    c2.download_button("⬇ Excel", to_excel_bytes(d), "fused_dataset_filtered.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="p6x", **shell.stretch())
    c3.download_button("⬇ Statistics CSV", stats.describe_table(d).to_csv(index=False).encode(), "descriptive_statistics.csv", "text/csv", key="p6d", **shell.stretch())
