import io
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import requests
import rasterio

from config import (
    COPERNICUS_CLIENT_ID,
    COPERNICUS_CLIENT_SECRET,
)

from pathlib import Path


# ============================================================
# COPERNICUS SENTINEL-5P NO2 API
# ============================================================
# This version:
# 1. Tests Copernicus authentication.
# 2. Reads cities from the CPCB historical dataset.
# 3. Uses coordinates from a supplied coordinates file when
#    available, otherwise uses a small built-in fallback.
# 4. Requests real Sentinel-5P NO2 observations.
# 5. Saves only cities for which a real valid observation exists.
#
# It never creates fake NO2 values.
# ============================================================


BASE_DIR = Path(__file__).resolve().parent

CPCB_FILE = BASE_DIR / "data" / "cpcb_historical_data.csv"

COORDINATES_FILE = (
    BASE_DIR / "live_data" / "openweather_city_coordinates.csv"
)

OUTPUT_DIR = BASE_DIR / "live_data"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = (
    OUTPUT_DIR / "sentinel5p_no2_current.csv"
)


TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)

PROCESS_URL = (
    "https://sh.dataspace.copernicus.eu/"
    "process/v1"
)


# ============================================================
# FALLBACK COORDINATES FOR THE ORIGINAL MONITORED CITIES
# ============================================================

FALLBACK_COORDINATES = {
    "Ahmedabad": (23.0225, 72.5714),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2704),
    "Delhi": (28.6139, 77.2090),
    "Hyderabad": (17.3850, 78.4867),
    "Jaipur": (26.9124, 75.7873),
    "Kolkata": (22.5726, 88.3639),
    "Mumbai": (19.0760, 72.8777),
    "Nagpur": (21.1458, 79.0882),
    "Nashik": (19.9975, 73.7898),
    "Pune": (18.5204, 73.8567),
}


# ============================================================
# LOAD CPCB CITIES
# ============================================================

def load_cpcb_cities():
    if not CPCB_FILE.exists():
        raise FileNotFoundError(
            f"CPCB dataset not found: {CPCB_FILE}"
        )

    df = pd.read_csv(
        CPCB_FILE,
        usecols=["City"],
        low_memory=False
    )

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

    return sorted(
        cities.unique().tolist()
    )


# ============================================================
# LOAD COORDINATES
# ============================================================

def load_coordinates(cities):
    """
    Read coordinates produced by openweather_api.py.

    Expected columns:
        City
        Latitude
        Longitude
    """

    coordinates = {}

    if COORDINATES_FILE.exists():

        try:
            df = pd.read_csv(
                COORDINATES_FILE
            )

            df.columns = [
                str(c).strip()
                for c in df.columns
            ]

            if {
                "City",
                "Latitude",
                "Longitude",
            }.issubset(df.columns):

                for _, row in df.iterrows():

                    city = str(
                        row["City"]
                    ).strip()

                    try:

                        lat = float(
                            row["Latitude"]
                        )

                        lon = float(
                            row["Longitude"]
                        )

                        if (
                            np.isfinite(lat)
                            and np.isfinite(lon)
                        ):
                            coordinates[city] = (
                                lat,
                                lon
                            )

                    except (
                        TypeError,
                        ValueError
                    ):
                        pass

        except Exception as exc:

            print(
                "Warning: Could not read coordinate file."
            )

            print(exc)

    # Add the original fallback coordinates
    # without overriding better coordinates.
    for city, coords in FALLBACK_COORDINATES.items():

        if city not in coordinates:
            coordinates[city] = coords

    # Keep only requested CPCB cities.
    return {
        city: coordinates[city]
        for city in cities
        if city in coordinates
    }


# ============================================================
# GET COPERNICUS ACCESS TOKEN
# ============================================================

def get_access_token():
    """Get a temporary Copernicus access token."""

    if (
        not COPERNICUS_CLIENT_ID
        or not COPERNICUS_CLIENT_SECRET
    ):
        raise ValueError(
            "COPERNICUS_CLIENT_ID or "
            "COPERNICUS_CLIENT_SECRET is missing "
            "from config.py"
        )

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": COPERNICUS_CLIENT_ID,
            "client_secret": COPERNICUS_CLIENT_SECRET,
        },
        timeout=30,
    )

    if response.status_code != 200:

        try:
            detail = response.json()

        except Exception:
            detail = response.text

        raise RuntimeError(
            f"Copernicus authentication failed "
            f"(HTTP {response.status_code}): {detail}"
        )

    token = response.json().get(
        "access_token"
    )

    if not token:
        raise RuntimeError(
            "Copernicus authentication succeeded "
            "but no access token was returned."
        )

    return token


# ============================================================
# REQUEST SENTINEL-5P NO2
# ============================================================

def get_no2_data(
    latitude,
    longitude,
    days_back=2,
    token=None
):
    """
    Request Sentinel-5P NO2 data around a location.

    Returns:
        Mean valid NO2 value as float,
        or None when no valid observation exists.
    """

    if token is None:
        token = get_access_token()

    delta = 0.25

    bbox = [
        longitude - delta,
        latitude - delta,
        longitude + delta,
        latitude + delta,
    ]

    evalscript = """
    //VERSION=3

    function setup() {
        return {
            input: ["NO2", "dataMask"],
            output: {
                bands: 2,
                sampleType: "FLOAT32"
            }
        };
    }

    function evaluatePixel(sample) {
        return [
            sample.NO2,
            sample.dataMask
        ];
    }
    """

    end_time = datetime.now(
        timezone.utc
    )

    start_time = (
        end_time
        - timedelta(days=days_back)
    )

    request_body = {
        "input": {
            "bounds": {
                "properties": {
                    "crs": (
                        "http://www.opengis.net/def/"
                        "crs/OGC/1.3/CRS84"
                    )
                },
                "bbox": bbox,
            },
            "data": [
                {
                    "type": "sentinel-5p-l2",
                    "dataFilter": {
                        "timeRange": {
                            "from": start_time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ"
                            ),
                            "to": end_time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ"
                            ),
                        },
                        "timeliness": "NRTI",
                    },
                }
            ],
        },
        "output": {
            "width": 10,
            "height": 10,
            "responses": [
                {
                    "identifier": "default",
                    "format": {
                        "type": "image/tiff"
                    },
                }
            ],
        },
        "evalscript": evalscript,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        PROCESS_URL,
        headers=headers,
        json=request_body,
        timeout=120,
    )

    if response.status_code != 200:

        try:
            detail = response.json()

        except Exception:
            detail = response.text

        raise RuntimeError(
            f"Sentinel-5P request failed "
            f"(HTTP {response.status_code}): {detail}"
        )

    if not response.content:
        return None

    # Read TIFF directly from the API response.
    with rasterio.open(
        io.BytesIO(response.content)
    ) as dataset:

        data = dataset.read()

    if data.shape[0] < 2:
        return None

    no2_values = data[0]
    data_mask = data[1]

    # Keep only valid pixels.
    valid_values = no2_values[
        data_mask > 0
    ]

    valid_values = valid_values[
        np.isfinite(valid_values)
    ]

    if len(valid_values) == 0:
        return None

    return float(
        np.mean(valid_values)
    )


# ============================================================
# MAIN COLLECTION
# ============================================================

if __name__ == "__main__":

    print("=" * 90)
    print("COPERNICUS SENTINEL-5P NO2 - REAL DATA COLLECTION")
    print("=" * 90)

    try:

        # ----------------------------------------------------
        # AUTHENTICATION
        # ----------------------------------------------------

        print("\nChecking Copernicus authentication...")

        token = get_access_token()

        print(
            "Copernicus authentication: SUCCESS"
        )

        # ----------------------------------------------------
        # CITIES
        # ----------------------------------------------------

        cities = load_cpcb_cities()

        coordinates = load_coordinates(
            cities
        )

        print(
            f"\nCPCB cities found: {len(cities)}"
        )

        print(
            f"Cities with coordinates: "
            f"{len(coordinates)}"
        )

        missing_coordinates = [
            city
            for city in cities
            if city not in coordinates
        ]

        if missing_coordinates:

            print(
                "\nCities skipped because no coordinates "
                "are available:"
            )

            for city in missing_coordinates:
                print("-", city)

        # ----------------------------------------------------
        # QUERY SENTINEL-5P
        # ----------------------------------------------------

        records = []
        failed = []

        print(
            "\nRequesting real Sentinel-5P observations..."
        )

        for number, city in enumerate(
            coordinates,
            start=1
        ):

            latitude, longitude = (
                coordinates[city]
            )

            print(
                f"\n[{number}/{len(coordinates)}] "
                f"{city}"
            )

            try:

                no2 = get_no2_data(
                    latitude,
                    longitude,
                    days_back=2,
                    token=token,
                )

                if no2 is None:

                    print(
                        "No valid Sentinel-5P "
                        "NO2 observation available."
                    )

                    failed.append(
                        (
                            city,
                            "No valid observation"
                        )
                    )

                    continue

                record = {
                    "City": city,
                    "Latitude": latitude,
                    "Longitude": longitude,
                    "Satellite": "Sentinel-5P",
                    "Parameter": "NO2",
                    "Mean_NO2": no2,
                    "Observation_Window_Days": 2,
                    "Collected_At_UTC": (
                        datetime.now(
                            timezone.utc
                        ).strftime(
                            "%Y-%m-%d %H:%M:%S UTC"
                        )
                    ),
                }

                records.append(record)

                print(
                    "Status: SUCCESS"
                )

                print(
                    f"Mean NO2: {no2:.8f}"
                )

            except Exception as exc:

                print(
                    "ERROR:",
                    exc
                )

                failed.append(
                    (
                        city,
                        str(exc)
                    )
                )

        # ----------------------------------------------------
        # SAVE ONLY REAL OBSERVATIONS
        # ----------------------------------------------------

        if records:

            df = pd.DataFrame(
                records
            )

            df.to_csv(
                OUTPUT_FILE,
                index=False
            )

            print(
                "\n" + "=" * 90
            )

            print(
                "SENTINEL-5P COLLECTION SUMMARY"
            )

            print(
                "=" * 90
            )

            print(
                f"\nCPCB cities: "
                f"{len(cities)}"
            )

            print(
                f"Cities with coordinates: "
                f"{len(coordinates)}"
            )

            print(
                f"Real satellite observations: "
                f"{len(df)}"
            )

            print(
                f"No observation / failed: "
                f"{len(failed)}"
            )

            print(
                f"\nSaved: {OUTPUT_FILE}"
            )

            print(
                "\nReal Sentinel-5P data:"
            )

            print(
                df.to_string(
                    index=False
                )
            )

        else:

            print(
                "\nNo valid Sentinel-5P observations "
                "were returned."
            )

        # ----------------------------------------------------
        # FAILED SUMMARY
        # ----------------------------------------------------

        if failed:

            print(
                "\n" + "=" * 90
            )

            print(
                "CITIES WITHOUT A VALID SATELLITE RESULT"
            )

            print(
                "=" * 90
            )

            for city, reason in failed:
                print(
                    f"- {city}: {reason}"
                )

        print(
            "\n" + "=" * 90
        )

        print(
            "SENTINEL-5P API TEST / COLLECTION COMPLETE"
        )

        print(
            "=" * 90
        )

    except Exception as exc:

        print(
            "\n" + "=" * 90
        )

        print(
            "COPERNICUS SENTINEL-5P ERROR"
        )

        print(
            "=" * 90
        )

        print(
            "\n",
            exc
        )