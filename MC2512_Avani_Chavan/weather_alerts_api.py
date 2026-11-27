from pathlib import Path
from urllib.parse import quote

import requests
import pandas as pd

from config import WEATHER_ALERTS_API_KEY


# ============================================================
# WEATHER ALERTS API - REAL DATA COLLECTION
# Uses cities from the CPCB historical dataset.
# WeatherAPI provides forecast + alert information.
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CPCB_FILE = BASE_DIR / "data" / "cpcb_historical_data.csv"
OUTPUT_DIR = BASE_DIR / "live_data"

OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "weather_alerts_current.csv"

BASE_URL = "https://api.weatherapi.com/v1/forecast.json"


# ============================================================
# LOAD CITIES FROM CPCB DATASET
# ============================================================

def load_cpcb_cities():
    if not CPCB_FILE.exists():
        print("\nERROR: CPCB historical dataset was not found.")
        print(f"Expected file: {CPCB_FILE}")
        raise SystemExit(1)

    try:
        df = pd.read_csv(
            CPCB_FILE,
            usecols=["City"],
            low_memory=False
        )
    except Exception as exc:
        print("\nERROR: Could not read CPCB historical dataset.")
        print(exc)
        raise SystemExit(1)

    cities = (
        df["City"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    cities = cities[
        (cities != "")
        & (cities.str.lower() != "unknown")
        & (cities.str.lower() != "nan")
    ]

    return sorted(cities.unique().tolist())


CITIES = load_cpcb_cities()


# ============================================================
# CHECK API KEY
# ============================================================

if (
    not WEATHER_ALERTS_API_KEY
    or not str(WEATHER_ALERTS_API_KEY).strip()
):

    print("\nERROR: WEATHER_ALERTS_API_KEY is missing.")
    print("Add WEATHER_ALERTS_API_KEY to config.py")
    raise SystemExit(1)


# ============================================================
# HEADER
# ============================================================

print("=" * 90)
print("WEATHER ALERTS API - REAL DATA COLLECTION")
print("=" * 90)

print(f"\nCPCB cities available: {len(CITIES)}")
print("WeatherAPI will be queried for all available cities.")

print("\nFirst cities:")
for city in CITIES[:20]:
    print("-", city)

if len(CITIES) > 20:
    print(f"... and {len(CITIES) - 20} more cities")


# ============================================================
# FETCH ALERT DATA
# ============================================================

records = []
failed_cities = []

print("\nFetching weather/alert data...")


for number, city in enumerate(CITIES, start=1):

    print(f"\n[{number}/{len(CITIES)}] Processing: {city}")

    params = {
        "key": WEATHER_ALERTS_API_KEY,
        "q": city,
        "days": 1,
        "alerts": "yes",
    }

    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30
        )

        if response.status_code != 200:

            print("ERROR: WeatherAPI request failed.")
            print("Status code:", response.status_code)

            try:
                error_data = response.json()
                print(
                    "Message:",
                    error_data.get("error", {}).get(
                        "message",
                        "Unknown error"
                    )
                )
            except Exception:
                print("Response:", response.text)

            failed_cities.append(
                (city, f"HTTP {response.status_code}")
            )

            continue

        data = response.json()

        location = data.get("location") or {}
        current = data.get("current") or {}
        alerts_container = data.get("alerts") or {}

        alerts = alerts_container.get("alert") or []

        # WeatherAPI returns a valid response even when
        # there are zero active alerts. That is valid real data.
        alert_count = len(alerts)

        # ----------------------------------------------------
        # Build one real record per city.
        # ----------------------------------------------------

        if alerts:

            for alert in alerts:

                record = {
                    "City": city,
                    "Latitude": location.get("lat"),
                    "Longitude": location.get("lon"),
                    "Location_Name": location.get("name"),
                    "Region": location.get("region"),
                    "Country": location.get("country"),
                    "Current_Temperature_C": current.get("temp_c"),
                    "Current_Humidity": current.get("humidity"),
                    "Current_Wind_KPH": current.get("wind_kph"),
                    "Current_Condition": (
                        current.get("condition") or {}
                    ).get("text"),
                    "Alert_Count": alert_count,
                    "Has_Active_Alert": True,
                    "Alert_Headline": alert.get("headline"),
                    "Alert_Event": alert.get("event"),
                    "Alert_Severity": alert.get("severity"),
                    "Alert_Urgency": alert.get("urgency"),
                    "Alert_Areas": alert.get("areas"),
                    "Alert_Categories": alert.get("category"),
                    "Alert_Certainty": alert.get("certainty"),
                    "Alert_Effective": alert.get("effective"),
                    "Alert_Expires": alert.get("expires"),
                    "Alert_Description": alert.get("desc"),
                    "Alert_Instruction": alert.get("instruction"),
                }

                records.append(record)

            print("Status: SUCCESS")
            print("Active alerts:", alert_count)

        else:

            # A real "no active alerts" response is kept.
            record = {
                "City": city,
                "Latitude": location.get("lat"),
                "Longitude": location.get("lon"),
                "Location_Name": location.get("name"),
                "Region": location.get("region"),
                "Country": location.get("country"),
                "Current_Temperature_C": current.get("temp_c"),
                "Current_Humidity": current.get("humidity"),
                "Current_Wind_KPH": current.get("wind_kph"),
                "Current_Condition": (
                    current.get("condition") or {}
                ).get("text"),
                "Alert_Count": 0,
                "Has_Active_Alert": False,
                "Alert_Headline": None,
                "Alert_Event": None,
                "Alert_Severity": None,
                "Alert_Urgency": None,
                "Alert_Areas": None,
                "Alert_Categories": None,
                "Alert_Certainty": None,
                "Alert_Effective": None,
                "Alert_Expires": None,
                "Alert_Description": None,
                "Alert_Instruction": None,
            }

            records.append(record)

            print("Status: SUCCESS")
            print("Active alerts: 0")
            print("No active weather alerts.")

    except requests.exceptions.Timeout:

        print(f"ERROR: Request timed out for {city}")

        failed_cities.append(
            (city, "Request timeout")
        )

    except requests.exceptions.ConnectionError:

        print(
            f"ERROR: Internet connection problem for {city}"
        )

        failed_cities.append(
            (city, "Connection error")
        )

    except requests.exceptions.RequestException as exc:

        print(
            f"ERROR: Request failed for {city}"
        )

        print(exc)

        failed_cities.append(
            (city, str(exc))
        )

    except ValueError as exc:

        print(
            f"ERROR: Invalid JSON returned for {city}"
        )

        print(exc)

        failed_cities.append(
            (city, "Invalid JSON")
        )

    except Exception as exc:

        print(
            f"ERROR: Unexpected error for {city}"
        )

        print(exc)

        failed_cities.append(
            (city, str(exc))
        )


# ============================================================
# CHECK RESULTS
# ============================================================

if not records:

    print("\n" + "=" * 90)
    print("NO WEATHER ALERT DATA RECEIVED")
    print("=" * 90)

    print("\nPossible reasons:")
    print("1. Weather Alerts API key is incorrect")
    print("2. API key is not active")
    print("3. City/location could not be resolved")
    print("4. API request limit reached")
    print("5. Internet connection problem")

    raise SystemExit(1)


# ============================================================
# CREATE DATAFRAME
# ============================================================

df = pd.DataFrame(records)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

successful_cities = (
    df["City"].dropna().astype(str).nunique()
)

cities_with_alerts = (
    df.loc[
        df["Has_Active_Alert"] == True,
        "City"
    ]
    .dropna()
    .astype(str)
    .nunique()
)

cities_without_alerts = (
    successful_cities - cities_with_alerts
)

print("\n" + "=" * 90)
print("WEATHER ALERTS API SUMMARY")
print("=" * 90)

print(
    f"\nCPCB cities requested      : {len(CITIES)}"
)

print(
    f"Successful cities          : {successful_cities}"
)

print(
    f"Cities with active alerts  : {cities_with_alerts}"
)

print(
    f"Cities with no active alerts: {cities_without_alerts}"
)

print(
    f"Total records saved        : {len(df)}"
)

print(
    f"\nSaved: {OUTPUT_FILE}"
)


# ============================================================
# DISPLAY RESULT
# ============================================================

display_columns = [
    "City",
    "Current_Temperature_C",
    "Current_Humidity",
    "Current_Condition",
    "Alert_Count",
    "Has_Active_Alert",
    "Alert_Event",
    "Alert_Severity",
    "Alert_Urgency",
]

display_columns = [
    column
    for column in display_columns
    if column in df.columns
]

print("\n" + "=" * 90)
print("REAL WEATHER ALERTS DATA")
print("=" * 90)

print(
    df[display_columns]
    .to_string(index=False)
)


# ============================================================
# FAILED CITY SUMMARY
# ============================================================

if failed_cities:

    print("\n" + "=" * 90)
    print("CITIES WITHOUT A SUCCESSFUL API RESPONSE")
    print("=" * 90)

    for city, reason in failed_cities:
        print(f"- {city}: {reason}")


print("\n" + "=" * 90)
print("WEATHER ALERTS API COLLECTION COMPLETE")
print("=" * 90)