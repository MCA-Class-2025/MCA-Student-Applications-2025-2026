
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

st.set_page_config(
    page_title="Travel Destination Intelligence",
    page_icon="🌍",
    layout="wide"
)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():
    enriched = DATA / "travel_attractions_enriched.csv"
    csv = DATA / "travel_attractions_1500.csv"
    xlsx = DATA / "travel_attractions_master.xlsx"

    if enriched.exists():
        return pd.read_csv(enriched)

    if xlsx.exists():
        try:
            return pd.read_excel(xlsx, sheet_name="Attractions")
        except Exception:
            pass

    if csv.exists():
        return pd.read_csv(csv)

    return pd.DataFrame()


df = load_data()

st.title("🌍 Travel Destination Intelligence System")
st.caption(
    "Worldwide attraction analytics, multi-source data enrichment "
    "and retrieval-augmented destination assistant."
)

if df.empty:
    st.warning(
        "Dataset not found. Run python setup_project.py "
        "from the project folder, then refresh this page."
    )
    st.stop()


# --------------------------------------------------
# SIDEBAR AND FILTERS
# --------------------------------------------------

numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

with st.sidebar:
    st.header("Explore the data")

    page = st.radio(
        "Navigate",
        [
            "Overview",
            "EDA & Visualizations",
            "Explore Attractions",
            "Destination Map",
            "AI Travel Assistant",
            "About & Data Sources"
        ]
    )

    countries = (
        sorted(df["country_en"].dropna().astype(str).unique())
        if "country_en" in df.columns else []
    )

    selected_countries = st.multiselect(
        "Filter countries", countries, default=[]
    )

    cats = (
        sorted(df["category"].dropna().astype(str).unique())
        if "category" in df.columns else []
    )

    selected_cats = st.multiselect(
        "Filter categories", cats, default=[]
    )


view = df.copy()

if selected_countries and "country_en" in view.columns:
    view = view[view["country_en"].isin(selected_countries)]

if selected_cats and "category" in view.columns:
    view = view[view["category"].isin(selected_cats)]


# --------------------------------------------------
# 1. OVERVIEW
# --------------------------------------------------

if page == "Overview":

    st.subheader("Dataset Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Attractions", f"{len(view):,}")

    c2.metric(
        "Countries",
        view["country_en"].nunique()
        if "country_en" in view.columns else "—"
    )

    c3.metric(
        "Cities",
        view["city_en"].nunique()
        if "city_en" in view.columns else "—"
    )

    c4.metric(
        "Categories",
        view["category"].nunique()
        if "category" in view.columns else "—"
    )

    st.markdown("### Top countries by attraction records")

    if "country_en" in view.columns:

        top = (
            view["country_en"]
            .value_counts()
            .head(15)
            .rename_axis("Country")
            .reset_index(name="Attractions")
        )

        fig = px.bar(
            top,
            x="Country",
            y="Attractions",
            text="Attractions",
            title="Top 15 countries"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Attraction category distribution")

    if "category" in view.columns:

        topcat = (
            view["category"]
            .value_counts()
            .head(15)
            .rename_axis("Category")
            .reset_index(name="Count")
        )

        fig = px.bar(
            topcat,
            x="Category",
            y="Count",
            title="Most represented attraction categories"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.info(
        "Counts describe this curated dataset/sample, "
        "not the total number of tourist attractions in each country."
    )


# --------------------------------------------------
# 2. EXPLORATORY DATA ANALYSIS
# --------------------------------------------------

elif page == "EDA & Visualizations":

    st.subheader("Exploratory Data Analysis")

    st.markdown(
        "All plots are calculated from the currently filtered dataset."
    )

    # HEATMAP

    st.markdown("#### 1. Heatmap — Country vs Attraction Category")

    if {"country_en", "category"}.issubset(view.columns):

        top_c = view["country_en"].value_counts().head(15).index
        top_k = view["category"].value_counts().head(12).index

        heat_data = view[
            view["country_en"].isin(top_c)
            & view["category"].isin(top_k)
        ]

        matrix = pd.crosstab(
            heat_data["country_en"],
            heat_data["category"]
        )

        fig = px.imshow(
            matrix,
            labels={
                "x": "Attraction category",
                "y": "Country",
                "color": "Record count"
            },
            aspect="auto",
            color_continuous_scale="YlOrRd",
            title="Attraction category concentration by country"
        )

        st.plotly_chart(fig, use_container_width=True)

    # CORRELATION MATRIX

    st.markdown("#### 2. Correlation Matrix — Numerical Variables")

    corr_candidates = [
        c for c in numeric_cols
        if c in view.columns
        and view[c].notna().sum() > 2
        and view[c].nunique(dropna=True) > 1
    ]

    corr_candidates = [
        c for c in corr_candidates
        if not c.lower().endswith(("latitude", "longitude"))
    ]

    defaults = [
        c for c in [
            "wikidata_pagerank",
            "sitelinks",
            "search_impressions_decile",
            "forecast_avg_max_temp_c",
            "forecast_avg_min_temp_c",
            "past_30d_avg_temp_c",
            "currency_inr_per_unit",
            "public_holidays_this_year"
        ]
        if c in corr_candidates
    ]

    chosen = st.multiselect(
        "Numerical fields for correlation",
        corr_candidates,
        default=defaults[:8]
    )

    if len(chosen) >= 2:

        corr = view[chosen].corr(numeric_only=True)

        fig = px.imshow(
            corr,
            text_auto=".2f",
            zmin=-1,
            zmax=1,
            color_continuous_scale="RdBu_r",
            title="Pearson Correlation Matrix"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Correlation measures linear association; "
            "it does not establish causation."
        )

    else:
        st.info(
            "Select at least two numerical fields with variation."
        )

    # SCATTER PLOT - UPDATED AND FIXED

    st.markdown("#### 3. Scatter Plot — Relationship Between Variables")

    if len(corr_candidates) >= 2:

        x = st.selectbox(
            "X-axis",
            corr_candidates,
            index=0
        )

        y_options = [
            c for c in corr_candidates if c != x
        ]

        y = st.selectbox(
            "Y-axis",
            y_options,
            index=0
        )

        color_options = ["category", "country_en"]

        color = st.selectbox(
            "Color points by",
            ["None"] + [
                c for c in color_options if c in view.columns
            ]
        )

        # Include hover columns in the scatter DataFrame.
        hover_cols = [
            c for c in ["name_en", "city_en", "country_en"]
            if c in view.columns
        ]

        scatter_cols = list(dict.fromkeys([x, y] + hover_cols))

        if color != "None" and color in view.columns:
            scatter_cols.append(color)

        # Remove duplicate column names.
        scatter_cols = list(dict.fromkeys(scatter_cols))

        scatter = view[scatter_cols].dropna(subset=[x, y])

        if not scatter.empty:

            fig = px.scatter(
                scatter,
                x=x,
                y=y,
                color=None if color == "None" else color,
                hover_data=hover_cols,
                title=f"{y} vs {x}",
                opacity=0.75
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning(
                "No valid records available for the selected variables."
            )

    else:
        st.info(
            "At least two numerical variables with variation are required."
        )

    # BAR GRAPH

    st.markdown("#### 4. Bar Graph — Grouped Comparison")

    if "country_en" in view.columns:

        metric = st.selectbox(
            "Compare by",
            [
                "Attraction count",
                "Average Wikidata PageRank",
                "Average sitelinks"
            ]
        )

        group = view.groupby("country_en", dropna=True)

        if metric == "Attraction count":

            bar = (
                group.size()
                .rename("Value")
                .reset_index()
            )

        else:

            col = (
                "wikidata_pagerank"
                if metric == "Average Wikidata PageRank"
                else "sitelinks"
            )

            if col not in view.columns:

                st.warning(
                    f"{col} is unavailable in this dataset."
                )

                bar = pd.DataFrame()

            else:

                bar = (
                    group[col]
                    .mean()
                    .dropna()
                    .rename("Value")
                    .reset_index()
                )

        if not bar.empty:

            bar = (
                bar.sort_values("Value", ascending=False)
                .head(15)
            )

            fig = px.bar(
                bar,
                x="country_en",
                y="Value",
                text_auto=".2s",
                title=metric + " by country"
            )

            st.plotly_chart(fig, use_container_width=True)

    # DATA QUALITY

    st.markdown("#### Data Quality")

    missing = (
        view.isna()
        .sum()
        .rename("Missing values")
        .to_frame()
    )

    st.dataframe(
        missing[missing["Missing values"] > 0],
        use_container_width=True
    )


# --------------------------------------------------
# 3. EXPLORE ATTRACTIONS
# --------------------------------------------------

elif page == "Explore Attractions":

    st.subheader("Search and Explore Attractions")

    q = st.text_input(
        "Search attraction, city or country"
    )

    result = view.copy()

    if q:

        mask = pd.Series(False, index=result.index)

        for col in [
            "name_en",
            "city_en",
            "country_en",
            "category"
        ]:

            if col in result.columns:

                mask |= (
                    result[col]
                    .astype(str)
                    .str.contains(q, case=False, na=False)
                )

        result = result[mask]

    cols = [
        c for c in [
            "name_en",
            "city_en",
            "country_en",
            "category",
            "wikipedia_summary",
            "wikidata_description",
            "forecast_avg_max_temp_c",
            "forecast_avg_min_temp_c",
            "currency_code",
            "currency_inr_per_unit",
            "next_public_holiday",
            "next_public_holiday_date",
            "official_website",
            "wikipedia_url"
        ]
        if c in result.columns
    ]

    st.write(f"{len(result):,} matching records")

    st.dataframe(
        result[cols],
        use_container_width=True,
        height=600
    )

    st.download_button(
        "Download filtered data",
        result.to_csv(index=False).encode("utf-8"),
        "filtered_attractions.csv",
        "text/csv"
    )


# --------------------------------------------------
# 4. DESTINATION MAP
# --------------------------------------------------

elif page == "Destination Map":

    st.subheader("Worldwide Attraction Map")

    if {"latitude", "longitude"}.issubset(view.columns):

        points = view.dropna(
            subset=["latitude", "longitude"]
        ).copy()

        if len(points) > 2500:
            points = points.sample(
                2500,
                random_state=42
            )

        if not points.empty:

            fig = px.scatter_geo(
                points,
                lat="latitude",
                lon="longitude",
                color=(
                    "category"
                    if "category" in points.columns
                    else None
                ),
                hover_name=(
                    "name_en"
                    if "name_en" in points.columns
                    else None
                ),
                hover_data=[
                    c for c in ["city_en", "country_en"]
                    if c in points.columns
                ],
                projection="natural earth",
                title="Geographical Distribution of Attractions"
            )

            fig.update_traces(
                marker=dict(size=6, opacity=0.7)
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.caption(
                "Map points represent attraction coordinates "
                "in the selected sample."
            )

        else:
            st.warning("No valid coordinates available.")

    else:
        st.warning(
            "Latitude/longitude columns are unavailable."
        )


# --------------------------------------------------
# 5. AI TRAVEL ASSISTANT
# --------------------------------------------------

elif page == "AI Travel Assistant":

    st.subheader("RAG-Based AI Travel Assistant")

    st.write(
        "Ask questions about attractions represented in your dataset. "
        "Answers are grounded in retrieved records."
    )

    st.caption(
        "First-time setup downloads the embedding model. "
        "Ollama must be installed and running locally."
    )

    with st.expander("Setup Instructions"):

        st.code(
            "ollama pull qwen2.5:3b\n"
            "pip install -r requirements.txt\n"
            "python -c \"from rag_engine import build_index; print(build_index())\""
        )

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for message in st.session_state.chat:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Ask about destinations, attractions, weather or comparisons..."
    )

    if prompt:

        st.session_state.chat.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            with st.spinner(
                "Retrieving destination information and generating an answer..."
            ):

                try:

                    from rag_engine import answer

                    response = answer(prompt)

                    st.markdown(response)

                except Exception as e:

                    response = (
                        f"Unable to answer right now: {e}\n\n"
                        "Check that Ollama is running, the model is "
                        "installed, and the RAG index has been built."
                    )

                    st.error(response)

        st.session_state.chat.append(
            {"role": "assistant", "content": response}
        )


# --------------------------------------------------
# 6. ABOUT AND DATA SOURCES
# --------------------------------------------------

else:

    st.subheader("About the Project")

    st.write(
        "A travel destination intelligence application combining "
        "a curated attractions dataset, external API enrichment, "
        "exploratory analysis, geospatial visualization and "
        "local retrieval-augmented generation."
    )

    st.markdown("**Data Sources**")

    st.markdown("""
    - Audiala Places dataset — original attraction metadata.
    - Open-Meteo — weather forecast and historical archive.
    - Wikipedia REST API — descriptive summaries.
    - Wikidata — structured entity facts.
    - Frankfurter — reference exchange rates.
    - Nager.Date — public holiday data.
    """)

    st.warning(
        "Data coverage varies by provider. Missing fields mean "
        "information was not available from the source, "
        "not necessarily that the fact does not exist."
    )
