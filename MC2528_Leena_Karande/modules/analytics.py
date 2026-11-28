"""Dataset Insights page.

Laid out like a BI dashboard (filter panel top-right, KPI strip, dense
grid of small-multiple charts all visible at once, no tabs to click
through) -- in the app's own purple/teal/gold theme rather than a
generic BI blue.

Combines three layers, and every chart/KPI reacts to the filter panel:
  1. Live charts computed from the curated dataset (data/dance_forms.json).
  2. API + Kaggle enrichment coverage + geography, computed live from the
     final fused dataset (data/dancecompass_final_fused_allsources.csv).
  3. Live text-analysis charts computed from the fused dataset -- no
     static PNGs, so it always reflects the current, filtered data.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.dance_data import load_dance_forms
from utils.merged_data import load_eda_tables, load_merged_df
from utils.styles import kpi_card

_CHART_CONFIG = {"displayModeBar": False, "scrollZoom": False, "doubleClick": False}

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#CBD5E1",
    font_family="Segoe UI, sans-serif",
    showlegend=False,
    height=260,
    margin=dict(l=10, r=10, t=28, b=10),
    dragmode=False,
    hoverlabel=dict(bgcolor="#1E293B", font_color="#F8FAFC"),
)

_PALETTE = ["#8B7CF6", "#38DACB", "#F472B6", "#FACC15", "#60A5FA", "#34D399", "#FB923C"]

_ENERGY_ORDER = ["Low", "Low-Medium", "Medium", "Medium-High", "High"]


def _style(fig):
    fig.update_layout(**_LAYOUT)
    fig.update_xaxes(gridcolor="rgba(255,255,255,.06)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,.06)", zeroline=False)
    return fig


def _chart(fig):
    st.plotly_chart(_style(fig), use_container_width=True, config=_CHART_CONFIG)


def _bucket_formation(s: str) -> str:
    s = s.lower()
    if "partner" in s:
        return "Partner"
    if "group" in s:
        return "Group"
    return "Solo"


def render():
    st.markdown(
        "<section class='home-hero' style='padding:32px 40px;'>"
        "<div><p class='eyebrow'>THE DATA BEHIND DANCECOMPASS</p>"
        "<h1 style='font-size:clamp(1.8rem,3.6vw,2.7rem);'>Dataset Insights</h1>"
        "<p>Filter the collection below and every chart updates together.</p></div>"
        "<div class='hero-orb' style='font-size:48px; width:110px; height:110px; flex-basis:110px;'>📊</div></section>",
        unsafe_allow_html=True,
    )

    dance_forms = load_dance_forms()
    df = pd.DataFrame(dance_forms)
    df["formation"] = df["solo_or_partner"].apply(_bucket_formation)
    merged_df = load_merged_df()

    # ---------------- Filter panel (Power-BI-style multi-select tiles) ----------------
    with st.container(border=True):
        st.markdown("<p class='prompt-label' style='margin:0 0 8px;'>🔎 Filters</p>", unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            category_filter = st.multiselect("Category", sorted(df["category"].unique()), placeholder="All categories")
        with f2:
            energy_filter = st.multiselect("Energy level", [e for e in _ENERGY_ORDER if e in df["energy_level"].unique()], placeholder="All energy levels")
        with f3:
            difficulty_filter = st.multiselect("Difficulty", sorted(df["learning_difficulty"].unique()), placeholder="All difficulties")
        with f4:
            formation_filter = st.multiselect("Formation", sorted(df["formation"].unique()), placeholder="All formations")

    filtered = df.copy()
    if category_filter:
        filtered = filtered[filtered["category"].isin(category_filter)]
    if energy_filter:
        filtered = filtered[filtered["energy_level"].isin(energy_filter)]
    if difficulty_filter:
        filtered = filtered[filtered["learning_difficulty"].isin(difficulty_filter)]
    if formation_filter:
        filtered = filtered[filtered["formation"].isin(formation_filter)]

    filtered_ids = set(filtered["id"]) if "id" in filtered.columns else set()
    merged_filtered = merged_df[merged_df["id"].isin(filtered_ids)] if not merged_df.empty else merged_df

    if filtered.empty:
        st.warning("No dance forms match the current filters. Try clearing one.")
        return

    st.write("")

    # ---------------- KPI strip ----------------
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi_card("Dance forms shown", f"{len(filtered)} / {len(df)}")
    with k2:
        kpi_card("Categories", str(filtered["category"].nunique()))
    with k3:
        kpi_card("Countries", str(merged_filtered["country"].nunique()) if not merged_filtered.empty and "country" in merged_filtered.columns else "n/a")
    with k4:
        if not merged_filtered.empty and "word_count" in merged_filtered.columns and len(merged_filtered):
            kpi_card("Avg. words / profile", f"{merged_filtered['word_count'].mean():.0f}")
        else:
            kpi_card("Avg. words / profile", "n/a")
    with k5:
        pct_group = round((filtered["formation"] == "Group").mean() * 100) if len(filtered) else 0
        kpi_card("Group dances", f"{pct_group}%")

    st.write("")

    # ---------------- Dense chart grid (everything visible, no tabs) ----------------
    row1c1, row1c2 = st.columns(2)
    with row1c1:
        with st.container(border=True):
            st.markdown("##### Dance Forms by Category")
            cat_counts = filtered["category"].value_counts().reset_index()
            cat_counts.columns = ["category", "count"]
            fig = px.bar(cat_counts, x="count", y="category", orientation="h", color_discrete_sequence=[_PALETTE[0]])
            _chart(fig)

    with row1c2:
        with st.container(border=True):
            st.markdown("##### Energy Level Distribution")
            energy_counts = filtered["energy_level"].value_counts().reindex(_ENERGY_ORDER).dropna().reset_index()
            energy_counts.columns = ["energy_level", "count"]
            fig2 = px.bar(energy_counts, x="energy_level", y="count", color_discrete_sequence=[_PALETTE[1]])
            _chart(fig2)

    row2c1, row2c2 = st.columns(2)
    with row2c1:
        with st.container(border=True):
            st.markdown("##### Formation")
            formation_counts = filtered["formation"].value_counts().reset_index()
            formation_counts.columns = ["formation", "count"]
            fig3 = px.pie(formation_counts, names="formation", values="count", hole=0.55, color_discrete_sequence=_PALETTE)
            fig3.update_traces(textfont_color="#F8FAFC")
            _chart(fig3)

    with row2c2:
        with st.container(border=True):
            st.markdown("##### Learning Difficulty")
            diff_counts = filtered["learning_difficulty"].value_counts().reset_index()
            diff_counts.columns = ["difficulty", "count"]
            fig4 = px.bar(diff_counts, x="difficulty", y="count", color_discrete_sequence=[_PALETTE[3]])
            _chart(fig4)

    if not merged_filtered.empty:
        row3c1, row3c2 = st.columns(2)
        with row3c1:
            with st.container(border=True):
                st.markdown("##### API Enrichment Coverage (filtered set)")
                sources = {"Wikidata": "wikidata_found", "Wikipedia": "wikipedia_found", "Nominatim": "location_found", "Open Library": "openlibrary_found", "MusicBrainz": "musicbrainz_found"}
                total = len(merged_filtered)
                cov_rows = []
                for label, col in sources.items():
                    if col in merged_filtered.columns:
                        found = int(merged_filtered[col].fillna(False).astype(bool).sum())
                        cov_rows.append({"source": label, "found": found, "coverage_%": round(found / total * 100, 1) if total else 0})
                cov_df = pd.DataFrame(cov_rows)
                fig5 = px.bar(cov_df, x="source", y="found", color_discrete_sequence=[_PALETTE[2]], text="coverage_%")
                fig5.update_traces(texttemplate="%{text}%", textposition="outside", textfont_color="#CBD5E1")
                fig5.update_layout(yaxis_title="Dance forms enriched", yaxis_range=[0, max(total, 1) + 4])
                _chart(fig5)

        with row3c2:
            with st.container(border=True):
                st.markdown("##### Profile Length (words)")
                if "word_count" in merged_filtered.columns:
                    text_df = merged_filtered[["name", "word_count"]].sort_values("word_count", ascending=True)
                    fig6 = px.bar(text_df, x="word_count", y="name", orientation="h", color_discrete_sequence=[_PALETTE[4]])
                    fig6.update_layout(height=max(260, 26 * len(text_df)))
                    _chart(fig6)
                else:
                    st.caption("Text-analysis columns aren't available yet.")

        if {"latitude", "longitude"}.issubset(merged_filtered.columns):
            with st.container(border=True):
                st.markdown("##### Geographic Origins (via Nominatim)")
                geo = merged_filtered.dropna(subset=["latitude", "longitude"])[["name", "latitude", "longitude", "country"]]
                if not geo.empty:
                    fig_map = px.scatter_geo(
                        geo, lat="latitude", lon="longitude", hover_name="name", color="country",
                        projection="natural earth", color_discrete_sequence=_PALETTE,
                    )
                    fig_map.update_traces(marker=dict(size=10, line=dict(width=1, color="#090A1B")))
                    fig_map.update_geos(
                        bgcolor="rgba(0,0,0,0)",
                        showland=True, landcolor="#1E293B",
                        showocean=True, oceancolor="#0B0D22",
                        showlakes=True, lakecolor="#0B0D22",
                        showcountries=True, countrycolor="#334155",
                        coastlinecolor="#334155",
                        showframe=False,
                    )
                    fig_map.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", font_color="#CBD5E1", font_family="Segoe UI, sans-serif",
                        height=380, margin=dict(l=10, r=10, t=10, b=10),
                        legend=dict(bgcolor="rgba(0,0,0,0)", font_color="#CBD5E1"),
                    )
                    st.plotly_chart(fig_map, use_container_width=True, config=_CHART_CONFIG)
                else:
                    st.caption("No geocoded dance forms in the current filter.")
    else:
        st.info("The fused dataset (data/dancecompass_final_fused_allsources.csv) isn't available, so API/geo/text charts can't be shown.")

    tables = load_eda_tables()
    if "summary" in tables:
        with st.container(border=True):
            st.markdown("##### Dataset Quality Summary")
            st.dataframe(tables["summary"], hide_index=True, use_container_width=True)

    st.caption("Computed live from data/dance_forms.json and data/dancecompass_final_fused_allsources.csv -- the original curated JSON is never modified.")
