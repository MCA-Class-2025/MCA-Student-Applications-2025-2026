# Phase 2 technical documentation — Part K

This file is the editable contents list for the technical submission. Paths are relative to the repository root. The original data has 17,976 cycle records. The final cleaned fused CSV has 17,976 rows and 56 columns.

| Required item | Uploaded file or folder | What it provides |
| --- | --- | --- |
| 1. Source code | `app.py`, `Dashboard/analytics/`, `Dashboard/utils/`, `Fusion/scripts/`, `LLM/embeddings/`, `LLM/rag/` | Application, API collection, fusion, cleaning, analysis, and assistant code. |
| 2. Original dataset | `Fusion/data/menstrual_dataset.csv` | Original cycle records used before API enrichment. |
| 3. API-collected datasets | `Fusion/data/api_fusion/static/census_state.csv`, `Fusion/data/api_fusion/static/cdc_places_state.csv`, `Fusion/data/api_fusion/dynamic/open_meteo_row_level.csv`, `Fusion/data/api_fusion/dynamic/us_state_capital_coordinates.csv` | Collected Census and CDC state context, weather by cycle date, and representative state capital coordinates. |
| 4. Final fused CSV | `Fusion/data/api_fusion/final/femcare_final_fused_dataset.csv`, `Fusion/data/api_fusion/final/femcare_final_cleaned.csv` | Fusion output and final cleaned analysis/RAG input. |
| 5. EDA script and outputs | `EDA/eda_final_dataset.py`, `EDA/outputs/` | Reproducible summaries, correlations, and figures. |
| 6. LLM/RAG implementation | `LLM/embeddings/build_phase2_knowledge_base.py`, `LLM/rag/phase2_retriever.py`, `LLM/rag/llm.py`, `LLM/vectorstore/phase2_original_index/index.joblib`, `LLM/vectorstore/phase2_fused_index/index.joblib` | Builds and uses comparable TF-IDF indexes; Llama receives retrieved context. |
| 7. Screenshots | `Dashboard/application_overview/`, `EDA/screenshots/` | Application and Phase 2 UI captures, with EDA views grouped beside the analysis. Refresh the EDA app screenshot after dashboard changes. |
| 8. README | `README.md`, this file | Setup, reproduction steps, and submission map. |
| 9. API references | Links below and collection scripts in `Fusion/scripts/` | API sources and exact endpoints/fields used. |
| 10. Results and observations | `Documents/report/phase2/FemCare_Phase_2_Report.docx`, `Documents/report/phase2/assets/phase2_rag_summary.csv`, `Documents/report/phase2/assets/phase2_rag_evaluation.csv`, `Documents/report/phase2/assets/knowledge_base_manifest.json`, `EDA/outputs/` | Report, per-question evidence, aggregate measures, knowledge-base counts, and EDA outputs. |

## Files involved in creating the fused CSV

| Stage | Code | Output or role |
| --- | --- | --- |
| Census API | `Fusion/scripts/api_census.py` | Reads 2024 ACS 5-year state values into `Fusion/data/api_fusion/static/census_state.csv`. The key comes from `CENSUS_API_KEY`. |
| CDC PLACES API | `Fusion/scripts/api_cdc_places.py` | Collects county data and computes population-weighted state indicators in `Fusion/data/api_fusion/static/cdc_places_state.csv`. |
| Open-Meteo API | `Fusion/scripts/api_open_meteo.py` | Uses state capitals and cycle dates to produce `Fusion/data/api_fusion/dynamic/open_meteo_row_level.csv`. `Fusion/scripts/retry_indiana_weather.py` records a weather collection retry. |
| Fusion | `Fusion/scripts/final_fusion.py` | Joins the original data to Census and CDC by state and weather by cycle-level keys, producing `femcare_final_fused_dataset.csv`. |
| Cleaning | `Fusion/scripts/clean_final_dataset.py` | Validates and produces `femcare_final_cleaned.csv`, including cleaning flags. |
| EDA | `EDA/eda_final_dataset.py` | Produces the summaries and charts in `EDA/outputs/`. |
| RAG preparation | `LLM/embeddings/build_phase2_knowledge_base.py` | Turns selected fields into text documents and creates the baseline and enhanced TF-IDF indexes. |
| Retrieval and LLM | `LLM/rag/phase2_retriever.py`, `LLM/rag/llm.py`, `app.py` | Retrieves relevant text, passes it to Llama, and displays the answer. |
| Comparison | `Fusion/scripts/evaluate_phase2_rag.py` | Runs the fixed before/after question set and saves the results. |

The baseline and enhanced comparisons use the same TF-IDF retrieval method and Llama model. The enhanced index adds 17,976 cycle documents, 50 state summaries, and 3 fusion analysis summaries. The baseline contains 31 medical knowledge sections and 1 original-data summary. The searchable text excludes `user_id`, latitude, and longitude. The CSV itself retains its original fields for reproducibility.

## API documentation

| Source | Documentation | Endpoint used in code |
| --- | --- | --- |
| U.S. Census 2024 ACS 5-year | [ACS dataset documentation](https://api.census.gov/data/2024/acs/acs5.html) | `https://api.census.gov/data/2024/acs/acs5` |
| CDC PLACES county data | [Dataset API reference](https://dev.socrata.com/foundry/data.cdc.gov/i46a-9kgh) | `https://data.cdc.gov/resource/i46a-9kgh.json` |
| Open-Meteo historical weather | [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) | `https://archive-api.open-meteo.com/v1/archive` |
| Open-Meteo location search | [Geocoding API](https://open-meteo.com/en/docs/geocoding-api) | `https://geocoding-api.open-meteo.com/v1/search` |

## Results and interpretation

The stored ten-question run reports 5/10 correct answers before fusion and 10/10 after fusion. The average local response times were 24.8 and 35.8 seconds, respectively. These are results for a small, hand-designed test set and one local run; they do not establish general accuracy or medical safety. State-level health values are context about a population and should not be interpreted as patient-level measurements. Weather represents a state capital, not each user's exact location.

## Phase 2 screenshots

The reviewed captures below are in `Dashboard/application_overview/phase2_evidence/`. EDA captures are in `EDA/screenshots/phase2/`. The source panels are collapsed in the answer captures; opening them in a future capture would make the evidence stronger.

| File | Status | What it shows |
| --- | --- | --- |
| `phase2_home.png` | Uploaded | FemCare chat interface and Phase 2 system status. |
| `phase2_general_answer.png` | Uploaded | A correct answer to “What is PCOS?” after the retriever fix. |
| `phase2_state_answer.png` | Uploaded | California median household income answer. |
| `phase2_comparison_answer.png` | Uploaded | California and Texas average pain values. |
| `phase2_fusion_pipeline.png` | Uploaded | Data Fusion page with pipeline stages and final dataset counts. |
| `phase2_limitations_answer.png` | Needs a new capture | The current local file shows an older clinical-style response with unsupported speculation. Ask the same question again in the updated app and capture a concise explanation that state association does not establish causation. |
| Current EDA dashboard | Needs a new capture | The misleading `phase2_analytics.png` duplicate was removed. Capture the updated EDA & Analytics page with the motion bubble chart for the next submission. |

Hide API keys, personal chat history, account details, and private identifiers in future captures.

The figures in `EDA/outputs/figures/` and `Documents/report/phase2/assets/` are generated charts, not screenshots of the running application.
