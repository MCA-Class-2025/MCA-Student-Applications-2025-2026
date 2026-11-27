import requests
import pandas as pd


# --------------------------------------------------
# API 1: Nominatim / OpenStreetMap
# --------------------------------------------------

def get_location(place):
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": place,
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }

    headers = {
        "User-Agent": "NoticeSenseAI/1.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        return None

    address_info = data[0].get("address", {})
    country_code = address_info.get("country_code", "").upper()
    country = address_info.get("country", "")

    return {
        "place": place,
        "address": data[0]["display_name"],
        "latitude": float(data[0]["lat"]),
        "longitude": float(data[0]["lon"]),
        "country": country,
        "country_code": country_code
    }


# --------------------------------------------------
# API 2: Open-Meteo Weather
# Gets 7 days of weather data
# --------------------------------------------------

def get_weather(latitude, longitude):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum,"
            "weather_code"
        ),
        "forecast_days": 7,
        "timezone": "auto"
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


# --------------------------------------------------
# API 3: Open-Meteo Air Quality
# Gets hourly AQI, PM2.5, PM10 and groups to daily
# --------------------------------------------------

def get_air_quality(latitude, longitude):
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "pm2_5,pm10,us_aqi",
        "timezone": "auto"
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    aq_data = response.json()

    if not aq_data or "hourly" not in aq_data:
        return {}

    hourly = aq_data["hourly"]
    times = hourly.get("time", [])
    pm2_5 = hourly.get("pm2_5", [])
    pm10 = hourly.get("pm10", [])
    us_aqi = hourly.get("us_aqi", [])

    daily_records = {}
    for i in range(len(times)):
        date_str = times[i][:10]  # Get YYYY-MM-DD
        if date_str not in daily_records:
            daily_records[date_str] = {"pm2_5": [], "pm10": [], "us_aqi": []}

        if i < len(pm2_5) and pm2_5[i] is not None:
            daily_records[date_str]["pm2_5"].append(pm2_5[i])
        if i < len(pm10) and pm10[i] is not None:
            daily_records[date_str]["pm10"].append(pm10[i])
        if i < len(us_aqi) and us_aqi[i] is not None:
            daily_records[date_str]["us_aqi"].append(us_aqi[i])

    daily_averages = {}
    for date_str, lists in daily_records.items():
        daily_averages[date_str] = {
            "pm2_5": round(sum(lists["pm2_5"]) / len(lists["pm2_5"]), 2) if lists["pm2_5"] else 0.0,
            "pm10": round(sum(lists["pm10"]) / len(lists["pm10"]), 2) if lists["pm10"] else 0.0,
            "us_aqi": round(sum(lists["us_aqi"]) / len(lists["us_aqi"]), 2) if lists["us_aqi"] else 0.0
        }
    return daily_averages


# --------------------------------------------------
# API 4: Hipo Universities List API
# --------------------------------------------------

def get_university_info(university_name):
    url = "http://universities.hipolabs.com/search"
    search_name = university_name.split(",")[0].strip()
    params = {"name": search_name}
    try:
        headers = {"User-Agent": "NoticeSenseAI/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            first_match = data[0]
            return {
                "uni_name": first_match.get("name", ""),
                "domain": first_match.get("domains", [""])[0] if first_match.get("domains") else "N/A",
                "web_page": first_match.get("web_pages", [""])[0] if first_match.get("web_pages") else "N/A",
                "alpha_two_code": first_match.get("alpha_two_code", "")
            }
    except Exception as e:
        print(f"Error fetching university info: {e}")
    return {
        "uni_name": search_name,
        "domain": "N/A",
        "web_page": "N/A",
        "alpha_two_code": ""
    }


# --------------------------------------------------
# API 5: REST Countries API
# --------------------------------------------------

def get_country_info(country_code):
    if not country_code:
        return {}
    url = f"https://restcountries.com/v3.1/alpha/{country_code}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            country_data = data[0]
            currencies = country_data.get("currencies", {})
            currency_info = "N/A"
            if currencies:
                curr_code = list(currencies.keys())[0]
                curr_details = currencies[curr_code]
                currency_info = f"{curr_details.get('name', '')} ({curr_code} {curr_details.get('symbol', '')})"

            languages = list(country_data.get("languages", {}).values())
            languages_str = ", ".join(languages) if languages else "N/A"

            return {
                "official_name": country_data.get("name", {}).get("official", "N/A"),
                "capital": country_data.get("capital", ["N/A"])[0] if country_data.get("capital") else "N/A",
                "population": country_data.get("population", 0),
                "currency": currency_info,
                "languages": languages_str,
                "flag": country_data.get("flag", ""),
                "region": country_data.get("region", "N/A")
            }
    except Exception as e:
        print(f"Error fetching country info: {e}")
    return {}


# --------------------------------------------------
# Extra API: Wikipedia Summary API
# --------------------------------------------------

def get_wikipedia_summary(title, fallback_title=None):
    headers = {
        "User-Agent": "NoticeSenseAI/1.0 (contact@noticesense.ai)"
    }
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "title": data.get("title", title),
                "extract": data.get("extract", ""),
                "thumbnail": data.get("thumbnail", {}).get("source", None)
            }
    except Exception as e:
        print(f"Error fetching Wikipedia summary for {title}: {e}")

    if fallback_title:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{fallback_title.replace(' ', '_')}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "title": data.get("title", fallback_title),
                    "extract": data.get("extract", ""),
                    "thumbnail": data.get("thumbnail", {}).get("source", None)
                }
        except Exception as e:
            print(f"Error fetching Wikipedia summary for fallback {fallback_title}: {e}")

    return None


# --------------------------------------------------
# Create fused dataset (5 APIs Fused)
# --------------------------------------------------

def create_fused_dataset(locations):

    all_records = []

    for place in locations:

        print(f"\nFetching location: {place}")

        # API 1: Nominatim Geocoding
        location = get_location(place)

        if location is None:
            print(f"Location not found: {place}")
            continue

        print(
            f"Coordinates: "
            f"{location['latitude']}, "
            f"{location['longitude']}"
        )

        # API 2: Open-Meteo Weather using coordinates
        try:
            weather = get_weather(
                location["latitude"],
                location["longitude"]
            )
            daily_weather = weather.get("daily", {})
        except Exception as e:
            print(f"Error fetching weather: {e}")
            daily_weather = {}

        # API 3: Open-Meteo Air Quality using coordinates
        try:
            daily_aq = get_air_quality(
                location["latitude"],
                location["longitude"]
            )
        except Exception as e:
            print(f"Error fetching air quality: {e}")
            daily_aq = {}

        # API 4: Hipo Universities using university name
        uni_info = get_university_info(place)

        # API 5: REST Countries using country_code from API 1 or API 4
        country_code = location.get("country_code") or uni_info.get("alpha_two_code")
        country_info = get_country_info(country_code)

        # Merge daily arrays
        dates = daily_weather.get("time", [])
        if not dates and daily_aq:
            dates = list(daily_aq.keys())

        for i in range(len(dates)):
            date_str = dates[i]
            
            # Weather details
            max_temp = daily_weather.get("temperature_2m_max", [None]*len(dates))[i] if "temperature_2m_max" in daily_weather else None
            min_temp = daily_weather.get("temperature_2m_min", [None]*len(dates))[i] if "temperature_2m_min" in daily_weather else None
            precip = daily_weather.get("precipitation_sum", [None]*len(dates))[i] if "precipitation_sum" in daily_weather else None
            wcode = daily_weather.get("weather_code", [None]*len(dates))[i] if "weather_code" in daily_weather else None

            # AQ details
            aq_for_day = daily_aq.get(date_str, {"pm2_5": None, "pm10": None, "us_aqi": None})

            record = {
                "Date": date_str,
                "Place": location["place"],
                "Address": location["address"],
                "Latitude": location["latitude"],
                "Longitude": location["longitude"],
                "Temperature Max (°C)": max_temp,
                "Temperature Min (°C)": min_temp,
                "Precipitation (mm)": precip,
                "Weather Code": wcode,
                "PM2.5 (µg/m³)": aq_for_day["pm2_5"],
                "PM10 (µg/m³)": aq_for_day["pm10"],
                "Air Quality Index (US AQI)": aq_for_day["us_aqi"],
                "University Webpage": uni_info.get("web_page", "N/A"),
                "University Domain": uni_info.get("domain", "N/A"),
                "Official Country Name": country_info.get("official_name", "N/A"),
                "Capital City": country_info.get("capital", "N/A"),
                "Country Population": country_info.get("population", 0),
                "Country Currency": country_info.get("currency", "N/A"),
                "Languages": country_info.get("languages", "N/A"),
                "Flag": country_info.get("flag", "")
            }

            all_records.append(record)

    return pd.DataFrame(all_records)


# --------------------------------------------------
# Save Excel
# --------------------------------------------------

def save_to_excel(df):

    output_file = "fused_api_data.xlsx"

    df.to_excel(
        output_file,
        index=False,
        sheet_name="Fused Data"
    )

    print(
        f"\nExcel file created successfully: "
        f"{output_file}"
    )


# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":

    locations = [
        "SNDT Women's University, Mumbai",
        "University of Mumbai, Mumbai",
        "IIT Bombay, Mumbai",
        "VJTI, Mumbai",
        "NMIMS, Mumbai"
    ]

    print("=" * 60)
    print("NoticeSenseAI - API Data Fusion")
    print("5 Locations × 7 Days")
    print("=" * 60)

    df = create_fused_dataset(locations)

    if df.empty:

        print("\nNo data was collected.")

    else:

        print("\n" + "=" * 60)
        print("FUSED DATASET")
        print("=" * 60)

        print(df.to_string(index=False))

        print("\nTotal records:", len(df))

        save_to_excel(df)