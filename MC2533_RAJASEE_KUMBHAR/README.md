# 🎓 NoticeSenseAI

## AI-Powered College Circular & Deadline Assistant using Large Language Models (LLMs), Multi-Source API Data Fusion, and Retrieval-Augmented Generation (RAG)

NoticeSenseAI is an end-to-end intelligent academic decision-support and circular question-answering system. Built for higher education institutions (including **SNDT Women's University**, **University of Mumbai**, **IIT Bombay**, **VJTI**, and **NMIMS**), the application combines internal institutional notices with **five external public REST APIs** (Geocoding, Meteorology, Air Quality, Academic Domains, and Sovereign Profiles) to enrich standard circular retrieval with real-time geographic, environmental, and security intelligence.

This project fulfills the comprehensive requirements of the **LLMs & RAG Course**, completing all deliverables for **Phase 1 (Parts A – E)** and **Phase 2 (Parts F – K)**.

---

## 📌 Project Overview & Architecture

NoticeSenseAI operates on a multi-stage data and retrieval pipeline:

```
                    ┌───────────────────────────────┐
                    │  5 Public REST APIs (Part B)  │
                    │  (Nominatim, Open-Meteo,      │
                    │   Hipo, REST Countries)       │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
┌─────────────────────────┐  Left Outer Join   ┌───────────────────────────┐
│ Original Dataset        ├───────────────────►│ Fused Dataset             │
│ (data/original_dataset) │  (src/data_fusion) │ (data/fused_dataset.csv)  │
│ 50 Records × 13 Cols    │                    │ 50 Records × 37 Cols      │
└─────────────────────────┘                    └─────────────┬─────────────┘
                                                             │
                                   ┌─────────────────────────┴─────────────────────────┐
                                   ▼                                                   ▼
                     ┌───────────────────────────┐                       ┌───────────────────────────┐
                     │ Exploratory Data Analysis │                       │ Enhanced LLM/RAG Pipeline │
                     │ (notebooks/fusion_eda)    │                       │ (src/llm_rag.py)          │
                     │ 6 Mandatory Visualizations│                       │ ChromaDB + Groq LPU       │
                     └───────────────────────────┘                       └───────────────────────────┘
```

---

## 📂 Repository Organization

```
NoticeSenseAI/
│
├── README.md                          # Comprehensive technical documentation & setup guide
├── requirements.txt                   # Dependency manifest (LangChain, ChromaDB, Streamlit, etc.)
├── api_keys.json                      # Hashed API keys for REST endpoints
├── api_usage_analytics.json           # API usage analytics and endpoint monitoring
├── app.py                             # Streamlit Web Application (Q&A, Dashboards, API Playground)
├── api.py                             # FastAPI REST Gateway with programmatic X-API-Key security
│
├── data/
│   ├── original_dataset.csv           # 50-record structured academic notices dataset
│   ├── api_dataset.csv                # 35-record multi-API meteorological & institutional dataset
│   ├── fused_dataset.csv              # 50-record 37-column merged, cleaned master dataset
│   └── notices/
│       └── list-of-documents-for-mca-admission.pdf   # Base MCA document checklist notice
│
├── notebooks/
│   └── fusion_eda.ipynb               # Fully executed Jupyter Notebook with EDA & visualizations
│
├── src/
│   ├── __init__.py                    # Source package initialization
│   ├── api_collection.py              # Automated 5-API data collection engine
│   ├── data_cleaning.py               # Missing value imputation, dtypes & outlier analysis
│   ├── data_fusion.py                 # Left Join fusion pipeline & discrepancy validation
│   └── llm_rag.py                     # ChromaDB vector store indexing & Groq LLM benchmark suite
│
├── screenshots/                       # Mandatory EDA plots and UI screenshots
│   ├── 01_system_homepage.png
│   ├── 02_notice_uploading.png
│   ├── 03_admission_query.png
│   ├── 04_interview_query.png
│   ├── 05_source_documents.png
│   ├── 07_eda_univariate_distribution.png
│   ├── 08_eda_univariate_boxplot.png
│   ├── 09_eda_bivariate_weather_vs_fee.png
│   ├── 10_eda_bivariate_aqi_vs_category.png
│   ├── 11_eda_multivariate_correlation_heatmap.png
│   └── 12_eda_fused_insight_travel_advisory.png
│
└── report/
    ├── project_report.md              # University technical report covering Parts A through K
    ├── llm_evaluation_results.csv     # Empirical benchmark evaluation log
    ├── generate_pdf_report.py         # ReportLab PDF compiler script
    └── project_report.pdf             # Submission-ready compiled PDF report
```

---

## 📊 Dataset Comparison & Validation Summary (Part C & D)

| Parameter | Original Dataset | API Dataset | Fused Dataset | Validation Status |
|---|---|---|---|---|
| **Number of Records** | 50 | 35 | **50** | 100% Retained (Left Join) |
| **Number of Attributes** | 13 | 23 | **37 (+24 New)** | Fully Enriched |
| **Unique Identifiers** | 50 (`Notice_ID`) | 35 (`API_Record_ID`) | **50 (`Notice_ID`)** | 0 Duplicate Keys |
| **Missing Values (Cells)**| 0 | 0 | **0** | Imputed / Clean |
| **Duplicate Records** | 0 | 0 | **0** | Clean |
| **Records Lost** | N/A | N/A | **0 (0.0%)** | Zero Loss |

---

## 📈 Mandatory Visualizations (Part E)

| Visualization Type | File Name | Key Finding / Insight |
|---|---|---|
| **1. Distribution Plot** | `screenshots/07_eda_univariate_distribution.png` | Normal distribution of max temperatures (Mean = 30.5°C) and bimodal fee distribution. |
| **2. Grouped Boxplot** | `screenshots/08_eda_univariate_boxplot.png` | AQI dispersion across campuses against EPA standards (Moderate urban ambient air). |
| **3. Bivariate Relationship 1** | `screenshots/09_eda_bivariate_weather_vs_fee.png` | High-stakes admission fees (>₹60k) coincide with high daytime heat exposure. |
| **4. Bivariate Relationship 2** | `screenshots/10_eda_bivariate_aqi_vs_category.png` | Admission & Interview categories exhibit higher ambient AQI (108.5) than exams. |
| **5. Correlation Heatmap** | `screenshots/11_eda_multivariate_correlation_heatmap.png` | Strong correlation between PM2.5 and US AQI ($r = 0.94$); negative between rain & temp. |
| **6. Fused Insight Plot** | `screenshots/12_eda_fused_insight_travel_advisory.png` | Multi-variable Campus Travel Advisory Index vs notice reporting urgency window. |

---

## 🔬 LLM Evaluation & Before-After Comparison (Part I & J)

| Evaluation Parameter | Before API Fusion (Baseline) | After API Fusion (Enhanced RAG) | Measured Benefit |
|---|---|---|---|
| **Questions Tested** | 10 Questions | 10 Questions | Standardized Benchmark |
| **Correct Answers** | 5 / 10 (50.0%) | **10 / 10 (100.0%)** | **+50.0% Absolute Accuracy Gain** |
| **Out-of-Domain Failures** | 5 / 10 (50.0%) | **0 / 10 (0.0%)** | Complete elimination of failures |
| **Completeness** | Document Text Only | **Document + Live Real-Time Context** | Multi-variable reasoning |
| **Hallucination Rate** | ~40% on external queries | **0.0% (Grounded in Vector Store)** | Verified Grounding |
| **Average Latency** | ~1,200 ms | ~1,850 ms | Fast inference with enriched prompt |

---

## 🚀 Quickstart & Installation

### 1. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/rajc01/NoticeSenseAI.git
cd NoticeSenseAI
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Linux / macOS
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the project root:
```ini
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Run Data Collection, Fusion & Evaluation
```bash
python src/generate_datasets.py        # Harvests API data & creates datasets
python src/data_cleaning.py            # Cleans & normalizes datasets
python src/data_fusion.py              # Executes Left Join fusion & logs validation
python src/generate_visualizations.py  # Generates 6 mandatory publication charts
python src/llm_rag.py                  # Builds Chroma vector DB & runs 10-query benchmark
python report/generate_pdf_report.py   # Compiles formal report/project_report.pdf
```

### 5. Launch Interactive Applications
* **Streamlit Web Application:**
  ```bash
  streamlit run app.py
  ```
* **FastAPI REST Server:**
  ```bash
  uvicorn api:app --reload --port 8000
  ```

---

## 👨‍💻 Author & Academic Information

* **Author:** Rajasee Kumbhar
* **Program:** Master of Computer Applications (MCA)
* **Department:** P.G. Department of Computer Science
* **Institution:** SNDT Women's University, Mumbai, Maharashtra, India
* **Course:** Large Language Models (LLMs) & Retrieval-Augmented Generation (RAG)
* **Date:** August 31, 2026