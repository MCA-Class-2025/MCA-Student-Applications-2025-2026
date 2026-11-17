import os
import pandas as pd
from duckduckgo_search import DDGS

def export_duckduckgo_dataset(query):
    """
    Search the web using DuckDuckGo and save results as CSV.
    """

    results_list = []

    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=10)

        for item in results:
            results_list.append({
                "query": query,
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", "")
            })

    os.makedirs("datasets", exist_ok=True)

    df = pd.DataFrame(results_list)

    # Ensure columns exist even if no results are returned
    if df.empty:
        df = pd.DataFrame(columns=["query", "title", "url", "snippet"])

    df.to_csv("datasets/duckduckgo_dataset.csv", index=False)

    print(f"DuckDuckGo dataset saved successfully. Rows: {len(df)}")

    return results_list