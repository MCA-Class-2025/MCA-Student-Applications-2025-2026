import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

if not GOOGLE_PLACES_API_KEY:
    raise ValueError("GOOGLE_PLACES_API_KEY was not found in .env")


def search_places(location, place_type="restaurant"):
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.googleMapsUri"
    }

    data = {
        "textQuery": f"{place_type} in {location}"
    }

    response = requests.post(
        url,
        headers=headers,
        json=data
    )

    if response.status_code != 200:
        raise Exception(
            f"Places API Error: {response.status_code} - {response.text}"
        )

    return response.json().get("places", [])