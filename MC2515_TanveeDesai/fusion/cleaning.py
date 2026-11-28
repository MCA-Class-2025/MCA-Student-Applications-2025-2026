"""
preprocessing/cleaning.py — Data cleaning pipeline.

Handles:
- Missing values
- Duplicate records
- Inconsistent naming / capitalization
- Whitespace normalization
- Malformed API responses
- Date standardization
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

from utils.logging import logger


# ── Text Cleaning ─────────────────────────────────────────────────────────────

def clean_text(text: Any) -> str:
    """Normalize a text field: strip, collapse whitespace, remove control chars."""
    if text is None or (isinstance(text, float) and np.isnan(text)):
        return ""
    text = str(text).strip()
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)  # control chars
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_drug_name(name: Any) -> str:
    """Normalize a drug name to title-case, stripped."""
    cleaned = clean_text(name)
    if not cleaned:
        return ""
    # Remove trailing dose info in parentheses for canonical name
    cleaned = re.sub(r"\s*\(.*?\)\s*$", "", cleaned)
    return cleaned.strip().title()


def clean_date(date_str: Any) -> Optional[str]:
    """
    Parse and normalize various date formats to ISO 8601 (YYYY-MM-DD).
    Returns None if unparseable.
    """
    if not date_str:
        return None
    date_str = str(date_str).strip()

    # Format → expected length of matching substring
    formats = [
        ("%Y%m%d", 8),
        ("%Y-%m-%d", 10),
        ("%Y-%m", 7),
        ("%B %d, %Y", None),
        ("%b %d, %Y", None),
        ("%Y %b %d", None),
        ("%Y %B", None),
        ("%d-%b-%Y", None),
        ("%Y", 4),
    ]
    for fmt, length in formats:
        try:
            target = date_str[:length] if length else date_str
            dt = datetime.strptime(target, fmt)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            continue

    # Try extracting just the year
    match = re.search(r"\b(19|20)\d{2}\b", date_str)
    if match:
        return f"{match.group()}-01-01"

    return None


def clean_list_field(value: Any) -> List[str]:
    """Convert a field that may be a list or string into a cleaned list."""
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_text(v) for v in value if v]
    if isinstance(value, str):
        if value.strip():
            return [clean_text(value)]
    return []


# ── DataFrame Cleaning ────────────────────────────────────────────────────────

def clean_adverse_events_df(records: List[Dict]) -> pd.DataFrame:
    """
    Clean adverse event records from openFDA.
    """
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Normalize text columns
    for col in ["reactions", "drug_names"]:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: [clean_text(r) for r in x] if isinstance(x, list) else []
            )

    # Standardize dates
    if "receive_date" in df.columns:
        df["receive_date"] = df["receive_date"].apply(clean_date)

    # Convert serious flag to bool
    if "serious" in df.columns:
        df["serious"] = df["serious"].apply(lambda x: str(x) == "1")

    # Drop exact duplicates
    before = len(df)
    df = df.drop_duplicates(subset=["report_id"], keep="first")
    removed = before - len(df)
    if removed:
        logger.info(f"Adverse events: removed {removed} duplicate report IDs")

    return df.reset_index(drop=True)


def clean_recalls_df(records: List[Dict]) -> pd.DataFrame:
    """
    Clean recall records from openFDA.
    """
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    text_cols = ["product_description", "reason_for_recall", "recalling_firm", "distribution_pattern"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)

    date_cols = ["recall_initiation_date", "report_date"]
    for col in date_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_date)

    if "classification" in df.columns:
        df["classification"] = df["classification"].apply(
            lambda x: clean_text(x).upper() if x else "UNKNOWN"
        )

    # Dedup on recall number
    if "recall_number" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["recall_number"], keep="first")
        if before - len(df):
            logger.info(f"Recalls: removed {before - len(df)} duplicates")

    return df.reset_index(drop=True)


def clean_articles_df(articles: List[Dict]) -> pd.DataFrame:
    """
    Clean PubMed article records.
    """
    if not articles:
        return pd.DataFrame()

    df = pd.DataFrame(articles)

    for col in ["title", "abstract", "journal"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)

    if "pub_date" in df.columns:
        df["pub_date_normalized"] = df["pub_date"].apply(clean_date)

    # Remove duplicates by PMID
    if "pmid" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["pmid"], keep="first")
        if before - len(df):
            logger.info(f"Articles: removed {before - len(df)} duplicate PMIDs")

    # Remove articles with empty titles
    if "title" in df.columns:
        df = df[df["title"].str.len() > 5]

    return df.reset_index(drop=True)


def clean_trials_df(trials: List[Dict]) -> pd.DataFrame:
    """
    Clean ClinicalTrials records.
    """
    if not trials:
        return pd.DataFrame()

    df = pd.DataFrame(trials)

    for col in ["title", "summary", "official_title"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)

    date_cols = ["start_date", "completion_date", "primary_completion_date"]
    for col in date_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_date)

    if "status" in df.columns:
        df["status"] = df["status"].apply(lambda x: clean_text(x).upper() if x else "UNKNOWN")

    # Dedup by NCT ID
    if "nct_id" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["nct_id"], keep="first")
        if before - len(df):
            logger.info(f"Trials: removed {before - len(df)} duplicate NCT IDs")

    return df.reset_index(drop=True)


def clean_labels_df(records: List[Dict]) -> pd.DataFrame:
    """
    Clean drug label records from openFDA / DailyMed.
    """
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    text_cols = [
        "warnings", "contraindications", "adverse_reactions",
        "boxed_warning", "indications_and_usage", "storage_and_handling",
        "warnings", "precautions", "indications", "dosage",
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)

    name_cols = ["brand_name", "generic_name", "manufacturer_name", "labeler"]
    for col in name_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_drug_name)

    return df.reset_index(drop=True)
