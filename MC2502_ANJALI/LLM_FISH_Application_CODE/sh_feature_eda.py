"""
fish_feature_eda.py

Feature-level EDA for the fish predicted from the uploaded image.

IMPORTANT
---------
This module does NOT perform dataset-level EDA.

It analyzes the FEATURES/ATTRIBUTES of the fish identified by
the CNN, using:

    1. CNN prediction information
    2. GBIF taxonomy
    3. GBIF occurrence/distribution
    4. USDA nutrition
    5. Gemini/RAG fact-sheet information

The uploaded image itself is only used to identify the fish.
Its pixels are NOT treated as the EDA dataset.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# HELPERS
# ============================================================

def safe_float(value: Any) -> Optional[float]:
    """
    Safely convert a value to float.
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return float(value)

    try:
        value = str(value).replace(",", "").strip()

        if value.lower() in {
            "",
            "none",
            "null",
            "nan",
            "n/a",
            "unknown",
            "—",
            "-",
        }:
            return None

        return float(value)

    except (ValueError, TypeError):
        return None


def clean_text(value: Any, default: str = "Not available") -> str:
    """
    Safely convert a value to readable text.
    """
    if value is None:
        return default

    text = str(value).strip()

    if not text:
        return default

    return text


def normalize_percent(value: Any) -> Optional[float]:
    """
    Convert confidence values into 0-100 percentage.

    Examples:
        0.95 -> 95
        95   -> 95
    """
    number = safe_float(value)

    if number is None:
        return None

    if 0 <= number <= 1:
        return number * 100

    return number


def numeric_dict(source: Any) -> Dict[str, float]:
    """
    Extract numeric values from a dictionary.
    """
    if not isinstance(source, dict):
        return {}

    result = {}

    for key, value in source.items():

        numeric_value = safe_float(value)

        if numeric_value is not None:
            result[str(key)] = numeric_value

    return result


# ============================================================
# FACT SHEET PARSER
# ============================================================

def parse_llm_fact_sheet(text: Optional[str]) -> Dict[str, str]:
    """
    Parse the existing Gemini fact-sheet format.

    Expected fields may include:

        Fish Name
        Scientific Name
        Habitat
        Nutrition
        Average Weight
        Cooking Uses
        Health Benefits

    The parser is deliberately tolerant because Gemini output
    can contain slightly different formatting.
    """

    if not text:
        return {}

    text = str(text)

    fields = [
        "Fish Name",
        "Scientific Name",
        "Habitat",
        "Nutrition",
        "Average Weight",
        "Cooking Uses",
        "Health Benefits",
    ]

    result = {}

    pattern = (
        r"("
        + "|".join(re.escape(field) for field in fields)
        + r")\s*:\s*"
    )

    parts = re.split(pattern, text, flags=re.IGNORECASE)

    if len(parts) >= 3:

        for i in range(1, len(parts) - 1, 2):

            key = parts[i].strip()
            value = parts[i + 1].strip()

            if value:
                result[key] = value

    return result


# ============================================================
# BUILD FEATURE RECORD
# ============================================================

def build_fish_feature_record(
    label: str,
    confidence: float,
    top3: Optional[List] = None,
    taxonomy: Optional[Dict] = None,
    nutrition: Optional[Dict] = None,
    distribution: Optional[Dict] = None,
    fact_sheet_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a feature-level representation of ONE predicted fish.

    This is NOT a dataset row.

    It is the feature profile of the fish predicted from the
    uploaded image.
    """

    taxonomy = taxonomy or {}
    nutrition = nutrition or {}
    distribution = distribution or {}

    facts = parse_llm_fact_sheet(fact_sheet_text)

    # --------------------------------------------------------
    # CNN FEATURES
    # --------------------------------------------------------

    prediction_confidence = normalize_percent(confidence)

    top3_rows = []

    if top3:

        for item in top3:

            try:
                species_name = item[0]
                species_confidence = item[1]

                top3_rows.append(
                    {
                        "Species": clean_text(species_name),
                        "Confidence": normalize_percent(
                            species_confidence
                        ),
                    }
                )

            except (IndexError, TypeError):
                continue

    # --------------------------------------------------------
    # GBIF FEATURES
    # --------------------------------------------------------

    canonical_name = clean_text(
        taxonomy.get("canonical_name")
        or taxonomy.get("species")
        or facts.get("Scientific Name")
    )

    gbif_family = clean_text(
        taxonomy.get("family")
    )

    gbif_order = clean_text(
        taxonomy.get("order")
    )

    gbif_class = clean_text(
        taxonomy.get("class")
    )

    gbif_phylum = clean_text(
        taxonomy.get("phylum")
    )

    gbif_kingdom = clean_text(
        taxonomy.get("kingdom")
    )

    gbif_genus = clean_text(
        taxonomy.get("genus")
    )

    gbif_confidence = normalize_percent(
        taxonomy.get("confidence")
    )

    gbif_status = clean_text(
        taxonomy.get("status")
    )

    # --------------------------------------------------------
    # DISTRIBUTION FEATURES
    # --------------------------------------------------------

    total_records = safe_float(
        distribution.get("total_records")
    )

    countries = distribution.get(
        "countries",
        []
    )

    country_count = 0

    if isinstance(countries, list):

        country_count = len(countries)

    points = distribution.get(
        "points",
        []
    )

    latitudes = []
    longitudes = []

    if isinstance(points, list):

        for point in points:

            if not isinstance(point, dict):
                continue

            lat = safe_float(
                point.get("lat")
            )

            lon = safe_float(
                point.get("lon")
            )

            if lat is not None:
                latitudes.append(lat)

            if lon is not None:
                longitudes.append(lon)

    mean_latitude = (
        float(np.mean(latitudes))
        if latitudes
        else None
    )

    mean_longitude = (
        float(np.mean(longitudes))
        if longitudes
        else None
    )

    latitude_range = None
    longitude_range = None

    if len(latitudes) >= 2:

        latitude_range = (
            max(latitudes) - min(latitudes)
        )

    if len(longitudes) >= 2:

        longitude_range = (
            max(longitudes) - min(longitudes)
        )

    # --------------------------------------------------------
    # USDA FEATURES
    # --------------------------------------------------------

    nutrient_data = nutrition.get(
        "nutrients_per_100g",
        {}
    )

    nutrient_data = numeric_dict(
        nutrient_data
    )

    # --------------------------------------------------------
    # FACT-SHEET FEATURES
    # --------------------------------------------------------

    habitat = facts.get(
        "Habitat",
        "Not available",
    )

    average_weight = facts.get(
        "Average Weight",
        "Not available",
    )

    cooking_uses = facts.get(
        "Cooking Uses",
        "Not available",
    )

    health_benefits = facts.get(
        "Health Benefits",
        "Not available",
    )

    llm_nutrition = facts.get(
        "Nutrition",
        "Not available",
    )

    # --------------------------------------------------------
    # COMPLETE FEATURE RECORD
    # --------------------------------------------------------

    feature_record = {

        # CNN
        "cnn_predicted_species": label,
        "cnn_confidence_percent": prediction_confidence,

        # GBIF taxonomy
        "scientific_name": canonical_name,
        "kingdom": gbif_kingdom,
        "phylum": gbif_phylum,
        "class": gbif_class,
        "order": gbif_order,
        "family": gbif_family,
        "genus": gbif_genus,
        "gbif_confidence_percent": gbif_confidence,
        "gbif_taxonomic_status": gbif_status,

        # Distribution
        "gbif_occurrence_records": total_records,
        "gbif_country_count": country_count,
        "gbif_coordinate_count": len(points)
        if isinstance(points, list)
        else 0,
        "gbif_mean_latitude": mean_latitude,
        "gbif_mean_longitude": mean_longitude,
        "gbif_latitude_range": latitude_range,
        "gbif_longitude_range": longitude_range,

        # LLM / RAG qualitative attributes
        "habitat": habitat,
        "average_weight": average_weight,
        "llm_nutrition": llm_nutrition,
        "cooking_uses": cooking_uses,
        "health_benefits": health_benefits,

        # USDA
        "usda_matched_food": clean_text(
            nutrition.get(
                "matched_food_name"
            )
        ),

        "usda_generic_fallback": bool(
            nutrition.get(
                "used_generic_fallback",
                False,
            )
        ),

        # Full nutrient dictionary
        "nutrients": nutrient_data,

        # Top predictions
        "top3_predictions": top3_rows,

        # Raw distribution information
        "countries": countries,

        # Raw feature counts
        "feature_count": 0,
    }

    # Count actual populated features
    populated = 0

    for key, value in feature_record.items():

        if key in {
            "nutrients",
            "top3_predictions",
            "countries",
            "feature_count",
        }:
            continue

        if value is not None:

            if isinstance(value, str):

                if value != "Not available":
                    populated += 1

            else:
                populated += 1

    populated += len(nutrient_data)

    feature_record["feature_count"] = populated

    return feature_record


# ============================================================
# FEATURE TABLE
# ============================================================

def create_feature_table(
    record: Dict[str, Any]
) -> pd.DataFrame:
    """
    Create a clean feature-value table.
    """

    rows = []

    feature_groups = {

        "CNN": [
            (
                "CNN predicted species",
                record.get(
                    "cnn_predicted_species"
                ),
            ),
            (
                "CNN confidence (%)",
                record.get(
                    "cnn_confidence_percent"
                ),
            ),
        ],

        "GBIF Taxonomy": [
            ("Scientific name", record.get("scientific_name")),
            ("Kingdom", record.get("kingdom")),
            ("Phylum", record.get("phylum")),
            ("Class", record.get("class")),
            ("Order", record.get("order")),
            ("Family", record.get("family")),
            ("Genus", record.get("genus")),
            (
                "GBIF confidence (%)",
                record.get(
                    "gbif_confidence_percent"
                ),
            ),
            (
                "Taxonomic status",
                record.get(
                    "gbif_taxonomic_status"
                ),
            ),
        ],

        "GBIF Distribution": [
            (
                "Occurrence records",
                record.get(
                    "gbif_occurrence_records"
                ),
            ),
            (
                "Countries represented",
                record.get(
                    "gbif_country_count"
                ),
            ),
            (
                "Coordinates available",
                record.get(
                    "gbif_coordinate_count"
                ),
            ),
            (
                "Mean latitude",
                record.get(
                    "gbif_mean_latitude"
                ),
            ),
            (
                "Mean longitude",
                record.get(
                    "gbif_mean_longitude"
                ),
            ),
            (
                "Latitude range",
                record.get(
                    "gbif_latitude_range"
                ),
            ),
            (
                "Longitude range",
                record.get(
                    "gbif_longitude_range"
                ),
            ),
        ],

        "LLM / RAG": [
            (
                "Habitat",
                record.get("habitat"),
            ),
            (
                "Average weight",
                record.get(
                    "average_weight"
                ),
            ),
            (
                "Nutrition summary",
                record.get(
                    "llm_nutrition"
                ),
            ),
            (
                "Cooking uses",
                record.get(
                    "cooking_uses"
                ),
            ),
            (
                "Health benefits",
                record.get(
                    "health_benefits"
                ),
            ),
        ],

        "USDA": [
            (
                "Matched food",
                record.get(
                    "usda_matched_food"
                ),
            ),
            (
                "Generic fallback used",
                record.get(
                    "usda_generic_fallback"
                ),
            ),
        ],
    }

    for group, values in feature_groups.items():

        for feature_name, value in values:

            if value is None:
                value = "Not available"

            rows.append(
                {
                    "Feature Group": group,
                    "Feature": feature_name,
                    "Value": value,
                }
            )

    # Add USDA nutrient features
    for nutrient_name, value in record.get(
        "nutrients",
        {},
    ).items():

        rows.append(
            {
                "Feature Group": "USDA Nutrition",
                "Feature": nutrient_name,
                "Value": value,
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# NUMERICAL FEATURES
# ============================================================

def numerical_feature_dataframe(
    record: Dict[str, Any]
) -> pd.DataFrame:
    """
    Extract numerical features for visualization.
    """

    rows = []

    numeric_features = {

        "CNN confidence": record.get(
            "cnn_confidence_percent"
        ),

        "GBIF confidence": record.get(
            "gbif_confidence_percent"
        ),

        "GBIF occurrence records": record.get(
            "gbif_occurrence_records"
        ),

        "GBIF country count": record.get(
            "gbif_country_count"
        ),

        "GBIF coordinate count": record.get(
            "gbif_coordinate_count"
        ),

        "Mean latitude": record.get(
            "gbif_mean_latitude"
        ),

        "Mean longitude": record.get(
            "gbif_mean_longitude"
        ),

        "Latitude range": record.get(
            "gbif_latitude_range"
        ),

        "Longitude range": record.get(
            "gbif_longitude_range"
        ),
    }

    for name, value in numeric_features.items():

        numeric_value = safe_float(value)

        if numeric_value is not None:

            rows.append(
                {
                    "Feature": name,
                    "Value": numeric_value,
                }
            )

    for nutrient_name, value in record.get(
        "nutrients",
        {},
    ).items():

        numeric_value = safe_float(value)

        if numeric_value is not None:

            rows.append(
                {
                    "Feature": nutrient_name,
                    "Value": numeric_value,
                }
            )

    return pd.DataFrame(rows)


# ============================================================
# RENDER EDA
# ============================================================

def render_feature_eda(
    record: Dict[str, Any]
) -> None:
    """
    Render complete feature-level EDA in Streamlit.
    """

    st.markdown(
        """
        <div class="fusion-header">
            <h2>📊 Fish Feature-Level EDA</h2>
            <p>
            Exploratory analysis of the attributes associated with the
            fish identified from the uploaded photograph.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "This is feature-level EDA for the predicted fish. "
        "The uploaded image is used for CNN identification; "
        "image pixels are not treated as the EDA dataset."
    )

    # ========================================================
    # FEATURE COUNT
    # ========================================================

    feature_count = record.get(
        "feature_count",
        0,
    )

    nutrients = record.get(
        "nutrients",
        {},
    )

    numeric_df = numerical_feature_dataframe(
        record
    )

    total_numeric_features = len(
        numeric_df
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Predicted Fish",
        record.get(
            "cnn_predicted_species",
            "Unknown",
        ),
    )

    c2.metric(
        "Populated Features",
        feature_count,
    )

    c3.metric(
        "Numerical Features",
        total_numeric_features,
    )

    c4.metric(
        "USDA Nutrients",
        len(nutrients),
    )

    # ========================================================
    # 1. CNN FEATURES
    # ========================================================

    st.markdown("### 🧠 1. CNN Prediction Features")

    cnn_col1, cnn_col2 = st.columns(
        [1, 2]
    )

    with cnn_col1:

        confidence = record.get(
            "cnn_confidence_percent"
        )

        if confidence is not None:

            st.metric(
                "CNN Confidence",
                f"{confidence:.2f}%",
            )

            st.progress(
                min(
                    max(
                        confidence / 100,
                        0,
                    ),
                    1,
                )
            )

    with cnn_col2:

        top3 = record.get(
            "top3_predictions",
            [],
        )

        if top3:

            top3_df = pd.DataFrame(
                top3
            )

            top3_df = top3_df.dropna(
                subset=["Confidence"]
            )

            if not top3_df.empty:

                top3_df["Confidence"] = (
                    top3_df["Confidence"]
                )

                st.bar_chart(
                    top3_df.set_index(
                        "Species"
                    )["Confidence"]
                )

    # ========================================================
    # 2. TAXONOMIC FEATURES
    # ========================================================

    st.markdown(
        "### 🧬 2. Taxonomic Feature Profile"
    )

    tax_cols = st.columns(4)

    tax_values = [
        (
            "Kingdom",
            record.get("kingdom"),
        ),
        (
            "Phylum",
            record.get("phylum"),
        ),
        (
            "Class",
            record.get("class"),
        ),
        (
            "Order",
            record.get("order"),
        ),
    ]

    for column, (name, value) in zip(
        tax_cols,
        tax_values,
    ):

        column.metric(
            name,
            clean_text(value),
        )

    tax_cols2 = st.columns(4)

    tax_values2 = [
        (
            "Family",
            record.get("family"),
        ),
        (
            "Genus",
            record.get("genus"),
        ),
        (
            "Scientific name",
            record.get("scientific_name"),
        ),
        (
            "GBIF status",
            record.get(
                "gbif_taxonomic_status"
            ),
        ),
    ]

    for column, (name, value) in zip(
        tax_cols2,
        tax_values2,
    ):

        column.metric(
            name,
            clean_text(value),
        )

    # ========================================================
    # 3. TAXONOMIC HIERARCHY
    # ========================================================

    st.markdown(
        "#### Taxonomic hierarchy"
    )

    hierarchy = [
        record.get("kingdom"),
        record.get("phylum"),
        record.get("class"),
        record.get("order"),
        record.get("family"),
        record.get("genus"),
        record.get("scientific_name"),
    ]

    hierarchy = [
        clean_text(x)
        for x in hierarchy
    ]

    hierarchy_text = " → ".join(
        hierarchy
    )

    st.code(
        hierarchy_text,
        language="text",
    )

    # ========================================================
    # 4. USDA NUTRITION
    # ========================================================

    st.markdown(
        "### 🥗 3. Nutritional Feature EDA"
    )

    if nutrients:

        nutrition_df = pd.DataFrame(
            {
                "Nutrient": list(
                    nutrients.keys()
                ),
                "Value": list(
                    nutrients.values()
                ),
            }
        )

        nutrition_df["Value"] = pd.to_numeric(
            nutrition_df["Value"],
            errors="coerce",
        )

        nutrition_df = (
            nutrition_df
            .dropna()
            .sort_values(
                "Value",
                ascending=False,
            )
        )

        if not nutrition_df.empty:

            st.bar_chart(
                nutrition_df.set_index(
                    "Nutrient"
                )["Value"]
            )

            st.dataframe(
                nutrition_df,
                use_container_width=True,
                hide_index=True,
            )

        st.caption(
            "Nutritional values are displayed using the nutrient values returned "
            "by the USDA integration. Units depend on the USDA nutrient field."
        )

    else:

        st.warning(
            "No numerical USDA nutrient values are currently available "
            "for this predicted fish."
        )

    # ========================================================
    # 5. NUTRITION SUMMARY
    # ========================================================

    if nutrients:

        st.markdown(
            "#### Macronutrient feature summary"
        )

        macro_candidates = {}

        for key, value in nutrients.items():

            key_lower = key.lower()

            if (
                "protein" in key_lower
                or "fat" in key_lower
                or "carbohydrate" in key_lower
                or "calorie" in key_lower
                or "energy" in key_lower
            ):

                macro_candidates[
                    key
                ] = value

        if macro_candidates:

            macro_df = pd.DataFrame(
                {
                    "Feature": list(
                        macro_candidates.keys()
                    ),
                    "Value": list(
                        macro_candidates.values()
                    ),
                }
            )

            st.bar_chart(
                macro_df.set_index(
                    "Feature"
                )["Value"]
            )

    # ========================================================
    # 6. GEOGRAPHIC FEATURES
    # ========================================================

    st.markdown(
        "### 🌍 4. Geographic Feature EDA"
    )

    geo_cols = st.columns(4)

    geo_cols[0].metric(
        "Occurrence Records",
        (
            f"{int(record['gbif_occurrence_records']):,}"
            if record.get(
                "gbif_occurrence_records"
            )
            is not None
            else "—"
        ),
    )

    geo_cols[1].metric(
        "Countries",
        record.get(
            "gbif_country_count",
            0,
        ),
    )

    geo_cols[2].metric(
        "Coordinates",
        record.get(
            "gbif_coordinate_count",
            0,
        ),
    )

    geo_cols[3].metric(
        "Mean Latitude",
        (
            f"{record['gbif_mean_latitude']:.4f}"
            if record.get(
                "gbif_mean_latitude"
            )
            is not None
            else "—"
        ),
    )

    geo2 = st.columns(3)

    geo2[0].metric(
        "Mean Longitude",
        (
            f"{record['gbif_mean_longitude']:.4f}"
            if record.get(
                "gbif_mean_longitude"
            )
            is not None
            else "—"
        ),
    )

    geo2[1].metric(
        "Latitude Range",
        (
            f"{record['gbif_latitude_range']:.4f}"
            if record.get(
                "gbif_latitude_range"
            )
            is not None
            else "—"
        ),
    )

    geo2[2].metric(
        "Longitude Range",
        (
            f"{record['gbif_longitude_range']:.4f}"
            if record.get(
                "gbif_longitude_range"
            )
            is not None
            else "—"
        ),
    )

    # ========================================================
    # 7. DISTRIBUTION MAP
    # ========================================================

    countries = record.get(
        "countries",
        [],
    )

    if countries:

        st.markdown(
            "#### Geographic occurrence profile"
        )

        country_rows = []

        for item in countries:

            try:

                if isinstance(item, (list, tuple)):

                    country = item[0]
                    count = item[1]

                elif isinstance(item, dict):

                    country = (
                        item.get("name")
                        or item.get("country")
                    )

                    count = (
                        item.get("count")
                    )

                else:
                    continue

                country_rows.append(
                    {
                        "Country": clean_text(
                            country
                        ),
                        "Records": safe_float(
                            count
                        ),
                    }
                )

            except Exception:
                continue

        if country_rows:

            country_df = pd.DataFrame(
                country_rows
            )

            country_df["Records"] = pd.to_numeric(
                country_df["Records"],
                errors="coerce",
            )

            country_df = (
                country_df
                .dropna()
                .sort_values(
                    "Records",
                    ascending=False,
                )
                .head(15)
            )

            st.bar_chart(
                country_df.set_index(
                    "Country"
                )["Records"]
            )

    # ========================================================
    # 8. LLM / RAG FEATURES
    # ========================================================

    st.markdown(
        "### 🤖 5. LLM / RAG Feature Profile"
    )

    st.caption(
        "These are qualitative attributes returned by the existing "
        "Gemini/RAG fact-sheet stage. They are shown as feature information, "
        "not treated as independently measured numerical data."
    )

    llm_features = [
        (
            "🌊 Habitat",
            record.get("habitat"),
        ),
        (
            "⚖️ Average Weight",
            record.get(
                "average_weight"
            ),
        ),
        (
            "🥗 Nutrition",
            record.get(
                "llm_nutrition"
            ),
        ),
        (
            "🍳 Cooking Uses",
            record.get(
                "cooking_uses"
            ),
        ),
        (
            "💪 Health Benefits",
            record.get(
                "health_benefits"
            ),
        ),
    ]

    for i in range(
        0,
        len(llm_features),
        2,
    ):

        cols = st.columns(2)

        for j in range(2):

            index = i + j

            if index >= len(
                llm_features
            ):
                break

            title, value = (
                llm_features[index]
            )

            with cols[j]:

                st.markdown(
                    f"""
                    <div class="fact-card">
                        <div class="fact-label">
                            {title}
                        </div>
                        <div class="fact-value">
                            {clean_text(value)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ========================================================
    # 9. COMPLETE FEATURE TABLE
    # ========================================================

    st.markdown(
        "### 📋 6. Complete Feature Profile"
    )

    feature_df = create_feature_table(
        record
    )

    st.dataframe(
        feature_df,
        use_container_width=True,
        hide_index=True,
    )

    # ========================================================
    # 10. NUMERICAL FEATURE VISUALIZATION
    # ========================================================

    st.markdown(
        "### 📈 7. Numerical Feature Overview"
    )

    if not numeric_df.empty:

        display_df = (
            numeric_df
            .copy()
            .sort_values(
                "Value",
                ascending=False,
            )
        )

        st.bar_chart(
            display_df.set_index(
                "Feature"
            )["Value"]
        )

    else:

        st.info(
            "No numerical feature values are currently available."
        )

    # ========================================================
    # 11. FEATURE AVAILABILITY
    # ========================================================

    st.markdown(
        "### ✅ 8. Feature Availability"
    )

    feature_groups = {
        "CNN": [
            record.get(
                "cnn_predicted_species"
            ),
            record.get(
                "cnn_confidence_percent"
            ),
        ],

        "GBIF Taxonomy": [
            record.get(
                "scientific_name"
            ),
            record.get(
                "family"
            ),
            record.get(
                "order"
            ),
            record.get(
                "class"
            ),
        ],

        "GBIF Distribution": [
            record.get(
                "gbif_occurrence_records"
            ),
            record.get(
                "gbif_country_count"
            ),
            record.get(
                "gbif_coordinate_count"
            ),
        ],

        "USDA": list(
            nutrients.values()
        ),

        "LLM / RAG": [
            record.get("habitat"),
            record.get(
                "average_weight"
            ),
            record.get(
                "llm_nutrition"
            ),
            record.get(
                "cooking_uses"
            ),
            record.get(
                "health_benefits"
            ),
        ],
    }

    availability_rows = []

    for group, values in feature_groups.items():

        total = len(values)

        available = 0

        for value in values:

            if value is None:
                continue

            if isinstance(value, str):

                if value.strip() in {
                    "",
                    "Not available",
                }:
                    continue

            available += 1

        percentage = (
            available / total * 100
            if total
            else 0
        )

        availability_rows.append(
            {
                "Feature Group": group,
                "Available": available,
                "Total": total,
                "Availability (%)": percentage,
            }
        )

    availability_df = pd.DataFrame(
        availability_rows
    )

    st.dataframe(
        availability_df.style.format(
            {
                "Availability (%)":
                    "{:.1f}%"
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.bar_chart(
        availability_df.set_index(
            "Feature Group"
        )["Availability (%)"]
    )

    # ========================================================
    # RESEARCH INTERPRETATION
    # ========================================================

    st.markdown(
        "### 🔎 Feature-Level Interpretation"
    )

    st.success(
        f"""
        The uploaded photograph was classified as **{
            record.get('cnn_predicted_species', 'Unknown')
        }**.

        The EDA shown above describes the attributes associated with
        that predicted fish: CNN confidence, taxonomic information,
        biodiversity occurrence information, geographic features,
        USDA nutritional features, and qualitative LLM/RAG attributes.

        This is therefore **fish-specific feature EDA**, rather than
        dataset-level EDA or pixel-level image analysis.
        """
    )