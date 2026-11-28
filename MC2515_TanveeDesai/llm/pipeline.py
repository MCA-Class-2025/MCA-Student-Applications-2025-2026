"""
pipeline.py — Master pipeline orchestrator.

Orchestrates the complete data collection → fusion → analysis → RAG pipeline.
This is the main entry point called by the Streamlit UI.
"""

import time
from typing import Any, Dict, Optional

import streamlit as st

from services import rxnorm_service, openfda_service, dailymed_service, pubmed_service, clinicaltrials_service
from preprocessing.fusion import DataFusionPipeline
from analysis.eda import run_full_eda
from analysis.features import build_full_feature_set
from analysis.clustering import cluster_adverse_reactions, detect_anomalies_in_ae, classify_reporting_activity
from analysis.statistics import compute_recall_trend, compute_research_trend
from nlp.keywords import extract_research_topics, extract_keywords_from_warnings
from rag.rag_pipeline import RAGPipeline
from llm.chatbot import DrugSafetyChatbot
from llm.client import LLMClient
from utils.logging import logger


# ── Cache keys ────────────────────────────────────────────────────────────────

def _drug_key(drug_name: str) -> str:
    return drug_name.lower().strip()


# ── Source Status Reporter ─────────────────────────────────────────────────────

def build_source_status(
    rxnorm_ok: bool,
    openfda_ok: bool,
    dailymed_ok: bool,
    pubmed_ok: bool,
    ct_ok: bool,
    rxnorm_err: str = "",
    openfda_err: str = "",
    dailymed_err: str = "",
    pubmed_err: str = "",
    ct_err: str = "",
) -> Dict[str, Dict]:
    return {
        "RxNorm": {"ok": rxnorm_ok, "error": rxnorm_err},
        "openFDA": {"ok": openfda_ok, "error": openfda_err},
        "DailyMed": {"ok": dailymed_ok, "error": dailymed_err},
        "PubMed": {"ok": pubmed_ok, "error": pubmed_err},
        "ClinicalTrials.gov": {"ok": ct_ok, "error": ct_err},
    }


# ── Main Pipeline ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def run_full_pipeline(drug_name: str) -> Dict[str, Any]:
    """
    Execute the complete Medicine Safety Intelligence pipeline.

    Steps:
    1. RxNorm normalization
    2. Query 5 APIs in parallel (sequential for reliability)
    3. Data fusion
    4. EDA
    5. Feature engineering
    6. NLP / keyword extraction
    7. RAG index build (returned separately to avoid serialization issues)

    Returns comprehensive dataset dict.
    """
    t0 = time.time()
    logger.info(f"=== Pipeline START: '{drug_name}' ===")

    result: Dict[str, Any] = {
        "drug_name": drug_name,
        "pipeline_ok": False,
        "source_status": {},
        "dataset": None,
        "eda": None,
        "features": None,
        "analytics": None,
        "errors": [],
        "elapsed_seconds": 0.0,
    }

    # ── Step 1: RxNorm ─────────────────────────────────────────────────────
    logger.info("Step 1: RxNorm normalization")
    try:
        rxnorm_data = rxnorm_service.get_full_drug_info(drug_name)
        rxnorm_ok = rxnorm_data.get("retrieval_ok", False)
        rxnorm_err = rxnorm_data.get("normalized", {}).get("error", "") or ""
    except Exception as e:
        rxnorm_data = {"retrieval_ok": False, "normalized": {}, "active_ingredients": [], "brand_names": [], "drug_classes": []}
        rxnorm_ok = False
        rxnorm_err = str(e)
        result["errors"].append(f"RxNorm: {e}")

    # Get best search term for downstream APIs
    rxcui = rxnorm_data.get("normalized", {}).get("rxcui")
    canonical_name = rxnorm_data.get("normalized", {}).get("name") or drug_name
    ingredients = rxnorm_data.get("active_ingredients", [])
    ingredient_name = ingredients[0].get("name", "") if ingredients else ""
    search_term = ingredient_name or canonical_name

    # ── Step 2: openFDA ────────────────────────────────────────────────────
    logger.info("Step 2: openFDA query")
    try:
        openfda_data = openfda_service.get_full_drug_info(search_term)
        openfda_ok = openfda_data.get("retrieval_ok", False)
        openfda_err = ""
    except Exception as e:
        openfda_data = {"retrieval_ok": False, "labels": {}, "adverse_events": {}, "recalls": {}, "top_adverse_reactions": []}
        openfda_ok = False
        openfda_err = str(e)
        result["errors"].append(f"openFDA: {e}")

    # ── Step 3: DailyMed ───────────────────────────────────────────────────
    logger.info("Step 3: DailyMed query")
    try:
        dailymed_data = dailymed_service.get_full_drug_info(search_term, rxcui=rxcui)
        dailymed_ok = dailymed_data.get("retrieval_ok", False)
        dailymed_err = dailymed_data.get("error", "") or ""
    except Exception as e:
        dailymed_data = {"retrieval_ok": False}
        dailymed_ok = False
        dailymed_err = str(e)
        result["errors"].append(f"DailyMed: {e}")

    # ── Step 4: PubMed ─────────────────────────────────────────────────────
    logger.info("Step 4: PubMed query")
    try:
        pubmed_data = pubmed_service.get_full_drug_info(drug_name, ingredient_name=ingredient_name)
        pubmed_ok = pubmed_data.get("retrieval_ok", False)
        pubmed_err = pubmed_data.get("error", "") or ""
    except Exception as e:
        pubmed_data = {"retrieval_ok": False, "articles": []}
        pubmed_ok = False
        pubmed_err = str(e)
        result["errors"].append(f"PubMed: {e}")

    # ── Step 5: ClinicalTrials.gov ─────────────────────────────────────────
    logger.info("Step 5: ClinicalTrials.gov query")
    try:
        ct_data = clinicaltrials_service.get_full_drug_info(drug_name, ingredient_name=ingredient_name)
        ct_ok = ct_data.get("retrieval_ok", False)
        ct_err = ct_data.get("error", "") or ""
    except Exception as e:
        ct_data = {"retrieval_ok": False, "trials": []}
        ct_ok = False
        ct_err = str(e)
        result["errors"].append(f"ClinicalTrials: {e}")

    result["source_status"] = build_source_status(
        rxnorm_ok, openfda_ok, dailymed_ok, pubmed_ok, ct_ok,
        rxnorm_err, openfda_err, dailymed_err, pubmed_err, ct_err,
    )

    # ── Step 6: Data Fusion ────────────────────────────────────────────────
    logger.info("Step 6: Data fusion")
    try:
        fusion = DataFusionPipeline(drug_name)
        dataset = fusion.run(rxnorm_data, openfda_data, dailymed_data, pubmed_data, ct_data)
        result["dataset"] = dataset
    except Exception as e:
        result["errors"].append(f"Fusion: {e}")
        logger.error(f"Data fusion failed: {e}")
        result["elapsed_seconds"] = round(time.time() - t0, 2)
        return result

    # ── Step 6b: LLM Intelligence Layer (on top of the fused data) ──────
    logger.info("Step 6b: LLM intelligence layer (understand + fuse to CSV)")
    try:
        from llm.intelligence import DrugIntelligenceExtractor
        extractor = DrugIntelligenceExtractor()
        result["llm_intelligence"] = extractor.run(
            drug_name,
            rxnorm_data,
            openfda_data,
            dailymed_data,
            pubmed_data,
            ct_data,
            dataset=dataset,
        )
    except Exception as e:
        result["errors"].append(f"LLM Intelligence: {e}")
        logger.warning(f"LLM intelligence layer failed: {e}")

    # ── Step 7: EDA ────────────────────────────────────────────────────────
    logger.info("Step 7: EDA")
    try:
        eda_result = run_full_eda(dataset)
        result["eda"] = eda_result
    except Exception as e:
        result["errors"].append(f"EDA: {e}")
        logger.warning(f"EDA failed: {e}")

    # ── Step 8: Feature Engineering ────────────────────────────────────────
    logger.info("Step 8: Feature engineering")
    try:
        features = build_full_feature_set(dataset)
        result["features"] = features
    except Exception as e:
        result["errors"].append(f"Features: {e}")
        logger.warning(f"Feature engineering failed: {e}")

    # ── Step 9: Analytics ─────────────────────────────────────────────────
    logger.info("Step 9: Analytics")
    analytics: Dict[str, Any] = {}
    try:
        dfs = dataset.get("dataframes", {})
        top_ae = dataset.get("top_adverse_reactions", [])

        # Classification
        ae_total = dataset.get("summary", {}).get("total_adverse_events", 0)
        analytics["reporting_classification"] = classify_reporting_activity(ae_total)

        # Clustering
        analytics["ae_clustering"] = cluster_adverse_reactions(top_ae)

        # Anomaly detection
        analytics["ae_anomalies"] = detect_anomalies_in_ae(top_ae)

        # Recall trend
        analytics["recall_trend"] = compute_recall_trend(dfs.get("recalls"))

        # Research trend
        analytics["research_trend"] = compute_research_trend(dfs.get("articles"))

        # Keywords
        articles = pubmed_data.get("articles", [])
        analytics["research_keywords"] = extract_research_topics(articles)

        # Warning keywords
        warnings_text = dailymed_data.get("warnings", "")
        if not warnings_text and not dfs.get("labels", None) is None:
            labels_df = dfs.get("labels")
            if labels_df is not None and not labels_df.empty:
                warnings_text = str(labels_df.iloc[0].get("warnings", ""))
        analytics["warning_keywords"] = extract_keywords_from_warnings(warnings_text)

        result["analytics"] = analytics
    except Exception as e:
        result["errors"].append(f"Analytics: {e}")
        logger.warning(f"Analytics failed: {e}")

    result["pipeline_ok"] = True
    result["elapsed_seconds"] = round(time.time() - t0, 2)
    logger.info(f"=== Pipeline COMPLETE: '{drug_name}' in {result['elapsed_seconds']}s ===")

    return result


@st.cache_resource(show_spinner=False)
def build_rag_pipeline(drug_name: str, _dataset: Any) -> RAGPipeline:
    """
    Build RAG pipeline (cached as resource to avoid re-embedding).
    Uses _dataset with leading underscore so Streamlit doesn't hash it.
    """
    rag = RAGPipeline()
    try:
        stats = rag.build(_dataset)
        logger.info(f"RAG pipeline built for '{drug_name}': {stats}")
    except Exception as e:
        logger.error(f"RAG pipeline build failed: {e}")
    return rag


@st.cache_resource(show_spinner=False)
def get_chatbot() -> DrugSafetyChatbot:
    """Return a singleton chatbot instance."""
    client = LLMClient()
    return DrugSafetyChatbot(llm_client=client)
