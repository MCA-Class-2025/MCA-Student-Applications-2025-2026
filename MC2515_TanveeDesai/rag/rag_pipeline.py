"""
rag/rag_pipeline.py — Master RAG pipeline orchestrator.

Connects: Data → Documents → Chunks → Embeddings → FAISS → Retriever
"""

import time
from typing import Any, Dict, List, Optional

from rag.document_builder import build_all_documents
from rag.chunking import chunk_all_documents
from rag.embeddings import embed_chunks
from rag.vector_store import FAISSVectorStore
from rag.retriever import Retriever
from utils.logging import logger


class RAGPipeline:
    """
    Complete RAG pipeline for a drug dataset.

    Usage:
        pipeline = RAGPipeline()
        pipeline.build(dataset)           # Build index from fused data
        results = pipeline.query("...")   # Retrieve relevant chunks
        context = pipeline.get_context("...")  # Format for LLM
    """

    def __init__(self):
        self.vector_store = FAISSVectorStore()
        self.retriever = Retriever(self.vector_store)
        self.drug_name: Optional[str] = None
        self.doc_count = 0
        self.chunk_count = 0
        self._build_time: float = 0.0

    def build(self, dataset: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the RAG index from a fused drug dataset.
        Returns build statistics.
        """
        t0 = time.time()
        self.drug_name = dataset.get("drug_name", "")
        logger.info(f"RAGPipeline: building index for '{self.drug_name}'")

        # 1. Build documents
        documents = build_all_documents(dataset)
        self.doc_count = len(documents)

        # 2. Chunk documents
        chunks = chunk_all_documents(documents)
        self.chunk_count = len(chunks)

        # 3. Embed chunks
        chunks_with_embeddings = embed_chunks(chunks)

        # 4. Build FAISS index
        self.vector_store.build_index(chunks_with_embeddings)

        # 5. Save index
        safe_name = (self.drug_name or "drug").lower().replace(" ", "_")
        self.vector_store.save(prefix=safe_name)

        self._build_time = time.time() - t0
        logger.info(
            f"RAGPipeline built: {self.doc_count} docs, {self.chunk_count} chunks, "
            f"{self.vector_store.total_vectors} vectors in {self._build_time:.1f}s"
        )

        return {
            "doc_count": self.doc_count,
            "chunk_count": self.chunk_count,
            "vector_count": self.vector_store.total_vectors,
            "build_time_seconds": round(self._build_time, 2),
        }

    def query(self, question: str, top_k: int = 6) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks for a question."""
        return self.retriever.retrieve(question, top_k=top_k)

    def get_context(self, question: str, top_k: int = 6) -> str:
        """Get formatted context string for LLM prompting."""
        results = self.query(question, top_k=top_k)
        return self.retriever.format_context(results)

    def get_sources(self, question: str, top_k: int = 6) -> List[Dict[str, str]]:
        """Get deduplicated source list for a question."""
        results = self.query(question, top_k=top_k)
        return self.retriever.get_source_summary(results)

    @property
    def is_ready(self) -> bool:
        return self.vector_store.is_ready

    def get_stats(self) -> Dict[str, Any]:
        return {
            "drug_name": self.drug_name,
            "documents": self.doc_count,
            "chunks": self.chunk_count,
            "vectors": self.vector_store.total_vectors,
            "build_time_seconds": self._build_time,
            "ready": self.is_ready,
        }
