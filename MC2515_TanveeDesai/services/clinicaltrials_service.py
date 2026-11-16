"""
services/clinicaltrials_service.py — ClinicalTrials.gov API v2 service.

Purpose:
- Clinical trials data
- Study status, phase, interventions
- Conditions, trial dates, summaries

API: https://clinicaltrials.gov/api/v2
No API key required.
"""

from typing import Any, Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import CLINICALTRIALS_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES, CT_PAGE_SIZE
from utils.logging import logger
from utils.caching import get_cached, set_cached

_session = requests.Session()
_session.headers.update({"Accept": "application/json"})


class ClinicalTrialsServiceError(Exception):
    pass


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True,
)
def _get(endpoint: str, params: Optional[Dict] = None) -> Dict:
    url = f"{CLINICALTRIALS_BASE_URL}/{endpoint}"
    resp = _session.get(url, params=params, timeout=REQUEST_TIMEOUT)
    if resp.status_code == 404:
        return {"studies": []}
    resp.raise_for_status()
    return resp.json()


# ── Search Studies ────────────────────────────────────────────────────────────

def search_trials(
    drug_name: str,
    page_size: int = CT_PAGE_SIZE,
    status_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search ClinicalTrials.gov v2 API for trials involving a drug.
    """
    cache_key = f"{drug_name.lower()}_{page_size}_{status_filter}"
    cached = get_cached("clinicaltrials_search", cache_key)
    if cached:
        return cached

    result: Dict[str, Any] = {
        "source": "ClinicalTrials.gov",
        "source_url": "https://clinicaltrials.gov",
        "drug_name": drug_name,
        "trials": [],
        "total": 0,
        "error": None,
        "retrieval_ok": False,
    }

    try:
        params: Dict[str, Any] = {
            "query.intr": drug_name,
            "pageSize": page_size,
            "format": "json",
            "fields": (
                "NCTId,BriefTitle,OfficialTitle,OverallStatus,Phase,"
                "StartDate,CompletionDate,StudyType,BriefSummary,"
                "Condition,InterventionName,InterventionType,"
                "LeadSponsorName,EnrollmentCount,ResultsFirstPostDate"
            ),
        }
        if status_filter:
            params["filter.overallStatus"] = status_filter

        data = _get("studies", params=params)
        studies_raw = data.get("studies", [])
        total_count = data.get("totalCount", len(studies_raw))

        parsed = []
        for study in studies_raw:
            parsed.append(_parse_study(study))

        result["trials"] = parsed
        result["total"] = total_count
        result["retrieval_ok"] = True
        set_cached("clinicaltrials_search", cache_key, result)
        logger.info(f"ClinicalTrials search for '{drug_name}': {len(parsed)} trials (total={total_count})")

    except requests.HTTPError as e:
        result["error"] = f"HTTP {e.response.status_code}"
        logger.warning(f"ClinicalTrials HTTP error for '{drug_name}': {e}")
    except requests.RequestException as e:
        result["error"] = f"Network error: {e}"
        logger.error(f"ClinicalTrials network error for '{drug_name}': {e}")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"ClinicalTrials unexpected error: {e}")

    return result


def _parse_study(study: Dict) -> Dict[str, Any]:
    """Parse a ClinicalTrials v2 study record into a flat dict."""
    protocol = study.get("protocolSection", {})
    id_module = protocol.get("identificationModule", {})
    status_module = protocol.get("statusModule", {})
    desc_module = protocol.get("descriptionModule", {})
    design_module = protocol.get("designModule", {})
    arms_module = protocol.get("armsInterventionsModule", {})
    conditions_module = protocol.get("conditionsModule", {})
    sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
    results_section = study.get("resultsSection", {})

    # Extract phase
    phases = design_module.get("phases", [])
    phase_str = ", ".join(phases) if phases else "N/A"

    # Extract interventions
    interventions = arms_module.get("interventions", [])
    intervention_names = [iv.get("name", "") for iv in interventions if iv.get("type") == "DRUG"]

    # Extract conditions
    conditions = conditions_module.get("conditions", [])

    # Lead sponsor
    lead_sponsor = sponsor_module.get("leadSponsor", {}).get("name", "")

    # Enrollment
    enrollment = design_module.get("enrollmentInfo", {})
    enrollment_count = enrollment.get("count", 0)

    return {
        "nct_id": id_module.get("nctId", ""),
        "title": id_module.get("briefTitle", ""),
        "official_title": id_module.get("officialTitle", ""),
        "status": status_module.get("overallStatus", ""),
        "phase": phase_str,
        "start_date": status_module.get("startDateStruct", {}).get("date", ""),
        "completion_date": status_module.get("completionDateStruct", {}).get("date", ""),
        "primary_completion_date": status_module.get("primaryCompletionDateStruct", {}).get("date", ""),
        "study_type": design_module.get("studyType", ""),
        "summary": desc_module.get("briefSummary", "")[:1000],
        "conditions": conditions[:5],
        "interventions": intervention_names[:5],
        "lead_sponsor": lead_sponsor,
        "enrollment": enrollment_count,
        "results_posted": bool(results_section),
        "source_url": f"https://clinicaltrials.gov/study/{id_module.get('nctId', '')}",
    }


# ── Phase / Status Statistics ─────────────────────────────────────────────────

def get_trial_statistics(trials: List[Dict]) -> Dict[str, Any]:
    """Compute summary statistics from a list of parsed trial dicts."""
    if not trials:
        return {}

    status_counts: Dict[str, int] = {}
    phase_counts: Dict[str, int] = {}
    active_count = 0
    completed_count = 0

    for t in trials:
        status = t.get("status", "Unknown")
        phase = t.get("phase", "Unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

        if status in ("RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION"):
            active_count += 1
        if status == "COMPLETED":
            completed_count += 1

    return {
        "total": len(trials),
        "active_count": active_count,
        "completed_count": completed_count,
        "status_distribution": status_counts,
        "phase_distribution": phase_counts,
    }


# ── Full Drug Info ────────────────────────────────────────────────────────────

def get_full_drug_info(drug_name: str, ingredient_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Collect comprehensive ClinicalTrials data for a drug.
    """
    search_term = ingredient_name or drug_name
    trials_result = search_trials(search_term)

    trials = trials_result.get("trials", [])
    stats = get_trial_statistics(trials)

    return {
        "source": "ClinicalTrials.gov",
        "source_url": "https://clinicaltrials.gov",
        "drug_name": drug_name,
        "search_term": search_term,
        "trials": trials,
        "total": trials_result.get("total", 0),
        "statistics": stats,
        "error": trials_result.get("error"),
        "retrieval_ok": trials_result.get("retrieval_ok", False),
    }
