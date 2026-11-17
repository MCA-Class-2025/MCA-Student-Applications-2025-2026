import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv


# ============================================================
# OPENAQ AIR QUALITY API DATA COLLECTION
# ============================================================

load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")

BASE_URL = "https://api.openaq.org/v3"

INPUT_FILE = "data/rest_countries.csv"
OUTPUT_FILE = "data/openaq_air_quality.csv"
VALIDATION_FILE = "data/openaq_validation.csv"


# OpenAQ parameter IDs
# 1  = PM10
# 2  = PM2.5
# 15 = NO2
# 32 = O3

TARGET_POLLUTANTS = {
    1: "PM10",
    2: "PM2.5",
    15: "NO2",
    32: "O3"
}


# ============================================================
# API REQUEST
# ============================================================

def api_get(endpoint, params=None, retries=3):

    url = f"{BASE_URL}{endpoint}"

    headers = {
        "X-API-Key": API_KEY,
        "Accept": "application/json"
    }

    for attempt in range(1, retries + 1):

        try:

            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )

            if response.status_code == 429:

                wait_time = 5 * attempt

                print(
                    f"Rate limit reached. "
                    f"Waiting {wait_time} seconds..."
                )

                time.sleep(wait_time)

                continue

            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as error:

            if attempt == retries:
                raise

            print(
                f"Request failed "
                f"(attempt {attempt}/{retries}): {error}"
            )

            time.sleep(2 * attempt)

    return None


# ============================================================
# LOAD REST COUNTRIES
# ============================================================

def load_country_data():

    print("Loading REST Countries data...")

    df = pd.read_csv(INPUT_FILE)

    print(
        f"REST Countries records loaded: {len(df)}"
    )

    required_columns = [
        "Country Name",
        "ISO Alpha-2",
        "ISO Alpha-3"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing required columns: "
            f"{missing_columns}"
        )

    # Normalize ISO codes
    df["ISO Alpha-2"] = (
        df["ISO Alpha-2"]
        .astype("string")
        .str.upper()
        .str.strip()
    )

    df["ISO Alpha-3"] = (
        df["ISO Alpha-3"]
        .astype("string")
        .str.upper()
        .str.strip()
    )

    return df


# ============================================================
# GET OPENAQ LOCATIONS
# ============================================================

def get_locations():

    print()
    print(
        "Retrieving air-quality monitoring locations..."
    )

    all_locations = []

    page = 1

    while True:

        print(
            f"Requesting locations page {page}..."
        )

        data = api_get(
            "/locations",
            params={
                "parameters_id": "1,2,15,32",
                "limit": 1000,
                "page": page
            }
        )

        if not data:
            break

        results = data.get(
            "results",
            []
        )

        if not results:
            break

        all_locations.extend(results)

        print(
            f"  Locations received: {len(results)}"
        )

        meta = data.get(
            "meta",
            {}
        )

        found = meta.get(
            "found"
        )

        if found is not None:

            try:

                if len(all_locations) >= int(found):
                    break

            except (
                ValueError,
                TypeError
            ):

                pass

        if len(results) < 1000:
            break

        page += 1

    print()
    print(
        f"Total OpenAQ locations retrieved: "
        f"{len(all_locations)}"
    )

    return all_locations


# ============================================================
# BUILD SENSOR MAPPING
# ============================================================

def build_sensor_mapping(locations):

    print()
    print(
        "Building sensor-to-pollutant mapping..."
    )

    records = []

    for location in locations:

        location_id = location.get(
            "id"
        )

        sensors = location.get(
            "sensors",
            []
        )

        if not isinstance(
            sensors,
            list
        ):
            continue

        for sensor in sensors:

            sensor_id = sensor.get(
                "id"
            )

            parameter = sensor.get(
                "parameter",
                {}
            )

            if not isinstance(
                parameter,
                dict
            ):
                continue

            parameter_id = parameter.get(
                "id"
            )

            parameter_name = parameter.get(
                "name"
            )

            units = parameter.get(
                "units"
            )

            pollutant = TARGET_POLLUTANTS.get(
                parameter_id
            )

            if sensor_id is None:
                continue

            if pollutant is None:
                continue

            records.append({
                "Sensor ID": sensor_id,
                "Location ID": location_id,
                "Pollutant": pollutant,
                "Parameter ID": parameter_id,
                "Parameter Name": parameter_name,
                "Unit": units
            })

    mapping_df = pd.DataFrame(
        records
    )

    if mapping_df.empty:

        raise ValueError(
            "No PM2.5, PM10, NO2 or O3 sensors "
            "were found."
        )

    mapping_df = (
        mapping_df
        .drop_duplicates(
            subset=["Sensor ID"]
        )
        .reset_index(drop=True)
    )

    print(
        f"Target pollutant sensors mapped: "
        f"{len(mapping_df)}"
    )

    print()
    print(
        "Pollutant sensor counts:"
    )

    print(
        mapping_df[
            "Pollutant"
        ]
        .value_counts()
        .to_string()
    )

    return mapping_df


# ============================================================
# SELECT ONE REPRESENTATIVE LOCATION PER COUNTRY
# ============================================================

def select_country_locations(
    locations,
    country_df
):

    print()
    print(
        "Selecting representative air-quality locations..."
    )

    valid_iso2 = set(
        country_df[
            "ISO Alpha-2"
        ]
        .dropna()
        .astype(str)
        .str.upper()
        .str.strip()
    )

    candidates = []

    for location in locations:

        location_id = location.get(
            "id"
        )

        location_name = location.get(
            "name"
        )

        country_info = location.get(
            "country",
            {}
        )

        if not isinstance(
            country_info,
            dict
        ):
            continue

        country_code = country_info.get(
            "code"
        )

        if not country_code:
            continue

        country_code = (
            str(country_code)
            .upper()
            .strip()
        )

        # Only accept valid ISO-2 codes
        # existing in REST Countries.
        if country_code not in valid_iso2:
            continue

        coordinates = location.get(
            "coordinates",
            {}
        )

        if not isinstance(
            coordinates,
            dict
        ):
            coordinates = {}

        latitude = coordinates.get(
            "latitude"
        )

        longitude = coordinates.get(
            "longitude"
        )

        sensors = location.get(
            "sensors",
            []
        )

        if not isinstance(
            sensors,
            list
        ):
            continue

        pollutants = set()

        for sensor in sensors:

            parameter = sensor.get(
                "parameter",
                {}
            )

            if not isinstance(
                parameter,
                dict
            ):
                continue

            parameter_id = parameter.get(
                "id"
            )

            if parameter_id in TARGET_POLLUTANTS:

                pollutants.add(
                    TARGET_POLLUTANTS[
                        parameter_id
                    ]
                )

        if not pollutants:
            continue

        candidates.append({
            "Location ID": location_id,
            "Location Name": location_name,
            "ISO Alpha-2": country_code,
            "OpenAQ Country Name":
                country_info.get("name"),
            "Latitude": latitude,
            "Longitude": longitude,
            "Pollutants Available":
                len(pollutants),
            "Pollutant List":
                ", ".join(
                    sorted(pollutants)
                )
        })

    candidate_df = pd.DataFrame(
        candidates
    )

    if candidate_df.empty:

        raise ValueError(
            "No valid OpenAQ locations were found."
        )

    # Prefer a location measuring the
    # greatest number of target pollutants.
    candidate_df = candidate_df.sort_values(
        by=[
            "ISO Alpha-2",
            "Pollutants Available"
        ],
        ascending=[
            True,
            False
        ]
    )

    selected = (
        candidate_df
        .drop_duplicates(
            subset=[
                "ISO Alpha-2"
            ],
            keep="first"
        )
        .reset_index(drop=True)
    )

    print(
        f"Countries with suitable OpenAQ "
        f"locations: {len(selected)}"
    )

    return selected


# ============================================================
# GET LATEST MEASUREMENTS
# ============================================================

def get_latest_measurements(
    selected_locations
):

    print()
    print(
        "Retrieving latest air-quality measurements..."
    )

    records = []

    total = len(
        selected_locations
    )

    for index, row in selected_locations.iterrows():

        location_id = int(
            row["Location ID"]
        )

        country_code = row[
            "ISO Alpha-2"
        ]

        location_name = row[
            "Location Name"
        ]

        print(
            f"[{index + 1}/{total}] "
            f"{country_code} - "
            f"{location_name}"
        )

        try:

            data = api_get(
                f"/locations/{location_id}/latest",
                params={
                    "limit": 100,
                    "page": 1
                }
            )

            if not data:

                print(
                    "   No response."
                )

                continue

            results = data.get(
                "results",
                []
            )

            if not results:

                print(
                    "   No latest measurements."
                )

                continue

            for measurement in results:

                sensor_id = measurement.get(
                    "sensorsId"
                )

                value = measurement.get(
                    "value"
                )

                if sensor_id is None:
                    continue

                if value is None:
                    continue

                datetime_info = measurement.get(
                    "datetime",
                    {}
                )

                if not isinstance(
                    datetime_info,
                    dict
                ):
                    datetime_info = {}

                coordinates = measurement.get(
                    "coordinates",
                    {}
                )

                if not isinstance(
                    coordinates,
                    dict
                ):
                    coordinates = {}

                records.append({
                    "ISO Alpha-2":
                        country_code,

                    "Location ID":
                        location_id,

                    "Location Name":
                        location_name,

                    "Latitude":
                        coordinates.get(
                            "latitude",
                            row["Latitude"]
                        ),

                    "Longitude":
                        coordinates.get(
                            "longitude",
                            row["Longitude"]
                        ),

                    "Sensor ID":
                        sensor_id,

                    "Measurement Value":
                        value,

                    "UTC Datetime":
                        datetime_info.get(
                            "utc"
                        ),

                    "Local Datetime":
                        datetime_info.get(
                            "local"
                        )
                })

        except Exception as error:

            print(
                f"   ERROR: {error}"
            )

    return pd.DataFrame(
        records
    )


# ============================================================
# BUILD FINAL DATASET
# ============================================================

def build_dataset(
    measurement_df,
    sensor_mapping_df,
    country_df
):

    print()
    print(
        "Building country-level OpenAQ dataset..."
    )

    if measurement_df.empty:

        raise ValueError(
            "No OpenAQ measurements were retrieved."
        )

    # Connect measurement to pollutant
    df = measurement_df.merge(
        sensor_mapping_df[
            [
                "Sensor ID",
                "Pollutant",
                "Unit",
                "Parameter ID"
            ]
        ],
        on="Sensor ID",
        how="left"
    )

    # Keep target pollutants only.
    df = df[
        df["Pollutant"].isin(
            [
                "PM2.5",
                "PM10",
                "NO2",
                "O3"
            ]
        )
    ].copy()

    # Convert values to numeric.
    df["Measurement Value"] = pd.to_numeric(
        df["Measurement Value"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "ISO Alpha-2",
            "Pollutant",
            "Measurement Value"
        ]
    )

    # Parse measurement time.
    df["UTC Parsed"] = pd.to_datetime(
        df["UTC Datetime"],
        errors="coerce",
        utc=True
    )

    # Sort newest first.
    df = df.sort_values(
        by=[
            "ISO Alpha-2",
            "Pollutant",
            "UTC Parsed"
        ],
        ascending=[
            True,
            True,
            False
        ]
    )

    # Keep the newest observation for each
    # country and pollutant.
    df = df.drop_duplicates(
        subset=[
            "ISO Alpha-2",
            "Pollutant"
        ],
        keep="first"
    )

    # --------------------------------------------------------
    # POLLUTANT VALUES
    # --------------------------------------------------------

    value_pivot = df.pivot_table(
        index="ISO Alpha-2",
        columns="Pollutant",
        values="Measurement Value",
        aggfunc="first"
    ).reset_index()

    value_pivot.columns.name = None

    # --------------------------------------------------------
    # MEASUREMENT TIMES
    # --------------------------------------------------------

    time_pivot = df.pivot_table(
        index="ISO Alpha-2",
        columns="Pollutant",
        values="UTC Datetime",
        aggfunc="first"
    ).reset_index()

    time_pivot.columns.name = None

    rename_time = {}

    for pollutant in [
        "PM2.5",
        "PM10",
        "NO2",
        "O3"
    ]:

        if pollutant in time_pivot.columns:

            rename_time[
                pollutant
            ] = (
                f"{pollutant} "
                f"Measurement Time"
            )

    time_pivot = time_pivot.rename(
        columns=rename_time
    )

    # --------------------------------------------------------
    # LOCATION INFORMATION
    # --------------------------------------------------------

    location_info = (
        df[
            [
                "ISO Alpha-2",
                "Location ID",
                "Location Name",
                "Latitude",
                "Longitude"
            ]
        ]
        .drop_duplicates(
            subset=[
                "ISO Alpha-2"
            ]
        )
    )

    # --------------------------------------------------------
    # START WITH REST COUNTRIES
    # --------------------------------------------------------

    final_df = country_df[
        [
            "Country Name",
            "ISO Alpha-2",
            "ISO Alpha-3"
        ]
    ].copy()

    final_df = (
        final_df
        .drop_duplicates(
            subset=[
                "ISO Alpha-2"
            ]
        )
    )

    # --------------------------------------------------------
    # MERGE LOCATION DATA
    # --------------------------------------------------------

    final_df = final_df.merge(
        location_info,
        on="ISO Alpha-2",
        how="left"
    )

    # --------------------------------------------------------
    # MERGE POLLUTANT VALUES
    # --------------------------------------------------------

    final_df = final_df.merge(
        value_pivot,
        on="ISO Alpha-2",
        how="left"
    )

    # --------------------------------------------------------
    # MERGE MEASUREMENT TIMES
    # --------------------------------------------------------

    final_df = final_df.merge(
        time_pivot,
        on="ISO Alpha-2",
        how="left"
    )

    # --------------------------------------------------------
    # ENSURE POLLUTANT COLUMNS EXIST
    # --------------------------------------------------------

    pollutants = [
        "PM2.5",
        "PM10",
        "NO2",
        "O3"
    ]

    for pollutant in pollutants:

        if pollutant not in final_df.columns:

            final_df[pollutant] = pd.NA

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    final_df[
        "API Source"
    ] = "OpenAQ v3"

    final_df[
        "Data Type"
    ] = "Latest available measurement"

    # --------------------------------------------------------
    # COLUMN ORDER
    # --------------------------------------------------------

    columns = [
        "Country Name",
        "ISO Alpha-2",
        "ISO Alpha-3",
        "Location ID",
        "Location Name",
        "Latitude",
        "Longitude",
        "PM2.5",
        "PM10",
        "NO2",
        "O3",
        "PM2.5 Measurement Time",
        "PM10 Measurement Time",
        "NO2 Measurement Time",
        "O3 Measurement Time",
        "API Source",
        "Data Type"
    ]

    final_df = final_df[
        [
            column
            for column in columns
            if column in final_df.columns
        ]
    ]

    return final_df


# ============================================================
# VALIDATION
# ============================================================

def validate_dataset(
    df,
    country_df
):

    print()
    print(
        "Validating OpenAQ air-quality data..."
    )

    validation = []

    pollutants = [
        "PM2.5",
        "PM10",
        "NO2",
        "O3"
    ]

    # --------------------------------------------------------
    # BASIC COUNTS
    # --------------------------------------------------------

    validation.append({
        "Check": "Total Country Records",
        "Value": len(df),
        "Status": "INFO"
    })

    validation.append({
        "Check": "Total Columns",
        "Value": len(df.columns),
        "Status": "INFO"
    })

    # --------------------------------------------------------
    # DUPLICATES
    # --------------------------------------------------------

    duplicate_countries = (
        df["Country Name"]
        .duplicated()
        .sum()
    )

    validation.append({
        "Check": "Duplicate Country Records",
        "Value": int(duplicate_countries),
        "Status": (
            "PASS"
            if duplicate_countries == 0
            else "CHECK"
        )
    })

    duplicate_iso2 = (
        df["ISO Alpha-2"]
        .duplicated()
        .sum()
    )

    validation.append({
        "Check": "Duplicate ISO Alpha-2 Codes",
        "Value": int(duplicate_iso2),
        "Status": (
            "PASS"
            if duplicate_iso2 == 0
            else "CHECK"
        )
    })

    # --------------------------------------------------------
    # MISSING VALUES
    # --------------------------------------------------------

    for pollutant in pollutants:

        missing = (
            df[pollutant]
            .isna()
            .sum()
        )

        validation.append({
            "Check":
                f"Missing {pollutant}",

            "Value":
                int(missing),

            "Status":
                (
                    "PASS"
                    if missing == 0
                    else "INFO"
                )
        })

    # --------------------------------------------------------
    # RANGE CHECKS
    # --------------------------------------------------------

    # Broad sanity-check ranges.
    # These are NOT health-standard limits.

    range_limits = {
        "PM2.5": (0, 1000),
        "PM10": (0, 2000),
        "NO2": (0, 1000),
        "O3": (0, 1000)
    }

    for pollutant, limits in range_limits.items():

        lower = limits[0]
        upper = limits[1]

        values = pd.to_numeric(
            df[pollutant],
            errors="coerce"
        )

        invalid = (
            (values < lower) |
            (values > upper)
        ).sum()

        validation.append({
            "Check":
                f"{pollutant} Range Violations",

            "Value":
                int(invalid),

            "Status":
                (
                    "PASS"
                    if invalid == 0
                    else "CHECK"
                )
        })

    # --------------------------------------------------------
    # COUNTRY COVERAGE
    # --------------------------------------------------------

    source_country_count = (
        country_df[
            "ISO Alpha-2"
        ]
        .dropna()
        .nunique()
    )

    countries_with_data = (
        df[
            pollutants
        ]
        .notna()
        .any(axis=1)
        .sum()
    )

    validation.append({
        "Check":
            "REST Countries Countries",

        "Value":
            int(source_country_count),

        "Status":
            "INFO"
    })

    validation.append({
        "Check":
            "Countries With OpenAQ Data",

        "Value":
            int(countries_with_data),

        "Status":
            "INFO"
    })

    if source_country_count > 0:

        coverage = (
            countries_with_data /
            source_country_count *
            100
        )

    else:

        coverage = 0

    validation.append({
        "Check":
            "OpenAQ Country Coverage (%)",

        "Value":
            round(
                coverage,
                2
            ),

        "Status":
            "INFO"
    })

    # --------------------------------------------------------
    # LOCATION MISSINGNESS
    # --------------------------------------------------------

    missing_locations = (
        df["Location ID"]
        .isna()
        .sum()
    )

    validation.append({
        "Check":
            "Missing OpenAQ Location",

        "Value":
            int(missing_locations),

        "Status":
            (
                "PASS"
                if missing_locations == 0
                else "INFO"
            )
    })

    # --------------------------------------------------------
    # TIMESTAMP MISSINGNESS
    # --------------------------------------------------------

    for pollutant in pollutants:

        time_column = (
            f"{pollutant} "
            f"Measurement Time"
        )

        if time_column not in df.columns:
            continue

        missing_time = (
            df[time_column]
            .isna()
            .sum()
        )

        validation.append({
            "Check":
                (
                    f"Missing {pollutant} "
                    f"Measurement Time"
                ),

            "Value":
                int(missing_time),

            "Status":
                (
                    "PASS"
                    if missing_time == 0
                    else "INFO"
                )
        })

    return pd.DataFrame(
        validation
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "OPENAQ AIR QUALITY API DATA COLLECTION"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # API KEY CHECK
    # --------------------------------------------------------

    if not API_KEY:

        print()
        print(
            "ERROR: OPENAQ_API_KEY is missing."
        )

        print()
        print(
            "Add this to your .env file:"
        )

        print()
        print(
            "OPENAQ_API_KEY=your_api_key_here"
        )

        print()

        return

    # --------------------------------------------------------
    # LOAD COUNTRIES
    # --------------------------------------------------------

    country_df = load_country_data()

    # --------------------------------------------------------
    # GET LOCATIONS
    # --------------------------------------------------------

    locations = get_locations()

    if not locations:

        raise ValueError(
            "No OpenAQ locations were retrieved."
        )

    # --------------------------------------------------------
    # SENSOR MAPPING
    # --------------------------------------------------------

    sensor_mapping_df = (
        build_sensor_mapping(
            locations
        )
    )

    # --------------------------------------------------------
    # SELECT LOCATIONS
    # --------------------------------------------------------

    selected_locations = (
        select_country_locations(
            locations,
            country_df
        )
    )

    print()
    print(
        "Selected monitoring locations:"
    )

    print(
        selected_locations
        .head(10)
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # LATEST MEASUREMENTS
    # --------------------------------------------------------

    measurement_df = (
        get_latest_measurements(
            selected_locations
        )
    )

    print()
    print(
        "Raw latest measurements retrieved: "
        f"{len(measurement_df)}"
    )

    if measurement_df.empty:

        raise ValueError(
            "No latest measurements were retrieved."
        )

    # --------------------------------------------------------
    # BUILD DATASET
    # --------------------------------------------------------

    final_df = build_dataset(
        measurement_df,
        sensor_mapping_df,
        country_df
    )

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    validation_df = validate_dataset(
        final_df,
        country_df
    )

    # --------------------------------------------------------
    # PRINT VALIDATION
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        "VALIDATION RESULTS"
    )
    print("=" * 60)

    print(
        validation_df.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # SHOW SAMPLE
    # --------------------------------------------------------

    print()
    print(
        "First 10 OpenAQ records"
    )

    print("=" * 60)

    print(
        final_df
        .head(10)
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    os.makedirs(
        "data",
        exist_ok=True
    )

    final_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    validation_df.to_csv(
        VALIDATION_FILE,
        index=False
    )

    # --------------------------------------------------------
    # COMPLETED
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        "OPENAQ STEP COMPLETED"
    )
    print("=" * 60)

    print()
    print(
        "Air-quality dataset:"
    )

    print(
        os.path.abspath(
            OUTPUT_FILE
        )
    )

    print()
    print(
        "Validation report:"
    )

    print(
        os.path.abspath(
            VALIDATION_FILE
        )
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()