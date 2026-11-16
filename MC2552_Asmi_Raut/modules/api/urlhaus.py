"""
urlhaus.py

API 3: URLhaus (abuse.ch)

Public threat-intel feed of actively tracked malware-distribution URLs.
No API key required for the "recent additions" endpoint used here:

    https://urlhaus-api.abuse.ch/v1/urls/recent/limit/100/

Join key with the existing dataset
-----------------------------------
NSL-KDD contains no URL field, so URLhaus data cannot be joined to NSL-KDD
records directly (there is nothing to join on) — inventing a URL per
network-flow record would be fabricated data, which this pipeline avoids.

Instead, URLhaus is treated as an independent Indicator-of-Compromise (IOC)
threat-intelligence feed. Its output CSV stands on its own (join key: `url`)
and is unioned into the final fused dataset as `record_type =
threat_intel_ioc`, clearly separate from the NSL-KDD-derived
`network_traffic_category` rows. This is the mapping strategy required by
the project spec when no real join key exists: don't force one.
"""

from typing import Dict, List
import os
from modules.api.base_client import safe_request, logger

URLHAUS_API_URL = "https://urlhaus-api.abuse.ch/v1/urls/recent/limit/{limit}/"
URLHAUS_API_KEY = os.getenv("URLHAUS_API_KEY", "").strip()

def fetch_recent_urls(limit: int = 25) -> List[Dict]:
    """
    Fetch the most recent confirmed-malicious URLs currently tracked by
    URLhaus. Returns a normalized list of dict rows:
        url, url_status, threat, tags, date_added, reporter, api_status
    """
    url =URLHAUS_API_URL.format(limit=limit)
    headers = {"Auth-Key": URLHAUS_API_KEY}
    result = safe_request("GET", url, api_name="URLhaus",headers=headers, timeout=20)

    if not result["ok"]:
        logger.error(f"[URLhaus] Failed to fetch recent URLs: {result['error']}")
        return [{
            "url": "",
            "url_status": "",
            "threat": "",
            "tags": "",
            "date_added": "",
            "reporter": "",
            "api_status": f"api_error:{result['error']}",
        }]

    data = result["data"]

    if not isinstance(data, dict) or data.get("query_status") != "ok":
        status = data.get("query_status", "unknown") if isinstance(data, dict) else "invalid_response"
        logger.warning(f"[URLhaus] query_status={status}")
        return [{
            "url": "",
            "url_status": "",
            "threat": "",
            "tags": "",
            "date_added": "",
            "reporter": "",
            "api_status": f"query_status:{status}",
        }]

    records = []

    for entry in data.get("urls", []):
        tags = entry.get("tags") or []

        records.append({
            "url": entry.get("url", ""),
            "url_status": entry.get("url_status", ""),
            "threat": entry.get("threat", ""),
            "tags": ", ".join(tags) if isinstance(tags, list) else str(tags),
            "date_added": entry.get("date_added", ""),
            "reporter": entry.get("reporter", ""),
            "api_status": "ok",
        })

    if not records:
        records.append({
            "url": "", "url_status": "", "threat": "", "tags": "",
            "date_added": "", "reporter": "", "api_status": "no_results",
        })

    return records
