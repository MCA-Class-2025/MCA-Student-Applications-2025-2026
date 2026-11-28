"""
PolicyPal API Data Fusion Builder
---------------------------------
Creates PolicyPal's structured Data Science dataset from the same five external
APIs used by the chatbot context layer:

1. Nager.Date       -> public holidays
2. ExchangeRate-API -> current currency rates
3. Open-Meteo       -> city weather
4. countries.dev    -> country metadata
5. NewsData.io      -> HR / labour / workplace news

IMPORTANT:
- This file creates the DATA SCIENCE DATASET. It does not replace PolicyPal's
  PDF/RAG knowledge base.
- API responses are cached locally so rerunning the script does not repeatedly
  spend API credits.
- Rows are "city + news article policy-context observations". A news article is
  the event-level observation; country/city/weather/currency/holiday fields are
  contextual enrichment.
- No fake API values are generated. Missing API responses remain missing and are
  marked through data_quality_flag/api_collection_status.

Run from the PolicyPal project root:
    python -m src.policy_data_fusion

Set:
    NEWSDATA_API_KEY=your_key

The script writes:
    data/PolicyPal_Master_Dataset.xlsx
    data/api_cache/*.json
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests

from .fusion_config import COUNTRIES, DATASET_COLUMNS, POLICY_TOPICS

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "Dataset"
CACHE_DIR = DATA_DIR / "api_cache"
OUTPUT_XLSX = DATA_DIR / "PolicyPal_Master_Dataset.xlsx"

TIMEOUT = 12
NEWS_LIMIT = 10
MAX_NEWS_REQUESTS = 100
SLEEP_BETWEEN_NEWS_REQUESTS = 0.25

NAGER_URL = "https://nagerholidays.com/api/v4/Holidays/{country}/{year}"
COUNTRY_URL = "https://countries.dev/alpha/{country_code}"
OPEN_METEO_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
FX_URL = "https://open.er-api.com/v6/latest/USD"
NEWSDATA_URL = "https://newsdata.io/api/1/news"


def cache_key(prefix: str, payload: Dict[str, Any]) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:24]
    return CACHE_DIR / f"{prefix}_{digest}.json"


def cached_get(
    prefix: str,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[Optional[Dict[str, Any]], str]:
    """GET JSON with a disk cache. Returns (payload, status)."""
    params = params or {}
    path = cache_key(prefix, {"url": url, "params": params})
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8")), "CACHE"
        except Exception:
            path.unlink(missing_ok=True)

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=TIMEOUT,
        )
        if response.status_code != 200:
            return None, f"HTTP_{response.status_code}"
        payload = response.json()
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload, "LIVE"
    except (requests.RequestException, ValueError) as exc:
        return None, f"ERROR:{exc}"


def get_country(country_code: str) -> Tuple[Dict[str, Any], str]:
    payload, status = cached_get(
        "country",
        COUNTRY_URL.format(country_code=country_code),
    )
    if not payload:
        return {}, status

    # countries.dev /alpha/{code} returns a country object. Keep parsing
    # defensive because currency/timezone shapes can vary by record.
    if isinstance(payload, list):
        payload = payload[0] if payload else {}
    currencies = payload.get("currencies") or []
    if isinstance(currencies, dict):
        currencies = list(currencies.values())
    currency = currencies[0] if isinstance(currencies, list) and currencies else {}
    timezones = payload.get("timezones") or []
    if isinstance(timezones, str):
        timezones = [timezones]

    return {
        "country_name": payload.get("name"),
        "alpha3_code": payload.get("alpha3Code"),
        "capital": payload.get("capital"),
        "region": payload.get("region"),
        "subregion": payload.get("subregion"),
        "population": payload.get("population"),
        "area_km2": payload.get("area"),
        "currency_code": currency.get("code"),
        "currency_name": currency.get("name"),
        "currency_symbol": currency.get("symbol"),
        "timezone": timezones[0] if timezones else None,
    }, status


def get_currency_rates() -> Tuple[Dict[str, float], str]:
    payload, status = cached_get("currency_usd", FX_URL)
    if not payload or payload.get("result") != "success":
        return {}, status
    return payload.get("rates", {}) or {}, status


def geocode(city: str, country_code: str) -> Tuple[Dict[str, Any], str]:
    payload, status = cached_get(
        "geocode",
        OPEN_METEO_GEOCODE,
        params={
            "name": city,
            "count": 10,
            "language": "en",
            "format": "json",
        },
    )
    if not payload:
        return {}, status

    matches = payload.get("results") or []
    # Prefer the requested ISO country when Open-Meteo supplies country_code.
    preferred = [
        x for x in matches
        if str(x.get("country_code", "")).upper() == country_code.upper()
    ]
    top = (preferred or matches)
    if not top:
        return {}, "NO_MATCH"

    item = top[0]
    return {
        "latitude": item.get("latitude"),
        "longitude": item.get("longitude"),
        "resolved_city": item.get("name"),
    }, status


def get_weather(city: str, country_code: str) -> Tuple[Dict[str, Any], str]:
    geo, geo_status = geocode(city, country_code)
    if not geo:
        return {}, geo_status

    payload, weather_status = cached_get(
        "weather",
        OPEN_METEO_FORECAST,
        params={
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "current": "temperature_2m,precipitation,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
    )
    if not payload:
        return {}, weather_status

    current = payload.get("current") or {}
    code = current.get("weather_code")
    label, severe = weather_label(code)
    temp = current.get("temperature_2m")
    severe = bool(severe) or (
        isinstance(temp, (int, float)) and temp >= 42
    )

    return {
        "latitude": geo["latitude"],
        "longitude": geo["longitude"],
        "temperature_c": temp,
        "precipitation_mm": current.get("precipitation"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "weather_code": code,
        "weather_condition": label,
        "is_severe_weather": severe,
    }, f"{geo_status}+{weather_status}"


WMO_LABELS = {
    0: ("Clear sky", False), 1: ("Mainly clear", False),
    2: ("Partly cloudy", False), 3: ("Overcast", False),
    45: ("Fog", False), 48: ("Depositing rime fog", False),
    51: ("Light drizzle", False), 53: ("Moderate drizzle", False),
    55: ("Dense drizzle", False), 56: ("Light freezing drizzle", True),
    57: ("Dense freezing drizzle", True), 61: ("Slight rain", False),
    63: ("Moderate rain", True), 65: ("Heavy rain", True),
    66: ("Light freezing rain", True), 67: ("Heavy freezing rain", True),
    71: ("Slight snow", False), 73: ("Moderate snow", True),
    75: ("Heavy snow", True), 77: ("Snow grains", False),
    80: ("Slight rain showers", False), 81: ("Moderate rain showers", True),
    82: ("Violent rain showers", True), 85: ("Slight snow showers", False),
    86: ("Heavy snow showers", True), 95: ("Thunderstorm", True),
    96: ("Thunderstorm with slight hail", True),
    99: ("Thunderstorm with heavy hail", True),
}


def weather_label(code: Any) -> Tuple[str, bool]:
    return WMO_LABELS.get(code, ("Unknown conditions", False))


def get_holidays(country_code: str, year: int) -> Tuple[List[Dict[str, Any]], str]:
    payload, status = cached_get(
        "holidays",
        NAGER_URL.format(year=year, country=country_code),
    )
    if not payload or not isinstance(payload, list):
        return [], status

    rows = []
    for item in payload:
        types = item.get("types")
        if isinstance(types, list):
            holiday_type = types[0] if types else None
        else:
            holiday_type = types or item.get("type")
        rows.append({
            "holiday_date": item.get("date"),
            "holiday_name": item.get("name") or item.get("localName"),
            "holiday_type": holiday_type,
            "is_public_holiday": True,
        })
    return rows, status


def get_news(api_key: str, country_code: str, topic: str) -> Tuple[List[Dict[str, Any]], str]:
    if not api_key:
        return [], "NO_API_KEY"

    payload, status = cached_get(
        "news",
        NEWSDATA_URL,
        params={
            "apikey": api_key,
            "q": topic,
            "country": country_code.lower(),
            "language": "en",
        },
    )
    if not payload:
        return [], status

    if payload.get("status") != "success":
        return [], status + "_API_ERROR"

    articles = []
    for item in (payload.get("results") or [])[:NEWS_LIMIT]:
        articles.append({
            "news_title": item.get("title"),
            "news_source": item.get("source_id"),
            "news_url": item.get("link"),
            "news_published_at": item.get("pubDate"),
            "news_country": country_code,
        })
    return articles, status


def choose_holiday(holidays: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Use the first holiday as a contextual annual holiday field.

    The complete holiday list is separately retained in the Holiday_Calendar
    workbook sheet. This prevents multiplying every news article by every
    holiday while still preserving holiday information in the master table.
    """
    if not holidays:
        return {
            "holiday_date": None,
            "holiday_name": None,
            "holiday_type": None,
            "is_public_holiday": False,
        }
    first = sorted(holidays, key=lambda x: x.get("holiday_date") or "")[0]
    return first


def quality_flag(row: Dict[str, Any]) -> str:
    required = [
        "country_name", "currency_code", "city", "latitude", "longitude",
        "news_title",
    ]
    missing = [x for x in required if row.get(x) in (None, "", [])]
    if not missing:
        return "COMPLETE"
    if len(missing) <= 2:
        return "PARTIAL"
    return "INCOMPLETE"


def build_dataset(news_api_key: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    today = date.today()
    countries_cache: Dict[str, Dict[str, Any]] = {}
    country_status: Dict[str, str] = {}
    weather_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
    weather_status: Dict[Tuple[str, str], str] = {}
    holiday_cache: Dict[Tuple[str, int], List[Dict[str, Any]]] = {}
    holiday_status: Dict[Tuple[str, int], str] = {}
    currency_rates, currency_status = get_currency_rates()

    rows: List[Dict[str, Any]] = []
    holiday_rows: List[Dict[str, Any]] = []
    api_log: List[Dict[str, Any]] = []
    request_count = 0

    for country_code, cfg in COUNTRIES.items():
        country, c_status = get_country(country_code)
        countries_cache[country_code] = country
        country_status[country_code] = c_status

        holidays, h_status = get_holidays(country_code, today.year)
        holiday_cache[(country_code, today.year)] = holidays
        holiday_status[(country_code, today.year)] = h_status

        for h in holidays:
            holiday_rows.append({
                "country_code": country_code,
                "country_name": country.get("country_name"),
                "year": today.year,
                **h,
                "api_status": h_status,
            })

        for city in cfg["cities"]:
            weather, w_status = get_weather(city, country_code)
            weather_cache[(country_code, city)] = weather
            weather_status[(country_code, city)] = w_status

        for topic in POLICY_TOPICS:
            if request_count >= MAX_NEWS_REQUESTS:
                break

            articles, n_status = get_news(news_api_key, country_code, topic)
            request_count += 1

            for article in articles:
                for city in cfg["cities"]:
                    weather = weather_cache.get((country_code, city), {})
                    holiday = choose_holiday(holidays)
                    currency_code = country.get("currency_code")
                    row = {
                        "record_id": hashlib.sha1(
                            f"{country_code}|{city}|{topic}|{article.get('news_url')}|{article.get('news_title')}".encode("utf-8")
                        ).hexdigest()[:16],
                        "observation_date": today.isoformat(),
                        "country_code": country_code,
                        **country,
                        "usd_to_local_rate": currency_rates.get(currency_code),
                        "city": city,
                        **weather,
                        **holiday,
                        "policy_topic": topic,
                        **article,
                        "api_collection_status": (
                            f"country={c_status};currency={currency_status};"
                            f"holiday={h_status};weather={weather_status.get((country_code, city))};"
                            f"news={n_status}"
                        ),
                    }
                    row["data_quality_flag"] = quality_flag(row)
                    rows.append(row)

            time.sleep(SLEEP_BETWEEN_NEWS_REQUESTS)

    master = pd.DataFrame(rows)
    if master.empty:
        master = pd.DataFrame(columns=DATASET_COLUMNS)
    else:
        master = master.reindex(columns=DATASET_COLUMNS)

    holidays_df = pd.DataFrame(holiday_rows)
    if holidays_df.empty:
        holidays_df = pd.DataFrame(
            columns=["country_code", "country_name", "year", "holiday_date",
                     "holiday_name", "holiday_type", "is_public_holiday", "api_status"]
        )

    # API run log is intentionally compact and reproducible.
    api_log.append({
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "news_requests_attempted": request_count,
        "master_rows_created": len(master),
        "countries": len(COUNTRIES),
        "cities_per_country": 5,
        "policy_topics": len(POLICY_TOPICS),
        "currency_cache_status": currency_status,
        "news_key_configured": bool(news_api_key),
    })
    log_df = pd.DataFrame(api_log)

    return master, holidays_df, log_df


def write_workbook(master: pd.DataFrame, holidays: pd.DataFrame, api_log: pd.DataFrame) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dictionary = pd.DataFrame({
        "column_name": DATASET_COLUMNS,
        "description": [
            "Unique fused observation identifier",
            "Date on which the API snapshot was collected",
            "ISO alpha-2 country code",
            "Country name from countries.dev",
            "ISO alpha-3 country code",
            "Country capital",
            "Geographic region",
            "Geographic subregion",
            "Primary country timezone",
            "Country population",
            "Country area in square kilometres",
            "ISO currency code",
            "Currency name",
            "Currency symbol",
            "Current USD to local-currency rate",
            "City used for weather contextualization",
            "Weather latitude",
            "Weather longitude",
            "Current temperature in Celsius",
            "Current precipitation reading in mm",
            "Current wind speed in km/h",
            "WMO weather code",
            "Human-readable weather condition",
            "Weather severity flag from PolicyPal's advisory logic",
            "Representative annual public-holiday date",
            "Representative annual public-holiday name",
            "Holiday classification",
            "Whether the representative holiday is public",
            "HR/policy topic used for NewsData query",
            "News article title",
            "News publisher/source identifier",
            "News article URL",
            "News publication timestamp",
            "Country used in the news query",
            "Status of the contributing API calls",
            "Completeness indicator; no API values are fabricated",
        ],
        "source": [
            "Derived", "System", "Input/config", "countries.dev", "countries.dev",
            "countries.dev", "countries.dev", "countries.dev", "countries.dev",
            "countries.dev", "countries.dev", "countries.dev", "countries.dev",
            "countries.dev", "open.er-api.com", "Input/config", "Open-Meteo",
            "Open-Meteo", "Open-Meteo", "Open-Meteo", "Open-Meteo", "Open-Meteo",
            "Derived from Open-Meteo", "Derived from Open-Meteo", "Nager.Date",
            "Nager.Date", "Nager.Date", "Nager.Date", "Input/config",
            "NewsData.io", "NewsData.io", "NewsData.io", "NewsData.io",
            "NewsData.io", "Derived", "Derived",
        ],
    })

    summary = pd.DataFrame([
        ["Dataset purpose", "PolicyPal Data Science & Analytics dataset"],
        ["Primary observation", "City + news article + policy-topic context"],
        ["API sources", "Nager.Date; ExchangeRate-API; Open-Meteo; countries.dev; NewsData.io"],
        ["Maximum NewsData requests per run", MAX_NEWS_REQUESTS],
        ["Maximum approximate master rows", "5,000 (if 100 requests each return 10 articles across 5 cities)"],
        ["Policy PDF/RAG relationship", "Separate knowledge base; this workbook is structured analytical context"],
        ["Fabricated API values", "None"],
    ], columns=["metric", "value"])

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        master.to_excel(writer, index=False, sheet_name="Master_Dataset")
        holidays.to_excel(writer, index=False, sheet_name="Holiday_Calendar")
        dictionary.to_excel(writer, index=False, sheet_name="Data_Dictionary")
        api_log.to_excel(writer, index=False, sheet_name="API_Run_Log")
        summary.to_excel(writer, index=False, sheet_name="Dataset_Summary")

        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for col in sheet.columns:
                max_len = min(
                    max(len(str(cell.value or "")) for cell in col) + 2,
                    45,
                )
                sheet.column_dimensions[col[0].column_letter].width = max_len

    return OUTPUT_XLSX


def main() -> None:
    key = os.getenv("NEWSDATA_API_KEY", "").strip()
    master, holidays, api_log = build_dataset(key)
    path = write_workbook(master, holidays, api_log)
    print(f"Created: {path}")
    print(f"Rows: {len(master):,}")
    print(f"Columns: {len(master.columns):,}")


if __name__ == "__main__":
    main()
