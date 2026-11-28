
import os
import requests
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
BASE_URL = "https://api.pexels.com/v1/search"


def search_destination_image(destination):

    if not PEXELS_API_KEY:
        print("Pexels API key is missing.")
        return None

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": destination,
        "per_page": 1
    }

    try:
        response = requests.get(
            BASE_URL,
            headers=headers,
            params=params,
            timeout=15
        )

        response.raise_for_status()
        data = response.json()

        if not data.get("photos"):
            print("No image found for:", destination)
            return None

        photo = data["photos"][0]

        return {
            "photo_id": photo["id"],
            "photographer": photo["photographer"],
            "image_url": photo["src"]["large"],
            "pexels_url": photo["url"]
        }

    except requests.RequestException as error:
        print("Pexels API Error:", error)
        return None
