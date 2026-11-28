import requests
import pandas as pd
from config import USDA_API_KEY, API_DATA_DIR

def collect_usda_data(food_names):
    results = []

    if not USDA_API_KEY:
        print("USDA API key missing!")
        return pd.DataFrame()

    url = "https://api.nal.usda.gov/fdc/v1/foods/search"

    for food in food_names:
        try:
            response = requests.get(
                url,
                params={
                    "api_key": USDA_API_KEY,
                    "query": food,
                    "pageSize": 1
                },
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if data.get("foods"):
                item = data["foods"][0]

                results.append({
                    "food_name": food,
                    "fdc_id": item.get("fdcId"),
                    "usda_description": item.get("description"),
                    "usda_data_type": item.get("dataType")
                })

            print("USDA collected:", food)

        except requests.RequestException as e:
            print("USDA error:", food, e)

    df = pd.DataFrame(results)

    df.to_csv(
        f"{API_DATA_DIR}/usda_data.csv",
        index=False
    )

    return df