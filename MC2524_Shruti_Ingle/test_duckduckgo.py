from src.duckduckgo_api import export_duckduckgo_dataset

results = export_duckduckgo_dataset("Retrieval-Augmented Generation")

print(results[:2])