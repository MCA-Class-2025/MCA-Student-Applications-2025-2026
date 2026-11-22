from services.fused_rag_service import build_rag_index

if __name__ == "__main__":
    summary = build_rag_index()
    print("Phase-2 RAG index created successfully.")
    for key, value in summary.items():
        print(f"{key}: {value}")
