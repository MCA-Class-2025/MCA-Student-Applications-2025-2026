"""
preprocessing/fusion.py — Data fusion pipeline.

Merges data from five sources into a unified Drug Intelligence Dataset.
Maintains data lineage via source metadata on every record.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from config.settings import FUSED_DIR, PROCESSED_DIR
from preprocessing.cleaning import (
    clean_adverse_events_df,
    clean_recalls_df,
    clean_articles_df,
    clean_trials_df,
    clean_labels_df,
    clean_text,
)
from preprocessing.normalization import (
    build_drug_identity,
    normalize_drug_name,
    normalize_status,
    normalize_recall_classification,
    normalize_phase,
    extract_year,
)
from utils.logging import logger


# ── Timestamp ─────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Source Lineage Helper ─────────────────────────────────────────────────────

def _lineage(source: str, source_type: str, record_id: str = "", url: str = "") -> Dict:
    return {
        "source": source,
        "source_type": source_type,
        "source_id": record_id,
        "source_url": url,
        "retrieved_at": _now_iso(),
    }


# ── Individual Source Transformers ────────────────────────────────────────────

def transform_rxnorm(rxnorm_data: Dict) -> pd.DataFrame:
    """Convert RxNorm data into a single-row identity DataFrame."""
    identity = build_drug_identity(rxnorm_data)
    row = {
        **identity,
        **_lineage("RxNorm", "drug_identity", identity.get("rxcui", ""), "https://rxnav.nlm.nih.gov"),
    }
    return pd.DataFrame([row])


def transform_openfda_labels(labels_data: Dict, drug_name: str) -> pd.DataFrame:
    """Transform openFDA label records."""
    records = labels_data.get("records", [])
    if not records:
        return pd.DataFrame()

    df = clean_labels_df(records)
    if df.empty:
        return pd.DataFrame()

    df["drug_name"] = drug_name
    df["source"] = "openFDA"
    df["source_type"] = "drug_label"
    df["source_url"] = labels_data.get("source_url", "")
    df["retrieved_at"] = _now_iso()
    return df


def transform_openfda_adverse_events(ae_data: Dict, drug_name: str) -> pd.DataFrame:
    """Transform openFDA adverse event records."""
    records = ae_data.get("records", [])
    if not records:
        return pd.DataFrame()

    df = clean_adverse_events_df(records)
    if df.empty:
        return pd.DataFrame()

    df["drug_name"] = drug_name
    df["source"] = "openFDA"
    df["source_type"] = "adverse_event"
    df["source_url"] = ae_data.get("source_url", "")
    df["retrieved_at"] = _now_iso()
    return df


def transform_openfda_recalls(recalls_data: Dict, drug_name: str) -> pd.DataFrame:
    """Transform openFDA recall records."""
    records = recalls_data.get("records", [])
    if not records:
        return pd.DataFrame()

    df = clean_recalls_df(records)
    if df.empty:
        return pd.DataFrame()

    df["classification_readable"] = df["classification"].apply(normalize_recall_classification)
    df["drug_name"] = drug_name
    df["source"] = "openFDA"
    df["source_type"] = "recall"
    df["source_url"] = recalls_data.get("source_url", "")
    df["retrieved_at"] = _now_iso()
    return df


def transform_dailymed(dailymed_data: Dict, drug_name: str) -> pd.DataFrame:
    """Transform DailyMed labeling data."""
    if not dailymed_data.get("retrieval_ok"):
        return pd.DataFrame()

    row: Dict[str, Any] = {
        "drug_name": drug_name,
        "labeler": dailymed_data.get("labeler", ""),
        "published_date": dailymed_data.get("published_date", ""),
        "warnings": clean_text(dailymed_data.get("warnings", "")),
        "contraindications": clean_text(dailymed_data.get("contraindications", "")),
        "precautions": clean_text(dailymed_data.get("precautions", "")),
        "adverse_reactions": clean_text(dailymed_data.get("adverse_reactions", "")),
        "storage": clean_text(dailymed_data.get("storage", "")),
        "indications": clean_text(dailymed_data.get("indications", "")),
        "dosage": clean_text(dailymed_data.get("dosage", "")),
        "interactions": clean_text(dailymed_data.get("interactions", "")),
        "spl_count": len(dailymed_data.get("spls", [])),
        "source": "DailyMed",
        "source_type": "official_label",
        "source_url": dailymed_data.get("source_url", "https://dailymed.nlm.nih.gov"),
        "retrieved_at": _now_iso(),
    }
    return pd.DataFrame([row])


def transform_pubmed(pubmed_data: Dict, drug_name: str) -> pd.DataFrame:
    """Transform PubMed article records."""
    articles = pubmed_data.get("articles", [])
    if not articles:
        return pd.DataFrame()

    df = clean_articles_df(articles)
    if df.empty:
        return pd.DataFrame()

    df["drug_name"] = drug_name
    df["pub_year"] = df.get("pub_year", pd.Series(dtype="object"))
    df["source"] = "PubMed"
    df["source_type"] = "research_article"
    df["retrieved_at"] = _now_iso()
    return df


def transform_clinical_trials(ct_data: Dict, drug_name: str) -> pd.DataFrame:
    """Transform ClinicalTrials records."""
    trials = ct_data.get("trials", [])
    if not trials:
        return pd.DataFrame()

    df = clean_trials_df(trials)
    if df.empty:
        return pd.DataFrame()

    df["drug_name"] = drug_name
    df["status_normalized"] = df["status"].apply(normalize_status) if "status" in df.columns else "Unknown"
    df["phase_normalized"] = df["phase"].apply(normalize_phase) if "phase" in df.columns else "N/A"
    df["start_year"] = df["start_date"].apply(extract_year) if "start_date" in df.columns else None
    df["source"] = "ClinicalTrials.gov"
    df["source_type"] = "clinical_trial"
    df["retrieved_at"] = _now_iso()
    return df


# ── Master Fuser ──────────────────────────────────────────────────────────────

class DataFusionPipeline:
    """
    Orchestrates the full data fusion from raw API payloads into a
    Unified Drug Intelligence Dataset.

    Usage:
        pipeline = DataFusionPipeline(drug_name)
        dataset = pipeline.run(rxnorm_data, openfda_data, dailymed_data, pubmed_data, ct_data)
    """

    def __init__(self, drug_name: str):
        self.drug_name = drug_name
        self.record_counts: Dict[str, Dict[str, int]] = {}

    def run(
        self,
        rxnorm_data: Dict,
        openfda_data: Dict,
        dailymed_data: Dict,
        pubmed_data: Dict,
        ct_data: Dict,
    ) -> Dict[str, Any]:
        """
        Execute the fusion pipeline.
        Returns a comprehensive dataset dict.
        """
        logger.info(f"DataFusionPipeline: starting for '{self.drug_name}'")

        # ── Transform each source ──────────────────────────────────────────
        identity_df = transform_rxnorm(rxnorm_data)
        labels_df = transform_openfda_labels(openfda_data.get("labels", {}), self.drug_name)
        ae_df = transform_openfda_adverse_events(openfda_data.get("adverse_events", {}), self.drug_name)
        recalls_df = transform_openfda_recalls(openfda_data.get("recalls", {}), self.drug_name)
        dailymed_df = transform_dailymed(dailymed_data, self.drug_name)
        articles_df = transform_pubmed(pubmed_data, self.drug_name)
        trials_df = transform_clinical_trials(ct_data, self.drug_name)

        # ── Record counts (raw) ────────────────────────────────────────────
        self.record_counts = {
            "RxNorm": {"raw": len(identity_df), "after_cleaning": len(identity_df)},
            "openFDA_labels": {"raw": len(labels_df), "after_cleaning": len(labels_df)},
            "openFDA_adverse_events": {"raw": len(ae_df), "after_cleaning": len(ae_df)},
            "openFDA_recalls": {"raw": len(recalls_df), "after_cleaning": len(recalls_df)},
            "DailyMed": {"raw": len(dailymed_df), "after_cleaning": len(dailymed_df)},
            "PubMed": {"raw": len(articles_df), "after_cleaning": len(articles_df)},
            "ClinicalTrials": {"raw": len(trials_df), "after_cleaning": len(trials_df)},
        }

        # ── Build drug identity anchor ────────────────────────────────────
        drug_identity: Dict[str, Any] = {}
        if not identity_df.empty:
            drug_identity = identity_df.iloc[0].to_dict()

        # Enrich identity from DailyMed if RxNorm is sparse
        if not drug_identity.get("drug_class") and not dailymed_df.empty:
            drug_identity["labeler"] = dailymed_df.iloc[0].get("labeler", "")

        # ── Summary stats ─────────────────────────────────────────────────
        total_ae = int(openfda_data.get("adverse_events", {}).get("total", len(ae_df)))
        total_recalls = int(openfda_data.get("recalls", {}).get("total", len(recalls_df)))
        top_ae = openfda_data.get("top_adverse_reactions", [])

        dataset = {
            "drug_name": self.drug_name,
            "identity": drug_identity,
            "sources": {
                "rxnorm": {
                    "data": rxnorm_data,
                    "retrieval_ok": rxnorm_data.get("retrieval_ok", False),
                },
                "openfda": {
                    "data": openfda_data,
                    "retrieval_ok": openfda_data.get("retrieval_ok", False),
                },
                "dailymed": {
                    "data": dailymed_data,
                    "retrieval_ok": dailymed_data.get("retrieval_ok", False),
                },
                "pubmed": {
                    "data": pubmed_data,
                    "retrieval_ok": pubmed_data.get("retrieval_ok", False),
                },
                "clinicaltrials": {
                    "data": ct_data,
                    "retrieval_ok": ct_data.get("retrieval_ok", False),
                },
            },
            "dataframes": {
                "identity": identity_df,
                "labels": labels_df,
                "adverse_events": ae_df,
                "recalls": recalls_df,
                "dailymed": dailymed_df,
                "articles": articles_df,
                "trials": trials_df,
            },
            "summary": {
                "total_adverse_events": total_ae,
                "ae_records_retrieved": len(ae_df),
                "total_recalls": total_recalls,
                "recall_records": len(recalls_df),
                "research_articles": len(articles_df),
                "clinical_trials": len(trials_df),
                "active_trials": sum(
                    1 for t in ct_data.get("trials", [])
                    if t.get("status", "") in (
                        "RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION"
                    )
                ),
                "has_recalls": len(recalls_df) > 0,
                "has_boxed_warning": any(
                    bool(r.get("boxed_warning", "")) for r in openfda_data.get("labels", {}).get("records", [])
                ),
            },
            "top_adverse_reactions": top_ae,
            "record_counts": self.record_counts,
            "retrieval_timestamp": _now_iso(),
        }

        # ── Persist to disk ────────────────────────────────────────────────
        self._persist(dataset)

        logger.info(
            f"DataFusionPipeline complete for '{self.drug_name}': "
            f"AE={total_ae}, recalls={total_recalls}, "
            f"articles={len(articles_df)}, trials={len(trials_df)}"
        )
        return dataset

    def _persist(self, dataset: Dict) -> None:
        """Save DataFrames to Parquet and summary to JSON."""
        safe_name = normalize_drug_name(self.drug_name).replace(" ", "_")

        for name, df in dataset["dataframes"].items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                path = FUSED_DIR / f"{safe_name}_{name}.parquet"
                try:
                    df.to_parquet(path, index=False)
                except Exception as e:
                    logger.warning(f"Could not save {name} parquet: {e}")

        # Save summary as JSON
        summary_path = FUSED_DIR / f"{safe_name}_summary.json"
        try:
            summary = {
                "drug_name": dataset["drug_name"],
                "identity": {
                    k: v for k, v in dataset["identity"].items()
                    if isinstance(v, (str, int, float, bool, list, type(None)))
                },
                "summary": dataset["summary"],
                "record_counts": dataset["record_counts"],
                "retrieval_timestamp": dataset["retrieval_timestamp"],
            }
            with open(summary_path, "w") as f:
                json.dump(summary, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save summary JSON: {e}")
