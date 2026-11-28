import streamlit as st
from modules import charts as ch, pagecharts as pc, shell, stats
from modules.data import METRICS, to_csv_bytes

ctx = shell.setup()
T, d = ctx.T, ctx.d
U = ctx.sel if len(ctx.sel) >= 2 else ctx.names_all
dU = ctx.subset(U)
cu = ch.color_map(U, T, ctx.names_all)
if dU.empty:
    st.warning("No records with the current filters.")
    st.stop()
st.markdown(f"<div class='hint'>Statistics for <b>{'selected commodities' if len(ctx.sel) >= 2 else 'all commodities'}</b> · {ctx.metric} · {ctx.rng} {ctx.cal}</div>", unsafe_allow_html=True)

t1, t2, t3, t4, t5 = st.tabs(["Descriptive statistics", "Correlation & distribution", "Outliers", "Data quality", "Data explorer & export"])
desc = stats.describe_table(dU, ctx.metric)

with t1:
    st.markdown("**Summary statistics by commodity** (prices in each commodity's own units)")
    st.dataframe(desc, hide_index=True, **shell.stretch(st.dataframe))
    st.caption("ret_* columns are daily % returns. cv_pct = std / mean. Skew and kurtosis describe distribution shape.")

with t2:
    x1, x2 = st.columns(2)
    with x1:
        with shell.card("p6a", "Price Correlation Heatmap", "levels, overlapping dates — trends can inflate this"):
            shell.plot(pc.corr_heatmap(dU.pivot_table(index="date", columns="name", values=METRICS[ctx.metric]), T, 420), "p6a")
    with x2:
        with shell.card("p6b", "Price Distribution", f"{ctx.metric} · box plot"):
            shell.plot(pc.box_price(dU, U, ctx.metric, T, cu, 420), "p6b")

with t3:
    z = st.slider("Flag daily returns with |z-score| above", 3.0, 8.0, 4.0, 0.5, key="p6_z")
    out = stats.outliers(dU, z)
    o1, o2 = st.columns([1, 1.3])
    with o1:
        with shell.card("p6c", "Flagged Observations by Commodity", f"|z| > {z}"):
            shell.plot(pc.outlier_bar(out, T, 360), "p6c")
    with o2:
        st.markdown(f"**{len(out):,} flagged daily returns** (largest first)")
        st.dataframe(out, hide_index=True, height=360, **shell.stretch(st.dataframe))
    st.caption("Outliers are flagged for investigation, not classified as errors — large moves are often real market events.")

with t4:
    st.markdown("**Validation checks (full dataset)**")
    st.dataframe(stats.validation_table(ctx.df, ctx.q), hide_index=True, **shell.stretch(st.dataframe))
    st.markdown("**Longest gaps between consecutive records (> 7 days)** — gaps are reported, not filled; not every calendar day is a trading day")
    st.dataframe(stats.gaps(ctx.df), hide_index=True, **shell.stretch(st.dataframe))

with t5:
    cols = ["date", "name", "symbol", "open", "high", "low", "close", "volume", "change", "ret", "range", "range_pct", "typical", "year", "month", "quarter", "dow"]
    st.markdown(f"**{len(d):,} records** match the current slicers (all commodities if none selected)")
    st.dataframe(d[cols].sort_values(["date", "name"], ascending=[False, True]), hide_index=True, height=420, **shell.stretch(st.dataframe))
    e1, e2, e3 = st.columns([1, 1, 3])
    e1.download_button("Download CSV", to_csv_bytes(d[cols]), "commodity_filtered.csv", "text/csv", icon=":material/download:", **shell.stretch(st.download_button))
    key = (tuple(ctx.sel), ctx.rng, ctx.metric, str(ctx.start), str(ctx.end), ctx.cal)
    if e2.button("Prepare Excel", icon=":material/table_view:", **shell.stretch(st.button)):
        with st.spinner("Building Excel file..."):
            st.session_state["xl"] = (key, stats.to_excel_bytes(d[cols], desc))
    if st.session_state.get("xl", (None,))[0] == key:
        e3.download_button("Download Excel (.xlsx)", st.session_state["xl"][1], "commodity_filtered.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", icon=":material/download:")
