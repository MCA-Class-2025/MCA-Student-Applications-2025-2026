"""Exact answers to supported aggregate questions about the fused dataset."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import pandas as pd


DATASET = (
    Path(__file__).resolve().parents[2]
    / "Fusion" / "data" / "api_fusion" / "final" / "femcare_final_cleaned.csv"
)
SOURCE_LABEL = "Fusion/data/api_fusion/final/femcare_final_cleaned.csv"


@lru_cache(maxsize=2)
def _pcos_counts(modified_ns: int) -> tuple[int, int] | None:
    rows = pd.read_csv(DATASET, usecols=["user_id", "pcos_diagnosed"])
    labels = rows.groupby("user_id")["pcos_diagnosed"]
    if (labels.nunique(dropna=False) != 1).any():
        return None
    users = labels.first()
    numeric = pd.to_numeric(users, errors="coerce")
    if numeric.isna().any() or not numeric.isin([0, 1]).all():
        return None
    return int(numeric.sum()), int(len(numeric))


def answer_dataset_question(question: str) -> tuple[str, dict] | None:
    q = question.lower()
    if not re.search(r"\bpcos\b", q):
        return None
    if not re.search(r"\b(?:femcare|dataset|data|users?|participants?)\b", q):
        return None
    if not re.search(
        r"\b(?:what percentage|what percent|how many|proportion|fraction|"
        r"percent|percentage|prevalence|count|number|rate)\b", q
    ):
        return None
    if not DATASET.exists():
        return None
    counts = _pcos_counts(DATASET.stat().st_mtime_ns)
    if counts is None:
        return (
            "I found inconsistent or missing PCOS labels across user records, "
            "so I can't calculate a reliable user-level percentage yet.",
            {"source": SOURCE_LABEL, "text": "PCOS labels failed consistency checks."},
        )
    diagnosed, total = counts
    percentage = 100 * diagnosed / total if total else 0
    answer = (
        f"In the FemCare fused dataset, **{diagnosed:,} of {total:,} distinct users "
        f"({percentage:.1f}%)** are marked `pcos_diagnosed = 1`. "
        "I counted each user once, even if they have several cycle records. "
        "This describes this dataset, not the rate of PCOS in the general population "
        "and not a new diagnosis."
    )
    return answer, {
        "source": SOURCE_LABEL,
        "text": f"Distinct users: {total}; users marked PCOS: {diagnosed}; {percentage:.1f}%.",
    }
