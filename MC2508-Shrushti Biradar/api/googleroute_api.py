import os
import requests
from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

GOOGLE_ROUTES_API_KEY = os.getenv("GOOGLE_ROUTES_API_KEY")


# =========================================================
# GOOGLE ROUTES API URL
# =========================================================

ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"


# =========================================================
# GET ROUTE INFORMATION
# =========================================================

def get_route(
    origin,
    destination,
    travel_mode="DRIVE"
):
    """
    Calculate distance and travel time between origin
    and destination using Google Routes API.

    Example:

        get_route(
            "Mumbai",
            "Juhu Beach, Mumbai"
        )
    """

    # -----------------------------------------------------
    # CHECK API KEY
    # -----------------------------------------------------

    if not GOOGLE_ROUTES_API_KEY:
        raise ValueError(
            "GOOGLE_ROUTES_API_KEY is missing in the .env file."
        )


    # -----------------------------------------------------
    # REQUEST HEADERS
    # -----------------------------------------------------

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_ROUTES_API_KEY,
        "X-Goog-FieldMask": (
            "routes.distanceMeters,"
            "routes.duration,"
            "routes.staticDuration"
        )
    }


    # -----------------------------------------------------
    # REQUEST DATA
    # -----------------------------------------------------

    data = {

        "origin": {
            "address": origin
        },

        "destination": {
            "address": destination
        },

        "travelMode": travel_mode,

        "routingPreference": "TRAFFIC_AWARE",

        "computeAlternativeRoutes": False,

        "languageCode": "en-US",

        "units": "METRIC"
    }


    # -----------------------------------------------------
    # SEND REQUEST
    # -----------------------------------------------------

    response = requests.post(
        ROUTES_URL,
        headers=headers,
        json=data,
        timeout=30
    )


    # -----------------------------------------------------
    # CHECK RESPONSE
    # -----------------------------------------------------

    if response.status_code != 200:

        try:
            error_data = response.json()

        except Exception:
            error_data = response.text

        raise Exception(
            f"Google Routes API Error "
            f"{response.status_code}: {error_data}"
        )


    # -----------------------------------------------------
    # CONVERT RESPONSE TO JSON
    # -----------------------------------------------------

    result = response.json()


    # -----------------------------------------------------
    # CHECK ROUTES
    # -----------------------------------------------------

    routes = result.get("routes", [])

    if not routes:
        raise Exception(
            "No route found between the given locations."
        )


    # -----------------------------------------------------
    # FIRST / BEST ROUTE
    # -----------------------------------------------------

    route = routes[0]


    # =====================================================
    # DISTANCE
    # =====================================================

    distance_meters = route.get(
        "distanceMeters",
        0
    )

    distance_km = distance_meters / 1000


    # =====================================================
    # DURATION
    # =====================================================

    duration_string = route.get(
        "duration",
        "0s"
    )

    duration_seconds = parse_duration(
        duration_string
    )


    duration_minutes = round(
        duration_seconds / 60
    )


    # =====================================================
    # RETURN RESULT
    # =====================================================

    return {

        "origin": origin,

        "destination": destination,

        "distance_meters": distance_meters,

        "distance_km": round(
            distance_km,
            2
        ),

        "duration_seconds": duration_seconds,

        "duration_minutes": duration_minutes,

        "duration_text": format_duration(
            duration_seconds
        )
    }


# =========================================================
# PARSE GOOGLE DURATION
# =========================================================

def parse_duration(duration_string):
    """
    Convert Google duration such as:

        1234s

    into seconds.
    """

    try:

        if duration_string.endswith("s"):

            return float(
                duration_string[:-1]
            )

        return float(duration_string)

    except Exception:

        return 0


# =========================================================
# FORMAT DURATION
# =========================================================

def format_duration(seconds):

    seconds = int(seconds)

    hours = seconds // 3600

    minutes = (seconds % 3600) // 60


    if hours > 0:

        return f"{hours} hr {minutes} min"

    return f"{minutes} min"