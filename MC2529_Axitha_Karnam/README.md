# Finance RAG modular refactor (compatibility-first)

## Contents
- `rag.py`: original RAG application and stable `ask_question(question)` entry point.
- `apis/`: separate public modules for Alpha Vantage, Frankfurter, CoinGecko, FRED, and Marketaux financial news.
- `fusion/history.py`: append-only interaction history writer.

## Run
Keep your existing project dependencies, `database.py`, Chroma directory, model setup, and `csv/` datasets in the same project root. Copy the contents of this folder into that root (or use this folder as the project root). Continue importing `ask_question` from `rag.py` as before.

## Fusion history
Each API interaction can be appended with `append_api_history(api_name, question, api_result, answer, fusion_mode)`. It writes to `csv/fused/api_conversation_history.csv`, appending every interaction without deduplication. Existing per-API fused CSVs remain separate.

## Important compatibility note
This is a compatibility-first first-stage refactor. The original routing and API implementation remains in `rag.py` so existing behavior and application imports are not broken. The new `apis/` modules expose API-specific entry points through a lazy bridge. The next safe extraction step is moving each API's implementation and its private helpers into its module after running your project's integration tests; the uploaded file alone does not include all runtime dependencies, datasets, credentials, or test fixtures needed to validate that larger move.
