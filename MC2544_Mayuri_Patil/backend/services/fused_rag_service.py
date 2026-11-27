"""Build and query the local vector knowledge base for the Phase 1 fused dataset."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FUSED_DATASET_PATH = (
    PROJECT_ROOT
    / "analysis"
    / "phase1_output"
    / "data"
    / "phase1_fused_heart_failure_loinc.csv"
)
ORIGINAL_DATASET_PATH = (
    PROJECT_ROOT
    / "dataset"
    / "heart_failure_source"
    / "heart_failure_clinical_records_dataset.csv"
)
KNOWLEDGE_BASE_PATH = (
    PROJECT_ROOT / "analysis" / "phase2_output" / "rag" / "fused_knowledge_base.joblib"
)


class KnowledgeBaseError(RuntimeError):
    """Raised when the local Phase 2 knowledge base is unavailable or invalid."""


def build_knowledge_base() -> int:
    """Create a persisted TF-IDF vector store from original and fused records."""
    if not FUSED_DATASET_PATH.exists() or not ORIGINAL_DATASET_PATH.exists():
        raise KnowledgeBaseError(
            "Phase 1 datasets are unavailable. Run analysis/phase1_fusion_eda.py first."
        )

    original_data = pd.read_csv(ORIGINAL_DATASET_PATH)
    fused_data = pd.read_csv(FUSED_DATASET_PATH)
    documents = _build_documents(original_data, fused_data)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    vectors = vectorizer.fit_transform([document["text"] for document in documents])

    KNOWLEDGE_BASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "documents": documents,
            "vectorizer": vectorizer,
            "vectors": vectors,
        },
        KNOWLEDGE_BASE_PATH,
    )
    return len(documents)


def retrieve(question: str, limit: int = 3) -> list[dict[str, object]]:
    """Return the highest-scoring source records for a Phase 2 question."""
    if not question.strip():
        raise ValueError("The question must not be blank.")
    if limit < 1 or limit > 10:
        raise ValueError("The retrieval limit must be between 1 and 10.")
    if not KNOWLEDGE_BASE_PATH.exists():
        raise KnowledgeBaseError(
            "The Phase 2 knowledge base has not been built. Run analysis/phase2_rag_eda.py."
        )

    knowledge_base = joblib.load(KNOWLEDGE_BASE_PATH)
    documents = knowledge_base.get("documents")
    vectorizer = knowledge_base.get("vectorizer")
    vectors = knowledge_base.get("vectors")
    if not isinstance(documents, list) or vectorizer is None or vectors is None:
        raise KnowledgeBaseError("The Phase 2 knowledge base is invalid. Rebuild it.")

    query_vector = vectorizer.transform([question])
    scores = (vectors @ query_vector.T).toarray().ravel()
    document_indexes = np.argsort(scores)[::-1][:limit]
    return [
        {
            "source": str(documents[index]["source"]),
            "record_id": str(documents[index]["record_id"]),
            "text": str(documents[index]["text"]),
            "score": round(float(scores[index]), 4),
        }
        for index in document_indexes
    ]


def _build_documents(
    original_data: pd.DataFrame, fused_data: pd.DataFrame
) -> list[dict[str, str]]:
    death_count = int(original_data["DEATH_EVENT"].sum())
    survivor_count = len(original_data) - death_count
    documents: list[dict[str, str]] = [
        {
            "source": "original_dataset_summary",
            "record_id": "original-summary",
            "text": (
                f"Original UCI Heart Failure Clinical Records dataset: {len(original_data)} "
                f"patient records and {len(original_data.columns)} attributes. The target "
                f"DEATH_EVENT has {death_count} death events and {survivor_count} survivors."
            ),
        },
        {
            "source": "fusion_summary",
            "record_id": "fusion-summary",
            "text": (
                f"The Phase 1 fused dataset has {len(fused_data)} patient-laboratory records "
                f"and {len(fused_data.columns)} attributes. It uses a left join on "
                "measurement_name. Every fused record has LOINC metadata."
            ),
        },
    ]

    metadata = (
        fused_data.groupby("measurement_name", as_index=False)
        .first()[
            [
                "measurement_name",
                "loinc_code",
                "loinc_display_name",
                "unit",
                "api_provider",
                "api_result_count",
            ]
        ]
    )
    for row in metadata.itertuples(index=False):
        display_measurement_name = str(row.measurement_name).replace("_", " ")
        documents.append(
            {
                "source": "api_loinc_metadata",
                "record_id": str(row.measurement_name),
                "text": (
                    f"API metadata for {display_measurement_name} "
                    f"(internal name {row.measurement_name}): LOINC code {row.loinc_code}; "
                    f"LOINC display name {row.loinc_display_name}; unit {row.unit}; provider "
                    f"{row.api_provider}; API result count {row.api_result_count}."
                ),
            }
        )

    for row in fused_data.itertuples(index=False):
        outcome = "death event" if row.DEATH_EVENT == 1 else "survived"
        documents.append(
            {
                "source": "fused_patient_lab_record",
                "record_id": f"{row.source_record_id}-{row.measurement_name}",
                "text": (
                    f"Patient record {row.source_record_id}: age {row.age}; ejection fraction "
                    f"{row.ejection_fraction}; {row.measurement_name} value "
                    f"{row.clinical_value} {row.unit}; outcome {outcome}; LOINC code "
                    f"{row.loinc_code}; LOINC display name {row.loinc_display_name}."
                ),
            }
        )
    return documents
