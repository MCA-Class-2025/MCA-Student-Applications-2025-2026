"""
Free weather lookup (Open-Meteo - no API key needed).
"""

import requests

from .api_log import timed_api_call

WEATHER_CODE_MAP = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    61: "slight rain", 63: "moderate rain", 65: "heavy rain",
    66: "light freezing rain", 67: "heavy freezing rain",
    71: "slight snow fall", 73: "moderate snow fall", 75: "heavy snow fall",
    77: "snow grains",
    80: "slight rain showers", 81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


def get_city_coordinates(city_name: str) -> dict:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 1}

    with timed_api_call("Open-Meteo Geocoding", url, city_name):
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        results = response.json().get("results")

        if not results:
            raise ValueError(f"City '{city_name}' was not found.")

        first = results[0]

        return {
            "latitude": first["latitude"],
            "longitude": first["longitude"],
            "name": first.get("name", city_name),
            "country": first.get("country", ""),
        }


def get_weather_data(latitude: float, longitude: float) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True,
    }

    with timed_api_call(
        "Open-Meteo Forecast", url, f"lat={latitude}, lon={longitude}"
    ):
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        current = response.json().get("current_weather", {})
        weather_code = current.get("weathercode", 0)

        return {
            "temperature": current.get("temperature"),
            "windspeed": current.get("windspeed"),
            "weathercode": weather_code,
            "description": WEATHER_CODE_MAP.get(weather_code, "unknown weather"),
        }


def build_weather_image_prompt(
    city: str, weather_description: str, temperature: float
) -> str:
    return (
        f"A beautiful artistic storybook illustration of {city} "
        f"experiencing {weather_description} weather at {temperature} "
        f"degrees Celsius, vibrant colors, magical children's book "
        f"illustration style, highly detailed"
    )
