"""Cleaning and preparing the dataset. The raw DataFrame is never modified."""

import re
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# Label used for categorical values that are legitimately empty
# (e.g. City is only recorded for Weather-Based stories).
NOT_RECORDED = "Not recorded"

CATEGORICAL_COLUMNS = ["Mode", "Language", "City", "Weather Condition", "Detected Emotion"]


def _clean_markdown(text) -> str:
    """Remove markdown symbols such as ** and ### that appear in generated titles/stories."""
    if pd.isna(text):
        return ""
    text = re.sub(r"[*#_`]+", "", str(text))
    return re.sub(r"[ \t]+", " ", text).strip()


def _yes_no_to_bool(series: pd.Series) -> pd.Series:
    """Convert Yes/No style text to True/False (case-insensitive). Unknown -> <NA>."""
    mapping = {"yes": True, "y": True, "true": True, "1": True,
               "no": False, "n": False, "false": False, "0": False}
    cleaned = series.astype("object").map(lambda v: str(v).strip().lower() if pd.notna(v) else None)
    return cleaned.map(mapping).astype("boolean")


def _text(series: pd.Series) -> pd.Series:
    """Return a plain object-dtype text column, keeping missing values as NaN."""
    return series.astype("object").map(lambda v: str(v).strip() if pd.notna(v) else np.nan)


def find_inconsistent_labels(df: pd.DataFrame) -> Dict[str, List[Tuple[str, List[str]]]]:
    """Find labels that differ only by case, spacing or punctuation.

    Example: 'Joy', 'joy ' and 'JOY' would all be reported as one group.
    """
    problems: Dict[str, List[Tuple[str, List[str]]]] = {}
    for col in CATEGORICAL_COLUMNS:
        if col not in df.columns:
            continue
        values = df[col].dropna().astype(str).unique()
        groups: Dict[str, List[str]] = {}
        for value in values:
            key = re.sub(r"\W+", "", value.lower())
            groups.setdefault(key, []).append(value)
        issues = [(key, variants) for key, variants in groups.items() if len(variants) > 1]
        if issues:
            problems[col] = issues
    return problems


def preprocess(raw: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Return (processed_dataframe, log_of_steps)."""
    log: List[str] = []
    df = raw.copy()

    # 1. Strip whitespace from every text column; empty strings become missing values.
    for col in df.columns:
        if df[col].dtype == object or str(df[col].dtype) in ("str", "string"):
            df[col] = _text(df[col]).replace({"": np.nan})
    log.append("Trimmed leading/trailing spaces and converted empty strings to missing values.")

    # 2. Remove exact duplicate rows only (same values in every column).
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    removed = before - len(df)
    log.append(
        f"Removed {removed} exact duplicate row(s)." if removed
        else "No exact duplicate rows found, so no records were removed."
    )
    duplicate_ids = int(df["Story ID"].duplicated().sum())
    if duplicate_ids:
        log.append(f"Note: {duplicate_ids} repeated Story ID value(s) remain (rows differ, so they were kept).")

    # 3. Timestamp -> datetime (invalid values become NaT instead of crashing).
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    bad_ts = int(df["Timestamp"].isna().sum())
    log.append(
        f"Converted Timestamp to datetime; {bad_ts} value(s) could not be parsed (kept, excluded from time charts)."
        if bad_ts else "Converted Timestamp to datetime; all values parsed successfully."
    )

    # 4. Numeric columns.
    df["Temperature (C)"] = pd.to_numeric(df["Temperature (C)"], errors="coerce")
    df["Emotion Confidence"] = pd.to_numeric(df["Emotion Confidence"], errors="coerce")
    log.append("Converted Temperature (C) and Emotion Confidence to numeric; missing values stay NaN (never treated as 0).")

    # 5. Validate the scale of Emotion Confidence.
    conf = df["Emotion Confidence"].dropna()
    scale = "0-1"
    if len(conf):
        if conf.max() <= 1.0 and conf.min() >= 0.0:
            log.append(f"Emotion Confidence is on a 0-1 scale (min {conf.min():.3f}, max {conf.max():.3f}); used as is.")
        elif conf.max() <= 100.0 and conf.min() >= 0.0:
            df["Emotion Confidence"] = df["Emotion Confidence"] / 100.0
            scale = "0-100 (converted to 0-1)"
            log.append("Emotion Confidence was on a 0-100 scale and was divided by 100 to get a 0-1 scale.")
        else:
            log.append("Warning: Emotion Confidence has values outside 0-1 and 0-100; values left unchanged.")
            scale = "unknown"
    df.attrs["confidence_scale"] = scale

    # 6. Normalise categorical labels.
    # Language: 'Marathi (मराठी)' -> 'Marathi' (the English name is enough for charts).
    lang = _text(df["Language"]).str.replace(r"\s*\(.*\)\s*", "", regex=True).str.strip().str.title()
    df["Language"] = lang.fillna(NOT_RECORDED)
    df["Detected Emotion"] = _text(df["Detected Emotion"]).str.lower().str.title().fillna(NOT_RECORDED)
    df["Mode"] = _text(df["Mode"]).str.title().fillna(NOT_RECORDED)
    df["City"] = _text(df["City"]).str.title().fillna(NOT_RECORDED)
    df["Weather Condition"] = _text(df["Weather Condition"]).str.lower().str.capitalize().fillna(NOT_RECORDED)
    log.append("Standardised label case/spacing and shortened Language (e.g. 'Marathi (मराठी)' -> 'Marathi'). "
               f"Empty City/Weather values are labelled '{NOT_RECORDED}' (they exist only for Weather-Based stories).")

    # 7. Yes/No flags -> booleans, then readable labels for charts.
    df["Background Music Added"] = _yes_no_to_bool(df["Background Music Added"])
    df["Video Created"] = _yes_no_to_bool(df["Video Created"])
    df["Has Audio File"] = df["Audio File Path"].notna()
    df["Has Video File"] = df["Video File Path"].notna()
    df["Music Label"] = df["Background Music Added"].map({True: "Music added", False: "No music"}).fillna("Unknown")
    df["Video Label"] = df["Video Created"].map({True: "Video created", False: "No video"}).fillna("Unknown")
    log.append("Converted Background Music Added / Video Created to True/False; file-path columns kept as text "
               "(an empty path means the media was not created, not an error).")

    # 8. Clean generated text.
    df["Title"] = df["Title"].map(_clean_markdown)
    df["Story Text"] = df["Story Text"].map(_clean_markdown)
    log.append("Removed markdown symbols (**, ###) from Title and Story Text.")

    # 9. Derived features (only where the timestamp is valid).
    ts = df["Timestamp"]
    df["Year"] = ts.dt.year
    df["Month"] = ts.dt.month
    df["Month Name"] = ts.dt.strftime("%Y-%m")
    df["Day"] = ts.dt.day
    df["Date"] = ts.dt.normalize()
    df["Hour"] = ts.dt.hour
    df["Weekday"] = ts.dt.day_name()
    df["Story Word Count"] = df["Story Text"].str.split().str.len()
    df["Story Char Count"] = df["Story Text"].str.len()
    log.append("Created Year, Month, Day, Hour, Weekday, Date, Story Word Count and Story Char Count.")

    return df, log
