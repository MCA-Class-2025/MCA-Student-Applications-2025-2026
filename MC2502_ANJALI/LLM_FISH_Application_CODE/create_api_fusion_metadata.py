# ============================================================
# API-BASED MULTIMODAL FUSION METADATA GENERATOR
# ============================================================
#
# DATA SOURCES
#   1. GBIF
#   2. USDA FoodData Central
#   3. OpenWeatherMap
#
# IMPORTANT:
#   GBIF coordinates represent recorded species occurrences.
#   They are NOT claimed to be the location where each image
#   was photographed.
#
# OUTPUT:
#   data/api_fusion_metadata.csv
#
# ============================================================

from pathlib import Path
import os
import time
import json

import numpy as np
import pandas as pd
import requests

from dotenv import load_dotenv

from gbif_utils import (
    verify_species,
    get_available_countries,
    get_distribution,
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_CSV = (
    PROJECT_ROOT
    / "data"
    / "fusion_metadata.csv"
)

OUTPUT_CSV = (
    PROJECT_ROOT
    / "data"
    / "api_fusion_metadata.csv"
)

CACHE_DIR = (
    PROJECT_ROOT
    / "data"
    / "api_cache"
)

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(
    PROJECT_ROOT / ".env"
)

USDA_API_KEY = os.getenv(
    "USDA_API_KEY"
)

OPENWEATHER_API_KEY = os.getenv(
    "OPENWEATHER_API_KEY"
)


# ============================================================
# SETTINGS
# ============================================================

REQUEST_TIMEOUT = 30

REQUEST_DELAY = 0.25

GBIF_DISTRIBUTION_LIMIT = 100


# ============================================================
# IMPORTANT:
# DATASET LABEL → SCIENTIFIC NAME
# ============================================================
#
# These are the six classes actually present in your dataset.
#
# Confirmed against your existing GBIF utility:
#
#   Pampus argenteus       → GBIF species
#   Labeo rohita           → GBIF species
#   Penaeus indicus        → GBIF species
#   Parastromateus niger   → GBIF species
#
# The published Indian Seafood Fish Dataset identifies:
#
#   Black Snapper → Apsilus dentatus
#   Pink Perch    → Zalembius rosaceus
#
# ============================================================

SPECIES_CONFIG = {

    "Type 1 Pomfret": {

        "scientific_name":
            "Pampus argenteus",

        "usda_query":
            "silver pomfret fish",

    },


    "Type 3 Black Snapper": {

        "scientific_name":
            "Apsilus dentatus",

        "usda_query":
            "black snapper fish",

    },


    "Type 4 Indian Carp": {

        "scientific_name":
            "Labeo rohita",

        "usda_query":
            "rohu fish",

    },


    "Type 5 Prawn": {

        "scientific_name":
            "Penaeus indicus",

        "usda_query":
            "Indian prawn",

    },


    "Type 6 Pink Perch": {

        "scientific_name":
            "Zalembius rosaceus",

        "usda_query":
            "pink perch fish",

    },


    "Type 8 Black Pomfret": {

        "scientific_name":
            "Parastromateus niger",

        "usda_query":
            "black pomfret fish",

    },

}


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update({

    "User-Agent":
        "Fish-AI-Multimodal-Fusion/1.0"

})


# ============================================================
# CACHE FUNCTIONS
# ============================================================

def cache_path(name):

    return CACHE_DIR / name


def read_cache(name):

    path = cache_path(name)

    if not path.exists():
        return None

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return None


def write_cache(name, data):

    path = cache_path(name)

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2
        )


# ============================================================
# USDA
# ============================================================

def get_usda_data(query):

    result = {

        "usda_fdc_id": np.nan,

        "usda_description": "",

        "usda_calories": np.nan,

        "usda_protein": np.nan,

        "usda_fat": np.nan,

        "usda_carbohydrate": np.nan,

        "usda_status":
            "not_requested"

    }


    if not USDA_API_KEY:

        result["usda_status"] = (
            "missing_api_key"
        )

        return result


    safe_name = (
        query
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )

    cache_name = (
        f"usda_{safe_name}.json"
    )


    cached = read_cache(
        cache_name
    )


    if cached is None:

        url = (
            "https://api.nal.usda.gov/fdc/v1/foods/search"
        )

        params = {

            "api_key":
                USDA_API_KEY,

            "query":
                query,

            "pageSize":
                10

        }


        try:

            response = session.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            cached = response.json()

            write_cache(
                cache_name,
                cached
            )

            time.sleep(
                REQUEST_DELAY
            )

        except Exception as error:

            print(
                "USDA error:",
                query,
                error
            )

            result["usda_status"] = (
                "api_error"
            )

            return result


    foods = cached.get(
        "foods",
        []
    )


    if not foods:

        result["usda_status"] = (
            "no_match"
        )

        return result


    # --------------------------------------------------------
    # Prefer a Foundation/SR-like food if available.
    # Otherwise use first returned food.
    # --------------------------------------------------------

    food = foods[0]

    for candidate in foods:

        data_type = str(
            candidate.get(
                "dataType",
                ""
            )
        ).lower()

        if (
            "foundation" in data_type
            or "sr legacy" in data_type
        ):

            food = candidate

            break


    result["usda_fdc_id"] = (
        food.get("fdcId", np.nan)
    )

    result["usda_description"] = (
        food.get("description", "")
    )


    nutrients = food.get(
        "foodNutrients",
        []
    )


    for nutrient in nutrients:

        name = str(
            nutrient.get(
                "nutrientName",
                ""
            )
        ).lower()

        value = nutrient.get(
            "value"
        )


        if value is None:
            continue


        # Energy

        if (
            "energy" in name
            and "kcal" in name
        ):

            result[
                "usda_calories"
            ] = value


        # Protein

        elif "protein" in name:

            result[
                "usda_protein"
            ] = value


        # Fat

        elif (
            "total lipid" in name
            or name == "fat"
        ):

            result[
                "usda_fat"
            ] = value


        # Carbohydrate

        elif (
            "carbohydrate" in name
        ):

            result[
                "usda_carbohydrate"
            ] = value


    result["usda_status"] = (
        "success"
    )

    return result


# ============================================================
# OPENWEATHER
# ============================================================

def get_weather_data(
    latitude,
    longitude
):

    result = {

        "weather_temperature": np.nan,

        "weather_humidity": np.nan,

        "weather_pressure": np.nan,

        "weather_wind_speed": np.nan,

        "weather_clouds": np.nan,

        "weather_description": "",

        "weather_location": "",

        "weather_status":
            "not_requested"

    }


    if not OPENWEATHER_API_KEY:

        result["weather_status"] = (
            "missing_api_key"
        )

        return result


    if (
        latitude is None
        or longitude is None
        or pd.isna(latitude)
        or pd.isna(longitude)
    ):

        result["weather_status"] = (
            "no_coordinates"
        )

        return result


    latitude = float(latitude)

    longitude = float(longitude)


    # Round for caching.

    lat_key = round(
        latitude,
        2
    )

    lon_key = round(
        longitude,
        2
    )


    cache_name = (
        "weather_"
        + str(lat_key)
        .replace("-", "m")
        .replace(".", "_")
        + "_"
        + str(lon_key)
        .replace("-", "m")
        .replace(".", "_")
        + ".json"
    )


    cached = read_cache(
        cache_name
    )


    if cached is None:

        url = (
            "https://api.openweathermap.org/data/2.5/weather"
        )

        params = {

            "lat":
                latitude,

            "lon":
                longitude,

            "appid":
                OPENWEATHER_API_KEY,

            "units":
                "metric"

        }


        try:

            response = session.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            cached = response.json()

            write_cache(
                cache_name,
                cached
            )

            time.sleep(
                REQUEST_DELAY
            )

        except Exception as error:

            print(
                "OpenWeather error:",
                error
            )

            result["weather_status"] = (
                "api_error"
            )

            return result


    main = cached.get(
        "main",
        {}
    )

    wind = cached.get(
        "wind",
        {}
    )

    clouds = cached.get(
        "clouds",
        {}
    )

    weather_list = cached.get(
        "weather",
        []
    )


    result[
        "weather_temperature"
    ] = main.get(
        "temp",
        np.nan
    )


    result[
        "weather_humidity"
    ] = main.get(
        "humidity",
        np.nan
    )


    result[
        "weather_pressure"
    ] = main.get(
        "pressure",
        np.nan
    )


    result[
        "weather_wind_speed"
    ] = wind.get(
        "speed",
        np.nan
    )


    result[
        "weather_clouds"
    ] = clouds.get(
        "all",
        np.nan
    )


    if weather_list:

        result[
            "weather_description"
        ] = weather_list[0].get(
            "description",
            ""
        )


    result[
        "weather_location"
    ] = cached.get(
        "name",
        ""
    )


    result[
        "weather_status"
    ] = "success"


    return result


# ============================================================
# GBIF FEATURES
# ============================================================

def get_gbif_data(
    scientific_name
):

    result = {

        "gbif_taxon_key":
            np.nan,

        "gbif_canonical_name":
            "",

        "gbif_confidence":
            np.nan,

        "gbif_rank":
            "",

        "gbif_occurrence_count":
            np.nan,

        "gbif_country_count":
            np.nan,

        "gbif_coordinate_count":
            np.nan,

        "gbif_mean_latitude":
            np.nan,

        "gbif_mean_longitude":
            np.nan,

        "gbif_top_country":
            "",

        "gbif_top_country_records":
            np.nan,

        "gbif_status":
            "not_requested"

    }


    # --------------------------------------------------------
    # 1. TAXONOMY VERIFICATION
    # --------------------------------------------------------

    taxonomy = verify_species(
        scientific_name
    )


    if taxonomy is None:

        result["gbif_status"] = (
            "no_taxon_match"
        )

        return result


    result[
        "gbif_taxon_key"
    ] = taxonomy.get(
        "gbif_key",
        np.nan
    )


    result[
        "gbif_canonical_name"
    ] = taxonomy.get(
        "canonical_name",
        ""
    )


    result[
        "gbif_confidence"
    ] = taxonomy.get(
        "confidence",
        np.nan
    )


    result[
        "gbif_rank"
    ] = taxonomy.get(
        "rank",
        ""
    )


    # --------------------------------------------------------
    # 2. COUNTRY DISTRIBUTION
    # --------------------------------------------------------

    countries = get_available_countries(
        scientific_name,
        top_n=15
    )


    if countries:

        result[
            "gbif_country_count"
        ] = len(countries)


        result[
            "gbif_top_country"
        ] = countries[0].get(
            "name",
            ""
        )


        result[
            "gbif_top_country_records"
        ] = countries[0].get(
            "count",
            np.nan
        )


    # --------------------------------------------------------
    # 3. OCCURRENCE DISTRIBUTION
    # --------------------------------------------------------

    distribution = get_distribution(

        scientific_name,

        limit=GBIF_DISTRIBUTION_LIMIT

    )


    if distribution is None:

        result[
            "gbif_occurrence_count"
        ] = 0

        result[
            "gbif_coordinate_count"
        ] = 0

        result[
            "gbif_status"
        ] = "taxonomy_only"

        return result


    result[
        "gbif_occurrence_count"
    ] = distribution.get(
        "total_records",
        0
    )


    points = distribution.get(
        "points",
        []
    )


    result[
        "gbif_coordinate_count"
    ] = len(points)


    # --------------------------------------------------------
    # Representative coordinate
    #
    # This is calculated from actual GBIF occurrence records.
    # It is NOT the image capture location.
    # --------------------------------------------------------

    latitudes = []

    longitudes = []


    for point in points:

        lat = point.get(
            "lat"
        )

        lon = point.get(
            "lon"
        )


        if lat is not None:

            latitudes.append(
                float(lat)
            )


        if lon is not None:

            longitudes.append(
                float(lon)
            )


    if latitudes:

        result[
            "gbif_mean_latitude"
        ] = float(
            np.mean(
                latitudes
            )
        )


    if longitudes:

        result[
            "gbif_mean_longitude"
        ] = float(
            np.mean(
                longitudes
            )
        )


    result[
        "gbif_status"
    ] = "success"


    return result


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print(
        "=" * 75
    )

    print(
        "      API MULTIMODAL FUSION METADATA"
    )

    print(
        "=" * 75
    )


    # --------------------------------------------------------
    # Check input
    # --------------------------------------------------------

    if not INPUT_CSV.exists():

        raise FileNotFoundError(
            f"\nInput CSV not found:\n{INPUT_CSV}"
        )


    print()

    print(
        "Input CSV:",
        INPUT_CSV
    )

    print(
        "Output CSV:",
        OUTPUT_CSV
    )


    # --------------------------------------------------------
    # Read dataset
    # --------------------------------------------------------

    df = pd.read_csv(
        INPUT_CSV
    )


    print()

    print(
        "Dataset rows:",
        len(df)
    )


    dataset_species = sorted(
        df["species"]
        .astype(str)
        .unique()
    )


    print()

    print(
        "Dataset species:"
    )


    for species in dataset_species:

        print(
            " -",
            species
        )


    # --------------------------------------------------------
    # Make sure every class has mapping
    # --------------------------------------------------------

    missing = [

        species

        for species
        in dataset_species

        if species
        not in SPECIES_CONFIG

    ]


    if missing:

        raise ValueError(
            "\nMissing species mappings:\n"
            + "\n".join(missing)
        )


    # --------------------------------------------------------
    # Query APIs ONCE PER SPECIES
    # --------------------------------------------------------

    species_data = {}


    for species in dataset_species:

        config = SPECIES_CONFIG[
            species
        ]


        scientific_name = config[
            "scientific_name"
        ]


        print()

        print(
            "-" * 75
        )

        print(
            "Processing:",
            species
        )

        print(
            "Scientific name:",
            scientific_name
        )


        # ====================================================
        # GBIF
        # ====================================================

        print(
            "  Querying GBIF..."
        )


        gbif = get_gbif_data(
            scientific_name
        )


        print(
            "  GBIF:",
            gbif[
                "gbif_status"
            ]
        )


        if (
            gbif[
                "gbif_canonical_name"
            ]
        ):

            print(
                "  Matched:",
                gbif[
                    "gbif_canonical_name"
                ]
            )


        print(
            "  GBIF occurrence count:",
            gbif[
                "gbif_occurrence_count"
            ]
        )


        print(
            "  GBIF coordinate count:",
            gbif[
                "gbif_coordinate_count"
            ]
        )


        # ====================================================
        # USDA
        # ====================================================

        print(
            "  Querying USDA..."
        )


        usda = get_usda_data(

            config[
                "usda_query"
            ]

        )


        print(
            "  USDA:",
            usda[
                "usda_status"
            ]
        )


        if usda[
            "usda_description"
        ]:

            print(
                "  USDA match:",
                usda[
                    "usda_description"
                ]
            )


        # ====================================================
        # WEATHER
        # ====================================================
        #
        # Weather is queried at a representative coordinate
        # derived from actual GBIF occurrence records.
        #
        # It is contextual weather, NOT image-capture weather.
        #
        # ====================================================

        print(
            "  Querying weather..."
        )


        weather = get_weather_data(

            gbif[
                "gbif_mean_latitude"
            ],

            gbif[
                "gbif_mean_longitude"
            ]

        )


        print(
            "  Weather:",
            weather[
                "weather_status"
            ]
        )


        if weather[
            "weather_location"
        ]:

            print(
                "  Weather location:",
                weather[
                    "weather_location"
                ]
            )


        species_data[
            species
        ] = {

            **gbif,

            **usda,

            **weather

        }


    # ========================================================
    # CREATE ROWS
    # ========================================================

    print()

    print(
        "=" * 75
    )

    print(
        "BUILDING OUTPUT DATASET"
    )

    print(
        "=" * 75
    )


    rows = []


    for _, row in df.iterrows():

        species = str(
            row["species"]
        )


        api = species_data[
            species
        ]


        output = {

            # ------------------------------------------------
            # Dataset information
            # ------------------------------------------------

            "image_path":
                row["image_path"],

            "species":
                species,

            "split":
                row["split"],


            # ------------------------------------------------
            # GBIF
            # ------------------------------------------------

            "gbif_taxon_key":
                api[
                    "gbif_taxon_key"
                ],

            "gbif_canonical_name":
                api[
                    "gbif_canonical_name"
                ],

            "gbif_confidence":
                api[
                    "gbif_confidence"
                ],

            "gbif_rank":
                api[
                    "gbif_rank"
                ],

            "gbif_occurrence_count":
                api[
                    "gbif_occurrence_count"
                ],

            "gbif_country_count":
                api[
                    "gbif_country_count"
                ],

            "gbif_coordinate_count":
                api[
                    "gbif_coordinate_count"
                ],

            "gbif_mean_latitude":
                api[
                    "gbif_mean_latitude"
                ],

            "gbif_mean_longitude":
                api[
                    "gbif_mean_longitude"
                ],

            "gbif_top_country":
                api[
                    "gbif_top_country"
                ],

            "gbif_top_country_records":
                api[
                    "gbif_top_country_records"
                ],

            "gbif_status":
                api[
                    "gbif_status"
                ],


            # ------------------------------------------------
            # USDA
            # ------------------------------------------------

            "usda_fdc_id":
                api[
                    "usda_fdc_id"
                ],

            "usda_description":
                api[
                    "usda_description"
                ],

            "usda_calories":
                api[
                    "usda_calories"
                ],

            "usda_protein":
                api[
                    "usda_protein"
                ],

            "usda_fat":
                api[
                    "usda_fat"
                ],

            "usda_carbohydrate":
                api[
                    "usda_carbohydrate"
                ],

            "usda_status":
                api[
                    "usda_status"
                ],


            # ------------------------------------------------
            # WEATHER
            # ------------------------------------------------

            "weather_temperature":
                api[
                    "weather_temperature"
                ],

            "weather_humidity":
                api[
                    "weather_humidity"
                ],

            "weather_pressure":
                api[
                    "weather_pressure"
                ],

            "weather_wind_speed":
                api[
                    "weather_wind_speed"
                ],

            "weather_clouds":
                api[
                    "weather_clouds"
                ],

            "weather_description":
                api[
                    "weather_description"
                ],

            "weather_location":
                api[
                    "weather_location"
                ],

            "weather_status":
                api[
                    "weather_status"
                ],

        }


        rows.append(
            output
        )


    output_df = pd.DataFrame(
        rows
    )


    # ========================================================
    # SAVE
    # ========================================================

    output_df.to_csv(
        OUTPUT_CSV,
        index=False
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print(
        "=" * 75
    )

    print(
        "API FUSION METADATA CREATED"
    )

    print(
        "=" * 75
    )

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
        "Saved:",
        OUTPUT_CSV
    )


    # ========================================================
    # STATUS REPORT
    # ========================================================

    print()

    print(
        "GBIF STATUS:"
    )

    print(
        output_df[
            "gbif_status"
        ].value_counts(
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
        ].value_counts(
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
        ].value_counts(
            dropna=False
        )
    )


    print()

    print(
        "=" * 75
    )

    print(
        "DONE"
    )

    print(
        "=" * 75
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()