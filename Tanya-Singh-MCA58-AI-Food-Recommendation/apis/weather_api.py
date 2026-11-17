import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv(
    "OPENWEATHER_API_KEY"
)

BASE_URL = (
    "https://api.openweathermap.org/data/2.5/weather"
)


def get_weather(city):

    if not OPENWEATHER_API_KEY:

        return {
            "success": False,
            "error": (
                "OPENWEATHER_API_KEY "
                "is missing from .env"
            )
        }

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }

    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=15
        )

        if response.status_code != 200:

            return {
                "success": False,
                "error": (
                    f"OpenWeather API Error: "
                    f"{response.status_code}"
                )
            }

        data = response.json()

        weather = data.get(
            "weather",
            [{}]
        )[0]

        main = data.get(
            "main",
            {}
        )

        result = {

            "city": data.get(
                "name",
                city
            ),

            "country": data.get(
                "sys",
                {}
            ).get(
                "country",
                ""
            ),

            "temperature": main.get(
                "temp"
            ),

            "feels_like": main.get(
                "feels_like"
            ),

            "humidity": main.get(
                "humidity"
            ),

            "weather": weather.get(
                "main",
                ""
            ),

            "description": weather.get(
                "description",
                ""
            ),

            "wind_speed": data.get(
                "wind",
                {}
            ).get(
                "speed"
            )
        }

        return {
            "success": True,
            "data": result
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def get_weather_category(city):

    result = get_weather(city)

    if not result["success"]:
        return result

    data = result["data"]

    weather = data["weather"].lower()

    temperature = data["temperature"]

    if "rain" in weather:

        category = "Rainy"

    elif "snow" in weather:

        category = "Cold"

    elif "cloud" in weather:

        category = "Cloudy"

    elif temperature is not None and temperature >= 30:

        category = "Hot"

    elif temperature is not None and temperature <= 20:

        category = "Cool"

    else:

        category = "Sunny"

    data["weather_category"] = category

    return {
        "success": True,
        "data": data
    }


if __name__ == "__main__":

    print("=" * 60)
    print("OPENWEATHERMAP API TEST")
    print("=" * 60)

    result = get_weather_category(
        "Mumbai"
    )

    if result["success"]:

        data = result["data"]

        print(
            "City:",
            data["city"]
        )

        print(
            "Temperature:",
            data["temperature"],
            "°C"
        )

        print(
            "Weather:",
            data["weather"]
        )

        print(
            "Description:",
            data["description"]
        )

        print(
            "Weather Category:",
            data["weather_category"]
        )

    else:

        print(
            "ERROR:",
            result["error"]
        )