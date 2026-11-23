import os
import json
import time
import requests
from pathlib import Path

RAW_DIR = Path("data/raw")
os.makedirs(RAW_DIR, exist_ok=True)

def fetch_with_retry(url, retries=2, timeout=25):
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
            else:
                print(f"API failed after {retries} retries for URL {url}: {e}")
    return None

def fetch_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
    res = fetch_with_retry(url)
    return res if res else {}

def fetch_air_quality(lat, lon):
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=pm10,pm2_5,nitrogen_dioxide,ozone"
    res = fetch_with_retry(url)
    return res if res else {}

def fetch_country(country_code):
    url = f"https://restcountries.com/v3.1/alpha/{country_code}"
    res = fetch_with_retry(url)
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    elif isinstance(res, dict):
        return res
    return {}

def fetch_world_bank(country_code):
    metrics = {
        "population": "SP.POP.TOTL",
        "gdp": "NY.GDP.MKTP.CD",
        "urban_pct": "SP.URB.TOTL.IN.ZS"
    }
    data = {}
    for key, indicator in metrics.items():
        url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}?format=json&per_page=1"
        res = fetch_with_retry(url)
        try:
            if res and len(res) > 1 and res[1]:
                for entry in res[1]:
                    if entry.get("value") is not None:
                        data[key] = entry["value"]
                        break
        except Exception:
            data[key] = None
    return data

def fetch_exchange_rates():
    url = "https://open.er-api.com/v6/latest/USD"
    res = fetch_with_retry(url)
    return res if res else {}

def collect_all_apis(cities_df):
    results = []
    
    print("Fetching exchange rates...")
    exchange_data = fetch_exchange_rates()
    rates = exchange_data.get("rates", {})
    
    # Fallback for exchange rates if API failed
    if not rates:
        try:
            with open(RAW_DIR / "exchange_rates.json", "r") as f:
                exchange_data = json.load(f)
                rates = exchange_data.get("rates", {})
                print("Used CACHED ExchangeRate API data.")
        except FileNotFoundError:
            pass
            
    if rates:
        with open(RAW_DIR / "exchange_rates.json", "w") as f:
            json.dump(exchange_data, f)
        
    for idx, row in cities_df.iterrows():
        city = row["city"]
        lat = row["latitude"]
        lon = row["longitude"]
        cc = row["country_code"]
        
        print(f"Fetching data for {city}...")
        weather = fetch_weather(lat, lon)
        air = fetch_air_quality(lat, lon)
        country = fetch_country(cc)
        wb = fetch_world_bank(cc)
        
        # Check if fallback to cached data is needed
        cached_used = False
        raw_file = RAW_DIR / f"{city.replace(' ', '_')}_raw.json"
        
        if (not weather or not air or not country) and raw_file.exists():
            try:
                with open(raw_file, "r") as f:
                    cached = json.load(f)
                    if not weather: weather = cached.get("weather", {})
                    if not air: air = cached.get("air_quality", {})
                    if not country: country = cached.get("country", {})
                    if not wb: wb = cached.get("world_bank", {})
                cached_used = True
            except Exception:
                pass
                
        if cached_used:
            print(f"Used CACHED raw API data for {city} due to timeout.")
        
        # Save raw JSON
        city_raw = {
            "weather": weather,
            "air_quality": air,
            "country": country,
            "world_bank": wb
        }
        with open(raw_file, "w") as f:
            json.dump(city_raw, f)
            
        # Compile a flat dictionary for this city
        flat_data = {
            "city": city,
            "country": row["country"],
            "country_code": cc,
            "latitude": lat,
            "longitude": lon,
            "base_population": row["population"],
            "cached_used": cached_used
        }
        
        # Extract Weather
        current_w = weather.get("current", {})
        flat_data["temperature"] = current_w.get("temperature_2m")
        flat_data["humidity"] = current_w.get("relative_humidity_2m")
        flat_data["precipitation"] = current_w.get("precipitation")
        flat_data["wind_speed"] = current_w.get("wind_speed_10m")
        
        # Extract Air Quality
        current_a = air.get("current", {})
        if not current_a and "hourly" in air:
            # Safely grab the last valid entry in the hourly arrays
            hourly = air["hourly"]
            
            def get_last_valid(arr):
                for val in reversed(arr):
                    if val is not None: return val
                return None
                
            flat_data["pm2_5"] = get_last_valid(hourly.get("pm2_5", []))
            flat_data["pm10"] = get_last_valid(hourly.get("pm10", []))
            flat_data["no2"] = get_last_valid(hourly.get("nitrogen_dioxide", []))
            flat_data["o3"] = get_last_valid(hourly.get("ozone", []))
        else:
            flat_data["pm2_5"] = current_a.get("pm2_5")
            flat_data["pm10"] = current_a.get("pm10")
            flat_data["no2"] = current_a.get("nitrogen_dioxide")
            flat_data["o3"] = current_a.get("ozone")
        
        # Extract Country Data
        flat_data["region"] = country.get("region")
        flat_data["subregion"] = country.get("subregion")
        currencies = country.get("currencies", {})
        currency_code = list(currencies.keys())[0] if currencies else "USD"
        flat_data["currency"] = currency_code
        
        languages = country.get("languages", {})
        flat_data["primary_language"] = list(languages.values())[0] if languages else "Unknown"
        
        # Extract Exchange Rate
        flat_data["exchange_rate"] = rates.get(currency_code, 1.0)
        
        # Extract World Bank
        flat_data["wb_population"] = wb.get("population")
        flat_data["wb_gdp"] = wb.get("gdp")
        flat_data["wb_urban_pct"] = wb.get("urban_pct")
        
        results.append(flat_data)
        time.sleep(0.5) # respect rate limits
        
    return results