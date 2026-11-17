"""
MovieMind AI - Advanced Analytics Dashboard

Uses the fused movie dataset and Plotly for interactive visualizations.
All insights are calculated from the dataset; no unsupported LLM claims
or fabricated values are generated here.
"""

import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# Keep charts consistent with the existing MovieMind AI dark theme.
BG = "#0F1117"
CARD = "#1A1D29"
TEXT = "#FFFFFF"
MUTED = "#A6A9B8"
ORANGE = "#FF6B00"
PINK = "#FF3D71"
PURPLE = "#6C63FF"
PALETTE = [ORANGE, PINK, PURPLE, "#21C7A8", "#F5C451", "#55A6FF", "#B78CFF"]


@st.cache_data(show_spinner="Loading movie analytics...")
def load_analytics_data(path="data/fused_movies.csv"):
    """Load and prepare the fused dataset once, then cache it."""
    data = pd.read_csv(path, encoding="latin1")

    for column in ["vote_average", "popularity", "runtime", "tmdb_rating", "prices"]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")

    if "release_date" in data.columns:
        # The source file contains dates in more than one common format.
        try:
            data["release_date_parsed"] = pd.to_datetime(
                data["release_date"], errors="coerce", format="mixed"
            )
        except (TypeError, ValueError):
            # Compatibility fallback for older pandas versions.
            data["release_date_parsed"] = pd.to_datetime(
                data["release_date"], errors="coerce"
            )
        data["release_year"] = data["release_date_parsed"].dt.year
        data["release_decade"] = (
            (data["release_year"] // 10 * 10).astype("Int64").astype("string") + "s"
        )

    if "genres_clean" in data.columns:
        data["genres_clean"] = data["genres_clean"].fillna("").astype(str)

    if "streaming_platforms" in data.columns:
        data["streaming_platforms"] = data["streaming_platforms"].fillna("").astype(str)

    return data


def _chart_layout(fig, height=360):
    fig.update_layout(
        height=height,
        paper_bgcolor=BG,
        plot_bgcolor=CARD,
        font=dict(color=TEXT, family="Inter, sans-serif"),
        margin=dict(l=20, r=20, t=55, b=35),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        title_font=dict(size=17, color=TEXT),
        hoverlabel=dict(bgcolor=CARD, font_color=TEXT),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.12)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.12)")
    return fig


def _split_values(series):
    """Split comma-separated values into individual values."""
    values = (
        series.dropna()
        .astype(str)
        .str.split(",")
        .explode()
        .str.strip()
    )
    return values[values.ne("") & values.str.lower().ne("nan")]


def _genre_long(data):
    if "genres_clean" not in data.columns:
        return pd.DataFrame(columns=["title", "genre", "vote_average", "popularity", "release_year"])
    cols = [c for c in ["title", "genres_clean", "vote_average", "popularity", "release_year"] if c in data.columns]
    result = data[cols].copy()
    result["genre"] = result["genres_clean"].fillna("").str.split(",")
    result = result.explode("genre")
    result["genre"] = result["genre"].astype(str).str.strip()
    result = result[result["genre"].ne("") & result["genre"].str.lower().ne("nan")]
    return result


def _api_counts(data):
    api_columns = {
        "TMDB": "tmdb_id",
        "YouTube": "video_id",
        "Watchmode": "watchmode_id",
    }
    rows = []
    total = len(data)
    for api, column in api_columns.items():
        matched = int(data[column].notna().sum()) if column in data.columns else 0
        rows.append({
            "API": api,
            "Matched": matched,
            "Unmatched": max(total - matched, 0),
            "Coverage (%)": round((matched / total * 100), 2) if total else 0,
        })
    return pd.DataFrame(rows)


def _render_filters(data):
    st.markdown("### 🎛️ Dashboard Filters")
    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 1.4])

    genre_values = sorted(
        set(_split_values(data.get("genres_clean", pd.Series(dtype=str))).tolist())
    )
    with c1:
        selected_genres = st.multiselect(
            "Genre",
            options=genre_values,
            placeholder="All genres",
            key="analytics_genres",
        )

    valid_years = data["release_year"].dropna() if "release_year" in data.columns else pd.Series(dtype=float)
    year_min = int(valid_years.min()) if not valid_years.empty else 1900
    year_max = int(valid_years.max()) if not valid_years.empty else 2026
    if year_min == year_max:
        year_min = max(year_min - 1, 1800)
    with c2:
        selected_years = st.slider(
            "Release year",
            min_value=year_min,
            max_value=year_max,
            value=(year_min, year_max),
            key="analytics_year_range",
        )

    with c3:
        minimum_rating = st.slider(
            "Minimum rating",
            min_value=0.0,
            max_value=10.0,
            value=0.0,
            step=0.5,
            key="analytics_min_rating",
        )

    platform_values = sorted(
        set(_split_values(data.get("streaming_platforms", pd.Series(dtype=str))).tolist())
    )
    with c4:
        selected_platform = st.selectbox(
            "Streaming platform",
            options=["All platforms"] + platform_values,
            key="analytics_platform",
        )

    filtered = data.copy()

    if selected_genres and "genres_clean" in filtered.columns:
        pattern = "|".join(re.escape(g) for g in selected_genres)
        filtered = filtered[
            filtered["genres_clean"].str.contains(pattern, case=False, regex=True, na=False)
        ]

    if "release_year" in filtered.columns:
        filtered = filtered[
            filtered["release_year"].between(selected_years[0], selected_years[1], inclusive="both")
            | filtered["release_year"].isna()
        ]

    if "vote_average" in filtered.columns:
        filtered = filtered[
            filtered["vote_average"].isna() | filtered["vote_average"].ge(minimum_rating)
        ]

    if selected_platform != "All platforms" and "streaming_platforms" in filtered.columns:
        filtered = filtered[
            filtered["streaming_platforms"].str.contains(
                re.escape(selected_platform), case=False, regex=True, na=False
            )
        ]

    st.caption(f"Showing **{len(filtered):,}** of **{len(data):,}** movie records after filters.")
    return filtered


def _kpi_cards(data, full_data):
    total = len(data)
    avg_rating = data["vote_average"].mean() if "vote_average" in data else np.nan
    avg_runtime = data["runtime"].mean() if "runtime" in data else np.nan
    genres = _split_values(data.get("genres_clean", pd.Series(dtype=str)))
    top_genre = genres.value_counts().index[0] if not genres.empty else "N/A"
    api_rows = _api_counts(data)
    any_api = int(data[[c for c in ["tmdb_id", "video_id", "watchmode_id"] if c in data.columns]].notna().any(axis=1).sum()) if any(c in data.columns for c in ["tmdb_id", "video_id", "watchmode_id"]) else 0

    metrics = [
        ("🎬 Movies", f"{total:,}"),
        ("⭐ Average rating", f"{avg_rating:.2f}/10" if pd.notna(avg_rating) else "N/A"),
        ("⏱ Average runtime", f"{avg_runtime:.0f} min" if pd.notna(avg_runtime) else "N/A"),
        ("🎭 Top genre", top_genre),
        ("🔗 API enriched", f"{any_api:,}"),
    ]
    cols = st.columns(5)
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)


def _overview_tab(data):
    _kpi_cards(data, data)
    st.divider()
    left, right = st.columns(2)

    with left:
        st.markdown("#### 🎭 Genre distribution")
        genres = _split_values(data.get("genres_clean", pd.Series(dtype=str))).value_counts().head(10)
        if not genres.empty:
            fig = px.pie(
                names=genres.index,
                values=genres.values,
                hole=0.55,
                color_discrete_sequence=PALETTE,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(_chart_layout(fig, 390), use_container_width=True)
        else:
            st.info("No genre information is available for the selected filters.")

    with right:
        st.markdown("#### ⭐ Rating distribution")
        ratings = data["vote_average"].dropna() if "vote_average" in data else pd.Series(dtype=float)
        ratings = ratings[ratings.between(0, 10)]
        if not ratings.empty:
            fig = px.histogram(
                x=ratings,
                nbins=20,
                labels={"x": "Movie rating", "y": "Number of movies"},
                color_discrete_sequence=[ORANGE],
            )
            st.plotly_chart(_chart_layout(fig), use_container_width=True)
        else:
            st.info("No valid ratings are available for the selected filters.")

    st.markdown("#### 📅 Movies released over time")
    if "release_year" in data.columns:
        yearly = data.dropna(subset=["release_year"]).groupby("release_year").size().reset_index(name="Movies")
        if not yearly.empty:
            fig = px.line(yearly, x="release_year", y="Movies", markers=True, color_discrete_sequence=[PINK])
            fig.update_xaxes(title="Release year")
            st.plotly_chart(_chart_layout(fig, 350), use_container_width=True)


def _genre_tab(data):
    genre_data = _genre_long(data)
    if genre_data.empty:
        st.info("Genre information is not available.")
        return

    counts = genre_data["genre"].value_counts().head(15).reset_index()
    counts.columns = ["Genre", "Movies"]
    left, right = st.columns(2)

    with left:
        st.markdown("#### Top genres")
        fig = px.bar(
            counts.sort_values("Movies"),
            x="Movies",
            y="Genre",
            orientation="h",
            color="Movies",
            color_continuous_scale=["#6C63FF", "#FF6B00"],
        )
        st.plotly_chart(_chart_layout(fig, 430), use_container_width=True)

    with right:
        st.markdown("#### Genre share")
        fig = px.treemap(counts, path=["Genre"], values="Movies", color="Movies", color_continuous_scale="Magma")
        st.plotly_chart(_chart_layout(fig, 430), use_container_width=True)

    st.markdown("#### Average rating by genre")
    rating_genres = genre_data.dropna(subset=["vote_average"])
    rating_genres = rating_genres[rating_genres["vote_average"].between(0, 10)]
    top_names = counts["Genre"].head(10).tolist()
    rating_genres = rating_genres[rating_genres["genre"].isin(top_names)]
    if not rating_genres.empty:
        fig = px.box(
            rating_genres,
            x="genre",
            y="vote_average",
            color="genre",
            color_discrete_sequence=PALETTE,
            points="outliers",
        )
        fig.update_layout(showlegend=False)
        fig.update_xaxes(title="Genre")
        fig.update_yaxes(title="Rating")
        st.plotly_chart(_chart_layout(fig, 430), use_container_width=True)

    if "release_year" in genre_data.columns:
        st.markdown("#### Genre trends by decade")
        decade_data = genre_data.dropna(subset=["release_year"]).copy()
        decade_data["Decade"] = (decade_data["release_year"] // 10 * 10).astype(int).astype(str) + "s"
        decade_top = counts["Genre"].head(6).tolist()
        decade_data = decade_data[decade_data["genre"].isin(decade_top)]
        if not decade_data.empty:
            pivot = decade_data.groupby(["Decade", "genre"]).size().reset_index(name="Movies")
            fig = px.density_heatmap(
                pivot,
                x="Decade",
                y="genre",
                z="Movies",
                histfunc="sum",
                color_continuous_scale="Magma",
            )
            fig.update_layout(coloraxis_colorbar_title="Movies")
            st.plotly_chart(_chart_layout(fig, 380), use_container_width=True)


def _rating_tab(data):
    if "vote_average" not in data.columns:
        st.info("Rating data is not available.")
        return
    rated = data.dropna(subset=["vote_average"]).copy()
    rated = rated[rated["vote_average"].between(0, 10)]
    if rated.empty:
        st.info("No valid ratings are available for the selected filters.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Rating box plot")
        fig = px.box(rated, y="vote_average", points="outliers", color_discrete_sequence=[PURPLE])
        fig.update_yaxes(title="Rating (0–10)")
        st.plotly_chart(_chart_layout(fig), use_container_width=True)
    with c2:
        st.markdown("#### Rating violin plot")
        fig = px.violin(rated, y="vote_average", box=True, points="outliers", color_discrete_sequence=[PINK])
        fig.update_yaxes(title="Rating (0–10)")
        st.plotly_chart(_chart_layout(fig), use_container_width=True)

    if "popularity" in rated.columns:
        st.markdown("#### Rating vs popularity")
        scatter_data = rated.dropna(subset=["popularity"])
        if not scatter_data.empty:
            fig = px.scatter(
                scatter_data,
                x="popularity",
                y="vote_average",
                hover_name="title" if "title" in scatter_data.columns else None,
                size="runtime" if "runtime" in scatter_data.columns else None,
                size_max=22,
                color="vote_average",
                color_continuous_scale="Plasma",
                labels={"popularity": "Popularity", "vote_average": "Rating"},
            )
            st.plotly_chart(_chart_layout(fig, 440), use_container_width=True)

    if "tmdb_rating" in rated.columns:
        st.markdown("#### Original dataset rating vs TMDB rating")
        comparison = rated.dropna(subset=["tmdb_rating"])
        comparison = comparison[comparison["tmdb_rating"].between(0, 10)]
        if not comparison.empty:
            fig = px.scatter(
                comparison,
                x="vote_average",
                y="tmdb_rating",
                hover_name="title" if "title" in comparison.columns else None,
                color_discrete_sequence=[ORANGE],
                labels={"vote_average": "Original rating", "tmdb_rating": "TMDB rating"},
            )
            fig.add_shape(
                type="line", x0=0, y0=0, x1=10, y1=10,
                line=dict(color=MUTED, dash="dash"),
            )
            st.plotly_chart(_chart_layout(fig, 400), use_container_width=True)
            st.caption("The dashed diagonal represents equal ratings from both sources.")
        else:
            st.info("No records have both original and TMDB ratings under the current filters.")


def _release_tab(data):
    if "release_year" not in data.columns:
        st.info("Release-date information is not available.")
        return
    dated = data.dropna(subset=["release_year"]).copy()
    if dated.empty:
        st.info("No valid release dates are available.")
        return

    yearly = dated.groupby("release_year").size().reset_index(name="Movies")
    decade = dated.assign(
        Decade=(dated["release_year"] // 10 * 10).astype(int).astype(str) + "s"
    ).groupby("Decade").size().reset_index(name="Movies")

    st.markdown("#### Movies released per year")
    fig = px.line(yearly, x="release_year", y="Movies", markers=True, color_discrete_sequence=[ORANGE])
    st.plotly_chart(_chart_layout(fig, 370), use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.markdown("#### Release volume by decade")
        fig = px.bar(decade, x="Decade", y="Movies", color="Movies", color_continuous_scale="Sunset")
        st.plotly_chart(_chart_layout(fig, 360), use_container_width=True)

    with right:
        st.markdown("#### Release trend area chart")
        fig = px.area(yearly, x="release_year", y="Movies", color_discrete_sequence=[PURPLE])
        st.plotly_chart(_chart_layout(fig, 360), use_container_width=True)

    genre_data = _genre_long(dated)
    if not genre_data.empty:
        st.markdown("#### Genre releases over time")
        genre_data["Decade"] = (genre_data["release_year"] // 10 * 10).astype(int).astype(str) + "s"
        top_genres = genre_data["genre"].value_counts().head(6).index.tolist()
        stacked = genre_data[genre_data["genre"].isin(top_genres)].groupby(["Decade", "genre"]).size().reset_index(name="Movies")
        fig = px.bar(stacked, x="Decade", y="Movies", color="genre", barmode="stack", color_discrete_sequence=PALETTE)
        fig.update_layout(legend_title="Genre")
        st.plotly_chart(_chart_layout(fig, 420), use_container_width=True)


def _api_tab(data):
    api_df = _api_counts(data)
    st.markdown("#### API coverage")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            api_df,
            x="API",
            y="Coverage (%)",
            color="API",
            text="Coverage (%)",
            color_discrete_sequence=PALETTE,
        )
        fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        fig.update_yaxes(range=[0, max(5, float(api_df["Coverage (%)"].max()) * 1.25)])
        st.plotly_chart(_chart_layout(fig, 360), use_container_width=True)
    with c2:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Matched", x=api_df["API"], y=api_df["Matched"], marker_color=ORANGE))
        fig.add_trace(go.Bar(name="Unmatched", x=api_df["API"], y=api_df["Unmatched"], marker_color="#45495A"))
        fig.update_layout(barmode="group", title="Matched vs unmatched records")
        st.plotly_chart(_chart_layout(fig, 360), use_container_width=True)

    st.dataframe(api_df, use_container_width=True, hide_index=True)

    st.markdown("#### Streaming platforms")
    if "streaming_platforms" in data.columns:
        platforms = _split_values(data["streaming_platforms"]).value_counts().head(15).reset_index()
        platforms.columns = ["Platform", "Records"]
        if not platforms.empty:
            fig = px.bar(platforms.sort_values("Records"), x="Records", y="Platform", orientation="h", color="Records", color_continuous_scale="Viridis")
            st.plotly_chart(_chart_layout(fig, 420), use_container_width=True)
        else:
            st.info("No streaming platform records are available under the current filters.")

    st.markdown("#### Missing data heatmap")
    api_fields = [
        c for c in [
            "tmdb_id", "tmdb_title", "tmdb_overview", "tmdb_poster_url", "tmdb_rating",
            "video_id", "trailer_title", "channel", "thumbnail", "youtube_url",
            "watchmode_id", "streaming_platforms", "availability_types", "prices",
            "qualities", "streaming_urls",
        ] if c in data.columns
    ]
    if api_fields and len(data):
        missing_pct = data[api_fields].isna().mean().mul(100).to_frame("Missing (%)")
        fig = px.imshow(
            missing_pct.T,
            text_auto=".1f",
            aspect="auto",
            color_continuous_scale="Reds",
            labels=dict(x="API fields", y="", color="Missing (%)"),
        )
        st.plotly_chart(_chart_layout(fig, 330), use_container_width=True)


def _insights_tab(data):
    st.markdown("#### 📌 Automatically calculated insights")
    insights = []

    if "genres_clean" in data.columns:
        genre_counts = _split_values(data["genres_clean"]).value_counts()
        if not genre_counts.empty:
            insights.append(f"**Most represented genre:** {genre_counts.index[0]} ({int(genre_counts.iloc[0]):,} genre assignments in the filtered data).")

    if "vote_average" in data.columns:
        ratings = data["vote_average"].dropna()
        ratings = ratings[ratings.between(0, 10)]
        if not ratings.empty:
            insights.append(f"**Average movie rating:** {ratings.mean():.2f}/10 across {len(ratings):,} rated records.")

    if "popularity" in data.columns and "vote_average" in data.columns:
        paired = data[["popularity", "vote_average"]].dropna()
        paired = paired[paired["vote_average"].between(0, 10)]
        if len(paired) >= 2:
            corr = paired["popularity"].corr(paired["vote_average"])
            if pd.notna(corr):
                direction = "positive" if corr > 0.1 else "negative" if corr < -0.1 else "weak or near-zero"
                insights.append(f"**Rating and popularity relationship:** Pearson correlation is {corr:.2f}, indicating a {direction} linear relationship. Correlation does not prove causation.")

    if "release_year" in data.columns:
        years = data["release_year"].dropna()
        if not years.empty:
            decade = (years // 10 * 10).astype(int).value_counts().sort_values(ascending=False)
            insights.append(f"**Most represented release decade:** {int(decade.index[0])}s ({int(decade.iloc[0]):,} records).")

    if "runtime" in data.columns:
        runtimes = data["runtime"].dropna()
        runtimes = runtimes[runtimes.gt(0)]
        if not runtimes.empty:
            insights.append(f"**Typical runtime:** median {runtimes.median():.0f} minutes; average {runtimes.mean():.0f} minutes.")

    for item in insights:
        st.markdown(f"- {item}")

    if not insights:
        st.info("There is not enough data in the current selection to calculate insights.")

    st.markdown("#### Correlation heatmap")
    numeric_cols = [c for c in ["vote_average", "tmdb_rating", "popularity", "runtime"] if c in data.columns]
    if len(numeric_cols) >= 2:
        corr_data = data[numeric_cols].apply(pd.to_numeric, errors="coerce")
        corr = corr_data.corr()
        if not corr.empty:
            fig = px.imshow(
                corr,
                text_auto=".2f",
                color_continuous_scale="RdBu",
                zmin=-1,
                zmax=1,
                aspect="auto",
                labels=dict(color="Correlation"),
            )
            st.plotly_chart(_chart_layout(fig, 420), use_container_width=True)

    st.markdown("#### Top-rated movies")
    if "vote_average" in data.columns and "title" in data.columns:
        top = data.dropna(subset=["vote_average"]).copy()
        top = top[top["vote_average"].between(0, 10)]
        top = top.sort_values(["vote_average", "popularity"] if "popularity" in top.columns else ["vote_average"], ascending=False).head(10)
        display_cols = [c for c in ["title", "vote_average", "popularity", "release_year", "genres_clean"] if c in top.columns]
        st.dataframe(top[display_cols], use_container_width=True, hide_index=True)

    st.markdown("#### Most popular movies")
    if "popularity" in data.columns and "title" in data.columns:
        popular = data.dropna(subset=["popularity"]).sort_values("popularity", ascending=False).head(10)
        display_cols = [c for c in ["title", "popularity", "vote_average", "release_year"] if c in popular.columns]
        st.dataframe(popular[display_cols], use_container_width=True, hide_index=True)


def render_analytics_dashboard():
    """Render the advanced analytics page inside the existing Streamlit app."""
    st.markdown(
        """
        <div style="text-align:center; padding: 0.5rem 0 1rem 0;">
            <h1>📊 MovieMind AI Analytics</h1>
            <p style="color:#A6A9B8;">Explore movie trends, ratings, genres and API data coverage</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        full_data = load_analytics_data()
    except Exception as exc:
        st.error(f"Unable to load data/fused_movies.csv: {exc}")
        st.info("Check that the CSV file exists inside the project's data folder.")
        return

    if full_data.empty:
        st.warning("The fused movie dataset is empty.")
        return

    filtered_data = _render_filters(full_data)
    st.divider()

    tabs = st.tabs([
        "📌 Overview",
        "🎭 Genre Analysis",
        "⭐ Rating Analysis",
        "📅 Release Trends",
        "🔌 API & Data Fusion",
        "💡 Advanced Insights",
    ])

    with tabs[0]:
        _overview_tab(filtered_data)
    with tabs[1]:
        _genre_tab(filtered_data)
    with tabs[2]:
        _rating_tab(filtered_data)
    with tabs[3]:
        _release_tab(filtered_data)
    with tabs[4]:
        _api_tab(filtered_data)
    with tabs[5]:
        _insights_tab(filtered_data)

    with st.expander("🗃️ View filtered dataset"):
        st.caption(f"{len(filtered_data):,} filtered records")
        st.dataframe(filtered_data.head(100), use_container_width=True, hide_index=True)

    st.caption("MovieMind AI · Analytics are calculated from the fused dataset. Missing API values are not treated as zero.")
