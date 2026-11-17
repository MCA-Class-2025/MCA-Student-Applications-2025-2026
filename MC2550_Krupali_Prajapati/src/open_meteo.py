import time
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# OPEN-METEO WEATHER API
# ============================================================

BASE_DIR = Path(__file__).parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

INPUT_FILE = DATA_DIR / "rest_countries.csv"

OUTPUT_FILE = DATA_DIR / "open_meteo_weather.csv"

VALIDATION_FILE = DATA_DIR / "open_meteo_validation.csv"

API_URL = "https://api.open-meteo.com/v1/forecast"


# ============================================================
# LOAD REST COUNTRIES DATA
# ============================================================

def load_country_data():

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"\nCould not find:\n{INPUT_FILE}\n\n"
            "Make sure rest_countries.py has been "
            "successfully executed first."
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"\nREST Countries records loaded: {len(df)}"
    )

    return df


# ============================================================
# WEATHER CODE INTERPRETATION
# ============================================================

def interpret_weather_code(code):

    if pd.isna(code):

        return None

    code = int(code)

    weather_codes = {

        0: "Clear sky",

        1: "Mainly clear",

        2: "Partly cloudy",

        3: "Overcast",

        45: "Fog",

        48: "Depositing rime fog",

        51: "Light drizzle",

        53: "Moderate drizzle",

        55: "Dense drizzle",

        56: "Light freezing drizzle",

        57: "Dense freezing drizzle",

        61: "Slight rain",

        63: "Moderate rain",

        65: "Heavy rain",

        66: "Light freezing rain",

        67: "Heavy freezing rain",

        71: "Slight snow fall",

        73: "Moderate snow fall",

        75: "Heavy snow fall",

        77: "Snow grains",

        80: "Slight rain showers",

        81: "Moderate rain showers",

        82: "Violent rain showers",

        85: "Slight snow showers",

        86: "Heavy snow showers",

        95: "Thunderstorm",

        96: "Thunderstorm with slight hail",

        99: "Thunderstorm with heavy hail"
    }

    return weather_codes.get(
        code,
        "Unknown"
    )


# ============================================================
# GET WEATHER FOR ONE COUNTRY
# ============================================================

def get_weather(
    latitude,
    longitude
):

    params = {

        "latitude": latitude,

        "longitude": longitude,

        "current": ",".join([

            "temperature_2m",

            "relative_humidity_2m",

            "apparent_temperature",

            "precipitation",

            "weather_code",

            "wind_speed_10m"
        ]),

        "timezone": "auto"
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    current = data.get(
        "current",
        {}
    )

    return {

        "Weather Observation Time":
            current.get("time"),

        "Temperature (°C)":
            current.get("temperature_2m"),

        "Relative Humidity (%)":
            current.get("relative_humidity_2m"),

        "Apparent Temperature (°C)":
            current.get("apparent_temperature"),

        "Precipitation (mm)":
            current.get("precipitation"),

        "Weather Code":
            current.get("weather_code"),

        "Weather Condition":
            interpret_weather_code(
                current.get("weather_code")
            ),

        "Wind Speed (km/h)":
            current.get("wind_speed_10m"),

        "Weather Timezone":
            data.get("timezone"),

        "Weather Latitude":
            data.get("latitude"),

        "Weather Longitude":
            data.get("longitude")
    }


# ============================================================
# COLLECT WEATHER DATA
# ============================================================

def collect_weather_data(df):

    results = []

    total = len(df)

    successful = 0

    failed = 0

    print("\nStarting Open-Meteo collection...")
    print(
        f"Countries to process: {total}"
    )

    for index, row in df.iterrows():

        country_name = row["Country Name"]

        capital = row["Capital"]

        latitude = row["Capital Latitude"]

        longitude = row["Capital Longitude"]

        # ----------------------------------------------------
        # Check coordinates
        # ----------------------------------------------------

        if pd.isna(latitude) or pd.isna(longitude):

            print(
                f"[{index + 1}/{total}] "
                f"{country_name}: "
                f"SKIPPED - missing capital coordinates"
            )

            results.append({

                "Country Name":
                    country_name,

                "ISO Alpha-3":
                    row["ISO Alpha-3"],

                "Capital":
                    capital,

                "Capital Latitude":
                    latitude,

                "Capital Longitude":
                    longitude,

                "API Status":
                    "Missing Coordinates"
            })

            failed += 1

            continue

        # ----------------------------------------------------
        # Request weather
        # ----------------------------------------------------

        print(
            f"[{index + 1}/{total}] "
            f"{country_name} - {capital}"
        )

        try:

            weather = get_weather(
                latitude,
                longitude
            )

            record = {

                "Country Name":
                    country_name,

                "ISO Alpha-3":
                    row["ISO Alpha-3"],

                "Capital":
                    capital,

                "Capital Latitude":
                    latitude,

                "Capital Longitude":
                    longitude,

                "API Status":
                    "Success"
            }

            record.update(
                weather
            )

            results.append(
                record
            )

            successful += 1

        except Exception as error:

            print(
                f"    ERROR: {error}"
            )

            results.append({

                "Country Name":
                    country_name,

                "ISO Alpha-3":
                    row["ISO Alpha-3"],

                "Capital":
                    capital,

                "Capital Latitude":
                    latitude,

                "Capital Longitude":
                    longitude,

                "API Status":
                    "Failed",

                "API Error":
                    str(error)
            })

            failed += 1

        # ----------------------------------------------------
        # Small delay
        # ----------------------------------------------------

        time.sleep(0.15)

    print("\nCollection completed.")

    print(
        "Successful:",
        successful
    )

    print(
        "Failed/Skipped:",
        failed
    )

    return pd.DataFrame(results)


# ============================================================
# VALIDATION
# ============================================================

def validate_weather_data(df):

    validation = []

    # --------------------------------------------------------
    # General
    # --------------------------------------------------------

    validation.append({

        "Check":
            "Total Records",

        "Value":
            len(df),

        "Status":
            "INFO"
    })

    validation.append({

        "Check":
            "Total Columns",

        "Value":
            len(df.columns),

        "Status":
            "INFO"
    })

    # --------------------------------------------------------
    # Duplicate countries
    # --------------------------------------------------------

    duplicates = int(
        df["Country Name"]
        .duplicated()
        .sum()
    )

    validation.append({

        "Check":
            "Duplicate Country Records",

        "Value":
            duplicates,

        "Status":
            "PASS"
            if duplicates == 0
            else "WARNING"
    })

    # --------------------------------------------------------
    # Successful API requests
    # --------------------------------------------------------

    if "API Status" in df.columns:

        success_count = int(
            (
                df["API Status"]
                == "Success"
            ).sum()
        )

        validation.append({

            "Check":
                "Successful API Requests",

            "Value":
                success_count,

            "Status":
                "PASS"
                if success_count > 0
                else "FAIL"
        })

        failed_count = int(
            (
                df["API Status"]
                != "Success"
            ).sum()
        )

        validation.append({

            "Check":
                "Failed/Skipped API Requests",

            "Value":
                failed_count,

            "Status":
                "INFO"
        })

    # --------------------------------------------------------
    # Missing weather values
    # --------------------------------------------------------

    weather_columns = [

        "Temperature (°C)",

        "Relative Humidity (%)",

        "Apparent Temperature (°C)",

        "Precipitation (mm)",

        "Weather Code",

        "Wind Speed (km/h)"
    ]

    for column in weather_columns:

        if column in df.columns:

            missing = int(
                df[column].isna().sum()
            )

            validation.append({

                "Check":
                    f"Missing {column}",

                "Value":
                    missing,

                "Status":
                    "PASS"
                    if missing == 0
                    else "INFO"
            })

    # --------------------------------------------------------
    # Temperature range check
    # --------------------------------------------------------

    if "Temperature (°C)" in df.columns:

        temperatures = pd.to_numeric(
            df["Temperature (°C)"],
            errors="coerce"
        )

        invalid_temperature = int(
            (
                (temperatures < -90)
                |
                (temperatures > 70)
            )
            .fillna(False)
            .sum()
        )

        validation.append({

            "Check":
                "Temperature Range Validation",

            "Value":
                invalid_temperature,

            "Status":
                "PASS"
                if invalid_temperature == 0
                else "WARNING"
        })

    # --------------------------------------------------------
    # Humidity range check
    # --------------------------------------------------------

    if "Relative Humidity (%)" in df.columns:

        humidity = pd.to_numeric(
            df["Relative Humidity (%)"],
            errors="coerce"
        )

        invalid_humidity = int(
            (
                (humidity < 0)
                |
                (humidity > 100)
            )
            .fillna(False)
            .sum()
        )

        validation.append({

            "Check":
                "Humidity Range Validation",

            "Value":
                invalid_humidity,

            "Status":
                "PASS"
                if invalid_humidity == 0
                else "WARNING"
        })

    # --------------------------------------------------------
    # Wind speed check
    # --------------------------------------------------------

    if "Wind Speed (km/h)" in df.columns:

        wind = pd.to_numeric(
            df["Wind Speed (km/h)"],
            errors="coerce"
        )

        invalid_wind = int(
            (
                wind < 0
            )
            .fillna(False)
            .sum()
        )

        validation.append({

            "Check":
                "Wind Speed Validation",

            "Value":
                invalid_wind,

            "Status":
                "PASS"
                if invalid_wind == 0
                else "WARNING"
        })

    return pd.DataFrame(
        validation
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("OPEN-METEO WEATHER API DATA COLLECTION")
    print("=" * 60)

    # --------------------------------------------------------
    # Load REST Countries data
    # --------------------------------------------------------

    df = load_country_data()

    # --------------------------------------------------------
    # Collect weather
    # --------------------------------------------------------

    weather_df = collect_weather_data(
        df
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    print("\nValidating weather data...")

    validation_df = validate_weather_data(
        weather_df
    )

    print("\nVALIDATION RESULTS")
    print("=" * 60)

    print(
        validation_df.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Save weather dataset
    # --------------------------------------------------------

    weather_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Save validation report
    # --------------------------------------------------------

    validation_df.to_csv(
        VALIDATION_FILE,
        index=False,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Display sample
    # --------------------------------------------------------

    print("\nFirst 10 weather records")
    print("=" * 60)

    print(
        weather_df.head(10).to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Final message
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("OPEN-METEO STEP COMPLETED")
    print("=" * 60)

    print(
        "\nWeather dataset:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nValidation report:"
    )

    print(
        VALIDATION_FILE
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except requests.exceptions.RequestException as error:

        print("\nAPI/NETWORK ERROR")
        print("-" * 40)
        print(error)

    except Exception as error:

        print("\nPROGRAM ERROR")
        print("-" * 40)
        print(
            type(error).__name__,
            ":",
            error
        )