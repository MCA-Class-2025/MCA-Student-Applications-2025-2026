import requests


# =========================================================
# NOMINATIM API
# =========================================================

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)


# =========================================================
# GEOCODE LOCATION
# =========================================================

def geocode_location(address):

    params = {

        "q": address,

        "format": "json",

        "limit": 1
    }

    headers = {

        "User-Agent":
            "FixAI-Maharashtra-Student-Project/1.0"
    }

    response = requests.get(

        NOMINATIM_URL,

        params=params,

        headers=headers,

        timeout=10
    )

    response.raise_for_status()

    results = response.json()


    if not results:

        return None


    result = results[0]


    return {

        "display_name":
            result.get("display_name"),

        "latitude":
            float(result["lat"]),

        "longitude":
            float(result["lon"]),

        "osm_type":
            result.get("type"),

        "osm_id":
            result.get("osm_id")
    }