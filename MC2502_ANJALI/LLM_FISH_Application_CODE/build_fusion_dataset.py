from pathlib import Path
import pandas as pd
import numpy as np
import json
import joblib

from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ============================================================
# INPUT
# ============================================================

API_METADATA = (
    PROJECT_ROOT
    / "data"
    / "fusion_analytics"
    / "api_fusion_metadata.csv"
)


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "fusion_analytics"
)

FINAL_DATASET = (
    OUTPUT_DIR
    / "final_fusion_dataset.csv"
)

API_MATRIX = (
    OUTPUT_DIR
    / "api_feature_matrix.csv"
)

FEATURE_NAMES = (
    OUTPUT_DIR
    / "api_feature_names.json"
)

ENCODER_FILE = (
    OUTPUT_DIR
    / "api_feature_encoder.joblib"
)


# ============================================================
# BASIC IMAGE INFORMATION
# ============================================================

BASE_COLUMNS = [
    "image_path",
    "species",
    "split",
]


# ============================================================
# COMPLETE GBIF INFORMATION
# ============================================================

GBIF_NUMERIC = [
    "gbif_taxon_key",
    "gbif_confidence",
    "gbif_occurrence_count",
    "gbif_country_count",
    "gbif_coordinate_count",
    "gbif_mean_latitude",
    "gbif_mean_longitude",
    "gbif_top_country_records",
]


GBIF_CATEGORICAL = [
    "gbif_canonical_name",
    "gbif_rank",
    "gbif_top_country",
    "gbif_status",
]


# ============================================================
# COMPLETE USDA INFORMATION
# ============================================================

USDA_NUMERIC = [
    "usda_fdc_id",
    "usda_calories",
    "usda_protein",
    "usda_fat",
    "usda_carbohydrate",
]


USDA_CATEGORICAL = [
    "usda_description",
    "usda_status",
]


# ============================================================
# COMPLETE WEATHER INFORMATION
# ============================================================

WEATHER_NUMERIC = [
    "weather_temperature",
    "weather_humidity",
    "weather_pressure",
    "weather_wind_speed",
    "weather_clouds",
]


WEATHER_CATEGORICAL = [
    "weather_description",
    "weather_location",
    "weather_status",
]


# ============================================================
# ALL API FIELDS
# ============================================================

ALL_API_FIELDS = (
    GBIF_NUMERIC
    + GBIF_CATEGORICAL
    + USDA_NUMERIC
    + USDA_CATEGORICAL
    + WEATHER_NUMERIC
    + WEATHER_CATEGORICAL
)


# ============================================================
# HELPER
# ============================================================

def clean_numeric_columns(df, columns):

    for column in columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("BUILDING COMPLETE API FUSION DATASET")
    print("=" * 80)

    print()
    print("Project root:")
    print(PROJECT_ROOT)

    print()
    print("Input:")
    print(API_METADATA)

    print()
    print("Final dataset:")
    print(FINAL_DATASET)

    print()
    print("API feature matrix:")
    print(API_MATRIX)

    # ========================================================
    # CHECK INPUT
    # ========================================================

    if not API_METADATA.exists():

        raise FileNotFoundError(
            "\nAPI metadata file not found:\n"
            + str(API_METADATA)
        )

    # ========================================================
    # READ
    # ========================================================

    df = pd.read_csv(API_METADATA)

    print()
    print(
        f"Input rows: {len(df)}"
    )

    print()
    print(
        f"Input columns: {len(df.columns)}"
    )

    # ========================================================
    # DISPLAY INPUT COLUMNS
    # ========================================================

    print()
    print("=" * 80)
    print("INPUT API COLUMNS")
    print("=" * 80)

    for column in df.columns:

        print(
            f" - {column}"
        )

    # ========================================================
    # CHECK BASE COLUMNS
    # ========================================================

    missing_base = [

        column
        for column in BASE_COLUMNS
        if column not in df.columns

    ]

    if missing_base:

        raise ValueError(
            "\nMissing base columns:\n"
            + "\n".join(missing_base)
        )

    # ========================================================
    # CHECK API COLUMNS
    # ========================================================

    missing_api = [

        column
        for column in ALL_API_FIELDS
        if column not in df.columns

    ]

    if missing_api:

        raise ValueError(
            "\nMissing API columns:\n"
            + "\n".join(missing_api)
        )

    # ========================================================
    # WORKING COPY
    # ========================================================

    working_df = df[
        BASE_COLUMNS + ALL_API_FIELDS
    ].copy()

    # ========================================================
    # NUMERIC CONVERSION
    # ========================================================

    print()
    print("=" * 80)
    print("CONVERTING NUMERICAL API FEATURES")
    print("=" * 80)

    numeric_features = (
        GBIF_NUMERIC
        + USDA_NUMERIC
        + WEATHER_NUMERIC
    )

    working_df = clean_numeric_columns(
        working_df,
        numeric_features
    )

    # ========================================================
    # MISSING NUMERICAL VALUES
    # ========================================================

    print()
    print("Missing numerical values before imputation:")

    print(
        working_df[numeric_features]
        .isna()
        .sum()
        .to_string()
    )

    # ========================================================
    # MEDIAN IMPUTATION
    # ========================================================

    print()
    print(
        "Applying median imputation..."
    )

    for column in numeric_features:

        median = working_df[column].median()

        if pd.isna(median):

            median = 0.0

        working_df[column] = (
            working_df[column]
            .fillna(median)
        )

    # ========================================================
    # CLEAN CATEGORICAL VALUES
    # ========================================================

    categorical_features = (
        GBIF_CATEGORICAL
        + USDA_CATEGORICAL
        + WEATHER_CATEGORICAL
    )

    print()
    print(
        "Cleaning categorical API fields..."
    )

    for column in categorical_features:

        working_df[column] = (
            working_df[column]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
        )

        working_df.loc[
            working_df[column] == "",
            column
        ] = "Unknown"

    # ========================================================
    # SHOW API INFORMATION
    # ========================================================

    print()
    print("=" * 80)
    print("API INFORMATION BEING USED")
    print("=" * 80)

    print()
    print("GBIF numerical:")

    for column in GBIF_NUMERIC:
        print(
            f" - {column}"
        )

    print()
    print("GBIF categorical/status:")

    for column in GBIF_CATEGORICAL:
        print(
            f" - {column}"
        )

    print()
    print("USDA numerical:")

    for column in USDA_NUMERIC:
        print(
            f" - {column}"
        )

    print()
    print("USDA categorical/status:")

    for column in USDA_CATEGORICAL:
        print(
            f" - {column}"
        )

    print()
    print("Weather numerical:")

    for column in WEATHER_NUMERIC:
        print(
            f" - {column}"
        )

    print()
    print("Weather categorical/status:")

    for column in WEATHER_CATEGORICAL:
        print(
            f" - {column}"
        )

    # ========================================================
    # ONE-HOT ENCODING
    # ========================================================

    print()
    print("=" * 80)
    print("ENCODING CATEGORICAL API FEATURES")
    print("=" * 80)

    categorical_df = working_df[
        categorical_features
    ].copy()

    encoder = OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=False
    )

    categorical_matrix = encoder.fit_transform(
        categorical_df
    )

    categorical_names = (
        encoder
        .get_feature_names_out(
            categorical_features
        )
        .tolist()
    )

    print()
    print(
        "Original categorical fields:",
        len(categorical_features)
    )

    print(
        "Encoded categorical dimensions:",
        len(categorical_names)
    )

    # ========================================================
    # NUMERICAL MATRIX
    # ========================================================

    numerical_matrix = (
        working_df[
            numeric_features
        ]
        .to_numpy(
            dtype=float
        )
    )

    # ========================================================
    # STANDARDIZE NUMERICAL FEATURES
    # ========================================================

    print()
    print(
        "Standardizing numerical API features..."
    )

    scaler = StandardScaler()

    numerical_matrix_scaled = (
        scaler.fit_transform(
            numerical_matrix
        )
    )

    # ========================================================
    # COMBINE API FEATURES
    # ========================================================

    api_matrix = np.concatenate(
        [
            numerical_matrix_scaled,
            categorical_matrix,
        ],
        axis=1
    )

    # ========================================================
    # FEATURE NAMES
    # ========================================================

    final_feature_names = (
        [
            f"num_{column}"
            for column in numeric_features
        ]
        + categorical_names
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    print()
    print("=" * 80)
    print("API FEATURE MATRIX")
    print("=" * 80)

    print(
        "Rows:",
        api_matrix.shape[0]
    )

    print(
        "Columns:",
        api_matrix.shape[1]
    )

    print(
        "Feature names:",
        len(final_feature_names)
    )

    if (
        api_matrix.shape[1]
        != len(final_feature_names)
    ):

        raise RuntimeError(
            "Feature matrix and feature names "
            "have different dimensions."
        )

    if np.isnan(api_matrix).any():

        raise RuntimeError(
            "NaN values remain in API matrix."
        )

    if np.isinf(api_matrix).any():

        raise RuntimeError(
            "Infinite values remain in API matrix."
        )

    # ========================================================
    # SAVE DIRECTORY
    # ========================================================

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # SAVE FINAL METADATA DATASET
    # ========================================================

    working_df.to_csv(
        FINAL_DATASET,
        index=False
    )

    # ========================================================
    # SAVE API MATRIX
    # ========================================================

    api_matrix_df = pd.DataFrame(
        api_matrix,
        columns=final_feature_names
    )

    # Keep image identity information
    # alongside the numerical matrix.

    api_matrix_df.insert(
        0,
        "split",
        working_df["split"].values
    )

    api_matrix_df.insert(
        0,
        "species",
        working_df["species"].values
    )

    api_matrix_df.insert(
        0,
        "image_path",
        working_df["image_path"].values
    )

    api_matrix_df.to_csv(
        API_MATRIX,
        index=False
    )

    # ========================================================
    # SAVE FEATURE NAMES
    # ========================================================

    with open(
        FEATURE_NAMES,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            final_feature_names,
            file,
            indent=2
        )

    # ========================================================
    # SAVE ENCODER
    # ========================================================

    joblib.dump(
        {
            "encoder": encoder,
            "scaler": scaler,
            "numeric_features": numeric_features,
            "categorical_features": categorical_features,
            "feature_names": final_feature_names,
        },
        ENCODER_FILE
    )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print()
    print("=" * 80)
    print("COMPLETE API FUSION DATASET CREATED")
    print("=" * 80)

    print()
    print(
        f"Images: {len(working_df)}"
    )

    print(
        f"Original API fields: "
        f"{len(ALL_API_FIELDS)}"
    )

    print(
        f"Numerical API fields: "
        f"{len(numeric_features)}"
    )

    print(
        f"Categorical/status fields: "
        f"{len(categorical_features)}"
    )

    print(
        f"Encoded API dimensions: "
        f"{api_matrix.shape[1]}"
    )

    print()
    print(
        "This means the original API information "
        "was NOT reduced to only 18 features."
    )

    print()
    print("Files created:")

    print(
        "\n1. Full API metadata:"
    )

    print(
        FINAL_DATASET
    )

    print(
        "\n2. Numerical API fusion matrix:"
    )

    print(
        API_MATRIX
    )

    print(
        "\n3. Feature names:"
    )

    print(
        FEATURE_NAMES
    )

    print(
        "\n4. Encoder/scaler:"
    )

    print(
        ENCODER_FILE
    )

    # ========================================================
    # SPECIES DISTRIBUTION
    # ========================================================

    print()
    print("Species distribution:")

    print(
        working_df[
            "species"
        ]
        .value_counts()
        .sort_index()
        .to_string()
    )

    # ========================================================
    # SPLIT DISTRIBUTION
    # ========================================================

    print()
    print("Split distribution:")

    print(
        working_df[
            "split"
        ]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print("=" * 80)
    print("DONE")
    print("=" * 80)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()