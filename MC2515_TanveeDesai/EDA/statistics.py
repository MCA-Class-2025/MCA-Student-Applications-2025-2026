"""
analysis/statistics.py — Statistical analysis for drug data.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

from utils.logging import logger


def compute_recall_trend(recalls_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute year-over-year recall trend using linear regression on counts.
    """
    if recalls_df is None or recalls_df.empty:
        return {"available": False}

    date_col = None
    for col in ["recall_initiation_date", "report_date"]:
        if col in recalls_df.columns:
            date_col = col
            break

    if not date_col:
        return {"available": False}

    dates = pd.to_datetime(recalls_df[date_col], errors="coerce")
    years = dates.dt.year.dropna().astype(int)

    if len(years) < 3:
        return {"available": False, "reason": "Insufficient data points"}

    year_counts = years.value_counts().sort_index()
    x = np.array(year_counts.index, dtype=float)
    y = np.array(year_counts.values, dtype=float)

    if len(x) >= 2:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        trend = "increasing" if slope > 0 else "decreasing"
        significant = p_value < 0.05

        return {
            "available": True,
            "year_counts": year_counts.to_dict(),
            "slope": round(slope, 4),
            "r_squared": round(r_value ** 2, 4),
            "p_value": round(p_value, 4),
            "trend": trend,
            "statistically_significant": significant,
        }
    return {"available": False}


def compute_research_trend(articles_df: pd.DataFrame) -> Dict[str, Any]:
    """Compute publication trend over time."""
    if articles_df is None or articles_df.empty or "pub_year" not in articles_df.columns:
        return {"available": False}

    years = articles_df["pub_year"].dropna().astype(int)
    if len(years) < 3:
        return {"available": False}

    year_counts = years.value_counts().sort_index()
    x = np.array(year_counts.index, dtype=float)
    y = np.array(year_counts.values, dtype=float)

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    return {
        "available": True,
        "year_counts": year_counts.to_dict(),
        "slope": round(slope, 4),
        "r_squared": round(r_value ** 2, 4),
        "p_value": round(p_value, 4),
        "trend": "increasing" if slope > 0 else "decreasing",
        "statistically_significant": p_value < 0.05,
    }


def describe_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate descriptive statistics for a dataframe.
    """
    if df is None or df.empty:
        return {}

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    stats_dict: Dict[str, Any] = {
        "shape": list(df.shape),
        "columns": df.columns.tolist(),
        "null_counts": df.isnull().sum().to_dict(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }

    if numeric_cols:
        desc = df[numeric_cols].describe()
        stats_dict["numeric_summary"] = desc.to_dict()

    return stats_dict
