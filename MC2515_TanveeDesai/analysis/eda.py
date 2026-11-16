"""
analysis/eda.py — Exploratory Data Analysis on the fused drug dataset.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from utils.logging import logger


def eda_adverse_events(ae_df: pd.DataFrame) -> Dict[str, Any]:
    """EDA on adverse event data."""
    if ae_df is None or ae_df.empty:
        return {"available": False}

    result: Dict[str, Any] = {"available": True}

    # Total counts
    result["total_records"] = len(ae_df)

    # Serious events
    if "serious" in ae_df.columns:
        result["serious_count"] = int(ae_df["serious"].sum())
        result["serious_rate"] = float(ae_df["serious"].mean())

    # Date distribution
    if "receive_date" in ae_df.columns:
        dates = pd.to_datetime(ae_df["receive_date"], errors="coerce")
        valid_dates = dates.dropna()
        if len(valid_dates) > 0:
            result["date_range"] = {
                "min": str(valid_dates.min().date()),
                "max": str(valid_dates.max().date()),
            }
            # Year distribution
            year_counts = valid_dates.dt.year.value_counts().sort_index()
            result["year_distribution"] = year_counts.to_dict()

    # Top reactions
    if "reactions" in ae_df.columns:
        all_reactions = []
        for reactions in ae_df["reactions"]:
            if isinstance(reactions, list):
                all_reactions.extend([r for r in reactions if r])
        if all_reactions:
            reaction_series = pd.Series(all_reactions)
            top_reactions = reaction_series.value_counts().head(20)
            result["top_reactions"] = top_reactions.to_dict()
            result["unique_reactions"] = len(reaction_series.unique())

    # Country distribution
    if "country" in ae_df.columns:
        country_counts = ae_df["country"].value_counts().head(10)
        result["country_distribution"] = country_counts.to_dict()

    return result


def eda_recalls(recalls_df: pd.DataFrame) -> Dict[str, Any]:
    """EDA on recall data."""
    if recalls_df is None or recalls_df.empty:
        return {"available": False}

    result: Dict[str, Any] = {"available": True}
    result["total_records"] = len(recalls_df)

    # Classification distribution
    if "classification" in recalls_df.columns:
        class_dist = recalls_df["classification"].value_counts().to_dict()
        result["classification_distribution"] = class_dist

    # Timeline
    date_col = "recall_initiation_date" if "recall_initiation_date" in recalls_df.columns else "report_date"
    if date_col in recalls_df.columns:
        dates = pd.to_datetime(recalls_df[date_col], errors="coerce")
        valid_dates = dates.dropna()
        if len(valid_dates) > 0:
            result["date_range"] = {
                "min": str(valid_dates.min().date()),
                "max": str(valid_dates.max().date()),
            }
            year_counts = valid_dates.dt.year.value_counts().sort_index()
            result["year_distribution"] = year_counts.to_dict()

    # Status distribution
    if "status" in recalls_df.columns:
        result["status_distribution"] = recalls_df["status"].value_counts().to_dict()

    # Voluntary vs mandated
    if "voluntary_mandated" in recalls_df.columns:
        result["voluntary_mandated"] = recalls_df["voluntary_mandated"].value_counts().to_dict()

    # Top reasons (first 50 chars of each)
    if "reason_for_recall" in recalls_df.columns:
        reasons = recalls_df["reason_for_recall"].dropna()
        result["top_reasons"] = reasons.head(10).tolist()

    return result


def eda_research(articles_df: pd.DataFrame) -> Dict[str, Any]:
    """EDA on PubMed research articles."""
    if articles_df is None or articles_df.empty:
        return {"available": False}

    result: Dict[str, Any] = {"available": True}
    result["total_articles"] = len(articles_df)

    # Year distribution
    if "pub_year" in articles_df.columns:
        years = articles_df["pub_year"].dropna().astype(int)
        if len(years) > 0:
            result["year_distribution"] = years.value_counts().sort_index().to_dict()
            result["year_range"] = {"min": int(years.min()), "max": int(years.max())}
            result["median_pub_year"] = float(years.median())

    # Journal distribution
    if "journal" in articles_df.columns:
        journals = articles_df["journal"].dropna()
        result["top_journals"] = journals.value_counts().head(10).to_dict()

    # Publication types
    if "pub_types" in articles_df.columns:
        all_types = []
        for pt in articles_df["pub_types"]:
            if isinstance(pt, list):
                all_types.extend(pt)
        if all_types:
            result["pub_type_distribution"] = (
                pd.Series(all_types).value_counts().head(10).to_dict()
            )

    return result


def eda_clinical_trials(trials_df: pd.DataFrame) -> Dict[str, Any]:
    """EDA on clinical trial data."""
    if trials_df is None or trials_df.empty:
        return {"available": False}

    result: Dict[str, Any] = {"available": True}
    result["total_trials"] = len(trials_df)

    # Status distribution
    if "status_normalized" in trials_df.columns:
        result["status_distribution"] = trials_df["status_normalized"].value_counts().to_dict()
    elif "status" in trials_df.columns:
        result["status_distribution"] = trials_df["status"].value_counts().to_dict()

    # Phase distribution
    if "phase_normalized" in trials_df.columns:
        result["phase_distribution"] = trials_df["phase_normalized"].value_counts().to_dict()
    elif "phase" in trials_df.columns:
        result["phase_distribution"] = trials_df["phase"].value_counts().to_dict()

    # Start year distribution
    if "start_year" in trials_df.columns:
        years = trials_df["start_year"].dropna().astype(int)
        if len(years) > 0:
            result["start_year_distribution"] = years.value_counts().sort_index().to_dict()

    # Enrollment stats
    if "enrollment" in trials_df.columns:
        enroll = trials_df["enrollment"].dropna()
        enroll = enroll[enroll > 0]
        if len(enroll) > 0:
            result["enrollment_stats"] = {
                "mean": float(enroll.mean()),
                "median": float(enroll.median()),
                "max": float(enroll.max()),
                "total": float(enroll.sum()),
            }

    # Sponsor distribution
    if "lead_sponsor" in trials_df.columns:
        sponsors = trials_df["lead_sponsor"].dropna()
        result["top_sponsors"] = sponsors.value_counts().head(10).to_dict()

    return result


def run_full_eda(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run EDA on all components of the fused dataset.
    Returns a comprehensive EDA results dict.
    """
    dfs = dataset.get("dataframes", {})

    ae_eda = eda_adverse_events(dfs.get("adverse_events", pd.DataFrame()))
    recall_eda = eda_recalls(dfs.get("recalls", pd.DataFrame()))
    research_eda = eda_research(dfs.get("articles", pd.DataFrame()))
    trial_eda = eda_clinical_trials(dfs.get("trials", pd.DataFrame()))

    return {
        "drug_name": dataset.get("drug_name", ""),
        "adverse_events": ae_eda,
        "recalls": recall_eda,
        "research": research_eda,
        "clinical_trials": trial_eda,
        "summary": dataset.get("summary", {}),
    }
