from pathlib import Path
import json
import time
import pandas as pd

from config import CITIES
from api_clients import (
    fetch_weather, fetch_air_quality, fetch_country,
    fetch_world_bank, fetch_exchange_rates, save_raw
)

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def hourly_to_df(city, weather, air):
    w = pd.DataFrame(weather["hourly"])
    a = pd.DataFrame(air["hourly"])

    w["time"] = pd.to_datetime(w["time"])
    a["time"] = pd.to_datetime(a["time"])

    df = pd.merge(w, a, on="time", how="inner")
    df["city"] = city["city"]
    df["country"] = city["country"]
    df["iso2"] = city["iso2"]
    df["lat"] = city["lat"]
    df["lon"] = city["lon"]
    df["currency"] = city["currency"]
    return df

def main():
    all_rows = []

    print("\nCITYFUSION - 5 API DATA COLLECTION\n")

    # API 5 is called once because rates are shared across cities.
    print("Calling API 5/5: ExchangeRate-API...")
    rates = fetch_exchange_rates()
    save_raw("05_exchange_rates.json", rates)

    for i, city in enumerate(CITIES, start=1):
        print(f"\n[{i}/{len(CITIES)}] {city['city']}")

        # API 1: Weather
        weather = fetch_weather(city)
        save_raw(f"01_weather_{city['iso2']}_{city['city'].replace(' ', '_')}.json", weather)

        # API 2: Air Quality
        air = fetch_air_quality(city)
        save_raw(f"02_air_quality_{city['iso2']}_{city['city'].replace(' ', '_')}.json", air)

        # API 3: REST Countries
        country = fetch_country(city["iso2"])
        save_raw(f"03_country_{city['iso2']}.json", country)

        # API 4: World Bank
        wb = fetch_world_bank(city["wb"])
        save_raw(f"04_world_bank_{city['wb']}.json", wb)

        country_obj = country[0] if isinstance(country, list) else country
        currencies = country_obj.get("currencies", {})
        currency_name = ""
        if currencies:
            currency_name = next(iter(currencies.values())).get("name", "")

        exchange_rate = rates.get("rates", {}).get(city["currency"])

        df = hourly_to_df(city, weather, air)
        df["population"] = wb.get("population")
        df["gdp_usd"] = wb.get("gdp_usd")
        df["urban_population_pct"] = wb.get("urban_population_pct")
        df["currency_name"] = currency_name
        df["usd_to_local"] = exchange_rate

        all_rows.append(df)
        time.sleep(0.25)

    final = pd.concat(all_rows, ignore_index=True)
    final.to_csv(PROCESSED_DIR / "fused_dataset.csv", index=False)

    print("\nSUCCESS")
    print(f"Saved {len(final):,} rows to data/processed/fused_dataset.csv")
    print("Raw API responses are saved in data/raw/")
    print("\nThis file is the result of RAW DATA FUSION.")
    print(final.head())

if __name__ == "__main__":
    main()
