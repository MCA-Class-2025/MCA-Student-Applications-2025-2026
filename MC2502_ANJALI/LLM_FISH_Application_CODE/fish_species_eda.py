from pathlib import Path
import math
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

API_METADATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "fusion_analytics"
    / "api_fusion_metadata.csv"
)

GBIF_DISTRIBUTION_PATH = (
    PROJECT_ROOT
    / "data"
    / "fusion_analytics"
    / "gbif_distribution.csv"
)


# ============================================================
# API NUMERICAL FEATURES
# ============================================================

GBIF_FEATURES = [
    "gbif_confidence",
    "gbif_occurrence_count",
    "gbif_country_count",
    "gbif_coordinate_count",
    "gbif_mean_latitude",
    "gbif_mean_longitude",
    "gbif_top_country_records",
]

USDA_FEATURES = [
    "usda_calories",
    "usda_protein",
    "usda_fat",
    "usda_carbohydrate",
]

WEATHER_FEATURES = [
    "weather_temperature",
    "weather_humidity",
    "weather_pressure",
    "weather_wind_speed",
    "weather_clouds",
]

ALL_NUMERIC_API_FEATURES = (
    GBIF_FEATURES
    + USDA_FEATURES
    + WEATHER_FEATURES
)


# ============================================================
# LOAD API METADATA
# ============================================================

@st.cache_data
def load_api_metadata():

    if not API_METADATA_PATH.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(API_METADATA_PATH)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data
def load_gbif_distribution():

    if not GBIF_DISTRIBUTION_PATH.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(GBIF_DISTRIBUTION_PATH)
    except Exception:
        return pd.DataFrame()


# ============================================================
# SAFE NUMERIC CONVERSION
# ============================================================

def numeric_value(value):

    try:

        if pd.isna(value):
            return np.nan

        return float(value)

    except Exception:

        return np.nan


# ============================================================
# GET SPECIES DATA
# ============================================================

def get_species_api_data(species):

    df = load_api_metadata()

    if df.empty:
        return pd.DataFrame()

    if "species" not in df.columns:
        return pd.DataFrame()

    result = df[
        df["species"].astype(str).str.strip()
        == str(species).strip()
    ].copy()

    return result


# ============================================================
# CNN EDA
# ============================================================

def render_cnn_eda(
    predicted_species,
    confidence,
    top_predictions=None,
):

    st.markdown("### 🧠 CNN Prediction Features")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Predicted Species",
            predicted_species,
        )

    with col2:

        st.metric(
            "CNN Confidence",
            f"{confidence * 100:.2f}%"
            if confidence <= 1
            else f"{confidence:.2f}%",
        )

    if not top_predictions:
        return

    rows = []

    for item in top_predictions:

        if isinstance(item, dict):

            name = item.get(
                "species",
                item.get(
                    "label",
                    "Unknown"
                )
            )

            score = item.get(
                "confidence",
                item.get(
                    "probability",
                    0
                )
            )

        elif isinstance(item, (tuple, list)):

            name = item[0]

            score = item[1]

        else:

            continue

        score = numeric_value(score)

        if pd.isna(score):
            continue

        if score <= 1:
            score *= 100

        rows.append(
            {
                "Species": name,
                "Probability": score,
            }
        )

    if not rows:
        return

    top_df = pd.DataFrame(rows)

    fig = px.bar(
        top_df,
        x="Probability",
        y="Species",
        orientation="h",
        title="Top CNN Predictions",
        text="Probability",
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
    )

    fig.update_layout(
        xaxis_title="Probability (%)",
        yaxis_title="",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# GBIF EDA
# ============================================================

def render_gbif_eda(species_df):

    st.markdown("### 🧬 GBIF Biodiversity Features")

    if species_df.empty:

        st.info(
            "No GBIF metadata is available for this species."
        )

        return

    row = species_df.iloc[0]

    gbif_values = {}

    for feature in GBIF_FEATURES:

        if feature in species_df.columns:

            value = numeric_value(
                row[feature]
            )

            if not pd.isna(value):

                gbif_values[feature] = value

    cols = st.columns(4)

    display_features = [
        (
            "gbif_confidence",
            "Taxonomy Confidence",
            "%",
        ),
        (
            "gbif_occurrence_count",
            "Occurrence Records",
            "",
        ),
        (
            "gbif_country_count",
            "Countries",
            "",
        ),
        (
            "gbif_coordinate_count",
            "Coordinate Records",
            "",
        ),
    ]

    for i, (feature, label, suffix) in enumerate(
        display_features
    ):

        with cols[i]:

            value = gbif_values.get(
                feature,
                np.nan,
            )

            if pd.isna(value):

                st.metric(
                    label,
                    "N/A",
                )

            else:

                if feature == "gbif_confidence":

                    st.metric(
                        label,
                        f"{value:.1f}{suffix}",
                    )

                else:

                    st.metric(
                        label,
                        f"{value:,.0f}",
                    )

    # --------------------------------------------------------
    # Geographic features
    # --------------------------------------------------------

    geo_rows = []

    for feature in [
        "gbif_mean_latitude",
        "gbif_mean_longitude",
        "gbif_top_country_records",
    ]:

        if feature in species_df.columns:

            value = numeric_value(
                row[feature]
            )

            if not pd.isna(value):

                geo_rows.append(
                    {
                        "Feature": feature,
                        "Value": value,
                    }
                )

    if geo_rows:

        geo_df = pd.DataFrame(
            geo_rows
        )

        fig = px.bar(
            geo_df,
            x="Feature",
            y="Value",
            title="GBIF Geographic Features",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# ============================================================
# USDA EDA
# ============================================================

def render_usda_eda(species_df):

    st.markdown(
        "### 🥗 USDA FoodData Central Features"
    )

    if species_df.empty:
        st.info(
            "No USDA metadata is available."
        )
        return

    row = species_df.iloc[0]

    values = []

    mapping = {
        "usda_calories": "Calories",
        "usda_protein": "Protein",
        "usda_fat": "Fat",
        "usda_carbohydrate": "Carbohydrates",
    }

    for column, label in mapping.items():

        if column not in species_df.columns:
            continue

        value = numeric_value(
            row[column]
        )

        if pd.isna(value):
            continue

        values.append(
            {
                "Feature": label,
                "Value": value,
            }
        )

    if not values:

        st.info(
            "USDA numerical nutrition values are unavailable."
        )

        return

    nutrition_df = pd.DataFrame(values)

    fig = px.bar(
        nutrition_df,
        x="Feature",
        y="Value",
        title="Nutritional Feature Profile",
        text="Value",
    )

    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.dataframe(
        nutrition_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# WEATHER EDA
# ============================================================

def render_weather_eda(species_df):

    st.markdown(
        "### 🌦️ Weather Features"
    )

    if species_df.empty:
        st.info(
            "Weather metadata is unavailable."
        )
        return

    row = species_df.iloc[0]

    mapping = {
        "weather_temperature": "Temperature",
        "weather_humidity": "Humidity",
        "weather_pressure": "Pressure",
        "weather_wind_speed": "Wind Speed",
        "weather_clouds": "Cloud Cover",
    }

    rows = []

    for column, label in mapping.items():

        if column not in species_df.columns:
            continue

        value = numeric_value(
            row[column]
        )

        if pd.isna(value):
            continue

        rows.append(
            {
                "Feature": label,
                "Value": value,
            }
        )

    if not rows:

        st.info(
            "No numerical weather values are available."
        )

        return

    weather_df = pd.DataFrame(rows)

    fig = px.bar(
        weather_df,
        x="Feature",
        y="Value",
        title="Weather Feature Profile",
        text="Value",
    )

    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# API FEATURE TABLE
# ============================================================

def render_api_feature_table(species_df):

    st.markdown(
        "### 📋 Complete API Feature Values"
    )

    if species_df.empty:

        st.info(
            "No API feature record found."
        )

        return

    row = species_df.iloc[0]

    rows = []

    for feature in ALL_NUMERIC_API_FEATURES:

        if feature not in species_df.columns:
            continue

        value = row[feature]

        if pd.isna(value):
            display_value = "N/A"
        else:
            display_value = value

        rows.append(
            {
                "API Feature": feature,
                "Value": display_value,
            }
        )

    if not rows:
        return

    feature_df = pd.DataFrame(rows)

    st.dataframe(
        feature_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# MISSING FEATURE ANALYSIS
# ============================================================

def render_missing_feature_analysis(species_df):

    st.markdown(
        "### 🔎 Feature Availability"
    )

    if species_df.empty:
        return

    available = []
    missing = []

    for feature in ALL_NUMERIC_API_FEATURES:

        if feature not in species_df.columns:

            missing.append(feature)
            continue

        value = species_df.iloc[0][feature]

        if pd.isna(value):

            missing.append(feature)

        else:

            available.append(feature)

    c1, c2 = st.columns(2)

    with c1:
        st.metric(
            "Available numerical features",
            len(available),
        )

    with c2:
        st.metric(
            "Missing numerical features",
            len(missing),
        )

    if missing:

        st.warning(
            "Missing features: "
            + ", ".join(missing)
        )


# ============================================================
# GBIF DISTRIBUTION MAP
# ============================================================

def render_species_distribution(species):

    st.markdown(
        "### 🗺️ Real GBIF Distribution"
    )

    df = load_gbif_distribution()

    if df.empty:

        st.info(
            "GBIF distribution data is unavailable."
        )

        return

    if "species" not in df.columns:

        st.info(
            "Distribution file does not contain species."
        )

        return

    species_df = df[
        df["species"].astype(str).str.strip()
        == str(species).strip()
    ].copy()

    if species_df.empty:

        st.info(
            f"No GBIF coordinate records found for {species}."
        )

        return

    required = [
        "latitude",
        "longitude",
    ]

    if not all(
        column in species_df.columns
        for column in required
    ):

        st.info(
            "Latitude/longitude columns are unavailable."
        )

        return

    species_df["latitude"] = pd.to_numeric(
        species_df["latitude"],
        errors="coerce",
    )

    species_df["longitude"] = pd.to_numeric(
        species_df["longitude"],
        errors="coerce",
    )

    species_df = species_df.dropna(
        subset=[
            "latitude",
            "longitude",
        ]
    )

    if species_df.empty:

        st.info(
            "No valid coordinates available."
        )

        return

    fig = px.scatter_geo(
        species_df,
        lat="latitude",
        lon="longitude",
        hover_name="country"
        if "country" in species_df.columns
        else None,
        hover_data=[
            c
            for c in [
                "country",
                "country_code",
                "gbif_occurrence_id",
            ]
            if c in species_df.columns
        ],
        title=f"GBIF Recorded Distribution — {species}",
    )

    fig.update_geos(
        showcountries=True,
        showland=True,
        showocean=True,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.caption(
        f"{len(species_df)} GBIF coordinate records "
        "are displayed for this species."
    )


# ============================================================
# COUNTRY DISTRIBUTION
# ============================================================

def render_country_distribution(species):

    st.markdown(
        "### 🌍 Recorded Countries"
    )

    df = load_gbif_distribution()

    if df.empty or "species" not in df.columns:
        return

    species_df = df[
        df["species"].astype(str).str.strip()
        == str(species).strip()
    ].copy()

    if species_df.empty:
        return

    if "country" not in species_df.columns:
        return

    country_df = (
        species_df
        .groupby("country")
        .size()
        .reset_index(
            name="GBIF Records"
        )
        .sort_values(
            "GBIF Records",
            ascending=False,
        )
        .head(15)
    )

    fig = px.bar(
        country_df,
        x="GBIF Records",
        y="country",
        orientation="h",
        title="Top Recorded Countries",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# MAIN EDA RENDERER
# ============================================================

def render_fish_species_eda(
    species,
    confidence=0.0,
    top_predictions=None,
):

    st.markdown("---")

    st.markdown(
        "# 📊 Fish-Specific Feature EDA"
    )

    st.caption(
        "This EDA describes the features of the "
        "fish species identified from the uploaded image. "
        "It is not image-level pixel EDA and is not "
        "dataset-wide EDA."
    )

    st.markdown(
        f"## 🐟 {species}"
    )

    # ========================================================
    # CNN
    # ========================================================

    render_cnn_eda(
        predicted_species=species,
        confidence=confidence,
        top_predictions=top_predictions,
    )

    species_df = get_species_api_data(
        species
    )

    # ========================================================
    # API EVIDENCE
    # ========================================================

    st.markdown("---")

    render_gbif_eda(
        species_df
    )

    st.markdown("---")

    render_usda_eda(
        species_df
    )

    st.markdown("---")

    render_weather_eda(
        species_df
    )

    # ========================================================
    # COMPLETE FEATURE TABLE
    # ========================================================

    st.markdown("---")

    render_api_feature_table(
        species_df
    )

    # ========================================================
    # FEATURE AVAILABILITY
    # ========================================================

    render_missing_feature_analysis(
        species_df
    )

    # ========================================================
    # GBIF MAP
    # ========================================================

    st.markdown("---")

    render_species_distribution(
        species
    )

    # ========================================================
    # COUNTRY CHART
    # ========================================================

    render_country_distribution(
        species
    )