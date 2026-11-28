import os
import requests
from dotenv import load_dotenv

load_dotenv()

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

BASE_URL = "https://api.aviationstack.com/v1"


def get_flights(dep_iata=None, arr_iata=None):

    url = f"{BASE_URL}/flights"

    params = {
        "access_key": AVIATIONSTACK_API_KEY
    }

    if dep_iata:
        params["dep_iata"] = dep_iata

    if arr_iata:
        params["arr_iata"] = arr_iata

    response = requests.get(url, params=params)

    # Show the actual API error without exposing the API key
    if response.status_code != 200:
        try:
            error_data = response.json()
        except Exception:
            error_data = response.text

        print("Aviationstack API Error:")
        print(error_data)
        return None

    return response.json()