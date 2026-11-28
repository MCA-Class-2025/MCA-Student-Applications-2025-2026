import os
import json
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

df_base = pd.read_csv("data/original_dataset.csv")
countries = df_base["country"].tolist()
print(f"Starting Multi-Section Encyclopedic Collection for {len(countries)} nations...")

HEADERS = {"User-Agent": "CountryWiseAI-Researcher/2.0 (academic.research@project.edu)"}

# Load reference data (ISO3, Capitals, Coordinates)
try:
    c_url = "https://raw.githubusercontent.com/mledoze/countries/master/countries.json"
    global_countries = requests.get(c_url, headers=HEADERS, timeout=15).json()
except Exception:
    global_countries = []

def lookup_country(name):
    name_clean = name.strip().lower()
    for item in global_countries:
        common = item.get("name", {}).get("common", "").lower()
        official = item.get("name", {}).get("official", "").lower()
        alt = [a.lower() for a in item.get("altSpellings", [])]
        if name_clean in (common, official) or name_clean in alt:
            return item
    for item in global_countries:
        if name_clean in item.get("name", {}).get("common", "").lower():
            return item
    return None

# Exchange rates
fx_rates = {}
try:
    fx_res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10).json()
    if fx_res.get("result") == "success":
        fx_rates = fx_res.get("rates", {})
except Exception:
    pass

def fetch_wiki_sections(country_name):
    """Fetches core encyclopedic sections: History, Government, Economy, Geography, Culture."""
    sections_out = {"history": "", "government": "", "economy": "", "geography": "", "culture": ""}
    try:
        # 1. Get section index
        idx_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={requests.utils.quote(country_name)}&prop=sections&format=json"
        res = requests.get(idx_url, headers=HEADERS, timeout=6).json()
        sections = res.get("parse", {}).get("sections", [])
        
        target_map = {
            "history": ["history", "origins", "etymology"],
            "government": ["government", "politics", "governance"],
            "economy": ["economy", "economic", "infrastructure"],
            "geography": ["geography", "climate", "environment"],
            "culture": ["culture", "demographics", "society"]
        }
        
        for domain, keywords in target_map.items():
            for sec in sections:
                line = sec.get("line", "").lower()
                if any(kw in line for kw in keywords) and sec.get("toclevel") == 1:
                    sec_id = sec.get("index")
                    # Fetch plaintext content of this section
                    content_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={requests.utils.quote(country_name)}&prop=text&section={sec_id}&format=json"
                    c_res = requests.get(content_url, headers=HEADERS, timeout=6).json()
                    html_text = c_res.get("parse", {}).get("text", {}).get("*", "")
                    soup = BeautifulSoup(html_text, "html.parser")
                    # Clean out citations [1], edit tags, etc.
                    for tag in soup(["sup", "table", "style", "script"]):
                        tag.decompose()
                    clean_text = soup.get_text(separator=" ").strip()
                    clean_text = " ".join(clean_text.split())[:1200]  # First ~1,200 chars of section
                    if clean_text:
                        sections_out[domain] = clean_text
                    break
    except Exception:
        pass
    return sections_out

api_records = []

for idx, country in enumerate(countries, 1):
    record = {
        "country": country,
        "iso3": None,
        "capital": None,
        "region": None,
        "subregion": None,
        "latitude": None,
        "longitude": None,
        "currency_code": None,
        "exchange_rate_usd": None,
        "wb_gdp_usd": None,
        "wb_life_expectancy": None,
        "annual_mean_temp_c": None,
        "annual_precipitation_mm": None,
        "wiki_summary": None,
        "wiki_history": None,
        "wiki_government": None,
        "wiki_economy": None,
        "wiki_geography": None,
        "wiki_culture": None
    }
    
    # Enrich metadata
    c_info = lookup_country(country)
    if c_info:
        record["iso3"] = c_info.get("cca3")
        cap = c_info.get("capital", [])
        record["capital"] = cap[0] if cap else None
        record["region"] = c_info.get("region")
        record["subregion"] = c_info.get("subregion")
        latlng = c_info.get("latlng", [])
        if len(latlng) >= 2:
            record["latitude"], record["longitude"] = latlng[0], latlng[1]
        
        curr = c_info.get("currency", [])
        if isinstance(curr, list) and curr:
            record["currency_code"] = curr[0]
            record["exchange_rate_usd"] = fx_rates.get(curr[0])
        elif isinstance(curr, dict) and curr:
            code = list(curr.keys())[0]
            record["currency_code"] = code
            record["exchange_rate_usd"] = fx_rates.get(code)

    # World Bank
    iso3 = record["iso3"]
    if iso3:
        try:
            wb_gdp = requests.get(f"https://api.worldbank.org/v2/country/{iso3}/indicator/NY.GDP.MKTP.CD?date=2019:2022&format=json", timeout=5).json()
            if len(wb_gdp) > 1 and wb_gdp[1]:
                for it in wb_gdp[1]:
                    if it.get("value") is not None:
                        record["wb_gdp_usd"] = it.get("value")
                        break
            wb_le = requests.get(f"https://api.worldbank.org/v2/country/{iso3}/indicator/SP.DYN.LE00.IN?date=2019:2022&format=json", timeout=5).json()
            if len(wb_le) > 1 and wb_le[1]:
                for it in wb_le[1]:
                    if it.get("value") is not None:
                        record["wb_life_expectancy"] = round(it.get("value"), 2)
                        break
        except Exception:
            pass

    # Open-Meteo
    lat, lon = record["latitude"], record["longitude"]
    if lat is not None and lon is not None:
        try:
            om_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2023-01-01&end_date=2023-12-31&daily=temperature_2m_mean,precipitation_sum&timezone=auto"
            om_res = requests.get(om_url, timeout=6).json()
            daily = om_res.get("daily", {})
            temps = [t for t in daily.get("temperature_2m_mean", []) if t is not None]
            precips = [p for p in daily.get("precipitation_sum", []) if p is not None]
            if temps: record["annual_mean_temp_c"] = round(sum(temps)/len(temps), 2)
            if precips: record["annual_precipitation_mm"] = round(sum(precips), 2)
        except Exception:
            pass

    # Wikipedia Sections Ingestion
    w_secs = fetch_wiki_sections(country)
    record["wiki_history"] = w_secs["history"]
    record["wiki_government"] = w_secs["government"]
    record["wiki_economy"] = w_secs["economy"]
    record["wiki_geography"] = w_secs["geography"]
    record["wiki_culture"] = w_secs["culture"]

    # Ingest general lead
    try:
        w_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(country)}"
        r = requests.get(w_url, headers=HEADERS, timeout=6).json()
        record["wiki_summary"] = r.get("extract", "").replace("\n", " ").strip()
    except Exception:
        pass

    api_records.append(record)
    print(f"[{idx}/156] {country} -> History: {len(record['wiki_history'])} chars | Gov: {len(record['wiki_government'])} chars | Econ: {len(record['wiki_economy'])} chars")
    time.sleep(0.05)

with open("data/api_data_raw.json", "w", encoding="utf-8") as f:
    json.dump(api_records, f, indent=2)

print("\nSaved multi-section encyclopedic records to data/api_data_raw.json")