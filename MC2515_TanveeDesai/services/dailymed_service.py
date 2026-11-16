"""
services/dailymed_service.py — DailyMed API service.

Purpose:
- Official FDA-approved drug labeling (SPL documents)
- Dosage forms, warnings, contraindications, precautions
- Storage information, manufacturers, labeling metadata

API: https://dailymed.nlm.nih.gov/dailymed/services/v2
No API key required.
"""

from typing import Any, Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import DAILYMED_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES
from utils.logging import logger
from utils.caching import get_cached, set_cached

_session = requests.Session()
_session.headers.update({"Accept": "application/json"})


class DailyMedServiceError(Exception):
    pass


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True,
)
def _get(path: str, params: Optional[Dict] = None) -> Dict:
    url = f"{DAILYMED_BASE_URL}/{path}"
    resp = _session.get(url, params=params, timeout=REQUEST_TIMEOUT)
    if resp.status_code == 404:
        return {"data": [], "metadata": {}}
    resp.raise_for_status()
    return resp.json()


# ── SPL Search ────────────────────────────────────────────────────────────────

def search_spls(drug_name: str, page_size: int = 5) -> Dict[str, Any]:
    """
    Search DailyMed for structured product labels matching a drug name.
    Returns metadata list of matching SPL records.
    """
    cache_key = f"{drug_name.lower()}_{page_size}"
    cached = get_cached("dailymed_search", cache_key)
    if cached:
        return cached

    result: Dict[str, Any] = {
        "source": "DailyMed",
        "source_url": "https://dailymed.nlm.nih.gov",
        "drug_name": drug_name,
        "spls": [],
        "total": 0,
        "error": None,
        "retrieval_ok": False,
    }

    try:
        data = _get("spls.json", params={"drug_name": drug_name, "pagesize": page_size})
        spls_raw = data.get("data", [])
        metadata = data.get("metadata", {})

        parsed = []
        for spl in spls_raw:
            parsed.append({
                "setid": spl.get("setid", ""),
                "title": spl.get("title", ""),
                "published_date": spl.get("published_date", ""),
                "spl_version": spl.get("spl_version", ""),
            })

        result["spls"] = parsed
        result["total"] = metadata.get("total_elements", len(parsed))
        result["retrieval_ok"] = True
        logger.info(f"DailyMed search for '{drug_name}': {len(parsed)} SPLs")

    except requests.HTTPError as e:
        result["error"] = f"HTTP {e.response.status_code}"
        logger.warning(f"DailyMed search HTTP error for '{drug_name}': {e}")
    except requests.RequestException as e:
        result["error"] = f"Network error: {e}"
        logger.error(f"DailyMed search network error for '{drug_name}': {e}")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"DailyMed search unexpected error: {e}")

    if result["retrieval_ok"]:
        set_cached("dailymed_search", cache_key, result)
    return result


# ── SPL Detail ────────────────────────────────────────────────────────────────

def get_spl_detail(setid: str) -> Dict[str, Any]:
    """
    Retrieve detailed SPL information for a given set ID.
    """
    cached = get_cached("dailymed_spl_detail", setid)
    if cached:
        return cached

    result: Dict[str, Any] = {
        "setid": setid,
        "title": "",
        "published_date": "",
        "dosage_forms": [],
        "routes": [],
        "labeler": "",
        "sections": [],
        "error": None,
        "retrieval_ok": False,
    }

    try:
        data = _get(f"spls/{setid}.json")
        spl_data = data.get("data", {})

        result["title"] = spl_data.get("title", "")
        result["published_date"] = spl_data.get("published_date", "")
        result["labeler"] = spl_data.get("labeler", "")

        # Parse sections
        sections = spl_data.get("sections", [])
        for sec in sections:
            result["sections"].append({
                "loinc_code": sec.get("loinc_code", ""),
                "title": sec.get("title", ""),
                "text": sec.get("text", "")[:2000] if sec.get("text") else "",
            })

        result["retrieval_ok"] = True
        set_cached("dailymed_spl_detail", setid, result)
        logger.info(f"DailyMed SPL detail for setid={setid}: {len(result['sections'])} sections")

    except requests.HTTPError as e:
        result["error"] = f"HTTP {e.response.status_code}"
        logger.warning(f"DailyMed SPL detail HTTP error for setid={setid}: {e}")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"DailyMed SPL detail error for setid={setid}: {e}")

    return result


def get_spl_by_rxcui(rxcui: str, page_size: int = 3) -> Dict[str, Any]:
    """Search DailyMed by RxCUI for more accurate matching."""
    cache_key = f"rxcui_{rxcui}_{page_size}"
    cached = get_cached("dailymed_rxcui", cache_key)
    if cached:
        return cached

    result: Dict[str, Any] = {
        "source": "DailyMed",
        "source_url": "https://dailymed.nlm.nih.gov",
        "rxcui": rxcui,
        "spls": [],
        "error": None,
        "retrieval_ok": False,
    }

    try:
        data = _get("spls.json", params={"rxcui": rxcui, "pagesize": page_size})
        spls_raw = data.get("data", [])
        result["spls"] = [
            {
                "setid": s.get("setid", ""),
                "title": s.get("title", ""),
                "published_date": s.get("published_date", ""),
            }
            for s in spls_raw
        ]
        result["retrieval_ok"] = True
        set_cached("dailymed_rxcui", cache_key, result)
        logger.info(f"DailyMed by RxCUI {rxcui}: {len(result['spls'])} SPLs")

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"DailyMed by RxCUI failed for {rxcui}: {e}")

    return result


# ── Full Drug Info ────────────────────────────────────────────────────────────

_SECTION_KEYWORDS = {
    "warnings": ["warning", "boxed warning", "black box"],
    "contraindications": ["contraindication"],
    "precautions": ["precaution", "warnings and precautions"],
    "adverse_reactions": ["adverse reaction", "side effect"],
    "storage": ["storage", "how supplied"],
    "indications": ["indication", "uses"],
    "dosage": ["dosage", "administration"],
    "interactions": ["drug interaction"],
}


def _extract_section(sections: List[Dict], category: str) -> str:
    """Find the first section matching the category keywords."""
    keywords = _SECTION_KEYWORDS.get(category, [category])
    for sec in sections:
        title = sec.get("title", "").lower()
        if any(kw in title for kw in keywords):
            return sec.get("text", "")
    return ""


def get_full_drug_info(drug_name: str, rxcui: Optional[str] = None) -> Dict[str, Any]:
    """
    Collect comprehensive DailyMed information for a drug.
    """
    # Try RxCUI search first for accuracy
    spls_result = None
    if rxcui:
        spls_result = get_spl_by_rxcui(rxcui)

    # Fall back to name search
    if not spls_result or not spls_result["spls"]:
        spls_result = search_spls(drug_name)

    info: Dict[str, Any] = {
        "source": "DailyMed",
        "source_url": "https://dailymed.nlm.nih.gov",
        "drug_name": drug_name,
        "rxcui": rxcui,
        "spls": [],
        "detailed_labels": [],
        "warnings": "",
        "contraindications": "",
        "precautions": "",
        "adverse_reactions": "",
        "storage": "",
        "indications": "",
        "dosage": "",
        "interactions": "",
        "labeler": "",
        "published_date": "",
        "retrieval_ok": spls_result.get("retrieval_ok", False),
        "error": spls_result.get("error"),
    }

    spls = spls_result.get("spls", [])
    info["spls"] = spls

    if not spls:
        return info

    # Get detail for the first (most relevant) SPL
    first_setid = spls[0].get("setid", "")
    if first_setid:
        detail = get_spl_detail(first_setid)
        if detail.get("retrieval_ok"):
            info["detailed_labels"].append(detail)
            sections = detail.get("sections", [])
            info["labeler"] = detail.get("labeler", "")
            info["published_date"] = detail.get("published_date", "")

            for category in _SECTION_KEYWORDS:
                info[category] = _extract_section(sections, category)

    return info
