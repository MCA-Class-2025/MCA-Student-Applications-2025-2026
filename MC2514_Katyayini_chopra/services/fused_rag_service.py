"""
FixAI Phase 2 - Embedding + FAISS RAG service.

Builds embeddings for the 20-row fused dataset, stores them in a local FAISS
vector index, and retrieves semantically relevant records for FixAI prompts.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import faiss
import numpy as np
import pandas as pd
from google import genai
from google.genai import types


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "fixai_fused_dataset.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"
INDEX_PATH = OUTPUT_DIR / "fixai_fused_faiss.index"
META_PATH = OUTPUT_DIR / "fixai_fused_rag_metadata.json"
CONFIG_PATH = OUTPUT_DIR / "fixai_fused_rag_config.json"

EMBEDDING_MODEL = os.getenv("FIXAI_EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = int(os.getenv("FIXAI_EMBEDDING_DIM", "768"))


def _client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "n/a", "na"} else text


def row_to_document(row: Dict[str, Any], row_number: int) -> str:
    """Convert one fused CSV row into a readable RAG document."""
    lines = [
        f"FixAI fused knowledge record {row_number}.",
        f"Original defect knowledge: work type={_clean(row.get('work_type'))}; "
        f"location={_clean(row.get('location'))}; element={_clean(row.get('element'))}; "
        f"defect={_clean(row.get('defect'))}; description={_clean(row.get('example_description'))}.",
        f"Derived service type={_clean(row.get('service_type'))}.",
        f"Geographic context: city={_clean(row.get('api_context_city'))}; "
        f"latitude={_clean(row.get('api_context_latitude'))}; "
        f"longitude={_clean(row.get('api_context_longitude'))}.",
        f"Weather: temperature={_clean(row.get('weather_temperature'))}; "
        f"humidity={_clean(row.get('weather_humidity'))}; "
        f"precipitation={_clean(row.get('weather_precipitation'))}; "
        f"daily rainfall={_clean(row.get('weather_daily_rainfall'))}; "
        f"daily max temperature={_clean(row.get('weather_daily_max_temperature'))}; "
        f"daily min temperature={_clean(row.get('weather_daily_min_temperature'))}.",
        f"Air quality: PM2.5={_clean(row.get('air_pm2_5'))}; PM10={_clean(row.get('air_pm10'))}; "
        f"US AQI={_clean(row.get('air_us_aqi'))}; ozone={_clean(row.get('air_ozone'))}; "
        f"nitrogen dioxide={_clean(row.get('air_nitrogen_dioxide'))}; "
        f"carbon monoxide={_clean(row.get('air_carbon_monoxide'))}.",
        f"Professional: id={_clean(row.get('professional_id'))}; "
        f"name={_clean(row.get('professional_name'))}; "
        f"service type={_clean(row.get('professional_service_type'))}; "
        f"city={_clean(row.get('professional_city'))}; area={_clean(row.get('professional_area'))}; "
        f"phone={_clean(row.get('professional_phone'))}; rating={_clean(row.get('professional_rating'))}; "
        f"experience={_clean(row.get('professional_experience'))} years; "
        f"price range={_clean(row.get('professional_price_range'))}; "
        f"latitude={_clean(row.get('professional_latitude'))}; "
        f"longitude={_clean(row.get('professional_longitude'))}.",
    ]
    return "\n".join(line for line in lines if line)


def _embed(texts: List[str], task_type: str) -> np.ndarray:
    client = _client()
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=EMBEDDING_DIM,
        ),
    )
    vectors = np.asarray([item.values for item in result.embeddings], dtype="float32")
    if len(vectors) != len(texts):
        raise RuntimeError(
            f"Expected {len(texts)} embeddings, received {len(vectors)}."
        )
    return vectors


def build_rag_index() -> Dict[str, Any]:
    """Build and persist the FAISS index from the current fused CSV."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Fused dataset not found: {CSV_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CSV_PATH)
    if df.empty:
        raise RuntimeError("The fused dataset is empty.")

    records: List[Dict[str, Any]] = []
    documents: List[str] = []
    for idx, row in df.iterrows():
        record = row.to_dict()
        row_number = idx + 1
        records.append(record)
        documents.append(row_to_document(record, row_number))

    # Documents use RETRIEVAL_DOCUMENT; queries use RETRIEVAL_QUERY.
    vectors = _embed(documents, "RETRIEVAL_DOCUMENT")
    faiss.normalize_L2(vectors)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(INDEX_PATH))

    metadata = [
        {
            "source_row": i + 1,
            "record": records[i],
            "document": documents[i],
        }
        for i in range(len(records))
    ]
    META_PATH.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    CONFIG_PATH.write_text(
        json.dumps(
            {
                "csv_path": str(CSV_PATH),
                "records": len(records),
                "embedding_model": EMBEDDING_MODEL,
                "embedding_dimension": int(vectors.shape[1]),
                "metric": "cosine_similarity_via_normalized_inner_product",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "records": len(records),
        "attributes": len(df.columns),
        "embedding_dimension": int(vectors.shape[1]),
        "index_path": str(INDEX_PATH),
    }


def _load_index() -> faiss.Index:
    if not INDEX_PATH.exists() or not META_PATH.exists():
        build_rag_index()
    return faiss.read_index(str(INDEX_PATH))


def _load_metadata() -> List[Dict[str, Any]]:
    if not META_PATH.exists():
        build_rag_index()
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def retrieve_fused_records(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieve the most semantically relevant fused records for a query."""
    query = (query or "").strip()
    if not query:
        return []

    index = _load_index()
    metadata = _load_metadata()

    query_vector = _embed([query], "RETRIEVAL_QUERY")
    faiss.normalize_L2(query_vector)

    k = max(1, min(int(top_k), len(metadata)))
    scores, indices = index.search(query_vector, k)

    results: List[Dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        item = metadata[int(idx)]
        record = dict(item["record"])
        record["_source_row"] = item["source_row"]
        record["_similarity_score"] = round(float(score), 4)
        results.append(record)
    return results


if __name__ == "__main__":
    summary = build_rag_index()
    print("RAG INDEX BUILT")
    print(summary)
    demo = retrieve_fused_records(
        "cracked wall with possible moisture; what repair service and environmental context are relevant?",
        top_k=5,
    )
    print(f"Retrieved records: {len(demo)}")
    for item in demo:
        print(
            item.get("_source_row"),
            item.get("defect"),
            item.get("location"),
            item.get("service_type"),
            item.get("_similarity_score"),
        )
