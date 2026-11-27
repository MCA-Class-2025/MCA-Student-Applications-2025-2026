import requests


# =========================================================
# OPEN-METEO API
# =========================================================

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"


# =========================================================
# GET WEATHER DATA
# =========================================================

def get_weather(latitude, longitude):

    params = {
        "latitude": latitude,
        "longitude": longitude,

        # Current weather
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "weather_code"
        ],

        # Today's weather
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "rain_sum"
        ],

        "timezone": "auto"
    }

    response = requests.get(
        WEATHER_API_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    return data


# =========================================================
# SIMPLE WEATHER SUMMARY
# =========================================================

def get_weather_summary(latitude, longitude):

    data = get_weather(
        latitude,
        longitude
    )

    current = data.get(
        "current",
        {}
    )

    daily = data.get(
        "daily",
        {}
    )

    summary = {

        "latitude": latitude,

        "longitude": longitude,

        "temperature": current.get(
            "temperature_2m"
        ),

        "humidity": current.get(
            "relative_humidity_2m"
        ),

        "precipitation": current.get(
            "precipitation"
        ),

        "rain": current.get(
            "rain"
        ),

        "weather_code": current.get(
            "weather_code"
        ),

        "today_max_temperature": (
            daily.get(
                "temperature_2m_max",
                [None]
            )[0]
        ),

        "today_min_temperature": (
            daily.get(
                "temperature_2m_min",
                [None]
            )[0]
        ),

        "today_rainfall": (
            daily.get(
                "rain_sum",
                [None]
            )[0]
        ),

        "today_precipitation": (
            daily.get(
                "precipitation_sum",
                [None]
            )[0]
        )
    }

    return summary