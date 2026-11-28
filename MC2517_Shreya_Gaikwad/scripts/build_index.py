"""
build_index.py
---------------
One-time (or re-run-on-update) ingestion script.
Runs Phases 3-5: loads raw documents -> cleans -> chunks -> embeds -> stores in FAISS.

Usage:
    python scripts/build_index.py
    python scripts/build_index.py --data-dir data/raw --out vectorstore
"""

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_processing import process_directory, validate_chunks
from src.embeddings import embed_texts
from src.vector_store import PolicyVectorStore


def main():
    parser = argparse.ArgumentParser(description="Build the FAISS vector index for the Policy Chatbot")
    parser.add_argument("--data-dir", default="Dataset/raw", help="Directory containing raw policy documents")
    parser.add_argument("--out", default="vectorstore", help="Output directory for the FAISS index")
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--chunk-overlap", type=int, default=150)
    parser.add_argument("--cohere-api-key", default=os.environ.get("COHERE_API_KEY", ""),
                         help="Cohere API key (or set the COHERE_API_KEY env var). Free key: dashboard.cohere.com/api-keys")
    args = parser.parse_args()

    if not args.cohere_api_key:
        print("❌ No Cohere API key provided. Pass --cohere-api-key or set the COHERE_API_KEY env var.")
        print("   Get a free key at: https://dashboard.cohere.com/api-keys")
        return

    print(f"\n📂 Loading & processing documents from '{args.data_dir}' ...")
    chunks = process_directory(args.data_dir, chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)

    if not chunks:
        print("❌ No chunks were produced. Check that data-dir contains supported files (.md .txt .csv .pdf .docx).")
        return

    report = validate_chunks(chunks)
    print("\n✅ Data validation report:")
    for k, v in report.items():
        print(f"   {k}: {v}")

    print(f"\n🧠 Generating embeddings for {len(chunks)} chunks via the Cohere Embed API ...")
    texts = [c.text for c in chunks]
    embeddings = embed_texts(texts, api_key=args.cohere_api_key)
    embedding_dim = embeddings.shape[1]
    print(f"   Embedding dimension: {embedding_dim}")

    print(f"\n💾 Building FAISS index and saving to '{args.out}' ...")
    store = PolicyVectorStore(embedding_dim=embedding_dim)
    store.add(embeddings, chunks)
    store.save(args.out)

    print(f"\n🎉 Done! Indexed {store.index.ntotal} chunks from {report['num_sources']} source documents.")
    print(f"   Vector store saved at: {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
