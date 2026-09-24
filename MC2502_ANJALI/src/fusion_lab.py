from pathlib import Path
import json
import ast

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "fusion_analytics"
    / "fusion_results.csv"
)

API_METADATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "fusion_analytics"
    / "api_fusion_metadata.csv"
)

FINAL_DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "fusion_analytics"
    / "final_fusion_dataset.csv"
)

DISTRIBUTION_PATH = (
    PROJECT_ROOT
    / "data"
    / "fusion_analytics"
    / "gbif_distribution.csv"
)


# ============================================================
# LOADERS
# ============================================================

@st.cache_data
def load_results():

    if not RESULTS_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(
        RESULTS_PATH
    )


@st.cache_data
def load_api_metadata():

    if not API_METADATA_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(
        API_METADATA_PATH
    )


@st.cache_data
def load_final_dataset():

    if not FINAL_DATASET_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(
        FINAL_DATASET_PATH
    )


@st.cache_data
def load_distribution():

    if not DISTRIBUTION_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(
        DISTRIBUTION_PATH
    )


# ============================================================
# API LIST
# ============================================================

def render_api_sources():

    st.markdown(
        "## 🌐 External Data Sources"
    )

    st.caption(
        "The fusion experiments use externally retrieved "
        "API-derived information rather than LLM-invented "
        "numerical values."
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
            ### 🧬 GBIF

            **Type:** External biodiversity API

            Used for:

            - Taxonomic verification
            - Taxonomic confidence
            - Occurrence records
            - Country count
            - Coordinate count
            - Mean latitude
            - Mean longitude
            - Top recorded country
            - Geographic distribution
            """
        )

    with col2:

        st.markdown(
            """
            ### 🥗 USDA FoodData Central

            **Type:** External nutrition API

            Used for:

            - FoodData Central ID
            - Food description
            - Calories
            - Protein
            - Fat
            - Carbohydrates
            - USDA verification status
            """
        )

    st.markdown(
        """
        ### 🌦️ Dynamic Weather API

        **Type:** Dynamic environmental API

        Used for:

        - Temperature
        - Humidity
        - Pressure
        - Wind speed
        - Cloud cover
        - Weather description
        - Weather location
        """
    )


# ============================================================
# SUMMARY
# ============================================================

def render_summary():

    api_df = load_api_metadata()
    final_df = load_final_dataset()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Dataset Images",
            f"{len(final_df):,}"
            if not final_df.empty
            else "N/A",
        )

    with c2:

        if not final_df.empty and "species" in final_df:

            count = final_df[
                "species"
            ].nunique()

        else:

            count = 0

        st.metric(
            "Species",
            count,
        )

    with c3:

        st.metric(
            "API Metadata Columns",
            len(api_df.columns)
            if not api_df.empty
            else 0,
        )

    with c4:

        st.metric(
            "Fusion Experiments",
            2,
        )


# ============================================================
# FUSION RESULTS
# ============================================================

def render_fusion_results():

    st.markdown(
        "## 🏆 Fusion Performance"
    )

    df = load_results()

    if df.empty:

        st.warning(
            "fusion_results.csv was not found."
        )

        return

    # --------------------------------------------------------
    # Only retain requested experiments
    # --------------------------------------------------------

    allowed = [
        "Raw/Data-Level Fusion",
        "Feature-Level Fusion",
    ]

    df = df[
        df["experiment"].isin(
            allowed
        )
    ].copy()

    if df.empty:

        st.warning(
            "Raw/Data-Level and Feature-Level "
            "Fusion results were not found."
        )

        return

    metric_columns = [
        "accuracy",
        "precision_weighted",
        "recall_weighted",
        "f1_weighted",
    ]

    available_metrics = [
        c
        for c in metric_columns
        if c in df.columns
    ]

    # --------------------------------------------------------
    # Cards
    # --------------------------------------------------------

    for _, row in df.iterrows():

        st.markdown(
            f"### {row['experiment']}"
        )

        cols = st.columns(
            len(available_metrics)
        )

        for col, metric in zip(
            cols,
            available_metrics,
        ):

            value = pd.to_numeric(
                row[metric],
                errors="coerce",
            )

            if pd.isna(value):
                text = "N/A"

            else:
                text = f"{value * 100:.2f}%"

            with col:

                st.metric(
                    metric.replace(
                        "_",
                        " ",
                    ).title(),
                    text,
                )

    # --------------------------------------------------------
    # Comparison chart
    # --------------------------------------------------------

    plot_df = df[
        [
            "experiment"
        ] + available_metrics
    ].copy()

    plot_df = plot_df.melt(
        id_vars="experiment",
        var_name="Metric",
        value_name="Score",
    )

    plot_df["Score"] *= 100

    fig = px.bar(
        plot_df,
        x="experiment",
        y="Score",
        color="Metric",
        barmode="group",
        text_auto=".2f",
        title="Raw vs Feature-Level Fusion",
    )

    fig.update_yaxes(
        title="Score (%)",
        range=[0, 100],
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# API FEATURE INVENTORY
# ============================================================

def render_feature_inventory():

    st.markdown(
        "## 🧩 Complete API Feature Inventory"
    )

    df = load_api_metadata()

    if df.empty:
        return

    columns = list(
        df.columns
    )

    categories = {
        "GBIF": [
            c for c in columns
            if c.startswith("gbif_")
        ],
        "USDA": [
            c for c in columns
            if c.startswith("usda_")
        ],
        "Weather": [
            c for c in columns
            if c.startswith("weather_")
        ],
    }

    for category, features in categories.items():

        st.markdown(
            f"### {category}"
        )

        if features:

            feature_df = pd.DataFrame(
                {
                    "Feature": features,
                    "Data Type": [
                        str(
                            df[f].dtype
                        )
                        for f in features
                    ],
                    "Non-Null Values": [
                        int(
                            df[f].notna().sum()
                        )
                        for f in features
                    ],
                }
            )

            st.dataframe(
                feature_df,
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# SPECIES API EVIDENCE
# ============================================================

def render_species_evidence():

    st.markdown(
        "## 🐟 External API Evidence by Species"
    )

    df = load_api_metadata()

    if df.empty or "species" not in df.columns:
        return

    summary_columns = [
        c for c in [
            "gbif_occurrence_count",
            "gbif_country_count",
            "gbif_coordinate_count",
            "usda_calories",
            "usda_protein",
            "usda_fat",
            "usda_carbohydrate",
        ]
        if c in df.columns
    ]

    if not summary_columns:
        return

    summary = (
        df.groupby(
            "species"
        )[summary_columns]
        .first()
        .reset_index()
    )

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# DATASET DISTRIBUTION
# ============================================================

def render_dataset_distribution():

    st.markdown(
        "## 📊 Dataset Distribution"
    )

    df = load_final_dataset()

    if df.empty or "species" not in df.columns:
        return

    species_counts = (
        df["species"]
        .value_counts()
        .sort_index()
        .reset_index()
    )

    species_counts.columns = [
        "Species",
        "Images",
    ]

    fig = px.bar(
        species_counts,
        x="Species",
        y="Images",
        title="Images per Fish Species",
        text="Images",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# RENDER FUSION LAB
# ============================================================

def render_fusion_lab():

    st.markdown("---")

    st.markdown(
        "# 🔬 Multimodal Fusion Analytics"
    )

    st.caption(
        "Comparison of Raw/Data-Level Fusion and "
        "Feature-Level Fusion using fish images and "
        "verified external API features."
    )

    render_summary()

    st.markdown("---")

    render_api_sources()

    st.markdown("---")

    st.markdown(
        "## 🧩 What is being fused?"
    )

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            """
            ### 🔵 Raw/Data-Level Fusion

            Image-related information and external
            API-derived information are combined
            at the data level before classification.

            **Image**

            +

            **GBIF + USDA + Weather**

            ↓

            **Combined representation**

            ↓

            **Classifier**
            """
        )

    with c2:

        st.markdown(
            """
            ### 🟣 Feature-Level Fusion

            The fish image is converted into learned
            CNN features.

            These are combined with numerical
            API-derived features.

            **CNN image features**

            +

            **GBIF + USDA + Weather features**

            ↓

            **Fused feature vector**

            ↓

            **Classifier**
            """
        )

    st.markdown("---")

    render_fusion_results()

    st.markdown("---")

    render_feature_inventory()

    st.markdown("---")

    render_species_evidence()

    st.markdown("---")

    render_dataset_distribution()