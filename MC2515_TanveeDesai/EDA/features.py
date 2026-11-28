"""
analysis/features.py — Feature engineering for Drug Safety Intelligence.

Creates analytical features including the Drug Safety Intelligence Score.
All scores are clearly presented as analytical indicators, NOT medical assessments.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from utils.logging import logger


# ── Count Features ────────────────────────────────────────────────────────────

def compute_count_features(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute count-based features from fused dataset.
    """
    summary = dataset.get("summary", {})
    dfs = dataset.get("dataframes", {})

    ae_df = dfs.get("adverse_events", pd.DataFrame())
    recalls_df = dfs.get("recalls", pd.DataFrame())
    articles_df = dfs.get("articles", pd.DataFrame())
    trials_df = dfs.get("trials", pd.DataFrame())
    dailymed_df = dfs.get("dailymed", pd.DataFrame())

    features: Dict[str, Any] = {}

    # Adverse events
    features["adverse_event_count"] = summary.get("total_adverse_events", 0)
    features["ae_records_retrieved"] = summary.get("ae_records_retrieved", 0)
    features["serious_ae_count"] = int(ae_df["serious"].sum()) if not ae_df.empty and "serious" in ae_df.columns else 0

    # Recalls
    features["recall_count"] = summary.get("recall_records", 0)
    features["total_recalls_reported"] = summary.get("total_recalls", 0)
    features["has_recalls"] = summary.get("has_recalls", False)

    # Recall classification breakdown
    if not recalls_df.empty and "classification" in recalls_df.columns:
        class_counts = recalls_df["classification"].value_counts().to_dict()
        features["class_i_recalls"] = class_counts.get("CLASS I", 0) + class_counts.get("CLASS I (MOST SEVERE)", 0)
        features["class_ii_recalls"] = class_counts.get("CLASS II", 0)
        features["class_iii_recalls"] = class_counts.get("CLASS III", 0)
    else:
        features["class_i_recalls"] = 0
        features["class_ii_recalls"] = 0
        features["class_iii_recalls"] = 0

    # Research
    features["research_count"] = summary.get("research_articles", 0)

    # Publication recency (% published in last 5 years)
    if not articles_df.empty and "pub_year" in articles_df.columns:
        recent_years = articles_df["pub_year"].dropna()
        if len(recent_years) > 0:
            current_year = pd.Timestamp.now().year
            recent_count = (recent_years >= current_year - 5).sum()
            features["research_recency"] = float(recent_count / len(recent_years))
        else:
            features["research_recency"] = 0.0
    else:
        features["research_recency"] = 0.0

    # Clinical trials
    features["clinical_trial_count"] = summary.get("clinical_trials", 0)
    features["active_trial_count"] = summary.get("active_trials", 0)

    if not trials_df.empty and "status_normalized" in trials_df.columns:
        status_counts = trials_df["status_normalized"].value_counts().to_dict()
        features["completed_trials"] = status_counts.get("Completed", 0)
        features["terminated_trials"] = status_counts.get("Terminated", 0)
    else:
        features["completed_trials"] = 0
        features["terminated_trials"] = 0

    # Label / warning features
    features["has_boxed_warning"] = summary.get("has_boxed_warning", False)

    if not dailymed_df.empty:
        row = dailymed_df.iloc[0]
        features["warning_length"] = len(str(row.get("warnings", "")))
        features["contraindication_length"] = len(str(row.get("contraindications", "")))
        features["has_storage_info"] = bool(row.get("storage", ""))
    else:
        features["warning_length"] = 0
        features["contraindication_length"] = 0
        features["has_storage_info"] = False

    return features


# ── Drug Safety Intelligence Score ────────────────────────────────────────────
# DISCLAIMER: This score is a purely analytical indicator derived from
# publicly available data. It does NOT constitute a medical assessment,
# clinical evaluation, or recommendation. Always consult a qualified
# healthcare professional for medical decisions.

_SCORE_WEIGHTS = {
    "adverse_events": 0.30,    # Reporting volume
    "recalls": 0.25,            # Recall history
    "boxed_warning": 0.20,      # FDA black-box warning presence
    "research_activity": 0.15,  # Research engagement
    "trial_activity": 0.10,     # Clinical trial activity
}

_SCORE_THRESHOLDS = {
    "low": 0.33,
    "moderate": 0.66,
}


def compute_safety_intelligence_score(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute a Drug Safety Intelligence Score (0–100) from analytical features.

    This is an ANALYTICAL INDICATOR only. A higher score does not mean a drug
    is more dangerous; it reflects higher observed reporting/recall activity
    in publicly available databases.
    """
    components: Dict[str, float] = {}

    # ── Adverse event component ────────────────────────────────────────────
    ae_count = features.get("adverse_event_count", 0)
    # Logarithmic scale to handle large variation (0 → 100K+ reports)
    ae_score = min(1.0, np.log1p(ae_count) / np.log1p(100_000))
    components["adverse_event_reporting"] = round(float(ae_score * 100), 1)

    # ── Recall component ──────────────────────────────────────────────────
    recall_score = 0.0
    if features.get("has_recalls"):
        # Weight by severity
        class_i = features.get("class_i_recalls", 0)
        class_ii = features.get("class_ii_recalls", 0)
        class_iii = features.get("class_iii_recalls", 0)
        weighted_recalls = class_i * 3 + class_ii * 2 + class_iii * 1
        recall_score = min(1.0, weighted_recalls / 10)
    components["recall_activity"] = round(float(recall_score * 100), 1)

    # ── Boxed warning component ────────────────────────────────────────────
    boxed_score = 1.0 if features.get("has_boxed_warning") else 0.0
    components["boxed_warning_presence"] = round(float(boxed_score * 100), 1)

    # ── Research activity component ────────────────────────────────────────
    research_count = features.get("research_count", 0)
    research_score = min(1.0, float(np.log1p(research_count) / np.log1p(1000)))
    components["research_activity"] = round(float(research_score * 100), 1)

    # ── Trial activity component ────────────────────────────────────────────
    trial_count = features.get("clinical_trial_count", 0)
    trial_score = min(1.0, float(np.log1p(trial_count) / np.log1p(200)))
    components["trial_activity"] = round(float(trial_score * 100), 1)

    # ── Weighted total ─────────────────────────────────────────────────────
    total_score = (
        ae_score * _SCORE_WEIGHTS["adverse_events"]
        + recall_score * _SCORE_WEIGHTS["recalls"]
        + boxed_score * _SCORE_WEIGHTS["boxed_warning"]
        + research_score * _SCORE_WEIGHTS["research_activity"]
        + trial_score * _SCORE_WEIGHTS["trial_activity"]
    )
    total_score_100 = round(total_score * 100, 1)

    # ── Category ───────────────────────────────────────────────────────────
    if total_score < _SCORE_THRESHOLDS["low"]:
        category = "Low Observed Reporting Activity"
        color = "green"
    elif total_score < _SCORE_THRESHOLDS["moderate"]:
        category = "Moderate Observed Reporting Activity"
        color = "orange"
    else:
        category = "High Observed Reporting Activity"
        color = "red"

    return {
        "score": total_score_100,
        "category": category,
        "color": color,
        "components": components,
        "weights": _SCORE_WEIGHTS,
        "disclaimer": (
            "This score is a purely analytical indicator based on publicly "
            "available data counts. It does NOT represent a clinical risk assessment "
            "or medical opinion. Consult a qualified healthcare professional for "
            "any medical decisions."
        ),
    }


def build_full_feature_set(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the complete feature set including count features and safety score.
    """
    count_features = compute_count_features(dataset)
    safety_score = compute_safety_intelligence_score(count_features)

    return {
        "count_features": count_features,
        "safety_intelligence_score": safety_score,
        "drug_name": dataset.get("drug_name", ""),
        "identity": dataset.get("identity", {}),
    }
