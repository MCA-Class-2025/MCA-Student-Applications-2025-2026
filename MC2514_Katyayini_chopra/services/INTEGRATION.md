# FixAI Phase 2 — Embedding + FAISS RAG

## 1. Copy files
Copy these two Python files into the FixAI project:

- `services/fused_rag_service.py`
- `build_rag_index.py` (project root)

## 2. Install dependency
From `C:\Users\USER\FixAI_Maharashtra` with the virtual environment active:

```powershell
pip install faiss-cpu numpy pandas google-genai
```

## 3. Build the vector index once

```powershell
python build_rag_index.py
```

Expected conceptually:

```text
Phase-2 RAG index created successfully.
records: 20
attributes: 32
embedding_dimension: 768
```

The command creates:

- `output/fixai_fused_faiss.index`
- `output/fixai_fused_rag_metadata.json`
- `output/fixai_fused_rag_config.json`

## 4. Replace the old keyword retrieval in `final_reasoning_service.py`

Add:

```python
from services.fused_rag_service import retrieve_fused_records
```

Then replace the old Phase-1 retrieval call such as:

```python
fused_knowledge = search_fused_knowledge(...)
```

with a semantic query built from the detected result:

```python
rag_query = (
    f"Defect issue: {issue}. "
    f"Category: {category}. "
    f"Element: {element}. "
    f"Recommended service: {recommended_service}. "
    f"Location: {location}."
)
fused_knowledge = retrieve_fused_records(rag_query, top_k=5)
```

Keep the retrieved records in the Gemini prompt as an additional knowledge source.

## 5. Chat integration
In `chat_service.py`, add:

```python
from services.fused_rag_service import retrieve_fused_records
```

Inside `ask_fixai()`, build the query from the question plus the current diagnosis:

```python
rag_query = (
    f"User question: {question}\n"
    f"Issue: {final_result.get('issue')}\n"
    f"Category: {final_result.get('category')}\n"
    f"Service: {final_result.get('recommended_service')}\n"
    f"Location: {fused_data.get('location', {}).get('address')}"
)
fused_records = retrieve_fused_records(rag_query, top_k=5)
```

Then insert `fused_records` into the existing Gemini chat context under a clear heading such as:

```text
SEMANTICALLY RETRIEVED FUSED KNOWLEDGE
Use these records as supporting evidence. Do not invent values that are not present in them.
```

No change is needed to the existing `app.py` call signature.

## 6. Important data-source rule

Keep the current live API objects separate from RAG records:

- Live weather/AQI = current runtime information.
- Live professional API = current location-specific professional information.
- FAISS RAG = semantic retrieval of the Phase-1 fused CSV knowledge.

Do not present RAG professional/weather values as current live values.

## 7. Phase-2 architecture for the report

```text
Original defect dataset
        +
API-enriched Phase-1 fused CSV
        |
Data preparation / record creation
        |
Gemini text embeddings
        |
FAISS vector index
        |
Semantic retriever
        |
Top-k relevant fused records
        +
Live API data
        |
Final Gemini reasoning
        |
FixAI diagnosis / chat response
```
