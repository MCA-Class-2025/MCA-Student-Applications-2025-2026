"""
services/rxnorm_service.py — RxNorm API service.

Purpose:
- Normalize drug names to canonical RxCUI identifiers
- Retrieve active ingredients, brand/generic relationships
- Provide standardized medicine identification for downstream API queries

API: https://rxnav.nlm.nih.gov/REST
No API key required.
"""

import time
from typing import Any, Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import RXNORM_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES
from utils.logging import logger
from utils.caching import get_cached, set_cached

# ── HTTP Session ──────────────────────────────────────────────────────────────
_session = requests.Session()
_session.headers.update({"Accept": "application/json"})


class RxNormServiceError(Exception):
    """Raised when RxNorm API is unavailable or returns an error."""


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True,
)
def _get(path: str, params: Optional[Dict] = None) -> Dict:
    """Low-level GET with retry logic."""
    url = f"{RXNORM_BASE_URL}/{path}"
    resp = _session.get(url, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# ── Public API ────────────────────────────────────────────────────────────────

def normalize_drug_name(drug_name: str) -> Dict[str, Any]:
    """
    Normalize a drug name and return RxCUI + canonical name.

    Returns dict with keys:
        rxcui, name, synonym, approximateMatch, status
    """
    cache_key = drug_name.lower().strip()
    cached = get_cached("rxnorm_normalize", cache_key)
    if cached:
        return cached

    result: Dict[str, Any] = {
        "input_name": drug_name,
        "rxcui": None,
        "name": None,
        "synonym": None,
        "approximate_match": False,
        "status": "not_found",
        "error": None,
    }

    try:
        # Step 1 — exact / normalized match
        data = _get("rxcui.json", params={"name": drug_name, "search": 1})
        id_group = data.get("idGroup", {})
        rxcui_list = id_group.get("rxnormId", [])

        if rxcui_list:
            rxcui = rxcui_list[0]
            result["rxcui"] = rxcui
            result["status"] = "found"
            result["approximate_match"] = False

            # Get the canonical name for this RXCUI
            name_data = _get(f"rxcui/{rxcui}/properties.json")
            props = name_data.get("properties", {})
            result["name"] = props.get("name", drug_name)
            result["synonym"] = props.get("synonym")
        else:
            # Step 2 — approximate match
            approx_data = _get(
                "approximateTerm.json",
                params={"term": drug_name, "maxEntries": 5},
            )
            candidates = (
                approx_data.get("approximateGroup", {})
                .get("candidate", [])
            )
            if candidates:
                best = candidates[0]
                rxcui = best.get("rxcui")
                result["rxcui"] = rxcui
                result["approximate_match"] = True
                result["status"] = "approximate"

                # Get canonical name
                name_data = _get(f"rxcui/{rxcui}/properties.json")
                props = name_data.get("properties", {})
                result["name"] = props.get("name", drug_name)
                result["synonym"] = props.get("synonym")

        set_cached("rxnorm_normalize", cache_key, result)
        logger.info(
            f"RxNorm normalize: '{drug_name}' → RXCUI={result['rxcui']} "
            f"name='{result['name']}' status={result['status']}"
        )
        return result

    except requests.RequestException as e:
        result["error"] = f"Network error: {e}"
        result["status"] = "error"
        logger.error(f"RxNorm normalize failed for '{drug_name}': {e}")
        return result
    except Exception as e:
        result["error"] = str(e)
        result["status"] = "error"
        logger.error(f"RxNorm normalize unexpected error for '{drug_name}': {e}")
        return result


def get_active_ingredients(rxcui: str) -> List[Dict[str, str]]:
    """
    Retrieve active ingredient(s) for a given RxCUI.

    Returns list of dicts: [{rxcui, name, tty}, ...]
    """
    cached = get_cached("rxnorm_ingredients", rxcui)
    if cached:
        return cached

    ingredients: List[Dict[str, str]] = []
    try:
        data = _get(f"rxcui/{rxcui}/related.json", params={"tty": "IN+PIN"})
        concept_groups = (
            data.get("relatedGroup", {}).get("conceptGroup", [])
        )
        for group in concept_groups:
            for concept in group.get("conceptProperties", []):
                ingredients.append({
                    "rxcui": concept.get("rxcui", ""),
                    "name": concept.get("name", ""),
                    "tty": concept.get("tty", ""),
                })
        set_cached("rxnorm_ingredients", rxcui, ingredients)
        logger.info(f"RxNorm ingredients for RXCUI {rxcui}: {len(ingredients)} found")
    except Exception as e:
        logger.warning(f"RxNorm get_active_ingredients failed for RXCUI {rxcui}: {e}")
    return ingredients


def get_brand_names(rxcui: str) -> List[Dict[str, str]]:
    """Return brand name drugs (BN) related to a given ingredient RxCUI."""
    cached = get_cached("rxnorm_brands", rxcui)
    if cached:
        return cached

    brands: List[Dict[str, str]] = []
    try:
        data = _get(f"rxcui/{rxcui}/related.json", params={"tty": "BN+SBD"})
        concept_groups = (
            data.get("relatedGroup", {}).get("conceptGroup", [])
        )
        for group in concept_groups:
            for concept in group.get("conceptProperties", []):
                brands.append({
                    "rxcui": concept.get("rxcui", ""),
                    "name": concept.get("name", ""),
                    "tty": concept.get("tty", ""),
                })
        set_cached("rxnorm_brands", rxcui, brands)
        logger.info(f"RxNorm brand names for RXCUI {rxcui}: {len(brands)} found")
    except Exception as e:
        logger.warning(f"RxNorm get_brand_names failed for RXCUI {rxcui}: {e}")
    return brands


def get_drug_classes(rxcui: str) -> List[Dict[str, str]]:
    """Return drug classes (e.g. ATC, VA class) for a given RxCUI."""
    cached = get_cached("rxnorm_classes", rxcui)
    if cached:
        return cached

    classes: List[Dict[str, str]] = []
    try:
        # Use RxClass API which is part of the RxNav family
        url = f"https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json"
        resp = _session.get(url, params={"rxcui": rxcui}, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            rx_class_drugs = data.get("rxclassDrugInfoList", {}).get("rxclassDrugInfo", [])
            seen = set()
            for item in rx_class_drugs:
                cls = item.get("rxclassMinConceptItem", {})
                class_id = cls.get("classId", "")
                class_name = cls.get("className", "")
                class_type = cls.get("classType", "")
                if class_id not in seen:
                    classes.append({
                        "class_id": class_id,
                        "class_name": class_name,
                        "class_type": class_type,
                    })
                    seen.add(class_id)
        set_cached("rxnorm_classes", rxcui, classes)
        logger.info(f"RxNorm drug classes for RXCUI {rxcui}: {len(classes)} found")
    except Exception as e:
        logger.warning(f"RxNorm get_drug_classes failed for RXCUI {rxcui}: {e}")
    return classes


def get_full_drug_info(drug_name: str) -> Dict[str, Any]:
    """
    Convenience: normalize name, then collect ingredients, brands, classes.
    Returns a comprehensive dict representing RxNorm data for this medicine.
    """
    norm = normalize_drug_name(drug_name)
    rxcui = norm.get("rxcui")

    info: Dict[str, Any] = {
        "source": "RxNorm",
        "source_url": "https://rxnav.nlm.nih.gov",
        "input_name": drug_name,
        "normalized": norm,
        "active_ingredients": [],
        "brand_names": [],
        "drug_classes": [],
        "retrieval_ok": norm.get("status") in ("found", "approximate"),
    }

    if rxcui:
        info["active_ingredients"] = get_active_ingredients(rxcui)
        info["brand_names"] = get_brand_names(rxcui)
        info["drug_classes"] = get_drug_classes(rxcui)

    return info
