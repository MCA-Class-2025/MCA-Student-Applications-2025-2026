"""
rag/document_builder.py — Build structured RAG documents from fused drug data.

Each document retains full source metadata for citation.
"""

from datetime import datetime
from typing import Any, Dict, List

from utils.logging import logger


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def build_drug_overview_doc(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """Build a general drug overview document."""
    identity = dataset.get("identity", {})
    drug_name = dataset.get("drug_name", "")

    content_parts = [
        f"Drug Overview: {drug_name}",
        f"Normalized Name: {identity.get('normalized_drug_name', drug_name)}",
        f"RxCUI: {identity.get('rxcui', 'N/A')}",
        f"Active Ingredient(s): {', '.join(identity.get('all_ingredients', [])) or 'N/A'}",
        f"Drug Class: {identity.get('drug_class', 'N/A')}",
        f"Brand Names: {', '.join(identity.get('brand_names', [])[:5]) or 'N/A'}",
    ]

    return {
        "doc_id": f"{drug_name.lower()}_overview",
        "title": f"Drug Overview — {drug_name}",
        "content": "\n".join(content_parts),
        "metadata": {
            "drug_name": drug_name,
            "source": "RxNorm",
            "source_type": "drug_identity",
            "record_id": identity.get("rxcui", ""),
            "date": _now(),
            "url": "https://rxnav.nlm.nih.gov",
        },
    }


def build_safety_doc(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """Build a safety document from labels and DailyMed data."""
    drug_name = dataset.get("drug_name", "")
    dfs = dataset.get("dataframes", {})

    # Get DailyMed data
    dailymed_df = dfs.get("dailymed")
    labels_df = dfs.get("labels")

    content_parts = [f"Drug Safety Information: {drug_name}"]

    # DailyMed official labeling
    dm_row = {}
    if dailymed_df is not None and not dailymed_df.empty:
        dm_row = dailymed_df.iloc[0].to_dict()

    # openFDA labels
    fda_warnings = ""
    fda_contraindications = ""
    fda_boxed = ""
    if labels_df is not None and not labels_df.empty:
        first_label = labels_df.iloc[0].to_dict()
        fda_warnings = str(first_label.get("warnings", ""))[:1000]
        fda_contraindications = str(first_label.get("contraindications", ""))[:500]
        fda_boxed = str(first_label.get("boxed_warning", ""))[:500]

    if fda_boxed:
        content_parts.append(f"BOXED WARNING (openFDA): {fda_boxed}")
    if fda_warnings:
        content_parts.append(f"Warnings (openFDA): {fda_warnings}")
    if dm_row.get("warnings"):
        content_parts.append(f"Warnings (DailyMed): {str(dm_row.get('warnings', ''))[:1000]}")
    if fda_contraindications:
        content_parts.append(f"Contraindications (openFDA): {fda_contraindications}")
    if dm_row.get("contraindications"):
        content_parts.append(f"Contraindications (DailyMed): {str(dm_row.get('contraindications', ''))[:500]}")
    if dm_row.get("precautions"):
        content_parts.append(f"Precautions (DailyMed): {str(dm_row.get('precautions', ''))[:500]}")
    if dm_row.get("storage"):
        content_parts.append(f"Storage (DailyMed): {dm_row.get('storage', '')}")
    if dm_row.get("interactions"):
        content_parts.append(f"Drug Interactions (DailyMed): {str(dm_row.get('interactions', ''))[:500]}")

    return {
        "doc_id": f"{drug_name.lower()}_safety",
        "title": f"Safety Information — {drug_name}",
        "content": "\n".join(content_parts) if len(content_parts) > 1 else f"No safety information available for {drug_name}",
        "metadata": {
            "drug_name": drug_name,
            "source": "DailyMed + openFDA",
            "source_type": "safety_label",
            "record_id": "",
            "date": _now(),
            "url": "https://dailymed.nlm.nih.gov",
        },
    }


def build_adverse_events_doc(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """Build an adverse events summary document."""
    drug_name = dataset.get("drug_name", "")
    top_ae = dataset.get("top_adverse_reactions", [])
    summary = dataset.get("summary", {})

    content_parts = [
        f"Adverse Event Reports: {drug_name}",
        f"Total adverse event reports in FDA FAERS database: {summary.get('total_adverse_events', 0):,}",
        f"Records retrieved for analysis: {summary.get('ae_records_retrieved', 0)}",
    ]

    if top_ae:
        content_parts.append(
            "Top reported adverse reactions (by MedDRA preferred term): "
            + "; ".join(f"{r['term']} ({r['count']:,} reports)" for r in top_ae[:15])
        )

    return {
        "doc_id": f"{drug_name.lower()}_adverse_events",
        "title": f"Adverse Event Reports — {drug_name}",
        "content": "\n".join(content_parts),
        "metadata": {
            "drug_name": drug_name,
            "source": "openFDA",
            "source_type": "adverse_events",
            "record_id": "",
            "date": _now(),
            "url": "https://api.fda.gov/drug/event.json",
        },
    }


def build_recall_doc(dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build recall documents — one per recall record."""
    drug_name = dataset.get("drug_name", "")
    dfs = dataset.get("dataframes", {})
    recalls_df = dfs.get("recalls")

    if recalls_df is None or recalls_df.empty:
        return [{
            "doc_id": f"{drug_name.lower()}_recalls",
            "title": f"Recall History — {drug_name}",
            "content": f"No drug recalls found for {drug_name} in openFDA enforcement database.",
            "metadata": {
                "drug_name": drug_name,
                "source": "openFDA",
                "source_type": "recall",
                "record_id": "",
                "date": _now(),
                "url": "https://api.fda.gov/drug/enforcement.json",
            },
        }]

    docs = []
    for _, row in recalls_df.iterrows():
        content = (
            f"Drug Recall Record: {drug_name}\n"
            f"Recall Number: {row.get('recall_number', 'N/A')}\n"
            f"Classification: {row.get('classification', 'N/A')}\n"
            f"Status: {row.get('status', 'N/A')}\n"
            f"Recalling Firm: {row.get('recalling_firm', 'N/A')}\n"
            f"Reason: {row.get('reason_for_recall', 'N/A')}\n"
            f"Product: {row.get('product_description', 'N/A')}\n"
            f"Initiation Date: {row.get('recall_initiation_date', 'N/A')}\n"
            f"Voluntary/Mandated: {row.get('voluntary_mandated', 'N/A')}"
        )
        docs.append({
            "doc_id": f"{drug_name.lower()}_recall_{row.get('recall_number', 'unknown')}",
            "title": f"Recall Record — {drug_name} — {row.get('recall_number', '')}",
            "content": content,
            "metadata": {
                "drug_name": drug_name,
                "source": "openFDA",
                "source_type": "recall",
                "record_id": str(row.get("recall_number", "")),
                "date": str(row.get("report_date", _now())),
                "url": "https://api.fda.gov/drug/enforcement.json",
            },
        })
    return docs


def build_research_docs(dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build one document per PubMed article."""
    drug_name = dataset.get("drug_name", "")
    dfs = dataset.get("dataframes", {})
    articles_df = dfs.get("articles")

    if articles_df is None or articles_df.empty:
        return [{
            "doc_id": f"{drug_name.lower()}_research",
            "title": f"Research Literature — {drug_name}",
            "content": f"No PubMed research articles retrieved for {drug_name}.",
            "metadata": {
                "drug_name": drug_name,
                "source": "PubMed",
                "source_type": "research_article",
                "record_id": "",
                "date": _now(),
                "url": "https://pubmed.ncbi.nlm.nih.gov",
            },
        }]

    docs = []
    for _, row in articles_df.iterrows():
        authors = row.get("authors", [])
        if isinstance(authors, list):
            authors_str = ", ".join(authors[:3])
        else:
            authors_str = str(authors)

        content = (
            f"Research Article: {drug_name}\n"
            f"Title: {row.get('title', 'N/A')}\n"
            f"Authors: {authors_str}\n"
            f"Journal: {row.get('journal', 'N/A')}\n"
            f"Published: {row.get('pub_date', 'N/A')}\n"
            f"Abstract: {row.get('abstract', 'N/A')}"
        )
        docs.append({
            "doc_id": f"{drug_name.lower()}_pubmed_{row.get('pmid', '')}",
            "title": row.get("title", f"Article — {drug_name}"),
            "content": content,
            "metadata": {
                "drug_name": drug_name,
                "source": "PubMed",
                "source_type": "research_article",
                "record_id": str(row.get("pmid", "")),
                "date": str(row.get("pub_date", "")),
                "url": str(row.get("source_url", "https://pubmed.ncbi.nlm.nih.gov")),
            },
        })
    return docs


def build_trial_docs(dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build one document per clinical trial."""
    drug_name = dataset.get("drug_name", "")
    dfs = dataset.get("dataframes", {})
    trials_df = dfs.get("trials")

    if trials_df is None or trials_df.empty:
        return [{
            "doc_id": f"{drug_name.lower()}_trials",
            "title": f"Clinical Trials — {drug_name}",
            "content": f"No clinical trials retrieved for {drug_name} from ClinicalTrials.gov.",
            "metadata": {
                "drug_name": drug_name,
                "source": "ClinicalTrials.gov",
                "source_type": "clinical_trial",
                "record_id": "",
                "date": _now(),
                "url": "https://clinicaltrials.gov",
            },
        }]

    docs = []
    for _, row in trials_df.iterrows():
        conditions = row.get("conditions", [])
        if isinstance(conditions, list):
            conditions_str = ", ".join(conditions)
        else:
            conditions_str = str(conditions)

        content = (
            f"Clinical Trial: {drug_name}\n"
            f"NCT ID: {row.get('nct_id', 'N/A')}\n"
            f"Title: {row.get('title', 'N/A')}\n"
            f"Status: {row.get('status', 'N/A')}\n"
            f"Phase: {row.get('phase', 'N/A')}\n"
            f"Conditions: {conditions_str}\n"
            f"Sponsor: {row.get('lead_sponsor', 'N/A')}\n"
            f"Enrollment: {row.get('enrollment', 'N/A')}\n"
            f"Start Date: {row.get('start_date', 'N/A')}\n"
            f"Completion Date: {row.get('completion_date', 'N/A')}\n"
            f"Summary: {str(row.get('summary', 'N/A'))[:500]}"
        )
        docs.append({
            "doc_id": f"{drug_name.lower()}_trial_{row.get('nct_id', '')}",
            "title": f"Clinical Trial — {row.get('nct_id', '')} — {row.get('title', drug_name)[:60]}",
            "content": content,
            "metadata": {
                "drug_name": drug_name,
                "source": "ClinicalTrials.gov",
                "source_type": "clinical_trial",
                "record_id": str(row.get("nct_id", "")),
                "date": str(row.get("start_date", "")),
                "url": str(row.get("source_url", "https://clinicaltrials.gov")),
            },
        })
    return docs


def build_all_documents(dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build the complete RAG corpus from the fused dataset.
    Returns a list of document dicts ready for chunking + embedding.
    """
    docs = []

    docs.append(build_drug_overview_doc(dataset))
    docs.append(build_safety_doc(dataset))
    docs.append(build_adverse_events_doc(dataset))
    docs.extend(build_recall_doc(dataset))
    docs.extend(build_research_docs(dataset))
    docs.extend(build_trial_docs(dataset))

    logger.info(f"Built {len(docs)} RAG documents for '{dataset.get('drug_name', '')}'")
    return docs
