# CardioCare AI

An educational cardiovascular-risk assessment system combining a Random Forest classifier with planned LLM-powered health assistance.

## Dataset

The project includes `dataset/cardio_train.csv`, the 70,000-record Cardiovascular Disease Dataset from Kaggle (`sulianova/cardiovascular-disease-dataset`). It uses `cardio` as its binary target and clinical/lifestyle features including age, blood pressure, cholesterol, glucose, smoking, alcohol intake, and physical activity.

## Five-model cardiovascular-risk comparison

Training evaluates five binary classifiers on the same stratified 80/20 split:

1. Logistic Regression
2. Decision Tree
3. K-Nearest Neighbors (KNN)
4. Linear Support Vector Machine (SVM), calibrated to return risk probabilities
5. Random Forest

Height/weight and blood-pressure inputs are also fused into BMI, pulse pressure, and mean arterial pressure. The model with the highest held-out ROC-AUC is selected for the prediction API; F1-score is the tie-breaker. Training saves all five fitted models in `backend/ml/model.joblib` and writes the comparison metrics to `backend/ml/model_metrics.json`. Retrieve the selected model and metrics at `GET /models/evaluation`.

## Feature-level data fusion

Training combines the raw patient measurements with derived anthropometric and hemodynamic features: body mass index (BMI), pulse pressure, and mean arterial pressure. Run the training command after this update to build a model that uses the fused feature set. The API remains compatible with the existing model while retraining is pending.

Each API assessment also requires a pseudonymous `patient_id`. This is the fusion key that identifies the patient record while its derived signals are assembled in `backend/ml/features.py`; it is excluded from the model features and must not contain a name, email address, or other direct personal identifier. Every successful assessment is saved to `dataset/fused_assessments.csv`, including the submitted values, the patient-keyed fused features, and the risk result. Use **Data fusion → Fused assessment records → Show data** to view recent records.

## Initial setup

1. Create a Python 3.12 virtual environment: `py -3.12 -m venv .venv`.
2. Install dependencies: `.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt`.
3. Train the model: `.\.venv\Scripts\python.exe backend\ml\train.py dataset\cardio_train.csv`.
4. Start the API: `.\.venv\Scripts\uvicorn.exe main:app --app-dir backend --reload`.
5. Start the frontend: `cd frontend` then `npm run dev`.

The prediction endpoint returns `503` if the trained model artifact is unavailable. This prevents fabricated risk results.

## AI wellness recommendations

Set `HF_TOKEN` in a local `.env` file before using the AI wellness guidance button. The endpoint sends the submitted health measurements and model result to the configured Hugging Face model, then returns general, non-diagnostic wellness information.

## External API integrations

CardioCare AI provides backend endpoints for these external services:

| Service | Endpoint | Configuration |
| --- | --- | --- |
| Hugging Face Inference Providers | `POST /recommendations` | `HF_TOKEN` |
| USDA FoodData Central | `GET /external/foods?query=...` | `USDA_API_KEY` |
| OpenFDA drug labels | `GET /external/drug-labels?query=...` | None |
| Open Food Facts | `GET /external/packaged-foods?query=...` | None |
| OpenStreetMap Nominatim | `GET /external/nearby-care?latitude=...&longitude=...` | None |

Food search requires a free [USDA FoodData Central API key](https://fdc.nal.usda.gov/api-key-signup.html). Drug-label results are educational references only and must not be used as prescribing guidance.

## API data storage

Each successful external API call is saved in its own CSV file inside `dataset`, alongside the training data. Every row contains a UTC timestamp, endpoint, request JSON, and response JSON so variable API payloads remain valid CSV data.

| API | CSV file |
| --- | --- |
| Fused assessments | `fused_assessments.csv` |
| Hugging Face recommendations | `huggingface_recommendations.csv` |
| USDA FoodData Central | `usda_foods.csv` |
| OpenFDA drug labels | `openfda_drug_labels.csv` |
| Open Food Facts | `openfoodfacts_packaged_foods.csv` |
| OpenStreetMap nearby care | `openstreetmap_nearby_care.csv` |

These generated CSV files are excluded from version control because they can contain health measurements and location data. Set `API_DATA_CSV_PATH` to store them in a different relative or absolute directory.

## Nearby care

The nearby-care feature uses the browser's location permission to find hospitals, clinics, doctors, and pharmacies through OpenStreetMap data. It is not a substitute for emergency services.

## Phase 1 fusion and EDA deliverables

The Phase 1 workflow uses the UCI Heart Failure Clinical Records dataset and the NLM Clinical Tables LOINC API to attach standardized metadata to serum creatinine and serum sodium records. It creates the API CSV, fused CSV, data-quality checks, visualizations, and the report for Parts A–E:

```powershell
.\.venv\Scripts\python.exe analysis\phase1_fusion_eda.py
```

Generated files are placed in `analysis\phase1_output`. The report is `analysis\phase1_output\phase1_report_parts_A_to_E.md`.

## Phase 2 RAG and evaluation deliverables

Phase 2 builds a local TF-IDF vector knowledge base from the original heart-failure CSV and its LOINC-enriched fused CSV. It generates the Parts F-K analysis, five evidence-based insights, API/fusion visualizations, ten LLM test cases, and a before/after comparison:

```powershell
.\.venv\Scripts\python.exe analysis\phase2_rag_eda.py
```

The generated report is `analysis\phase2_output\phase2_report_parts_F_to_K.md`. The knowledge-base artifact is `analysis\phase2_output\rag\fused_knowledge_base.joblib`.

To record live Hugging Face responses for the ten test questions, configure `HF_TOKEN` in `.env` and run:

```powershell
.\.venv\Scripts\python.exe analysis\phase2_rag_eda.py --run-llm-tests
```

Send a grounded fused-data question to `POST /phase2/questions` after building the knowledge base. The endpoint retrieves source records, provides them to the configured LLM, returns the answer with source IDs, and rejects unsupported facts through its system prompt. The frontend exposes this as the **Phase 2 RAG** navigation page, including the answer, disclaimer, and retrieved sources for report screenshots.
