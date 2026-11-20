import requests

from config import TOMTOM_API_KEY


# ============================================================
# TOMTOM API - CONNECTION TEST
# ============================================================

BASE_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"


# Pune coordinates
LATITUDE = 18.5204
LONGITUDE = 73.8567


print("=" * 70)
print("TOMTOM TRAFFIC API TEST")
print("=" * 70)


if not TOMTOM_API_KEY or not TOMTOM_API_KEY.strip():
    print("\nERROR: TOMTOM_API_KEY is missing.")
    print("Check config.py")
    raise SystemExit(1)


print("\nTomTom API key loaded successfully.")


params = {
    "point": f"{LATITUDE},{LONGITUDE}",
    "unit": "KMPH",
    "key": TOMTOM_API_KEY
}


try:

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=20
    )

    print("\nHTTP Status:", response.status_code)

    if response.status_code != 200:

        print("\nERROR: TomTom request failed.")

        try:
            print("Response:", response.json())
        except Exception:
            print("Response:", response.text)

        raise SystemExit(1)


    data = response.json()

    flow = data.get("flowSegmentData", {})

    print("\nAPI CONNECTION SUCCESSFUL")

    print("\nLocation:")
    print("Latitude :", LATITUDE)
    print("Longitude:", LONGITUDE)

    print("\nTraffic Data:")

    print(
        "Current Speed:",
        flow.get("currentSpeed"),
        "km/h"
    )

    print(
        "Free Flow Speed:",
        flow.get("freeFlowSpeed"),
        "km/h"
    )

    print(
        "Confidence:",
        flow.get("confidence")
    )

    print(
        "Road Closure:",
        flow.get("roadClosure")
    )

    print("\n" + "=" * 70)
    print("TOMTOM API TEST SUCCESSFUL")
    print("=" * 70)


except requests.exceptions.Timeout:

    print("\nERROR: TomTom request timed out.")


except requests.exceptions.ConnectionError:

    print("\nERROR: Internet connection problem.")


except requests.exceptions.RequestException as exc:

    print("\nERROR: TomTom request failed.")
    print(exc)


except Exception as exc:

    print("\nERROR: Unexpected error.")
    print(exc)