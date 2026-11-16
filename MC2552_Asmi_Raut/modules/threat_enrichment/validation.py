"""
validation.py

Data-integrity validation helpers, run before and after every merge in the
pipeline. Every check logs its result via modules.api.base_client.logger and
also returns a plain dict so callers (pipeline.py / fusion.py) can include
the numbers in the final verification report.
"""

from typing import Dict, List

import pandas as pd

from modules.api.base_client import logger


def validate_dataframe(df: pd.DataFrame, name: str, join_key: str) -> Dict:
    """
    Basic integrity check on a single dataframe before it's used in a merge:
    row count, null count on the join key, duplicate join-key count, dtype.
    """
    report = {
        "name": name,
        "rows": len(df),
        "columns": len(df.columns),
        "join_key": join_key,
        "join_key_present": join_key in df.columns,
        "join_key_nulls": int(df[join_key].isna().sum()) if join_key in df.columns else None,
        "join_key_dtype": str(df[join_key].dtype) if join_key in df.columns else None,
        "duplicate_join_keys": (
            int(df[join_key].duplicated().sum()) if join_key in df.columns else None
        ),
    }

    logger.info(f"[VALIDATE] {name}: rows={report['rows']} cols={report['columns']} "
                f"join_key_nulls={report['join_key_nulls']} "
                f"duplicate_join_keys={report['duplicate_join_keys']}")

    return report


def validate_merge(
    left: pd.DataFrame,
    merged: pd.DataFrame,
    merge_name: str,
    join_type: str,
) -> Dict:
    """
    Post-merge integrity check: compares row count before/after, flags
    unexpected row multiplication, counts matched vs unmatched records
    (based on presence of null values in the columns introduced by the
    right-hand side of the merge).
    """
    rows_before = len(left)
    rows_after = len(merged)
    row_multiplication = rows_after > rows_before

    new_cols = [c for c in merged.columns if c not in left.columns]
    if new_cols:
        matched = int(merged[new_cols[0]].notna().sum())
    else:
        matched = 0

    unmatched = rows_after - matched
    match_rate = round((matched / rows_after) * 100, 2) if rows_after else 0.0

    report = {
        "merge_name": merge_name,
        "join_type": join_type,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "row_multiplication_detected": row_multiplication,
        "matched_records": matched,
        "unmatched_records": unmatched,
        "match_rate_pct": match_rate,
    }

    level = "warning" if row_multiplication else "info"
    getattr(logger, level)(
        f"[MERGE:{merge_name}] {join_type} join | rows_before={rows_before} "
        f"rows_after={rows_after} matched={matched} unmatched={unmatched} "
        f"match_rate={match_rate}% row_multiplication={row_multiplication}"
    )

    if row_multiplication:
        logger.warning(
            f"[MERGE:{merge_name}] Row count increased after merge — "
            f"the right-hand table likely has duplicate join keys. Investigate before trusting this output."
        )

    return report


def print_report(reports: List[Dict], title: str) -> None:
    """Pretty-print a list of validation report dicts to the console/log."""
    logger.info(f"===== {title} =====")
    for r in reports:
        logger.info(str(r))
