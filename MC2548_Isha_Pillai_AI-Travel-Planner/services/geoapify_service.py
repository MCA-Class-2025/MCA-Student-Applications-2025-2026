import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

BASE_URL = "https://api.geoapify.com/v2/places"


def get_places(lat, lon):

    # Travel-related categories only
    categories = (
        "tourism.attraction,"
        "tourism.sights,"
        "entertainment.museum,"
        "entertainment.culture"
    )

    params = {
        "categories": categories,
        "filter": f"circle:{lon},{lat},10000",
        "limit": 20,
        "lang": "en",
        "apiKey": GEOAPIFY_API_KEY
    }

    response = requests.get(
        BASE_URL,
        params=params
    )

    if response.status_code != 200:

        try:
            error_data = response.json()
        except Exception:
            error_data = response.text

        print("Geoapify API Error:")
        print(error_data)

        return None

    return response.json()