from pathlib import Path
from datetime import datetime, timezone
import argparse

import pandas as pd
import requests

from config import TOMTOM_API_KEY


# ============================================================
# LARGE LIVE DATA FUSION
# ============================================================
# ONE SHEET
# ONE ROW = ONE CITY + ONE LIVE COLLECTION RUN
#
# The script uses only REAL API values.
# A row is written to the COMPLETE fused dataset only when
# all required source values are available:
#
#   OpenWeather
#   WAQI
#   TomTom
#   Sentinel-5P
#   Weather Alerts
#
# "No active weather alerts" is a valid real result.
#
# IMPORTANT:
# One execution gives one snapshot per eligible city.
# Run the API collectors + this script repeatedly to build
# thousands of genuine rows over time.
# ============================================================


BASE_DIR = Path(__file__).resolve().parent
LIVE_DIR = BASE_DIR / "live_data"

OUTPUT_FILE = (
    BASE_DIR / "Weather_AirQuality_Data_Fusion.xlsx"
)

HISTORY_FILE = (
    LIVE_DIR / "fused_live_history.csv"
)

OPENWEATHER_FILE = (
    LIVE_DIR / "openweather_current.csv"
)

WAQI_FILE = (
    LIVE_DIR / "waqi_live_data.csv"
)

WEATHER_ALERT_FILE = (
    LIVE_DIR / "weather_alerts_current.csv"
)

SATELLITE_FILE = (
    LIVE_DIR / "sentinel5p_no2_current.csv"
)

PREDICTION_FILE = (
    LIVE_DIR / "live_predictions.csv"
)

COORDINATES_FILE = (
    LIVE_DIR / "openweather_city_coordinates.csv"
)

TOMTOM_URL = (
    "https://api.tomtom.com/traffic/services/4/"
    "flowSegmentData/absolute/10/json"
)


# ============================================================
# HELPERS
# ============================================================

def read_csv(path):
    if not path.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(
            path,
            low_memory=False
        )

        df.columns = [
            str(column).strip()
            for column in df.columns
        ]

        return df

    except Exception as exc:

        print(
            f"Could not read {path.name}: {exc}"
        )

        return pd.DataFrame()


def clean_city_column(df):
    if df.empty or "City" not in df.columns:
        return df

    df["City"] = (
        df["City"]
        .astype(str)
        .str.strip()
    )

    return df[
        (df["City"] != "")
        & (df["City"].str.lower() != "unknown")
        & (df["City"].str.lower() != "nan")
    ].copy()


def latest_by_city(df):
    """Keep the newest record for each city."""

    df = clean_city_column(df)

    if df.empty:
        return df

    if "Timestamp" in df.columns:

        temp_time = pd.to_datetime(
            df["Timestamp"],
            errors="coerce",
            utc=True
        )

        df = (
            df.assign(__time=temp_time)
            .sort_values(
                "__time",
                ascending=True
            )
            .drop(
                columns=["__time"]
            )
        )

    return df.drop_duplicates(
        "City",
        keep="last"
    )


def value(row, column):
    """Return a value or None if the column is absent."""

    if column not in row.index:
        return None

    result = row[column]

    if pd.isna(result):
        return None

    return result


def require(value_to_check, field_name):
    """
    Raise an error for a missing required field.
    This guarantees that Complete_Fused_Data does not
    contain fake or missing API values.
    """

    if value_to_check is None:
        raise ValueError(
            f"Missing required field: {field_name}"
        )

    if isinstance(value_to_check, str):

        if not value_to_check.strip():
            raise ValueError(
                f"Missing required field: {field_name}"
            )

    return value_to_check


# ============================================================
# LOAD API DATA
# ============================================================

def load_api_tables():

    openweather = latest_by_city(
        read_csv(OPENWEATHER_FILE)
    )

    waqi = latest_by_city(
        read_csv(WAQI_FILE)
    )

    alerts = latest_by_city(
        read_csv(WEATHER_ALERT_FILE)
    )

    satellite = latest_by_city(
        read_csv(SATELLITE_FILE)
    )

    predictions = latest_by_city(
        read_csv(PREDICTION_FILE)
    )

    coordinates = latest_by_city(
        read_csv(COORDINATES_FILE)
    )

    return (
        openweather,
        waqi,
        alerts,
        satellite,
        predictions,
        coordinates,
    )


# ============================================================
# TOMTOM
# ============================================================

def get_tomtom(
    latitude,
    longitude
):

    if (
        not TOMTOM_API_KEY
        or not str(TOMTOM_API_KEY).strip()
    ):
        raise ValueError(
            "TOMTOM_API_KEY is missing"
        )

    response = requests.get(
        TOMTOM_URL,
        params={
            "point": f"{latitude},{longitude}",
            "unit": "KMPH",
            "key": TOMTOM_API_KEY,
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    flow = data.get(
        "flowSegmentData",
        {}
    )

    current_speed = flow.get(
        "currentSpeed"
    )

    free_flow_speed = flow.get(
        "freeFlowSpeed"
    )

    require(
        current_speed,
        "TomTom current speed"
    )

    require(
        free_flow_speed,
        "TomTom free-flow speed"
    )

    return {
        "TomTom_CurrentSpeed_kmh": current_speed,
        "TomTom_FreeFlowSpeed_kmh": free_flow_speed,
        "TomTom_Confidence": flow.get(
            "confidence"
        ),
        "TomTom_RoadClosure": flow.get(
            "roadClosure"
        ),
    }


# ============================================================
# BUILD ONE COMPLETE LIVE SNAPSHOT
# ============================================================

def build_snapshot():

    (
        openweather,
        waqi,
        alerts,
        satellite,
        predictions,
        coordinates,
    ) = load_api_tables()

    if openweather.empty:
        raise RuntimeError(
            "openweather_current.csv is missing or empty. "
            "Run openweather_api.py first."
        )

    if waqi.empty:
        raise RuntimeError(
            "waqi_live_data.csv is missing or empty. "
            "Run waqi_api.py first."
        )

    if alerts.empty:
        raise RuntimeError(
            "weather_alerts_current.csv is missing or empty. "
            "Run weather_alerts_api.py first."
        )

    if satellite.empty:
        raise RuntimeError(
            "sentinel5p_no2_current.csv is missing or empty. "
            "Run satellite_api.py first."
        )

    # Cities that have REAL records in every required source.
    common_cities = set(
        openweather["City"]
    ) & set(
        waqi["City"]
    ) & set(
        alerts["City"]
    ) & set(
        satellite["City"]
    )

    if not common_cities:

        raise RuntimeError(
            "No common cities currently have complete "
            "OpenWeather + WAQI + Weather Alerts + "
            "Sentinel-5P data."
        )

    common_cities = sorted(
        common_cities
    )

    print(
        f"\nCities with all four cached sources: "
        f"{len(common_cities)}"
    )

    rows = []

    collection_time = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    run_id = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%d_%H%M%S"
    )

    skipped = []

    for number, city in enumerate(
        common_cities,
        start=1
    ):

        print(
            f"[{number}/{len(common_cities)}] Fusing: {city}"
        )

        try:

            ow = openweather[
                openweather["City"] == city
            ].iloc[-1]

            wq = waqi[
                waqi["City"] == city
            ].iloc[-1]

            alert = alerts[
                alerts["City"] == city
            ].iloc[-1]

            sat = satellite[
                satellite["City"] == city
            ].iloc[-1]

            # ------------------------------------------------
            # Coordinates
            # ------------------------------------------------

            latitude = value(
                ow,
                "Latitude"
            )

            longitude = value(
                ow,
                "Longitude"
            )

            # Fallback to coordinate file.
            if (
                latitude is None
                or longitude is None
            ):

                coordinate_rows = coordinates[
                    coordinates["City"] == city
                ]

                if not coordinate_rows.empty:

                    cr = coordinate_rows.iloc[-1]

                    latitude = value(
                        cr,
                        "Latitude"
                    )

                    longitude = value(
                        cr,
                        "Longitude"
                    )

            require(
                latitude,
                "Latitude"
            )

            require(
                longitude,
                "Longitude"
            )

            # ------------------------------------------------
            # OpenWeather
            # ------------------------------------------------

            temperature = require(
                value(
                    ow,
                    "Temperature (°C)"
                ),
                "OpenWeather temperature"
            )

            humidity = require(
                value(
                    ow,
                    "Humidity (%)"
                ),
                "OpenWeather humidity"
            )

            pressure = require(
                value(
                    ow,
                    "Pressure (hPa)"
                ),
                "OpenWeather pressure"
            )

            wind_speed = require(
                value(
                    ow,
                    "Wind_Speed (m/s)"
                ),
                "OpenWeather wind speed"
            )

            weather_name = require(
                value(
                    ow,
                    "Weather"
                ),
                "OpenWeather weather"
            )

            # ------------------------------------------------
            # WAQI
            # ------------------------------------------------

            waqi_aqi = require(
                value(
                    wq,
                    "AQI"
                ),
                "WAQI AQI"
            )

            waqi_pm25 = require(
                value(
                    wq,
                    "PM2.5"
                ),
                "WAQI PM2.5"
            )

            # ------------------------------------------------
            # Sentinel-5P
            # ------------------------------------------------

            satellite_no2 = require(
                value(
                    sat,
                    "Mean_NO2"
                ),
                "Sentinel-5P NO2"
            )

            # ------------------------------------------------
            # Weather Alert
            # ------------------------------------------------
            #
            # "No active alerts" is real data, so it is stored
            # as text instead of null.
            # ------------------------------------------------

            alert_status = value(
                alert,
                "Has_Active_Alert"
            )

            if alert_status is None:

                alert_status = value(
                    alert,
                    "WeatherAlert_Status"
                )

            require(
                alert_status,
                "Weather alert status"
            )

            alert_count = value(
                alert,
                "Alert_Count"
            )

            if alert_count is None:
                alert_count = value(
                    alert,
                    "WeatherAlert_Count"
                )

            if alert_count is None:
                alert_count = 0

            if isinstance(
                alert_status,
                bool
            ):

                alert_text = (
                    "Active alert"
                    if alert_status
                    else "No active alerts"
                )

            else:

                alert_text = str(
                    alert_status
                )

            alert_event = (
                value(
                    alert,
                    "Alert_Event"
                )
                or value(
                    alert,
                    "WeatherAlert_Event"
                )
                or "None"
            )

            alert_severity = (
                value(
                    alert,
                    "Alert_Severity"
                )
                or value(
                    alert,
                    "WeatherAlert_Severity"
                )
                or "None"
            )

            # ------------------------------------------------
            # TomTom
            # ------------------------------------------------

            tomtom = get_tomtom(
                float(latitude),
                float(longitude)
            )

            # ------------------------------------------------
            # Prediction
            # ------------------------------------------------
            #
            # Prediction is included only when it genuinely
            # exists for the city. It is NOT required for a
            # complete API fusion row.
            # ------------------------------------------------

            predicted_pm25 = None
            prediction_change = None

            prediction_rows = predictions[
                predictions["City"] == city
            ]

            if not prediction_rows.empty:

                pr = prediction_rows.iloc[-1]

                predicted_pm25 = (
                    value(
                        pr,
                        "Predicted_PM25_Next_1Hour"
                    )
                    or value(
                        pr,
                        "Predicted_PM25"
                    )
                )

                prediction_change = value(
                    pr,
                    "Expected_Change"
                )

            # ------------------------------------------------
            # Final row
            # ------------------------------------------------

            row = {
                "Fusion_Run_ID": run_id,
                "Collection_Timestamp_UTC": collection_time,

                "City": city,

                "Latitude": latitude,
                "Longitude": longitude,

                "OpenWeather_Temperature_C": temperature,
                "OpenWeather_Humidity_pct": humidity,
                "OpenWeather_Pressure_hPa": pressure,
                "OpenWeather_WindSpeed_mps": wind_speed,
                "OpenWeather_Weather": weather_name,

                "WAQI_AQI": waqi_aqi,
                "WAQI_PM25_ug_m3": waqi_pm25,

                "TomTom_CurrentSpeed_kmh": (
                    tomtom[
                        "TomTom_CurrentSpeed_kmh"
                    ]
                ),

                "TomTom_FreeFlowSpeed_kmh": (
                    tomtom[
                        "TomTom_FreeFlowSpeed_kmh"
                    ]
                ),

                "TomTom_Confidence": (
                    tomtom[
                        "TomTom_Confidence"
                    ]
                ),

                "TomTom_RoadClosure": (
                    tomtom[
                        "TomTom_RoadClosure"
                    ]
                ),

                "Sentinel5P_NO2": satellite_no2,

                "WeatherAlert_Status": alert_text,
                "WeatherAlert_Count": alert_count,
                "WeatherAlert_Event": alert_event,
                "WeatherAlert_Severity": (
                    alert_severity
                ),

                "Predicted_PM25_1h_ug_m3": (
                    predicted_pm25
                ),

                "Expected_PM25_Change_ug_m3": (
                    prediction_change
                ),
            }

            rows.append(row)

            print(
                f"    SUCCESS: {city}"
            )

        except Exception as exc:

            skipped.append(
                (
                    city,
                    str(exc)
                )
            )

            print(
                f"    SKIPPED: {exc}"
            )

    return pd.DataFrame(rows), skipped


# ============================================================
# APPEND HISTORY
# ============================================================

def append_history(snapshot):

    if snapshot.empty:
        return pd.DataFrame()

    if HISTORY_FILE.exists():

        history = read_csv(
            HISTORY_FILE
        )

    else:

        history = pd.DataFrame()

    combined = pd.concat(
        [
            history,
            snapshot
        ],
        ignore_index=True
    )

    # Exact duplicate protection.
    duplicate_keys = [
        "Fusion_Run_ID",
        "City"
    ]

    combined = combined.drop_duplicates(
        subset=duplicate_keys,
        keep="last"
    )

    combined = combined.sort_values(
        [
            "Collection_Timestamp_UTC",
            "City"
        ]
    ).reset_index(
        drop=True
    )

    combined.to_csv(
        HISTORY_FILE,
        index=False
    )

    return combined


# ============================================================
# WRITE ONE-SHEET EXCEL
# ============================================================

def write_excel(df):

    if df.empty:
        raise ValueError(
            "No complete fused rows are available."
        )

    # ONE SHEET ONLY.
    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            sheet_name="Fused_Data",
            index=False
        )

        worksheet = writer[
            "Fused_Data"
        ]

        # Freeze the header.
        worksheet.freeze_panes = "A2"

        # Filter button on all columns.
        worksheet.auto_filter.ref = (
            worksheet.dimensions
        )

        # Reasonable widths.
        for column_cells in worksheet.columns:

            max_length = 0

            column_letter = (
                column_cells[0]
                .column_letter
            )

            for cell in column_cells[:100]:
                try:
                    max_length = max(
                        max_length,
                        len(str(cell.value))
                    )
                except Exception:
                    pass

            worksheet.column_dimensions[
                column_letter
            ].width = min(
                max(max_length + 2, 12),
                30
            )

    return OUTPUT_FILE


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Build one-sheet large live "
            "multi-API fused dataset."
        )
    )

    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help=(
            "Number of live collection snapshots "
            "to append. Default: 1."
        )
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help=(
            "Seconds to wait between runs. "
            "Recommended 60+ for repeated collection."
        )
    )

    args = parser.parse_args()

    if args.runs < 1:
        raise SystemExit(
            "--runs must be at least 1."
        )

    print("=" * 80)
    print(
        "API -> LARGE LIVE DATA FUSION -> ONE EXCEL SHEET"
    )
    print("=" * 80)

    print(
        "\nImportant:"
    )

    print(
        "Only complete REAL API observations are written."
    )

    print(
        "No API value is copied across historical timestamps."
    )

    print(
        "Repeated runs create additional genuine rows."
    )

    all_new_rows = 0

    for run_number in range(
        1,
        args.runs + 1
    ):

        print(
            "\n" + "=" * 80
        )

        print(
            f"LIVE FUSION RUN {run_number}/{args.runs}"
        )

        print(
            "=" * 80
        )

        try:

            snapshot, skipped = (
                build_snapshot()
            )

            if snapshot.empty:

                print(
                    "\nNo complete rows were produced."
                )

                if skipped:

                    print(
                        "\nSkipped cities:"
                    )

                    for city, reason in skipped:
                        print(
                            f"- {city}: {reason}"
                        )

            else:

                history = append_history(
                    snapshot
                )

                all_new_rows += len(
                    snapshot
                )

                output = write_excel(
                    history
                )

                print(
                    "\nRUN SUCCESS"
                )

                print(
                    f"New rows added: "
                    f"{len(snapshot)}"
                )

                print(
                    f"Total fused rows: "
                    f"{len(history):,}"
                )

                print(
                    f"Unique cities in history: "
                    f"{history['City'].nunique()}"
                )

                print(
                    f"Excel: {output}"
                )

                if skipped:

                    print(
                        f"\nCities skipped this run: "
                        f"{len(skipped)}"
                    )

        except Exception as exc:

            print(
                "\nDATA FUSION ERROR"
            )

            print(exc)

        # Wait before next collection.
        if (
            run_number < args.runs
            and args.interval > 0
        ):

            import time

            print(
                f"\nWaiting "
                f"{args.interval} seconds..."
            )

            time.sleep(
                args.interval
            )

    print(
        "\n" + "=" * 80
    )

    print(
        "FUSION PROCESS COMPLETE"
    )

    print(
        f"New rows added this execution: "
        f"{all_new_rows:,}"
    )

    print(
        f"Excel file: {OUTPUT_FILE}"
    )

    print(
        "=" * 80
    )