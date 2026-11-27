import requests
import pandas as pd
from config import OPENWEATHER_API_KEY, API_DATA_DIR

def collect_weather_data(city="Mumbai"):
    if not OPENWEATHER_API_KEY:
        print("OpenWeather API key missing!")
        return pd.DataFrame()

    url = "https://api.openweathermap.org/data/2.5/weather"

    try:
        response = requests.get(
            url,
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            },
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        result = {
            "city": data.get("name"),
            "temperature_c": data["main"].get("temp"),
            "feels_like_c": data["main"].get("feels_like"),
            "humidity": data["main"].get("humidity"),
            "weather": data["weather"][0].get("main"),
            "weather_description": data["weather"][0].get("description"),
            "wind_speed": data["wind"].get("speed")
        }

        df = pd.DataFrame([result])

        df.to_csv(
            f"{API_DATA_DIR}/weather_data.csv",
            index=False
        )

        print("Weather data collected successfully!")
        return df

    except requests.RequestException as e:
        print("Weather API error:", e)
        return pd.DataFrame()