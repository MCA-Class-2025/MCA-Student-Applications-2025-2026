import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Country Intelligence System",
    page_icon="🌍",
    layout="wide"
)

# ============================================================
# LOAD FUSED DATASET
# ============================================================

DATA_PATH = "data/fused_country_intelligence.csv"

try:
    df = pd.read_csv(DATA_PATH)
except Exception as e:
    st.error("Unable to load the fused dataset.")
    st.write(e)
    st.stop()

# ============================================================
# BASIC CLEANING
# ============================================================

numeric_columns = [
    "Population",
    "GDP",
    "GDP per capita",
    "Life expectancy",
    "Unemployment",
    "Internet usage",
    "Temperature (°C)",
    "Apparent Temperature (°C)",
    "Relative Humidity (%)",
    "Precipitation (mm)",
    "Wind Speed (km/h)",
    "Exchange Rate",
    "PM2.5",
    "PM10",
    "NO2",
    "O3",
    "Public Holidays 2026"
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🌍 Country Intelligence")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Country Explorer",
        "Compare Countries",
        "AI Country Assistant",
        "Data & Insights"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("Country Intelligence System")
st.sidebar.caption("Multi-API Data Fusion")


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title("🌍 Country Intelligence System")

    st.write(
        "Explore country information by combining development, "
        "geographic, weather, currency, air-quality and holiday data."
    )

    st.markdown("---")

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Countries",
            len(df)
        )

    with col2:
        st.metric(
            "Attributes",
            len(df.columns)
        )

    with col3:
        if "WDI Reference Year" in df.columns:
            year = int(df["WDI Reference Year"].dropna().iloc[0])
        else:
            year = "N/A"

        st.metric(
            "WDI Reference Year",
            year
        )

    with col4:
        st.metric(
            "Data Sources",
            "6"
        )

    st.markdown("---")

    st.subheader("Available Information")

    information = pd.DataFrame({
        "Category": [
            "Development Indicators",
            "Country & Geographic Information",
            "Weather",
            "Currency",
            "Air Quality",
            "Public Holidays"
        ],
        "Source": [
            "World Bank WDI",
            "REST Countries",
            "Open-Meteo",
            "Frankfurter",
            "OpenAQ",
            "Nager.Date"
        ]
    })

    st.table(information)

    st.markdown("---")

    st.subheader("Dataset Preview")

    preview_columns = [
        "Country Code",
        "Country Name",
        "Population",
        "GDP",
        "GDP per capita",
        "Life expectancy",
        "Temperature (°C)",
        "PM2.5"
    ]

    available = [
        c for c in preview_columns
        if c in df.columns
    ]

    st.dataframe(
        df[available].head(10),
        use_container_width=True
    )


# ============================================================
# COUNTRY EXPLORER
# ============================================================

elif page == "Country Explorer":

    st.title("🔎 Country Explorer")

    countries = sorted(
        df["Country Name"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_country = st.selectbox(
        "Select a country",
        countries
    )

    country = df[
        df["Country Name"] == selected_country
    ].iloc[0]

    st.markdown("---")

    st.subheader(selected_country)

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    st.markdown("### Basic Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(
            "**Capital:**",
            country.get("Capital", "N/A")
        )

        st.write(
            "**Region:**",
            country.get("Region", "N/A")
        )

    with col2:
        st.write(
            "**Subregion:**",
            country.get("Subregion", "N/A")
        )

        st.write(
            "**Currency:**",
            country.get("Currency Name", "N/A")
        )

    with col3:
        st.write(
            "**Area:**",
            country.get("Area (km²)", "N/A")
        )

        st.write(
            "**Languages:**",
            country.get("Languages", "N/A")
        )

    st.markdown("---")

    # --------------------------------------------------------
    # DEVELOPMENT INDICATORS
    # --------------------------------------------------------

    st.subheader("Development Indicators")

    development_columns = [
        "Population",
        "GDP",
        "GDP per capita",
        "Life expectancy",
        "Unemployment",
        "Internet usage"
    ]

    development_data = {}

    for col in development_columns:
        if col in df.columns:
            development_data[col] = country[col]

    development_df = pd.DataFrame(
        development_data.items(),
        columns=["Indicator", "Value"]
    )

    st.dataframe(
        development_df,
        hide_index=True,
        use_container_width=True
    )

    # --------------------------------------------------------
    # WEATHER
    # --------------------------------------------------------

    st.subheader("Weather")

    weather_columns = [
        "Temperature (°C)",
        "Apparent Temperature (°C)",
        "Relative Humidity (%)",
        "Precipitation (mm)",
        "Wind Speed (km/h)",
        "Weather Code"
    ]

    weather_data = {}

    for col in weather_columns:
        if col in df.columns:
            weather_data[col] = country[col]

    weather_df = pd.DataFrame(
        weather_data.items(),
        columns=["Weather Information", "Value"]
    )

    st.dataframe(
        weather_df,
        hide_index=True,
        use_container_width=True
    )

    # --------------------------------------------------------
    # CURRENCY
    # --------------------------------------------------------

    st.subheader("Currency Information")

    currency_columns = [
        "Currency Code",
        "Currency Name",
        "Exchange Rate",
        "Rate Date"
    ]

    currency_data = {}

    for col in currency_columns:
        if col in df.columns:
            currency_data[col] = country[col]

    currency_df = pd.DataFrame(
        currency_data.items(),
        columns=["Currency Information", "Value"]
    )

    st.dataframe(
        currency_df,
        hide_index=True,
        use_container_width=True
    )

    # --------------------------------------------------------
    # AIR QUALITY
    # --------------------------------------------------------

    st.subheader("Air Quality")

    air_columns = [
        "PM2.5",
        "PM10",
        "NO2",
        "O3"
    ]

    air_data = {}

    for col in air_columns:
        if col in df.columns:
            value = country[col]

            if pd.notna(value) and value < 0:
                value = None

            air_data[col] = value

    air_df = pd.DataFrame(
        air_data.items(),
        columns=["Pollutant", "Value"]
    )

    st.dataframe(
        air_df,
        hide_index=True,
        use_container_width=True
    )

    # --------------------------------------------------------
    # HOLIDAYS
    # --------------------------------------------------------

    st.subheader("Public Holidays")

    holiday_columns = [
        "Public Holidays 2026",
        "Holiday Names 2026",
        "Holiday Dates 2026"
    ]

    holiday_data = {}

    for col in holiday_columns:
        if col in df.columns:
            holiday_data[col] = country[col]

    holiday_df = pd.DataFrame(
        holiday_data.items(),
        columns=["Holiday Information", "Value"]
    )

    st.dataframe(
        holiday_df,
        hide_index=True,
        use_container_width=True
    )


# ============================================================
# COMPARE COUNTRIES
# ============================================================

elif page == "Compare Countries":

    st.title("📊 Compare Countries")

    countries = sorted(
        df["Country Name"]
        .dropna()
        .unique()
        .tolist()
    )

    col1, col2 = st.columns(2)

    with col1:
        country1 = st.selectbox(
            "First Country",
            countries,
            index=0
        )

    with col2:
        country2 = st.selectbox(
            "Second Country",
            countries,
            index=1 if len(countries) > 1 else 0
        )

    data1 = df[
        df["Country Name"] == country1
    ].iloc[0]

    data2 = df[
        df["Country Name"] == country2
    ].iloc[0]

    st.markdown("---")

    comparison_columns = [
        "Population",
        "GDP",
        "GDP per capita",
        "Life expectancy",
        "Unemployment",
        "Internet usage",
        "Temperature (°C)",
        "Exchange Rate",
        "PM2.5",
        "Public Holidays 2026"
    ]

    comparison = []

    for col in comparison_columns:

        if col in df.columns:

            comparison.append({
                "Indicator": col,
                country1: data1[col],
                country2: data2[col]
            })

    comparison_df = pd.DataFrame(comparison)

    st.subheader("Comparison")

    st.dataframe(
        comparison_df,
        hide_index=True,
        use_container_width=True
    )

    # --------------------------------------------------------
    # SIMPLE CHART
    # --------------------------------------------------------

    st.subheader("GDP per Capita Comparison")

    if "GDP per capita" in df.columns:

        chart_data = pd.DataFrame({
            "Country": [
                country1,
                country2
            ],
            "GDP per Capita": [
                data1["GDP per capita"],
                data2["GDP per capita"]
            ]
        })

        fig = px.bar(
            chart_data,
            x="Country",
            y="GDP per Capita",
            title="GDP per Capita"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )



# ============================================================
# AI COUNTRY ASSISTANT - GEMINI RAG
# ============================================================

elif page == "AI Country Assistant":

    from rag_engine import (
        answer_question,
        knowledge_base_count
    )

    st.title("AI Country Assistant")

    st.write(
        "Ask questions about countries using the "
        "integrated WDI and five-API knowledge base."
    )

    try:

        count = knowledge_base_count()

        st.success(
            f"RAG knowledge base ready: {count} country records"
        )

    except Exception as error:

        st.error(str(error))

        st.info(
            "Please run build_knowledge_base.py "
            "before using the AI assistant."
        )

        st.stop()

    st.markdown("---")

    question = st.text_input(
        "Enter your country-related question",
        placeholder="Example: What is the population and temperature of India?"
    )

    if st.button("Ask Gemini", type="primary"):

        if not question.strip():

            st.warning("Please enter a question.")

        else:

            with st.spinner(
                "Retrieving country information and generating answer..."
            ):

                try:

                    answer, sources = answer_question(
                        question.strip()
                    )

                    st.subheader("AI Response")

                    st.markdown(answer)

                    st.markdown("---")

                    st.subheader("Retrieved Sources")

                    source_df = pd.DataFrame(sources)

                    if not source_df.empty:

                        source_df = source_df.drop_duplicates()

                        st.dataframe(
                            source_df,
                            hide_index=True,
                            use_container_width=True
                        )

                except Exception as error:

                    st.error(
                        "Unable to generate the answer."
                    )

                    st.write(str(error))

    st.markdown("---")

    st.caption(
        "Powered by Gemini and Retrieval-Augmented Generation (RAG). "
        "Answers are generated using retrieved fused-dataset records."
    )




# ============================================================
# DATA & INSIGHTS
# ============================================================

elif page == "Data & Insights":

    st.title("📈 Data & Insights")

    st.write(
        "Explore important patterns from the fused country dataset."
    )

    # --------------------------------------------------------
    # DISTRIBUTION
    # --------------------------------------------------------

    st.subheader("GDP per Capita Distribution")

    if "GDP per capita" in df.columns:

        fig = px.histogram(
            df,
            x="GDP per capita",
            nbins=30,
            title="Distribution of GDP per Capita"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # BOXPLOT
    # --------------------------------------------------------

    st.subheader("GDP per Capita Boxplot")

    if "GDP per capita" in df.columns:

        fig = px.box(
            df,
            y="GDP per capita",
            title="GDP per Capita Boxplot"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # RELATIONSHIP 1
    # --------------------------------------------------------

    st.subheader(
        "GDP per Capita vs Life Expectancy"
    )

    if all(
        c in df.columns
        for c in [
            "GDP per capita",
            "Life expectancy"
        ]
    ):

        plot_df = df[
            [
                "GDP per capita",
                "Life expectancy"
            ]
        ].dropna()

        fig = px.scatter(
            plot_df,
            x="GDP per capita",
            y="Life expectancy",
            title="GDP per Capita vs Life Expectancy"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # RELATIONSHIP 2
    # --------------------------------------------------------

    st.subheader(
        "GDP per Capita vs PM2.5"
    )

    if all(
        c in df.columns
        for c in [
            "GDP per capita",
            "PM2.5"
        ]
    ):

        plot_df = df[
            [
                "GDP per capita",
                "PM2.5"
            ]
        ].copy()

        plot_df.loc[
            plot_df["PM2.5"] < 0,
            "PM2.5"
        ] = None

        plot_df = plot_df.dropna()

        fig = px.scatter(
            plot_df,
            x="GDP per capita",
            y="PM2.5",
            title="GDP per Capita vs PM2.5"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # CORRELATION HEATMAP
    # --------------------------------------------------------

    st.subheader("Correlation Heatmap")

    heatmap_columns = [
        "GDP per capita",
        "Population",
        "Life expectancy",
        "Internet usage",
        "Temperature (°C)",
        "Exchange Rate",
        "PM2.5",
        "Public Holidays 2026"
    ]

    available_heatmap = [
        c for c in heatmap_columns
        if c in df.columns
    ]

    corr = df[
        available_heatmap
    ].corr()

    fig = px.imshow(
        corr,
        text_auto=".2f",
        title="Correlation Between Selected Variables"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # --------------------------------------------------------
    # FUSION INSIGHT
    # --------------------------------------------------------

    st.subheader(
        "Fusion Insight: GDP per Capita and PM2.5"
    )

    if all(
        c in df.columns
        for c in [
            "GDP per capita",
            "PM2.5"
        ]
    ):

        insight_df = df[
            [
                "GDP per capita",
                "PM2.5"
            ]
        ].copy()

        insight_df.loc[
            insight_df["PM2.5"] < 0,
            "PM2.5"
        ] = None

        insight_df = insight_df.dropna()

        if len(insight_df) > 0:

            insight_df["GDP Group"] = pd.qcut(
                insight_df["GDP per capita"],
                q=4,
                labels=[
                    "Low",
                    "Lower-Middle",
                    "Upper-Middle",
                    "High"
                ],
                duplicates="drop"
            )

            group_summary = (
                insight_df
                .groupby("GDP Group", observed=True)["PM2.5"]
                .mean()
                .reset_index()
            )

            fig = px.bar(
                group_summary,
                x="GDP Group",
                y="PM2.5",
                title="Average PM2.5 by GDP Group"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.write(
                "This visualization demonstrates how the "
                "API-derived air-quality variable can be "
                "examined together with the original WDI "
                "economic indicator."
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Country Intelligence System | "
    "World Bank WDI + REST Countries + Open-Meteo + "
    "Frankfurter + OpenAQ + Nager.Date"
)