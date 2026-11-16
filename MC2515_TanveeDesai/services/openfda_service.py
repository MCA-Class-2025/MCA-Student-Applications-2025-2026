"""
services/openfda_service.py — openFDA API service.

Purpose:
- Drug adverse events (FAERS database)
- Drug enforcement / recalls
- Drug labels (SPL structured product labeling)

API: https://api.fda.gov
No key required for basic use; OPENFDA_API_KEY provides higher rate limits.
"""

from typing import Any, Dict, List, Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import (
    OPENFDA_BASE_URL,
    OPENFDA_API_KEY,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    OPENFDA_ADVERSE_LIMIT,
    OPENFDA_LABEL_LIMIT,
    OPENFDA_RECALL_LIMIT,
)
from utils.logging import logger
from utils.caching import get_cached, set_cached

_session = requests.Session()
_session.headers.update({"Accept": "application/json"})

_API_KEY_PARAM = {"api_key": OPENFDA_API_KEY} if OPENFDA_API_KEY else {}


class OpenFDAServiceError(Exception):
    pass


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True,
)
def _get(endpoint: str, params: Dict) -> Dict:
    url = f"{OPENFDA_BASE_URL}/{endpoint}"
    all_params = {**_API_KEY_PARAM, **params}
    resp = _session.get(url, params=all_params, timeout=REQUEST_TIMEOUT)
    if resp.status_code == 404:
        return {"results": [], "meta": {}}
    resp.raise_for_status()
    return resp.json()


# ── Adverse Events ────────────────────────────────────────────────────────────

def get_adverse_events(drug_name: str, limit: int = OPENFDA_ADVERSE_LIMIT) -> Dict[str, Any]:
    """
    Fetch adverse event reports from FDA FAERS for a given drug name.
    Returns raw results list + metadata.
    """
    cache_key = f"{drug_name.lower()}_{limit}"
    cached = get_cached("openfda_adverse", cache_key)
    if cached:
        return cached

    result: Dict[str, Any] = {
        "source": "openFDA",
        "source_type": "adverse_events",
        "source_url": "https://api.fda.gov/drug/event.json",
        "drug_name": drug_name,
        "records": [],
        "total": 0,
        "error": None,
        "retrieval_ok": False,
    }

    try:
        search_query = f'patient.drug.medicinalproduct:"{drug_name}"'
        data = _get(
            "drug/event.json",
            {"search": search_query, "limit": limit},
        )
        records = data.get("results", [])
        meta = data.get("meta", {})
        total = meta.get("results", {}).get("total", len(records))

        parsed = []
        for r in records:
            patient = r.get("patient", {})
            reactions = patient.get("reaction", [])
            drugs = patient.get("drug", [])
            parsed.append({
                "report_id": r.get("safetyreportid", ""),
                "receive_date": r.get("receivedate", ""),
                "serious": r.get("serious", ""),
                "serious_death": r.get("seriousnessdeath", ""),
                "reactions": [rx.get("reactionmeddrapt", "") for rx in reactions],
                "drug_names": [d.get("medicinalproduct", "") for d in drugs],
                "manufacturer": r.get("primarysource", {}).get("qualification", ""),
                "country": r.get("primarysource", {}).get("reportercountry", ""),
                "outcome": patient.get("patientdeath", {}).get("patientdeathdate", ""),
            })

        result["records"] = parsed
        result["total"] = total
        result["retrieval_ok"] = True
        logger.info(f"openFDA adverse events for '{drug_name}': {len(parsed)} records (total={total})")

    except requests.HTTPError as e:
        result["error"] = f"HTTP {e.response.status_code}"
        logger.warning(f"openFDA adverse events HTTP error for '{drug_name}': {e}")
    except requests.RequestException as e:
        result["error"] = f"Network error: {e}"
        logger.error(f"openFDA adverse events network error for '{drug_name}': {e}")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"openFDA adverse events unexpected error for '{drug_name}': {e}")

    if result["retrieval_ok"]:
        set_cached("openfda_adverse", cache_key, result)
    return result


# ── Drug Labels ───────────────────────────────────────────────────────────────

def get_drug_labels(drug_name: str, limit: int = OPENFDA_LABEL_LIMIT) -> Dict[str, Any]:
    """
    Fetch structured product labels from openFDA.
    """
    cache_key = f"{drug_name.lower()}_{limit}"
    cached = get_cached("openfda_labels", cache_key)
    if cached:
        return cached

    result: Dict[str, Any] = {
        "source": "openFDA",
        "source_type": "drug_labels",
        "source_url": "https://api.fda.gov/drug/label.json",
        "drug_name": drug_name,
        "records": [],
        "error": None,
        "retrieval_ok": False,
    }

    try:
        data = _get(
            "drug/label.json",
            {
                "search": f'openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}"',
                "limit": limit,
            },
        )
        records = data.get("results", [])

        parsed = []
        for r in records:
            openfda = r.get("openfda", {})
            parsed.append({
                "brand_name": openfda.get("brand_name", [""])[0] if openfda.get("brand_name") else "",
                "generic_name": openfda.get("generic_name", [""])[0] if openfda.get("generic_name") else "",
                "manufacturer_name": openfda.get("manufacturer_name", [""])[0] if openfda.get("manufacturer_name") else "",
                "product_type": openfda.get("product_type", [""])[0] if openfda.get("product_type") else "",
                "route": openfda.get("route", []),
                "substance_name": openfda.get("substance_name", []),
                "warnings": r.get("warnings", [""])[0][:2000] if r.get("warnings") else "",
                "contraindications": r.get("contraindications", [""])[0][:2000] if r.get("contraindications") else "",
                "adverse_reactions": r.get("adverse_reactions", [""])[0][:2000] if r.get("adverse_reactions") else "",
                "boxed_warning": r.get("boxed_warning", [""])[0][:2000] if r.get("boxed_warning") else "",
                "indications_and_usage": r.get("indications_and_usage", [""])[0][:2000] if r.get("indications_and_usage") else "",
                "dosage_and_administration": r.get("dosage_and_administration", [""])[0][:1000] if r.get("dosage_and_administration") else "",
                "storage_and_handling": r.get("storage_and_handling", [""])[0][:500] if r.get("storage_and_handling") else "",
                "pregnancy": r.get("pregnancy", [""])[0][:500] if r.get("pregnancy") else "",
                "set_id": r.get("set_id", ""),
                "version": r.get("version", ""),
                "effective_time": r.get("effective_time", ""),
            })

        result["records"] = parsed
        result["retrieval_ok"] = True
        logger.info(f"openFDA labels for '{drug_name}': {len(parsed)} records")

    except requests.HTTPError as e:
        result["error"] = f"HTTP {e.response.status_code}"
        logger.warning(f"openFDA labels HTTP error for '{drug_name}': {e}")
    except requests.RequestException as e:
        result["error"] = f"Network error: {e}"
        logger.error(f"openFDA labels network error for '{drug_name}': {e}")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"openFDA labels unexpected error: {e}")

    if result["retrieval_ok"]:
        set_cached("openfda_labels", cache_key, result)
    return result


# ── Drug Enforcement / Recalls ────────────────────────────────────────────────

def get_drug_recalls(drug_name: str, limit: int = OPENFDA_RECALL_LIMIT) -> Dict[str, Any]:
    """
    Fetch drug recall / enforcement actions from openFDA.
    """
    cache_key = f"{drug_name.lower()}_{limit}"
    cached = get_cached("openfda_recalls", cache_key)
    if cached:
        return cached

    result: Dict[str, Any] = {
        "source": "openFDA",
        "source_type": "drug_recalls",
        "source_url": "https://api.fda.gov/drug/enforcement.json",
        "drug_name": drug_name,
        "records": [],
        "total": 0,
        "error": None,
        "retrieval_ok": False,
    }

    try:
        data = _get(
            "drug/enforcement.json",
            {
                "search": f'product_description:"{drug_name}"',
                "limit": limit,
            },
        )
        records = data.get("results", [])
        meta = data.get("meta", {})
        total = meta.get("results", {}).get("total", len(records))

        parsed = []
        for r in records:
            parsed.append({
                "recall_number": r.get("recall_number", ""),
                "status": r.get("status", ""),
                "classification": r.get("classification", ""),
                "product_description": r.get("product_description", "")[:500],
                "reason_for_recall": r.get("reason_for_recall", "")[:500],
                "recall_initiation_date": r.get("recall_initiation_date", ""),
                "report_date": r.get("report_date", ""),
                "recalling_firm": r.get("recalling_firm", ""),
                "distribution_pattern": r.get("distribution_pattern", "")[:300],
                "voluntary_mandated": r.get("voluntary_mandated", ""),
                "product_quantity": r.get("product_quantity", ""),
                "city": r.get("city", ""),
                "state": r.get("state", ""),
                "country": r.get("country", ""),
            })

        result["records"] = parsed
        result["total"] = total
        result["retrieval_ok"] = True
        logger.info(f"openFDA recalls for '{drug_name}': {len(parsed)} records (total={total})")

    except requests.HTTPError as e:
        result["error"] = f"HTTP {e.response.status_code}"
        logger.warning(f"openFDA recalls HTTP error for '{drug_name}': {e}")
    except requests.RequestException as e:
        result["error"] = f"Network error: {e}"
        logger.error(f"openFDA recalls network error for '{drug_name}': {e}")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"openFDA recalls unexpected error: {e}")

    if result["retrieval_ok"]:
        set_cached("openfda_recalls", cache_key, result)
    return result


def get_top_adverse_reactions(drug_name: str, top_n: int = 15) -> List[Dict]:
    """
    Use openFDA count endpoint to get top reported adverse reactions for a drug.
    Returns list of {term, count}.
    """
    cache_key = f"{drug_name.lower()}_{top_n}"
    cached = get_cached("openfda_ae_count", cache_key)
    if cached:
        return cached

    results = []
    try:
        data = _get(
            "drug/event.json",
            {
                "search": f'patient.drug.medicinalproduct:"{drug_name}"',
                "count": "patient.reaction.reactionmeddrapt.exact",
                "limit": top_n,
            },
        )
        results = [{"term": r["term"], "count": r["count"]} for r in data.get("results", [])]
        set_cached("openfda_ae_count", cache_key, results)
        logger.info(f"openFDA top AE counts for '{drug_name}': {len(results)}")
    except Exception as e:
        logger.warning(f"openFDA top AE counts failed for '{drug_name}': {e}")

    return results


def get_full_drug_info(drug_name: str) -> Dict[str, Any]:
    """Convenience: collect labels, adverse events, recalls."""
    labels = get_drug_labels(drug_name)
    adverse = get_adverse_events(drug_name)
    recalls = get_drug_recalls(drug_name)
    ae_counts = get_top_adverse_reactions(drug_name)

    return {
        "source": "openFDA",
        "labels": labels,
        "adverse_events": adverse,
        "recalls": recalls,
        "top_adverse_reactions": ae_counts,
        "retrieval_ok": any([
            labels["retrieval_ok"],
            adverse["retrieval_ok"],
            recalls["retrieval_ok"],
        ]),
    }
