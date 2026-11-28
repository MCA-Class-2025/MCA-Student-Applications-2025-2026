"""
rag_utils.py
------------
Retrieval-Augmented Generation (RAG) pipeline for the fish knowledge base.

Flow:
    knowledge_base/fish_knowledge_base.md
            │
            ▼  chunked  (LangChain RecursiveCharacterTextSplitter)
    list of text chunks
            │
            ▼  embedded  (Google Generative AI embeddings)
    vectors
            │
            ▼  stored / indexed
    FAISS vector index (persisted to disk in models/faiss_index/
                         so it's only built once, not on every app start)
            │
            ▼  similarity search at query time
    top-k relevant chunks  ──►  passed into the LLM prompt as grounding context

This means fact-sheet generation isn't relying purely on the LLM's own
memorized knowledge — it's grounded in the specific facts we curated for
these 8 fish species, reducing hallucination and keeping numbers consistent.
"""

import os

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

KB_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "fish_knowledge_base.md")
INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "faiss_index")

EMBEDDING_MODEL = "models/embedding-001"

_vectorstore = None  # module-level cache so we only load/build this once per process


def _get_embeddings():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY not set. Copy .env.example to .env and add your key."
        )
    return GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)


def _build_vectorstore() -> FAISS:
    """Chunk the knowledge base and embed it into a fresh FAISS index."""
    with open(KB_PATH, "r", encoding="utf-8") as f:
        raw_text = f.read()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=950,
        chunk_overlap=100,
        separators=["\n## ", "\n\n", "\n", " "],  # prefer splitting on fish-section headers first
    )
    chunks = splitter.create_documents([raw_text])

    embeddings = _get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)

    os.makedirs(os.path.dirname(INDEX_DIR), exist_ok=True)
    vectorstore.save_local(INDEX_DIR)
    return vectorstore


def get_vectorstore() -> FAISS:
    """Load the FAISS index from disk if it exists; otherwise build it once."""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    if os.path.exists(INDEX_DIR):
        embeddings = _get_embeddings()
        _vectorstore = FAISS.load_local(
            INDEX_DIR, embeddings, allow_dangerous_deserialization=True
        )
    else:
        _vectorstore = _build_vectorstore()

    return _vectorstore


def get_relevant_context(query: str, k: int = 3) -> str:
    """
    Retrieve the top-k most relevant knowledge-base chunks for a query
    (typically a fish name, or a follow-up question) and return them
    joined as a single context string ready to insert into a prompt.
    """
    try:
        vectorstore = get_vectorstore()
        docs = vectorstore.similarity_search(query, k=k)
        return "\n\n---\n\n".join(doc.page_content for doc in docs)
    except Exception:
        # If retrieval fails for any reason (e.g. index not built yet, embedding
        # call failed), fail gracefully — the LLM can still answer without
        # grounding context, just less reliably on exact figures.
        return ""


if __name__ == "__main__":
    # quick manual test — builds/loads the index and runs one retrieval
    context = get_relevant_context("Rohu")
    print("Retrieved context for 'Rohu':\n")
    print(context)
