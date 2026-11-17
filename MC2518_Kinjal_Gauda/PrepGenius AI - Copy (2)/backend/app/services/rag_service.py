import numpy as np
from typing import List, Dict, Any, Tuple
from app.config import settings
from app.utils.logger import logger

# Try importing FAISS
FAISS_AVAILABLE = False
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    logger.warning("FAISS module not found. Using NumPy vector matrix search engine.")

# Try importing SentenceTransformer
ST_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    logger.warning("SentenceTransformers module not found. Using Scikit-Learn TF-IDF embedding engine.")

from sklearn.feature_extraction.text import TfidfVectorizer

class NumPyVectorIndex:
    """NumPy-based vector index fallback with L2 distance matching."""
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.vectors = np.empty((0, dimension), dtype=np.float32)

    @property
    def ntotal(self) -> int:
        return len(self.vectors)

    def add(self, embeddings: np.ndarray):
        if self.vectors.size == 0:
            self.vectors = embeddings.astype(np.float32)
        else:
            self.vectors = np.vstack([self.vectors, embeddings.astype(np.float32)])

    def search(self, query_vector: np.ndarray, top_k: int) -> Tuple[np.ndarray, np.ndarray]:
        if self.ntotal == 0:
            return np.array([[]]), np.array([[]])
        
        diff = self.vectors - query_vector[0]
        distances = np.sum(diff ** 2, axis=1)
        
        top_k = min(top_k, self.ntotal)
        indices = np.argsort(distances)[:top_k]
        top_distances = distances[indices]

        return np.array([top_distances]), np.array([indices])

class RAGEngine:
    _model = None
    _tfidf = None

    @classmethod
    def get_embedding_model(cls):
        if ST_AVAILABLE:
            if cls._model is None:
                try:
                    logger.info(f"Loading SentenceTransformer model: {settings.EMBEDDING_MODEL_NAME}...")
                    cls._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                    logger.info("SentenceTransformer model loaded successfully.")
                except Exception as e:
                    logger.warning(f"Could not load SentenceTransformer ({e}). Falling back to TF-IDF vectorizer.")
                    cls._model = None
            return cls._model
        return None

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Recursive character text splitter creating overlapping text chunks."""
        if not text or not text.strip():
            return []

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            if end < text_len:
                last_space = text.rfind(" ", start, end)
                if last_space != -1 and last_space > start + (chunk_size // 2):
                    end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap if end < text_len else text_len

        return chunks

    @classmethod
    def generate_embeddings(cls, texts: List[str]) -> Tuple[np.ndarray, Any]:
        """Generate dense embeddings using SentenceTransformers or TF-IDF matrix fallback."""
        model = cls.get_embedding_model()
        if model is not None:
            embeddings = model.encode(texts, convert_to_numpy=True).astype("float32")
            return embeddings, None
        else:
            # TF-IDF Fallback Vectorizer
            vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts).toarray().astype("float32")
            # Pad to 384 dimensions if max_features < 384
            if tfidf_matrix.shape[1] < 384:
                pad_width = 384 - tfidf_matrix.shape[1]
                tfidf_matrix = np.pad(tfidf_matrix, ((0, 0), (0, pad_width)), mode='constant')
            return tfidf_matrix, vectorizer

    @classmethod
    def build_vector_store(cls, documents_data: List[Dict[str, Any]]) -> Tuple[Any, List[Dict[str, Any]], Any]:
        """
        documents_data: List of dicts with keys: {'doc_id', 'filename', 'text'}
        Returns: Vector Index, Metadata Chunks mapping, Vectorizer reference.
        """
        chunk_metadata_list = []
        all_chunk_texts = []

        for doc in documents_data:
            doc_id = doc["doc_id"]
            filename = doc["filename"]
            raw_text = doc["text"]

            chunks = cls.chunk_text(raw_text)
            for idx, chunk in enumerate(chunks):
                all_chunk_texts.append(chunk)
                chunk_metadata_list.append({
                    "doc_id": doc_id,
                    "filename": filename,
                    "chunk_index": idx,
                    "snippet": chunk
                })

        d = 384
        if not all_chunk_texts:
            index = faiss.IndexFlatL2(d) if FAISS_AVAILABLE else NumPyVectorIndex(d)
            return index, [], None

        logger.info(f"Generating embeddings for {len(all_chunk_texts)} document chunks...")
        embeddings, vectorizer = cls.generate_embeddings(all_chunk_texts)

        dimension = embeddings.shape[1]
        if FAISS_AVAILABLE:
            index = faiss.IndexFlatL2(dimension)
        else:
            index = NumPyVectorIndex(dimension)

        index.add(embeddings)
        logger.info(f"Vector index built successfully with {index.ntotal} vectors.")
        return index, chunk_metadata_list, vectorizer

    @classmethod
    def search_relevant_chunks(
        cls, 
        query: str, 
        index: Any, 
        chunk_metadata: List[Dict[str, Any]], 
        vectorizer: Any = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using Vector Index to find top-k relevant document chunks."""
        if index.ntotal == 0 or not chunk_metadata:
            return []

        model = cls.get_embedding_model()
        if model is not None:
            query_embedding = model.encode([query], convert_to_numpy=True).astype("float32")
        elif vectorizer is not None:
            query_vec = vectorizer.transform([query]).toarray().astype("float32")
            if query_vec.shape[1] < 384:
                pad_width = 384 - query_vec.shape[1]
                query_vec = np.pad(query_vec, ((0, 0), (0, pad_width)), mode='constant')
            query_embedding = query_vec
        else:
            return []

        distances, indices = index.search(query_embedding, min(top_k, index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(chunk_metadata) and idx >= 0:
                meta = chunk_metadata[idx]
                similarity = float(1 / (1 + dist))
                results.append({
                    "doc_id": meta["doc_id"],
                    "filename": meta["filename"],
                    "chunk_index": meta["chunk_index"],
                    "snippet": meta["snippet"],
                    "relevance_score": round(similarity, 4),
                    "distance": float(dist)
                })

        return results
