import pandas as pd
import requests
from pathlib import Path
from time import sleep


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

ORIGINAL_FILE = BASE_DIR / "data" / "building_defect_knowledge.csv"

OUTPUT_DIR = BASE_DIR / "data"

FUSED_FILE = OUTPUT_DIR / "fixai_fused_dataset.csv"
VALIDATION_FILE = OUTPUT_DIR / "fusion_validation.csv"
QUALITY_FILE = OUTPUT_DIR / "data_quality_report.csv"


# =========================================================
# YOUR CUSTOM REST API
# =========================================================

FASTAPI_URL = "http://127.0.0.1:8000"


# =========================================================
# OPEN-METEO APIs
# =========================================================

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

AIR_QUALITY_URL = (
    "https://air-quality-api.open-meteo.com/v1/air-quality"
)


# =========================================================
# 10 MAHARASHTRA STUDY LOCATIONS
# =========================================================

# Two original defect records will be enriched with each
# location. The location is explicitly marked as API context.

STUDY_LOCATIONS = [
    {
        "city": "Mumbai",
        "latitude": 19.0760,
        "longitude": 72.8777
    },
    {
        "city": "Thane",
        "latitude": 19.2183,
        "longitude": 72.9781
    },
    {
        "city": "Navi Mumbai",
        "latitude": 19.0330,
        "longitude": 73.0297
    },
    {
        "city": "Pune",
        "latitude": 18.5204,
        "longitude": 73.8567
    },
    {
        "city": "Nagpur",
        "latitude": 21.1458,
        "longitude": 79.0882
    },
    {
        "city": "Nashik",
        "latitude": 20.0059,
        "longitude": 73.7629
    },
    {
        "city": "Chhatrapati Sambhajinagar",
        "latitude": 19.8762,
        "longitude": 75.3433
    },
    {
        "city": "Vasai-Virar",
        "latitude": 19.3919,
        "longitude": 72.8397
    },
    {
        "city": "Mira-Bhayandar",
        "latitude": 19.2952,
        "longitude": 72.8544
    },
    {
        "city": "Panvel",
        "latitude": 18.9894,
        "longitude": 73.1175
    }
]


# =========================================================
# SERVICE MAPPING
# =========================================================

def map_service_type(
    defect,
    element,
    work_type
):

    text = " ".join([
        str(defect),
        str(element),
        str(work_type)
    ]).lower()


    if any(
        word in text
        for word in [
            "leak",
            "plumb",
            "seepage",
            "water"
        ]
    ):
        return "plumber"


    if any(
        word in text
        for word in [
            "electrical",
            "electric",
            "wiring"
        ]
    ):
        return "electrician"


    if any(
        word in text
        for word in [
            "waterproof",
            "damp",
            "moisture"
        ]
    ):
        return "waterproofing"


    if any(
        word in text
        for word in [
            "wall",
            "plaster",
            "render",
            "detachment",
            "paint",
            "masonry",
            "crack"
        ]
    ):
        return "wall_repair"


    if any(
        word in text
        for word in [
            "wood",
            "carpenter",
            "timber"
        ]
    ):
        return "carpenter"


    if any(
        word in text
        for word in [
            "roof",
            "roofing"
        ]
    ):
        return "roofer"


    if any(
        word in text
        for word in [
            "paint",
            "painting"
        ]
    ):
        return "painter"


    return "handyman"


# =========================================================
# BATCH API REQUEST HELPER
# =========================================================

def batch_request(
    url,
    params,
    attempts=3,
    timeout=60
):

    last_error = None


    for attempt in range(1, attempts + 1):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=timeout
            )

            response.raise_for_status()

            return response.json()


        except Exception as error:

            last_error = error

            print(
                f"Attempt {attempt}/{attempts} failed: "
                f"{error}"
            )

            if attempt < attempts:

                sleep(3)


    print(
        f"API request failed after {attempts} attempts."
    )

    return None


# =========================================================
# WEATHER — ONE BATCH REQUEST FOR ALL LOCATIONS
# =========================================================

def get_all_weather():

    latitudes = ",".join(
        str(x["latitude"])
        for x in STUDY_LOCATIONS
    )

    longitudes = ",".join(
        str(x["longitude"])
        for x in STUDY_LOCATIONS
    )


    params = {

        "latitude":
            latitudes,

        "longitude":
            longitudes,

        "current":
            (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation"
            ),

        "daily":
            (
                "precipitation_sum,"
                "temperature_2m_max,"
                "temperature_2m_min"
            ),

        "timezone":
            "auto"
    }


    data = batch_request(
        WEATHER_URL,
        params
    )


    if data is None:
        return {}


    # Multiple coordinate queries return a list.
    if isinstance(data, list):

        responses = data

    else:

        responses = [data]


    weather_by_city = {}


    for index, item in enumerate(responses):

        if index >= len(
            STUDY_LOCATIONS
        ):
            break


        location = STUDY_LOCATIONS[index]

        current = item.get(
            "current",
            {}
        )

        daily = item.get(
            "daily",
            {}
        )


        weather_by_city[
            location["city"]
        ] = {

            "temperature":
                current.get(
                    "temperature_2m"
                ),

            "humidity":
                current.get(
                    "relative_humidity_2m"
                ),

            "precipitation":
                current.get(
                    "precipitation"
                ),

            "daily_rainfall":
                (
                    daily.get(
                        "precipitation_sum",
                        [None]
                    )[0]
                ),

            "daily_max_temperature":
                (
                    daily.get(
                        "temperature_2m_max",
                        [None]
                    )[0]
                ),

            "daily_min_temperature":
                (
                    daily.get(
                        "temperature_2m_min",
                        [None]
                    )[0]
                )
        }


    return weather_by_city


# =========================================================
# AIR QUALITY — ONE BATCH REQUEST FOR ALL LOCATIONS
# =========================================================

def get_all_air_quality():

    latitudes = ",".join(
        str(x["latitude"])
        for x in STUDY_LOCATIONS
    )

    longitudes = ",".join(
        str(x["longitude"])
        for x in STUDY_LOCATIONS
    )


    params = {

        "latitude":
            latitudes,

        "longitude":
            longitudes,

        "current":
            (
                "pm10,"
                "pm2_5,"
                "carbon_monoxide,"
                "nitrogen_dioxide,"
                "ozone,"
                "us_aqi"
            ),

        "timezone":
            "auto"
    }


    data = batch_request(
        AIR_QUALITY_URL,
        params,
        attempts=4,
        timeout=90
    )


    if data is None:
        return {}


    if isinstance(data, list):

        responses = data

    else:

        responses = [data]


    air_by_city = {}


    for index, item in enumerate(responses):

        if index >= len(
            STUDY_LOCATIONS
        ):
            break


        location = STUDY_LOCATIONS[index]


        current = item.get(
            "current",
            {}
        )


        air_by_city[
            location["city"]
        ] = {

            "pm10":
                current.get(
                    "pm10"
                ),

            "pm2_5":
                current.get(
                    "pm2_5"
                ),

            "carbon_monoxide":
                current.get(
                    "carbon_monoxide"
                ),

            "nitrogen_dioxide":
                current.get(
                    "nitrogen_dioxide"
                ),

            "ozone":
                current.get(
                    "ozone"
                ),

            "us_aqi":
                current.get(
                    "us_aqi"
                )
        }


    return air_by_city


# =========================================================
# YOUR CUSTOM PROFESSIONAL API
# =========================================================

def get_professionals(
    service_type,
    city
):

    # First try service + city
    response = requests.get(

        f"{FASTAPI_URL}/professionals",

        params={
            "service_type": service_type,
            "city": city,
            "limit": 100
        },

        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    professionals = data.get(
        "professionals",
        []
    )


    # If no professional exists in that city,
    # fall back to service type.

    if not professionals:

        response = requests.get(

            f"{FASTAPI_URL}/professionals",

            params={
                "service_type": service_type,
                "limit": 100
            },

            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        professionals = data.get(
            "professionals",
            []
        )


    return professionals


# =========================================================
# SELECT BEST PROFESSIONAL
# =========================================================

def select_best_professional(
    professionals
):

    if not professionals:

        return None


    # Prefer highest rating,
    # then experience.

    professionals = sorted(

        professionals,

        key=lambda x: (

            -float(
                x.get(
                    "rating",
                    0
                )
            ),

            -int(
                x.get(
                    "experience",
                    0
                )
            )
        )
    )


    return professionals[0]


# =========================================================
# MAIN
# =========================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    print("=" * 70)

    print(
        "FIXAI PHASE 1 — CONTEXTUAL DATA FUSION"
    )

    print("=" * 70)


    # =====================================================
    # LOAD ORIGINAL DATA
    # =====================================================

    original = pd.read_csv(
        ORIGINAL_FILE
    )


    original.columns = [

        column.strip().lower()

        for column
        in original.columns
    ]


    print(
        f"\nOriginal records: "
        f"{len(original)}"
    )

    print(
        f"Original attributes: "
        f"{len(original.columns)}"
    )


    required = [
        "defect",
        "element",
        "work_type"
    ]


    missing = [

        c for c in required

        if c not in original.columns
    ]


    if missing:

        raise ValueError(
            "Required columns missing: "
            + ", ".join(missing)
        )


    # =====================================================
    # MAP SERVICE
    # =====================================================

    original[
        "service_type"
    ] = original.apply(

        lambda row:
            map_service_type(

                row["defect"],

                row["element"],

                row["work_type"]
            ),

        axis=1
    )


    print(
        "\nService mapping:"
    )

    print(
        original[
            "service_type"
        ]
        .value_counts()
    )


    # =====================================================
    # COLLECT WEATHER ONCE
    # =====================================================

    print(
        "\nCollecting weather data for "
        f"{len(STUDY_LOCATIONS)} locations..."
    )

    weather_by_city = (
        get_all_weather()
    )


    print(
        f"Weather locations collected: "
        f"{len(weather_by_city)}"
    )


    # =====================================================
    # COLLECT AIR QUALITY ONCE
    # =====================================================

    print(
        "\nCollecting air-quality data for "
        f"{len(STUDY_LOCATIONS)} locations..."
    )

    air_by_city = (
        get_all_air_quality()
    )


    print(
        f"Air-quality locations collected: "
        f"{len(air_by_city)}"
    )


    # =====================================================
    # GET ONE PROFESSIONAL PER
    # SERVICE + CITY CONTEXT
    # =====================================================

    professional_cache = {}


    for location in STUDY_LOCATIONS:

        city = location[
            "city"
        ]


        service_types = (
            original[
                "service_type"
            ]
            .dropna()
            .unique()
            .tolist()
        )


        for service_type in service_types:

            key = (
                service_type,
                city
            )


            print(
                f"Professional API: "
                f"{service_type} / {city}"
            )


            try:

                professionals = (
                    get_professionals(

                        service_type,

                        city
                    )
                )


                selected = (
                    select_best_professional(
                        professionals
                    )
                )


                professional_cache[
                    key
                ] = selected


            except Exception as error:

                print(
                    f"Professional API error: "
                    f"{error}"
                )

                professional_cache[
                    key
                ] = None


    # =====================================================
    # BUILD 20 ROWS
    # =====================================================

    fused_rows = []


    # Assign the 20 original observations to
    # the 10 study locations, two observations
    # per location.

    for index, (_, row) in enumerate(
        original.iterrows()
    ):

        location = (
            STUDY_LOCATIONS[
                index % len(
                    STUDY_LOCATIONS
                )
            ]
        )


        city = location[
            "city"
        ]


        service_type = row[
            "service_type"
        ]


        weather = (
            weather_by_city.get(
                city,
                {}
            )
        )


        air = (
            air_by_city.get(
                city,
                {}
            )
        )


        professional = (
            professional_cache.get(
                (
                    service_type,
                    city
                )
            )
        )


        # -------------------------------------------------
        # START WITH ORIGINAL RECORD
        # -------------------------------------------------

        fused_row = row.to_dict()


        # -------------------------------------------------
        # API CONTEXT
        # -------------------------------------------------

        fused_row[
            "api_context_city"
        ] = city


        fused_row[
            "api_context_latitude"
        ] = location[
            "latitude"
        ]


        fused_row[
            "api_context_longitude"
        ] = location[
            "longitude"
        ]


        # -------------------------------------------------
        # WEATHER
        # -------------------------------------------------

        fused_row[
            "weather_temperature"
        ] = weather.get(
            "temperature"
        )


        fused_row[
            "weather_humidity"
        ] = weather.get(
            "humidity"
        )


        fused_row[
            "weather_precipitation"
        ] = weather.get(
            "precipitation"
        )


        fused_row[
            "weather_daily_rainfall"
        ] = weather.get(
            "daily_rainfall"
        )


        fused_row[
            "weather_daily_max_temperature"
        ] = weather.get(
            "daily_max_temperature"
        )


        fused_row[
            "weather_daily_min_temperature"
        ] = weather.get(
            "daily_min_temperature"
        )


        # -------------------------------------------------
        # AIR QUALITY
        # -------------------------------------------------

        fused_row[
            "air_pm2_5"
        ] = air.get(
            "pm2_5"
        )


        fused_row[
            "air_pm10"
        ] = air.get(
            "pm10"
        )


        fused_row[
            "air_us_aqi"
        ] = air.get(
            "us_aqi"
        )


        fused_row[
            "air_ozone"
        ] = air.get(
            "ozone"
        )


        fused_row[
            "air_nitrogen_dioxide"
        ] = air.get(
            "nitrogen_dioxide"
        )


        fused_row[
            "air_carbon_monoxide"
        ] = air.get(
            "carbon_monoxide"
        )


        # -------------------------------------------------
        # CUSTOM API PROFESSIONAL
        # -------------------------------------------------

        if professional:

            fused_row[
                "professional_id"
            ] = professional.get(
                "id"
            )


            fused_row[
                "professional_name"
            ] = professional.get(
                "name"
            )


            fused_row[
                "professional_service_type"
            ] = professional.get(
                "service_type"
            )


            fused_row[
                "professional_city"
            ] = professional.get(
                "city"
            )


            fused_row[
                "professional_area"
            ] = professional.get(
                "area"
            )


            fused_row[
                "professional_phone"
            ] = professional.get(
                "phone"
            )


            fused_row[
                "professional_rating"
            ] = professional.get(
                "rating"
            )


            fused_row[
                "professional_experience"
            ] = professional.get(
                "experience"
            )


            fused_row[
                "professional_price_range"
            ] = professional.get(
                "price_range"
            )


            fused_row[
                "professional_latitude"
            ] = professional.get(
                "latitude"
            )


            fused_row[
                "professional_longitude"
            ] = professional.get(
                "longitude"
            )

        else:

            for field in [

                "professional_id",
                "professional_name",
                "professional_service_type",
                "professional_city",
                "professional_area",
                "professional_phone",
                "professional_rating",
                "professional_experience",
                "professional_price_range",
                "professional_latitude",
                "professional_longitude"

            ]:

                fused_row[
                    field
                ] = None


        fused_rows.append(
            fused_row
        )


    # =====================================================
    # FUSED DATAFRAME
    # =====================================================

    fused = pd.DataFrame(
        fused_rows
    )


    # =====================================================
    # SAVE FUSED DATASET
    # =====================================================

    fused.to_csv(
        FUSED_FILE,
        index=False
    )


    # =====================================================
    # VALIDATION
    # =====================================================

    validation = pd.DataFrame({

        "parameter": [

            "Original records",

            "Original attributes",

            "Fused records",

            "Fused attributes",

            "Unique service types",

            "Study locations",

            "Weather locations successfully collected",

            "Air-quality locations successfully collected",

            "Professional matches",

            "Missing professional matches",

            "Duplicate original rows",

            "Duplicate fused rows",

            "Missing weather values",

            "Missing air-quality values"

        ],

        "value": [

            len(original),

            len(original.columns),

            len(fused),

            len(fused.columns),

            fused[
                "service_type"
            ].nunique(),

            len(
                STUDY_LOCATIONS
            ),

            len(
                weather_by_city
            ),

            len(
                air_by_city
            ),

            int(
                fused[
                    "professional_id"
                ]
                .notna()
                .sum()
            ),

            int(
                fused[
                    "professional_id"
                ]
                .isna()
                .sum()
            ),

            int(
                original
                .duplicated()
                .sum()
            ),

            int(
                fused
                .duplicated()
                .sum()
            ),

            int(
                fused[
                    "weather_temperature"
                ]
                .isna()
                .sum()
            ),

            int(
                fused[
                    "air_pm2_5"
                ]
                .isna()
                .sum()
            )
        ]
    })


    validation.to_csv(
        VALIDATION_FILE,
        index=False
    )


    # =====================================================
    # DATA QUALITY REPORT
    # =====================================================

    quality_rows = []


    for column in fused.columns:

        missing_count = int(
            fused[
                column
            ]
            .isna()
            .sum()
        )


        quality_rows.append({

            "attribute":
                column,

            "data_type":
                str(
                    fused[
                        column
                    ].dtype
                ),

            "unique_values":
                int(
                    fused[
                        column
                    ].nunique()
                ),

            "missing_values":
                missing_count,

            "missing_percentage":
                round(
                    (
                        missing_count
                        /
                        len(fused)
                        *
                        100
                    ),
                    2
                )
        })


    quality = pd.DataFrame(
        quality_rows
    )


    quality.to_csv(
        QUALITY_FILE,
        index=False
    )


    # =====================================================
    # PRINT PREVIEW
    # =====================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "FUSION COMPLETE"
    )

    print(
        "=" * 70
    )


    print(
        f"\nRows: {len(fused)}"
    )

    print(
        f"Columns: {len(fused.columns)}"
    )

    print(
        f"Professional matches: "
        f"{fused['professional_id'].notna().sum()}/"
        f"{len(fused)}"
    )


    print(
        "\nAPI context distribution:"
    )

    print(
        fused[
            "api_context_city"
        ].value_counts()
    )


    print(
        "\nCreated:"
    )

    print(
        FUSED_FILE
    )

    print(
        VALIDATION_FILE
    )

    print(
        QUALITY_FILE
    )


if __name__ == "__main__":

    main()
