"""
src/context_apis.py
--------------------
Four supplementary "live context" APIs beyond the core RAG stack (Groq +
Cohere) and the existing public-holiday lookup (app.py sidebar):

    1. Currency exchange  -- open.er-api.com          (no key)
    2. Weather / WFH advisory -- open-meteo.com        (no key)
    3. Country info ("verify employer country") -- countries.dev (no key)
    4. HR / labor-law news headlines -- newsdata.io     (free key required)

Every function follows the same contract used elsewhere in this project
(see the Nager->nagerholidays migration in app.py's sidebar): return a
plain dict with either the data or an "error" string, never raise past
this module, and never silently fabricate data when a live call fails.

Endpoint choices were verified against current docs/status as of this
writing (Aug 2026) rather than assumed from memory -- see README's
"Phase 8" notes on why each one was picked over the obvious-but-now-broken
default (e.g. restcountries.com v3.1 is deprecated; v5 needs a paid-ish key).
"""

from __future__ import annotations

import requests

DEFAULT_TIMEOUT = 6

# --------------------------------------------------------------------------- #
# 1. Currency exchange -- open.er-api.com (ExchangeRate-API's open, keyless
#    endpoint). Used for expense-policy INR<->USD context. No historical
#    rates on this tier -- current-rate only, which is all this feature needs.
# --------------------------------------------------------------------------- #

def get_exchange_rate(base: str = "USD", target: str = "INR") -> dict:
    """
    Fetches the current exchange rate for `target` per 1 unit of `base`.
    Returns {"base", "target", "rate", "last_updated", "error"}.
    """
    result = {"base": base, "target": target, "rate": None, "last_updated": None, "error": None}
    try:
        resp = requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=DEFAULT_TIMEOUT)
        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code} from open.er-api.com"
            return result
        data = resp.json()
        if data.get("result") != "success":
            result["error"] = f"API reported non-success result: {data.get('result')}"
            return result
        rates = data.get("rates", {})
        if target not in rates:
            result["error"] = f"'{target}' not found in rates response"
            return result
        result["rate"] = rates[target]
        result["last_updated"] = data.get("time_last_update_utc")
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)
    except (ValueError, KeyError) as e:
        result["error"] = f"Unexpected response format: {e}"
    return result


def convert_amount(amount: float, base: str = "USD", target: str = "INR") -> dict:
    """Convenience wrapper: converts `amount` of `base` into `target`."""
    fx = get_exchange_rate(base, target)
    out = dict(fx)
    out["amount_base"] = amount
    out["amount_target"] = round(amount * fx["rate"], 2) if fx["rate"] is not None else None
    return out


# --------------------------------------------------------------------------- #
# 2. Weather -- Open-Meteo (geocoding + forecast), both keyless.
#    Used for a simple WFH advisory: flag heavy rain / extreme heat / storm
#    conditions that plausibly justify invoking the remote-work policy on a
#    given day. This is a suggestion surfaced to the employee, not a policy
#    ruling -- the actual WFH eligibility rules still live in the indexed
#    remote_work_policy.md and are answered by the RAG pipeline, not this.
# --------------------------------------------------------------------------- #

# WMO weather codes (used by Open-Meteo) -> (label, is_severe)
_WMO_CODES = {
    0: ("Clear sky", False), 1: ("Mainly clear", False), 2: ("Partly cloudy", False),
    3: ("Overcast", False), 45: ("Fog", False), 48: ("Depositing rime fog", False),
    51: ("Light drizzle", False), 53: ("Moderate drizzle", False), 55: ("Dense drizzle", False),
    56: ("Light freezing drizzle", True), 57: ("Dense freezing drizzle", True),
    61: ("Slight rain", False), 63: ("Moderate rain", True), 65: ("Heavy rain", True),
    66: ("Light freezing rain", True), 67: ("Heavy freezing rain", True),
    71: ("Slight snow", False), 73: ("Moderate snow", True), 75: ("Heavy snow", True),
    77: ("Snow grains", False),
    80: ("Slight rain showers", False), 81: ("Moderate rain showers", True),
    82: ("Violent rain showers", True),
    85: ("Slight snow showers", False), 86: ("Heavy snow showers", True),
    95: ("Thunderstorm", True), 96: ("Thunderstorm with slight hail", True),
    99: ("Thunderstorm with heavy hail", True),
}


def geocode_city(city_name: str) -> dict:
    """Resolves a city name to lat/lon via Open-Meteo's geocoding API."""
    result = {"name": None, "country": None, "latitude": None, "longitude": None, "error": None}
    try:
        resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city_name, "count": 1, "language": "en", "format": "json"},
            timeout=DEFAULT_TIMEOUT,
        )
        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code} from geocoding-api.open-meteo.com"
            return result
        data = resp.json()
        matches = data.get("results") or []
        if not matches:
            result["error"] = f"No location found for '{city_name}'"
            return result
        top = matches[0]
        result.update({
            "name": top.get("name"), "country": top.get("country"),
            "latitude": top.get("latitude"), "longitude": top.get("longitude"),
        })
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)
    except (ValueError, KeyError) as e:
        result["error"] = f"Unexpected response format: {e}"
    return result


def get_wfh_advisory(city_name: str) -> dict:
    """
    Geocodes `city_name`, fetches current weather, and returns a simple
    WFH advisory alongside the raw reading. Never claims policy authority --
    just flags "conditions plausibly warrant checking the remote work policy".
    """
    result = {
        "city": city_name, "resolved_name": None, "temperature_c": None,
        "condition": None, "is_severe": False, "advisory": None, "error": None,
    }
    geo = geocode_city(city_name)
    if geo["error"]:
        result["error"] = geo["error"]
        return result
    result["resolved_name"] = f"{geo['name']}, {geo['country']}"

    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": geo["latitude"], "longitude": geo["longitude"],
                "current": "temperature_2m,precipitation,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
            timeout=DEFAULT_TIMEOUT,
        )
        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code} from api.open-meteo.com"
            return result
        current = resp.json().get("current", {})
        code = current.get("weather_code")
        label, is_severe = _WMO_CODES.get(code, ("Unknown conditions", False))
        temp = current.get("temperature_2m")

        result["temperature_c"] = temp
        result["condition"] = label
        result["is_severe"] = bool(is_severe) or (isinstance(temp, (int, float)) and temp >= 42)

        if result["is_severe"]:
            result["advisory"] = (
                f"⚠️ {label} in {result['resolved_name']}"
                + (f" ({temp}°C)" if temp is not None else "")
                + " -- conditions like this are a reasonable reason to check the remote work policy "
                  "for a WFH day. This is a suggestion, not an approval; eligibility still follows the "
                  "indexed remote_work_policy.md."
            )
        else:
            result["advisory"] = f"No weather-related WFH concern right now -- {label.lower()} in {result['resolved_name']}."
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)
    except (ValueError, KeyError) as e:
        result["error"] = f"Unexpected response format: {e}"
    return result


# --------------------------------------------------------------------------- #
# 3. Country info -- countries.dev (free, keyless alternative to
#    restcountries.com, whose v3.1 endpoint is now deprecated and whose v5
#    endpoint requires a paid-tier-adjacent API key -- confirmed directly,
#    not assumed). Framed as "employer country context", NOT as a true
#    company-registry verification -- a real registry lookup (MCA, Companies
#    House, etc.) needs per-country auth this app deliberately doesn't take on.
# --------------------------------------------------------------------------- #

def get_country_info(country_query: str) -> dict:
    """
    Looks up basic country-level data (capital, region, currency, calling
    code) by name via countries.dev. Used for the "employer country context"
    sidebar feature -- explicitly not a legal company-registry check.
    """
    # NOTE: countries.dev is a newer, less battle-tested service than the
    # restcountries.com it replaces -- its docs confirm keyless /alpha/{code}
    # and "search by name" endpoints exist, but the exact name-search path
    # wasn't independently confirmed via a live request (this environment's
    # network egress is locked to a small allowlist that doesn't include
    # countries.dev). Before relying on this in production, hit
    # https://countries.dev/name/<value> once by hand and adjust the path
    # below if it 404s -- the try/except ensures a wrong path fails as a
    # visible "no match" message in the UI rather than a crash, same as the
    # existing holiday-lookup fallback pattern.
    result = {
        "query": country_query, "name": None, "capital": None, "region": None,
        "currencies": None, "calling_code": None, "flag": None, "error": None,
    }
    try:
        resp = requests.get(
            "https://countries.dev/name/" + requests.utils.quote(country_query),
            timeout=DEFAULT_TIMEOUT,
        )
        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code} from countries.dev -- no match for '{country_query}'"
            return result
        data = resp.json()
        # Some countries.dev endpoints return a list for name search, others a
        # single object for exact/alpha lookups -- handle both defensively.
        record = data[0] if isinstance(data, list) and data else data
        if not isinstance(record, dict) or not record:
            result["error"] = f"No country data found for '{country_query}'"
            return result
        result.update({
            "name": record.get("name"),
            "capital": record.get("capital"),
            "region": record.get("region"),
            "currencies": record.get("currencies"),
            "calling_code": record.get("callingCode") or record.get("callingCodes"),
            "flag": record.get("flag"),
        })
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)
    except (ValueError, KeyError) as e:
        result["error"] = f"Unexpected response format: {e}"
    return result


# --------------------------------------------------------------------------- #
# 4. HR / labor-law news -- NewsData.io (free tier, 200 credits/day, allows
#    non-commercial demo use). Requires a free API key, same pattern as the
#    existing Groq/Cohere keys. GNews is a documented fallback if this key
#    isn't configured (see README) but isn't wired in by default to avoid
#    managing a third optional key for a "nice to have" feature.
# --------------------------------------------------------------------------- #

def get_hr_news(api_key: str, query: str = "labor law OR HR policy OR workplace regulation", country: str = "in", limit: int = 5) -> dict:
    """
    Fetches recent headlines relevant to labor law / HR news via NewsData.io.
    Returns {"articles": [...], "error": None} or {"articles": [], "error": "..."}.
    """
    result = {"articles": [], "error": None}
    if not api_key:
        result["error"] = "No NewsData.io API key configured."
        return result
    try:
        resp = requests.get(
            "https://newsdata.io/api/1/news",
            params={"apikey": api_key, "q": query, "country": country, "language": "en"},
            timeout=DEFAULT_TIMEOUT,
        )
        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code} from newsdata.io"
            return result
        data = resp.json()
        if data.get("status") != "success":
            result["error"] = data.get("results", {}).get("message", "NewsData.io reported an error") \
                if isinstance(data.get("results"), dict) else "NewsData.io reported an error"
            return result
        for item in (data.get("results") or [])[:limit]:
            result["articles"].append({
                "title": item.get("title"),
                "source": item.get("source_id"),
                "link": item.get("link"),
                "published": item.get("pubDate"),
            })
        if not result["articles"]:
            result["error"] = "No matching articles returned right now."
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)
    except (ValueError, KeyError) as e:
        result["error"] = f"Unexpected response format: {e}"
    return result
