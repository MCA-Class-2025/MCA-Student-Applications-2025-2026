import requests


# =========================================================
# OPEN-METEO AIR QUALITY API
# =========================================================

AIR_QUALITY_API_URL = (
    "https://air-quality-api.open-meteo.com/v1/air-quality"
)


# =========================================================
# GET AIR QUALITY
# =========================================================

def get_air_quality(
    latitude,
    longitude
):

    params = {

        "latitude": latitude,

        "longitude": longitude,

        # Air quality variables
        "current": [
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "ozone",
            "european_aqi",
            "us_aqi"
        ],

        "timezone": "auto"
    }


    # =====================================================
    # API REQUEST
    # =====================================================

    response = requests.get(

        AIR_QUALITY_API_URL,

        params=params,

        timeout=20
    )


    # =====================================================
    # ERROR HANDLING
    # =====================================================

    response.raise_for_status()


    # =====================================================
    # JSON RESPONSE
    # =====================================================

    data = response.json()


    current = data.get(
        "current",
        {}
    )


    # =====================================================
    # RETURN CLEAN DATA
    # =====================================================

    return {

        "latitude":
            latitude,

        "longitude":
            longitude,

        "pm10":
            current.get("pm10"),

        "pm2_5":
            current.get("pm2_5"),

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

        "european_aqi":
            current.get(
                "european_aqi"
            ),

        "us_aqi":
            current.get(
                "us_aqi"
            )
    }