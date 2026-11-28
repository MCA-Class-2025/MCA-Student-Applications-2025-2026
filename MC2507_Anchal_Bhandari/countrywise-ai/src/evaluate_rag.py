import os
import time
import json
import pandas as pd
from src.rag import build_documents, build_faiss_index, query_rag

print("--- RUNNING QUANTITATIVE RAG BENCHMARK (Part J) ---")

# 1. Load both datasets and build indices
df_base = pd.read_csv("data/original_dataset.csv")
docs_base = build_documents(df_base)
index_base = build_faiss_index(docs_base)

df_fused = pd.read_csv("data/fused_dataset.csv")
docs_fused = build_documents(df_fused)
index_fused = build_faiss_index(docs_fused)

# 2. Benchmark Queries
test_queries = [
    # Baseline WHR Queries
    {"q": "What is Finland's happiness score and rank?", "type": "baseline", "expected_key": "7.77"},
    {"q": "What is Denmark's social support score?", "type": "baseline", "expected_key": "1.58"},
    {"q": "Which nation ranks number 1 in happiness?", "type": "baseline", "expected_key": "Finland"},
    
    # Enhanced Multi-API Queries
    {"q": "What is the capital city of Finland?", "type": "enhanced", "expected_key": "Helsinki"},
    {"q": "What is the annual mean temperature of Finland?", "type": "enhanced", "expected_key": "3.64"},
    {"q": "What is the life expectancy in Denmark according to the World Bank?", "type": "enhanced", "expected_key": "81.30"},
    {"q": "What is the capital and climate of India?", "type": "enhanced", "expected_key": "New Delhi"},
    {"q": "What is the geographic region of Norway?", "type": "enhanced", "expected_key": "Europe"},
    
    # Negative / Grounding Checks
    {"q": "What is the stock market ticker for Nokia?", "type": "out_of_scope", "expected_key": "I do not have that information"},
    {"q": "Who is the president of France?", "type": "out_of_scope", "expected_key": "I do not have that information"}
]

results = []

for idx, t in enumerate(test_queries, 1):
    q = t["q"]
    q_type = t["type"]
    expected = t["expected_key"]
    print(f"\nEvaluating [{idx}/10]: '{q}' ({q_type})")

    # Run Baseline
    ans_base, ctx_base, lat_base = query_rag(q, index_base, docs_base, k=5)
    base_grounded = 1 if (expected.lower() in ans_base.lower() or ("do not have that information" in ans_base.lower() and q_type != "baseline")) else 0

    time.sleep(0.5)

    # Run Enhanced
    ans_fused, ctx_fused, lat_fused = query_rag(q, index_fused, docs_fused, k=5)
    fused_grounded = 1 if (expected.lower() in ans_fused.lower() or ("do not have that information" in ans_fused.lower() and q_type == "out_of_scope")) else 0

    results.append({
        "query": q,
        "category": q_type,
        "baseline_latency_s": lat_base,
        "baseline_success": base_grounded,
        "baseline_answer": ans_base.replace("\n", " ")[:90],
        "enhanced_latency_s": lat_fused,
        "enhanced_success": fused_grounded,
        "enhanced_answer": ans_fused.replace("\n", " ")[:90]
    })
    time.sleep(0.5)

res_df = pd.DataFrame(results)
res_df.to_csv("report/rag_evaluation_results.csv", index=False)

print("\n================== BENCHMARK SUMMARY TABLE ==================")
print(res_df[["query", "category", "baseline_success", "enhanced_success", "baseline_latency_s", "enhanced_latency_s"]].to_string())

print("\n--- AGGREGATE METRICS ---")
print(f"Baseline Accuracy / Groundedness: {res_df['baseline_success'].mean() * 100:.1f}%")
print(f"Enhanced Accuracy / Groundedness: {res_df['enhanced_success'].mean() * 100:.1f}%")
print(f"Mean Baseline Latency: {res_df['baseline_latency_s'].mean():.2f}s")
print(f"Mean Enhanced Latency: {res_df['enhanced_latency_s'].mean():.2f}s")
print("\nEvaluation results saved to report/rag_evaluation_results.csv")