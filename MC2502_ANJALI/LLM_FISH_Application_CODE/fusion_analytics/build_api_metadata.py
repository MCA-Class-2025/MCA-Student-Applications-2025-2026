from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PROJECT IMPORTS
# ============================================================

CURRENT_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = CURRENT_DIR.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT CONFIG
# ============================================================

from src.fusion_analytics.config import (
    INPUT_CSV,
    OUTPUT_CSV,
    FUSION_DIR,
    SPECIES_MAP,
    USDA_QUERIES,
    USDA_KEYWORDS,
    USDA_API_KEY,
    OPENWEATHER_API_KEY,
)


# ============================================================
# IMPORT CLIENTS
# ============================================================

from src.fusion_analytics.gbif_client import (
    get_gbif_features,
)

from src.fusion_analytics.usda_client import (
    get_usda_features,
)

from src.fusion_analytics.weather_client import (
    get_weather_features,
)

from src.noaa_utils import (
    get_ocean_environment_for_occurrences,
)


# ============================================================
# NOAA COLUMNS
# ============================================================

NOAA_COLUMNS = [

    "noaa_water_temperature",

    "noaa_salinity",

    "noaa_temperature_min",

    "noaa_temperature_max",

    "noaa_salinity_min",

    "noaa_salinity_max",

]


# ============================================================
# FINAL COLUMN ORDER
# ============================================================

FINAL_COLUMNS = [

    # --------------------------------------------------------
    # ORIGINAL DATASET
    # --------------------------------------------------------

    "image_path",
    "species",
    "split",


    # --------------------------------------------------------
    # GBIF
    # --------------------------------------------------------

    "gbif_taxon_key",
    "gbif_canonical_name",
    "gbif_confidence",
    "gbif_rank",
    "gbif_occurrence_count",
    "gbif_country_count",
    "gbif_coordinate_count",
    "gbif_mean_latitude",
    "gbif_mean_longitude",
    "gbif_top_country",
    "gbif_top_country_records",
    "gbif_status",


    # --------------------------------------------------------
    # USDA
    # --------------------------------------------------------

    "usda_fdc_id",
    "usda_description",
    "usda_calories",
    "usda_protein",
    "usda_fat",
    "usda_carbohydrate",
    "usda_status",


    # --------------------------------------------------------
    # WEATHER
    # --------------------------------------------------------

    "weather_temperature",
    "weather_humidity",
    "weather_pressure",
    "weather_wind_speed",
    "weather_clouds",
    "weather_description",
    "weather_location",
    "weather_status",


    # --------------------------------------------------------
    # NOAA
    # --------------------------------------------------------

    "noaa_water_temperature",
    "noaa_salinity",
    "noaa_temperature_min",
    "noaa_temperature_max",
    "noaa_salinity_min",
    "noaa_salinity_max",

]


# ============================================================
# EMPTY NOAA RESULT
# ============================================================

def empty_noaa_result():

    return {

        "noaa_water_temperature": np.nan,

        "noaa_salinity": np.nan,

        "noaa_temperature_min": np.nan,

        "noaa_temperature_max": np.nan,

        "noaa_salinity_min": np.nan,

        "noaa_salinity_max": np.nan,

    }


# ============================================================
# EXTRACT NUMBER SAFELY
# ============================================================

def safe_float(value):

    try:

        if value is None:
            return np.nan

        if pd.isna(value):
            return np.nan

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return np.nan


# ============================================================
# NOAA FEATURES
# ============================================================

def get_noaa_features(
    latitude,
    longitude,
):

    result = empty_noaa_result()

    try:

        latitude = float(latitude)
        longitude = float(longitude)

    except (
        TypeError,
        ValueError,
    ):

        print(
            "Invalid NOAA coordinates:",
            latitude,
            longitude
        )

        return result

    if not (
        -90 <= latitude <= 90
    ):

        return result

    occurrence = {

        "decimalLatitude":
            latitude,

        "decimalLongitude":
            longitude,

    }

    try:

        noaa = (
            get_ocean_environment_for_occurrences(

                [occurrence],

                max_locations=1,
            )
        )

    except Exception as exc:

        print(
            "NOAA request failed:"
        )

        print(
            type(exc).__name__,
            exc
        )

        return result

    if not isinstance(
        noaa,
        dict
    ):

        return result

    # --------------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------------

    result[
        "noaa_water_temperature"
    ] = safe_float(
        noaa.get(
            "temperature"
        )
    )

    # --------------------------------------------------------
    # SALINITY
    # --------------------------------------------------------

    result[
        "noaa_salinity"
    ] = safe_float(
        noaa.get(
            "salinity"
        )
    )

    # --------------------------------------------------------
    # TEMPERATURE RANGE
    # --------------------------------------------------------

    temperature_range = (
        noaa.get(
            "temperature_range"
        )
    )

    if isinstance(
        temperature_range,
        dict
    ):

        result[
            "noaa_temperature_min"
        ] = safe_float(
            temperature_range.get(
                "min"
            )
        )

        result[
            "noaa_temperature_max"
        ] = safe_float(
            temperature_range.get(
                "max"
            )
        )

    # --------------------------------------------------------
    # SALINITY RANGE
    # --------------------------------------------------------

    salinity_range = (
        noaa.get(
            "salinity_range"
        )
    )

    if isinstance(
        salinity_range,
        dict
    ):

        result[
            "noaa_salinity_min"
        ] = safe_float(
            salinity_range.get(
                "min"
            )
        )

        result[
            "noaa_salinity_max"
        ] = safe_float(
            salinity_range.get(
                "max"
            )
        )

    print()
    print(
        "NOAA RESULT:"
    )

    print(
        "  Temperature:",
        result[
            "noaa_water_temperature"
        ]
    )

    print(
        "  Salinity:",
        result[
            "noaa_salinity"
        ]
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print("=" * 75)

    print(
        "BUILDING COMPLETE API FUSION METADATA"
    )

    print("=" * 75)


    # ========================================================
    # LOAD DATASET
    # ========================================================

    print()

    print(
        "Input:",
        INPUT_CSV,
    )


    print(
        "Output:",
        OUTPUT_CSV,
    )


    df = pd.read_csv(
        INPUT_CSV
    )


    print()

    print(
        "Dataset rows:",
        len(df),
    )


    # ========================================================
    # VALIDATE REQUIRED COLUMNS
    # ========================================================

    required_columns = [

        "image_path",
        "species",
        "split",

    ]


    missing = [

        column

        for column in required_columns

        if column not in df.columns

    ]


    if missing:

        raise ValueError(

            "Missing required columns: "

            + str(missing)

        )


    # ========================================================
    # SPECIES CHECK
    # ========================================================

    unknown_species = (

        set(
            df["species"]
            .dropna()
            .unique()
        )

        -

        set(
            SPECIES_MAP.keys()
        )

    )


    if unknown_species:

        raise ValueError(

            "Unknown species found: "

            + str(
                unknown_species
            )

        )


    # ========================================================
    # API CACHE
    #
    # One GBIF + USDA + Weather call per species.
    #
    # NOAA is also called only once per unique
    # GBIF coordinate.
    # ========================================================

    api_cache = {}


    # ========================================================
    # PROCESS SPECIES
    # ========================================================

    for species in sorted(
        df["species"]
        .dropna()
        .unique()
    ):

        print()

        print("-" * 75)

        print(
            "Processing:",
            species,
        )


        scientific_name = SPECIES_MAP[
            species
        ]


        print(
            "Scientific name:",
            scientific_name,
        )


        # ====================================================
        # GBIF
        # ====================================================

        print()

        print(
            "GBIF..."
        )


        gbif = get_gbif_features(
            scientific_name
        )


        print(

            "GBIF:",

            gbif.get(
                "gbif_status"
            ),

            "| occurrences:",

            gbif.get(
                "gbif_occurrence_count"
            ),

            "| coordinates:",

            gbif.get(
                "gbif_coordinate_count"
            ),

        )


        # ====================================================
        # USDA
        # ====================================================

        print()

        print(
            "USDA..."
        )


        try:

            usda = get_usda_features(

                api_key=
                    USDA_API_KEY,

                query=
                    USDA_QUERIES[
                        species
                    ],

                keywords=
                    USDA_KEYWORDS[
                        species
                    ],

            )

        except Exception as exc:

            print(
                "USDA error:",
                exc
            )


            usda = {

                "usda_fdc_id": 0,

                "usda_description": "",

                "usda_calories": 0.0,

                "usda_protein": 0.0,

                "usda_fat": 0.0,

                "usda_carbohydrate": 0.0,

                "usda_status":
                    "api_error",

            }


        print(

            "USDA:",

            usda.get(
                "usda_status"
            ),

            "| match:",

            usda.get(
                "usda_description"
            ),

        )


        # ====================================================
        # WEATHER
        # ====================================================

        print()

        print(
            "Weather..."
        )


        latitude = gbif.get(
            "gbif_mean_latitude"
        )


        longitude = gbif.get(
            "gbif_mean_longitude"
        )


        weather = get_weather_features(

            api_key=
                OPENWEATHER_API_KEY,

            latitude=
                latitude,

            longitude=
                longitude,

        )


        print(

            "Weather:",

            weather.get(
                "weather_status"
            ),

            "| location:",

            weather.get(
                "weather_location"
            ),

        )


        # ====================================================
        # STORE RESULT
        # ====================================================

        api_cache[
            species
        ] = {

            **gbif,

            **usda,

            **weather,

        }


    # ========================================================
    # NOAA
    #
    # IMPORTANT:
    #
    # NOAA is NOT called once per image.
    #
    # We first find unique GBIF coordinates.
    # ========================================================

    print()

    print("=" * 75)

    print(
        "ADDING NOAA OCEAN FEATURES"
    )

    print("=" * 75)


    coordinate_columns = [

        "gbif_mean_latitude",

        "gbif_mean_longitude",

    ]


    coordinate_df = (

        pd.DataFrame([

            {

                "species":
                    species,

                "latitude":
                    api_cache[
                        species
                    ].get(
                        "gbif_mean_latitude"
                    ),

                "longitude":
                    api_cache[
                        species
                    ].get(
                        "gbif_mean_longitude"
                    ),

            }

            for species in api_cache

        ])

    )


    coordinate_df = (

        coordinate_df[

            [
                "latitude",
                "longitude",
            ]

        ]

        .dropna()

        .drop_duplicates()

        .reset_index(
            drop=True
        )

    )


    print()

    print(
        "Unique NOAA locations:",
        len(coordinate_df)
    )


    # ========================================================
    # NOAA CACHE
    # ========================================================

    noaa_cache = {}


    # ========================================================
    # QUERY NOAA
    # ========================================================

    for _, location in coordinate_df.iterrows():

        latitude = float(
            location["latitude"]
        )

        longitude = float(
            location["longitude"]
        )


        cache_key = (

            round(latitude, 6),

            round(longitude, 6),

        )


        print()

        print(
            "NOAA location:",
            latitude,
            longitude,
        )


        noaa_features = get_noaa_features(

            latitude,

            longitude,

        )


        noaa_cache[
            cache_key
        ] = noaa_features


        print(

            "NOAA temperature:",

            noaa_features[
                "noaa_water_temperature"
            ],

        )


        print(

            "NOAA salinity:",

            noaa_features[
                "noaa_salinity"
            ],

        )


    # ========================================================
    # ATTACH NOAA TO SPECIES CACHE
    # ========================================================

    for species in api_cache:

        latitude = api_cache[
            species
        ].get(
            "gbif_mean_latitude"
        )


        longitude = api_cache[
            species
        ].get(
            "gbif_mean_longitude"
        )


        latitude = safe_float(
            latitude
        )

        longitude = safe_float(
            longitude
        )


        if (
            pd.isna(latitude)
            or pd.isna(longitude)
        ):

            noaa_features = (
                empty_noaa_result()
            )

        else:

            cache_key = (

                round(
                    latitude,
                    6
                ),

                round(
                    longitude,
                    6
                ),

            )


            noaa_features = noaa_cache.get(

                cache_key,

                empty_noaa_result(),

            )


        api_cache[
            species
        ].update(
            noaa_features
        )


    # ========================================================
    # ATTACH EVERYTHING TO EVERY IMAGE
    # ========================================================

    print()

    print(
        "Attaching API features to",
        len(df),
        "images..."
    )


    records = []


    for _, row in df.iterrows():

        species = row[
            "species"
        ]


        api_features = api_cache[
            species
        ]


        record = {

            "image_path":
                row[
                    "image_path"
                ],

            "species":
                species,

            "split":
                row[
                    "split"
                ],

            **api_features,

        }


        records.append(
            record
        )


    output_df = pd.DataFrame(
        records
    )


    # ========================================================
    # FORCE COLUMN ORDER
    # ========================================================

    # Check that all expected columns exist.

    for column in FINAL_COLUMNS:

        if column not in output_df.columns:

            output_df[
                column
            ] = np.nan


    output_df = output_df[
        FINAL_COLUMNS
    ]


    # ========================================================
    # SAVE
    # ========================================================

    FUSION_DIR.mkdir(

        parents=True,

        exist_ok=True,

    )


    output_df.to_csv(

        OUTPUT_CSV,

        index=False,

    )


    # ========================================================
    # REPORT
    # ========================================================

    print()

    print("=" * 75)

    print(
        "COMPLETE FUSED DATASET CREATED"
    )

    print("=" * 75)


    print()

    print(
        "Rows:",
        len(output_df)
    )


    print(
        "Columns:",
        len(output_df.columns)
    )


    print()

    print(
        "Saved:"
    )


    print(
        OUTPUT_CSV
    )


    # ========================================================
    # NOAA REPORT
    # ========================================================

    print()

    print(
        "NOAA DATA CHECK"
    )


    for column in NOAA_COLUMNS:

        valid_count = (

            output_df[
                column
            ]

            .notna()

            .sum()

        )


        print(

            f"{column}: "
            f"{valid_count}/"
            f"{len(output_df)} "
            f"valid values"

        )


    print()

    print(
        "NOAA SAMPLE:"
    )


    print(

        output_df[

            [

                "species",

                "gbif_mean_latitude",

                "gbif_mean_longitude",

                "noaa_water_temperature",

                "noaa_salinity",

                "noaa_temperature_min",

                "noaa_temperature_max",

                "noaa_salinity_min",

                "noaa_salinity_max",

            ]

        ]

        .drop_duplicates()

        .to_string(
            index=False
        )

    )


    # ========================================================
    # STATUS REPORTS
    # ========================================================

    print()

    print(
        "GBIF STATUS:"
    )


    print(

        output_df[
            "gbif_status"
        ]

        .value_counts(
            dropna=False
        )

    )


    print()

    print(
        "USDA STATUS:"
    )


    print(

        output_df[
            "usda_status"
        ]

        .value_counts(
            dropna=False
        )

    )


    print()

    print(
        "WEATHER STATUS:"
    )


    print(

        output_df[
            "weather_status"
        ]

        .value_counts(
            dropna=False
        )

    )


    print()

    print("=" * 75)

    print(
        "DONE"
    )

    print("=" * 75)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()