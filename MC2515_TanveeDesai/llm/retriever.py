"""
rag/retriever.py — Retrieval component for RAG pipeline.
"""

from typing import Any, Dict, List

from config.settings import TOP_K_RETRIEVAL
from rag.embeddings import embed_query
from rag.vector_store import FAISSVectorStore
from utils.logging import logger


class Retriever:
    """
    Retrieves relevant document chunks for a given query
    using FAISS similarity search.
    """

    def __init__(self, vector_store: FAISSVectorStore):
        self.store = vector_store

    def retrieve(self, query: str, top_k: int = TOP_K_RETRIEVAL) -> List[Dict[str, Any]]:
        """
        Retrieve top_k most relevant chunks for a query.
        Returns list of result dicts with text, score, metadata.
        """
        if not self.store.is_ready:
            logger.warning("Vector store is not ready for retrieval")
            return []

        query_embedding = embed_query(query)
        results = self.store.search(query_embedding, top_k=top_k)

        logger.info(f"Retrieved {len(results)} chunks for query: '{query[:60]}'")
        return results

    def format_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Format retrieved results into a context string for LLM prompting.
        """
        if not results:
            return "No relevant information found in the knowledge base."

        parts = []
        for i, r in enumerate(results, 1):
            meta = r.get("metadata", {}).get("metadata", {})
            source = meta.get("source", "Unknown")
            source_type = meta.get("source_type", "")
            url = meta.get("url", "")
            title = r.get("metadata", {}).get("title", "")

            header = f"[Source {i}: {source} — {source_type}]"
            if title:
                header += f" {title}"
            if url:
                header += f" ({url})"

            parts.append(f"{header}\n{r['text']}")

        return "\n\n---\n\n".join(parts)

    def get_source_summary(self, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Return a deduplicated list of sources from retrieved results.
        """
        seen = set()
        sources = []
        for r in results:
            meta = r.get("metadata", {}).get("metadata", {})
            source = meta.get("source", "Unknown")
            source_type = meta.get("source_type", "")
            url = meta.get("url", "")
            key = f"{source}_{source_type}"
            if key not in seen:
                seen.add(key)
                sources.append({
                    "source": source,
                    "source_type": source_type,
                    "url": url,
                    "relevance_score": round(r.get("score", 0.0), 3),
                })
        return sources
