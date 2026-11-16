"""
preprocessing/normalization.py — Data normalization after cleaning.

Standardizes fields across sources so the fusion layer can merge records
from openFDA, DailyMed, PubMed, and ClinicalTrials using common identifiers.
"""

import re
from typing import Any, Dict, List, Optional

import pandas as pd

from utils.logging import logger


def normalize_drug_name(name: str) -> str:
    """Lowercase, strip punctuation → consistent internal key."""
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9\s\-]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def normalize_status(status: str) -> str:
    """Map various status strings to a small canonical set."""
    s = status.upper().strip()
    active_map = {
        "RECRUITING": "Active",
        "ACTIVE_NOT_RECRUITING": "Active",
        "ENROLLING_BY_INVITATION": "Active",
        "NOT_YET_RECRUITING": "Planned",
        "COMPLETED": "Completed",
        "TERMINATED": "Terminated",
        "WITHDRAWN": "Withdrawn",
        "SUSPENDED": "Suspended",
        "UNKNOWN": "Unknown",
        "ONGOING": "Active",
    }
    return active_map.get(s, status.title())


def normalize_recall_classification(cls: str) -> str:
    """Map openFDA recall class to readable strings."""
    mapping = {
        "CLASS I": "Class I (Most Severe)",
        "CLASS II": "Class II (Moderate)",
        "CLASS III": "Class III (Least Severe)",
    }
    return mapping.get(cls.upper().strip(), cls)


def normalize_phase(phase: str) -> str:
    """Normalize clinical trial phase strings."""
    if not phase:
        return "N/A"
    phase = phase.upper().strip()
    phase_map = {
        "PHASE1": "Phase 1",
        "PHASE 1": "Phase 1",
        "PHASE2": "Phase 2",
        "PHASE 2": "Phase 2",
        "PHASE3": "Phase 3",
        "PHASE 3": "Phase 3",
        "PHASE4": "Phase 4",
        "PHASE 4": "Phase 4",
        "PHASE1/PHASE2": "Phase 1/2",
        "PHASE2/PHASE3": "Phase 2/3",
        "EARLY PHASE 1": "Early Phase 1",
        "N/A": "N/A",
    }
    # Try direct map
    if phase in phase_map:
        return phase_map[phase]
    # Parse from comma-separated list (ClinicalTrials v2 returns ["PHASE2", ...])
    parts = [p.strip() for p in phase.split(",")]
    normalized_parts = [phase_map.get(p, p.title()) for p in parts]
    return ", ".join(normalized_parts)


def extract_year(date_str: Optional[str]) -> Optional[int]:
    """Extract year from ISO date string."""
    if not date_str:
        return None
    try:
        return int(date_str[:4])
    except (ValueError, TypeError):
        return None


def build_drug_identity(rxnorm_data: Dict) -> Dict[str, Any]:
    """
    Build a canonical drug identity record from RxNorm data.
    This becomes the anchor for all downstream source joins.
    """
    normalized = rxnorm_data.get("normalized", {})
    ingredients = rxnorm_data.get("active_ingredients", [])
    brands = rxnorm_data.get("brand_names", [])
    classes = rxnorm_data.get("drug_classes", [])

    # Primary ingredient name (prefer IN over PIN)
    primary_ingredient = ""
    for ing in ingredients:
        if ing.get("tty") == "IN":
            primary_ingredient = ing.get("name", "")
            break
    if not primary_ingredient and ingredients:
        primary_ingredient = ingredients[0].get("name", "")

    # Drug class (prefer ATC or VA class)
    primary_class = ""
    preferred_types = ["ATC1-4", "VA", "MESHPA", "EPC"]
    for pt in preferred_types:
        for cls in classes:
            if cls.get("class_type", "").upper() in (pt, pt.upper()):
                primary_class = cls.get("class_name", "")
                break
        if primary_class:
            break
    if not primary_class and classes:
        primary_class = classes[0].get("class_name", "")

    return {
        "drug_name": normalized.get("input_name", ""),
        "normalized_drug_name": normalized.get("name", ""),
        "rxcui": normalized.get("rxcui", ""),
        "active_ingredient": primary_ingredient,
        "all_ingredients": [i.get("name", "") for i in ingredients],
        "brand_names": [b.get("name", "") for b in brands[:10]],
        "drug_class": primary_class,
        "all_classes": classes[:10],
        "rxnorm_status": normalized.get("status", ""),
        "approximate_match": normalized.get("approximate_match", False),
    }
