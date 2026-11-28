import os
import requests
from dotenv import load_dotenv

load_dotenv()

EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")

BASE_URL = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/pair"


def convert_currency(from_currency, to_currency, amount):

    url = f"{BASE_URL}/{from_currency}/{to_currency}/{amount}"

    response = requests.get(url)

    if response.status_code != 200:
        try:
            error_data = response.json()
        except Exception:
            error_data = response.text

        print("ExchangeRate API Error:")
        print(error_data)
        return None

    return response.json()