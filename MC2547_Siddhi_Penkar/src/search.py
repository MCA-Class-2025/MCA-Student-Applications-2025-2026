"""
search.py
---------
High-level semantic search that retrieves from BOTH the PDF knowledge base
and the fused dataset (if available).
"""

from typing import List, Dict

from src.embedding import encode_query
from src.vector_store import load_faiss_index, search_index, VectorStoreError
from src.dataset_index import load_dataset_index, dataset_index_exists
from src.utils import get_logger

logger = get_logger(__name__)

DEFAULT_TOP_K = 3


class SearchError(Exception):
    pass


def semantic_search(query: str, top_k: int = DEFAULT_TOP_K, include_dataset: bool = True) -> List[Dict]:
    """
    Perform semantic search over:
      - PDF knowledge base (if exists)
      - Fused dataset (if available and include_dataset=True)

    Returns a list of results, each with 'text', 'source', 'chunk_id', 'score'.
    Dataset results have source = 'Fused Dataset' and include 'bug_id' extra.
    """
    if not query or not query.strip():
        raise SearchError("Please enter a valid, non-empty question.")

    all_results = []

    # 1. Search PDF knowledge base
    try:
        index, chunk_metadata = load_faiss_index()
        query_embedding = encode_query(query)
        scores, indices = search_index(index, query_embedding, top_k=top_k)
        for score, idx in zip(scores, indices):
            if idx == -1 or idx >= len(chunk_metadata):
                continue
            record = dict(chunk_metadata[idx])
            record["score"] = float(score)
            all_results.append(record)
    except VectorStoreError as e:
        logger.warning(f"PDF knowledge base not available: {e}")
    except Exception as e:
        logger.warning(f"Error searching PDF index: {e}")

    # 2. Search fused dataset (if enabled and index exists)
    if include_dataset and dataset_index_exists():
        try:
            dataset_index, dataset_metadata = load_dataset_index()
            if dataset_index is not None and dataset_index.ntotal > 0:
                query_emb = encode_query(query)
                scores, indices = dataset_index.search(query_emb.reshape(1, -1), top_k)
                for score, idx in zip(scores[0], indices[0]):
                    if idx >= 0 and idx < len(dataset_metadata):
                        row = dataset_metadata[idx]
                        # Build a text preview for the LLM
                        text_preview = (
                            f"Bug {row['bug_id']}: {row['title']}\n"
                            f"Priority: {row.get('gemini_priority_recommendation', 'N/A')}\n"
                            f"Risk: {row.get('risk_level', 'N/A')}\n"
                            f"Root Cause: {row.get('gemini_root_cause_analysis', 'N/A')}"
                        )
                        all_results.append({
                            "text": text_preview,
                            "source": "Fused Dataset",
                            "chunk_id": idx,
                            "score": float(score),
                            "bug_id": row['bug_id'],
                            "metadata": row  # full row for later use
                        })
        except Exception as e:
            logger.warning(f"Error searching dataset index: {e}")

    # Sort by score descending (higher is better)
    all_results.sort(key=lambda x: x["score"], reverse=True)

    # Keep only top_k overall (or optionally merge)
    # We'll return all results but cap at top_k * 2 maybe? For simplicity return top_k from combined.
    # Actually we might want to let the LLM have more context, so we return all.
    # But we can limit to top_k * 2 to avoid token overload.
    if len(all_results) > top_k * 2:
        all_results = all_results[:top_k * 2]

    if not all_results:
        raise SearchError("No relevant information found in PDFs or dataset for your query.")

    logger.info(f"Retrieved {len(all_results)} results (PDF + dataset).")
    return all_results