# FemCare AI

FemCare AI is a Streamlit web application that brings menstrual-health education, data exploration, and wellness tools together in one interface. It combines an educational AI chat assistant with a research workflow for enriching and analyzing cycle-level data. The project is a prototype for learning and demonstration; it is not a medical device or a substitute for professional care.

## Application overview

### Home dashboard

The Home page provides a starting point for the application's main tools, including MenoCare, the AI Copilot, Nutrition Guide, Healthcare Finder, and the research dataset overview. The interface supports light and dark themes and responsive layouts.

### AI Copilot

The chat assistant answers menstrual-health education questions using local medical knowledge and a local Llama 3.2 model. Retrieval provides relevant passages as context. For selected supported questions about the fused research dataset, the application can calculate an answer directly from the data. A basic urgent-symptom rule can direct users to seek care in certain concerning situations. The assistant does not diagnose conditions or provide a clinically validated risk score.

### MenoCare

MenoCare is a session-only menopause-transition symptom tracking prototype. It supports quick check-ins and separate records for symptom episodes, bleeding events, and medication changes. Users can review descriptive trends and weekly or monthly activity summaries, export records as CSV, and prepare a date-filtered appointment summary. Entries are held in the active Streamlit session and are not saved to an account or database.

### Nutrition Guide and Recipe AI

The Nutrition Guide provides food and nutrition information from a checked-in USDA FoodData Central dataset. The separate recipe assistant can suggest recipes from ingredients and preferences using a configured cloud AI provider. Recipe suggestions and cooking times are generated estimates, not an exhaustive recipe catalog or medical nutrition advice.

### Healthcare Finder

The Healthcare Finder helps users look for healthcare services using the application's location-search data and filters. Results depend on the available external map data and should be checked with the provider before visiting.

### EDA and research dashboard

The analytics area presents distributions, comparisons, correlations, and other exploratory visualizations for the menstrual-health dataset and its fused API context. These views are intended to help explore the data; observed associations do not establish cause and effect or describe an individual user's health.

## Data fusion and analysis

The research workflow starts with a cycle-level dataset and enriches it with external public data:

- U.S. Census ACS data adds selected state population, age-group, and household-income measures.
- CDC PLACES data adds selected state-level indicators such as obesity, physical inactivity, smoking, and depression prevalence.
- Open-Meteo historical weather data adds weather measures using representative state locations and cycle dates.

The API outputs are joined with the original records, then cleaned and validated. The resulting cleaned fused dataset contains 17,976 rows and 56 columns. The project includes scripts for collection, fusion, inspection, cleaning, and exploratory analysis. Because many added measures are state-level and repeated across multiple cycle records, analyses involving them must be interpreted at the appropriate geographic level.

## Machine-learning comparison

The project includes an experimental comparison of seven algorithms using pain level as the outcome: Naive Bayes, Random Forest, Decision Tree, Logistic Regression, Simple Linear Regression, Multiple Linear Regression, and Polynomial Regression. Classification and regression methods use different metrics. These results are exploratory and are not clinically validated predictions.

## Search and language-model evaluation

The Phase 2 retrieval workflow prepares readable documents from selected original and fused information and indexes them using TF-IDF. It compares a baseline knowledge base with an enhanced knowledge base that includes fused information, using the same language model and retrieval approach for the controlled comparison. Evaluation files and reports document the tested questions and observed results. Findings apply to that test set and are not evidence of clinical performance.

## Main project areas

| Folder or file | Purpose |
| --- | --- |
| `app.py` | Streamlit application entry point and page navigation |
| `analytics/` | EDA, charts, and dashboard views |
| `data/` | Original, API-collected, and fused datasets |
| `scripts/` | API collection, fusion, validation, EDA, and model evaluation scripts |
| `embeddings/` | Knowledge-base document and index preparation |
| `rag/` | Retrieval, prompts, answer routing, and language-model interface |
| `knowledge/` | Local medical reference text used by the assistant |
| `utils/` | Application features, settings, safety checks, and supporting logic |
| `report/` | Phase reports, figures, evaluation results, and algorithm comparison outputs |
| `screenshots/` | Visual evidence of the application and analysis |

## Running the application

Install the packages listed in `requirements.txt`, ensure Ollama is running with the configured Llama model, then start the app from the project directory:

```powershell
streamlit run app.py
```

The chat uses the Phase 2 TF-IDF index. After changing source data or knowledge documents, rebuild the indexes with:

```powershell
python embeddings/build_phase2_knowledge_base.py
```

The application also supports a cloud provider for recipe suggestions. Configure its API key in the local environment or Streamlit secrets. Keep all API keys private and out of Git.

## Reproducing the data workflow

The collected API output files are included in the repository. Collection scripts can be run to refresh data; Census collection requires a locally configured `CENSUS_API_KEY`.

```powershell
python scripts/api_census.py
python scripts/api_cdc_places.py
python scripts/api_open_meteo.py
python scripts/final_fusion.py
python scripts/clean_final_dataset.py
python scripts/inspect_final_dataset.py
python scripts/eda_final_dataset.py
python embeddings/build_phase2_knowledge_base.py
python scripts/evaluate_phase2_rag.py
```

Some API refreshes require network access and keys. The chatbot evaluation requires the configured Ollama model. Saved reports and result files are included for review without rerunning the workflow.

## Reports and outputs

- `report/phase1/` contains Phase 1 data-fusion and exploratory-analysis materials.
- `report/phase2/` contains Phase 2 retrieval and before/after evaluation materials.
- `report/algorithm_comparison/` contains model comparison results and figures.
- `docs/phase2_technical_documentation.md` describes key files, data flow, API references, and reproducible commands.

## Limitations and privacy

FemCare AI is an educational and research prototype. It may provide incomplete or incorrect information. It does not diagnose, prescribe treatment, or replace a qualified healthcare professional. Dataset findings may reflect data quality issues, geographic aggregation, missing values, or other limitations documented in the reports.

MenoCare records currently exist only in the active application session. The project does not yet provide user accounts, persistent patient storage, or clinician monitoring. Do not enter sensitive personal health information into a public deployment. Real-world use would require appropriate privacy and security controls, informed consent, clinical review, and evaluation.
