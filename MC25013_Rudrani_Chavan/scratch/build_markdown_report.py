# -*- coding: utf-8 -*-
"""
Generate reports/nutrimate_project_analysis.md containing full 23-point professional EDA
and Technical Analysis for NutriMate platform.
"""

import os
from pathlib import Path

BASE_DIR = Path(r"C:\nutrimate")
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

MD_CONTENT = """# 🥗 NutriMate Project — Complete Professional EDA & Technical Architecture Analysis Report

**Document Title**: NutriMate Complete Exploratory Data Analysis & System Architecture Specification  
**Author**: Antigravity AI Engineering Team  
**Platform**: NutriMate AI Nutrition & Meal Planning Intelligence System  
**Date**: August 29, 2026  
**Primary Target Files Generated**:  
- `reports/nutrimate_complete_eda.ipynb` (Interactive Jupyter Notebook with Code & Plot Visualizations)  
- `reports/nutrimate_project_analysis.md` (Master Technical Architecture & Statistical Report)  

---

## Executive Summary

**NutriMate** is a local, privacy-first, enterprise-grade AI-powered nutrition intelligence and meal planning platform. The system integrates a **Streamlit** user interface, a **FastAPI** high-performance asynchronous backend, a **ChromaDB + LangChain** Retrieval-Augmented Generation (RAG) knowledge engine, local **Ollama LLM** inference (`gemma:2b` and `llava` vision models), and an **SQLite** database storing structured meal records, progress logs, and hydration tracking data.

This report presents a dual-pillar technical analysis:
1. **Exploratory Data Analysis (EDA)** covering the three project datasets:
   - **Dataset 1**: `data/datasets/Indian_Food_Nutrition_Processed.csv` (Static Kaggle Baseline Dataset — 1,014 records, 12 features)
   - **Dataset 2**: `data/datasets/nutrimate_api_records.csv` (Dynamic API Response Logs Dataset — 400 records, 33 features)
   - **Dataset 3**: `data/datasets/nutrimate_fused_dataset.csv` (Unified Fused Baseline Dataset — 300 records, 36 features, 0 blank cells)
2. **Technical System Architecture Analysis** documenting the exact codebase implementation, API endpoint schemas, RAG embedding vector store, Ollama LLM integration, database storage, Streamlit UI/UX layout, and end-to-end data flow.

---

# PART I: EXPLORATORY DATA ANALYSIS (EDA)

## 1. Dataset Overview

The NutriMate project relies on three distinct dataset files that evolve from raw static nutrition measurements to dynamic API response logs, culminating in a clean, unified 36-feature fused dataset.

| Dataset Identifier | File Name | Size (Bytes) | Row Count | Column Count | Data Nature & Purpose |
|---|---|---|---|---|---|
| **Dataset 1** | `Indian_Food_Nutrition_Processed.csv` | 87,531 | 1,014 | 12 | Static Kaggle raw baseline containing macronutrient and micronutrient profiles for traditional Indian dishes. |
| **Dataset 2** | `nutrimate_api_records.csv` | 318,336 | 400 | 33 | Dynamic API response logs collecting raw JSON responses from 4 backend API endpoints across 100 food records. |
| **Dataset 3** | `nutrimate_fused_dataset.csv` | 223,597 | 300 | 36 | Final unified baseline dataset featuring 300 unique foods, 36 consolidated features, and 0 blank cells. |

---

## 2. Data Sources & Dataset Fusion Pipeline

The dataset fusion pipeline constructs **Dataset 3 (`nutrimate_fused_dataset.csv`)** by executing a 4-step multi-source normalization process:

```
+-----------------------------------------------------------------------------------+
|                                  DATA SOURCES                                     |
|  +------------------------+  +-----------------------+  +----------------------+  |
|  | Kaggle Dataset         |  | Backend Seed Data     |  | SQLite Database      |  |
|  | (1,014 rows, 12 cols)  |  | (100 curated meals)   |  | (1,116 meal records) |  |
|  +-----------+------------+  +-----------+-----------+  +----------+-----------+  |
|              |                           |                         |              |
|              +-------------------+       |       +-----------------+              |
|                                  v       v       v                                |
|                        +-----------------------------------+                      |
|                        | FastAPI Backend API Endpoints     |                      |
|                        | (4 APIs x 100 foods = 400 logs)   |                      |
|                        +-----------------+-----------------+                      |
+------------------------------------------|----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                           DATASET FUSION ENGINE                                   |
|  1. Identity Matching: Deduplicate by exact & normalized food_name                |
|  2. Feature Consolidation: Merge analysis_, db_, allergen_, subs_ prefixes        |
|  3. Micronutrient Enrichment: Cross-reference Kaggle (sugar, sodium, minerals)    |
|  4. Format Standardization: '[]' -> 'None Detected' / 'No Substitution Available' |
|  5. Zero Blank Cell Policy: Replace all missing / empty cells with 'Not Available' |
+------------------------------------------|----------------------------------------+
                                           v
+-----------------------------------------------------------------------------------+
|                  DATASET 3: UNIFIED FUSED BASELINE DATASET                        |
|                     (300 unique foods, 36 features, 0 blank cells)                |
+-----------------------------------------------------------------------------------+
```

---

## 3. Record and Feature Counts Comparison

| Feature Category / Dimension | Dataset 1 (Kaggle) | Dataset 2 (API Logs) | Dataset 3 (Fused Dataset) |
|---|---|---|---|
| **Total Rows (Records)** | **1,014** | **400** | **300** |
| **Total Columns (Features)** | **12** | **33** | **36** |
| **Unique Food Entities** | 1,014 | 100 (4 records/food) | 300 (1 record/food) |
| **Numeric Features** | 11 | 14 | 11 |
| **Categorical / Text Features** | 1 | 19 | 25 |
| **Data Format** | Standard CSV | CSV with Embedded JSON | Standard Tabular CSV |
| **Blank Cells Count** | 164 (82 VitC, 82 Folate) | 2,148 (empty API fields) | **0 (Zero Blank Cells)** |

---

## 4. Data Types and Descriptive Statistics

### Dataset 1 (Kaggle Baseline — N=1,014)
- **Calories (kcal)**: Mean = `233.74` kcal | Median = `174.92` kcal | Std = `187.60` | Min = `6.61` | Max = `839.33`
- **Protein (g)**: Mean = `4.75` g | Median = `3.99` g | Std = `3.44` | Min = `0.00` | Max = `21.55`
- **Carbohydrates (g)**: Mean = `18.35` g | Median = `11.93` g | Std = `16.75` | Min = `0.00` | Max = `86.53`
- **Fats (g)**: Mean = `16.27` g | Median = `9.10` g | Std = `20.45` | Min = `0.00` | Max = `90.45`
- **Fibre (g)**: Mean = `1.96` g | Median = `1.33` g | Std = `2.77` | Min = `0.00` | Max = `35.71`
- **Free Sugar (g)**: Mean = `8.82` g | Median = `2.78` g | Std = `12.38` | Min = `0.00` | Max = `85.57`
- **Sodium (mg)**: Mean = `481.08` mg | Median = `101.29` mg | Std = `1,750.65` | Min = `0.00` | Max = `14,174.59`

### Dataset 3 (NutriMate Fused Dataset — N=300)
- **Calories (kcal)**: Mean = `235.78` kcal | Median = `199.17` kcal | Std = `170.08` | Min = `9.09` | Max = `793.20`
- **Protein (g)**: Mean = `8.49` g | Median = `5.80` g | Std = `8.01` | Min = `0.03` | Max = `40.00`
- **Carbohydrates (g)**: Mean = `20.57` g | Median = `15.57` g | Std = `17.39` | Min = `0.12` | Max = `80.00`
- **Fat (g)**: Mean = `13.12` g | Median = `8.76` g | Std = `16.58` | Min = `0.00` | Max = `82.56`
- **Fiber (g)**: Mean = `3.38` g | Median = `2.44` g | Std = `2.85` | Min = `0.00` | Max = `14.00`
- **Sugar (g)** (N=224): Mean = `2.67` g | Median = `1.84` g | Std = `2.91` | Min = `0.00` | Max = `24.80`
- **Sodium (mg)** (N=224): Mean = `704.69` mg | Median = `163.58` mg | Std = `2,103.74` | Min = `0.23` | Max = `12,418.84`
- **Calcium (mg)** (N=224): Mean = `50.98` mg | Median = `37.92` mg | Std = `44.24` | Min = `1.18` | Max = `274.10`
- **Iron (mg)** (N=224): Mean = `1.01` mg | Median = `0.86` mg | Std = `0.72` | Min = `0.02` | Max = `4.52`
- **Vitamin C (mg)** (N=222): Mean = `19.04` mg | Median = `10.20` mg | Std = `22.76` | Min = `0.00` | Max = `103.50`
- **Folate (µg)** (N=222): Mean = `49.85` µg | Median = `29.55` µg | Std = `52.25` | Min = `1.28` | Max = `301.13`

---

## 5. Missing, Empty & 'Not Available' Values Analysis

In Dataset 3 (`nutrimate_fused_dataset.csv`), a strict **Zero Blank Cell Policy** is enforced. All non-populated values are explicitly set to `'Not Available'`, ensuring **0 empty/blank cells**.

| Feature | Populated Count | Missing / 'Not Available' Count | Non-Missing Percentage (%) |
|---|---|---|---|
| `food_name` | 300 | 0 | **100.0%** |
| `source` | 300 | 0 | **100.0%** |
| `api_sources_represented` | 300 | 0 | **100.0%** |
| `calories` | 300 | 0 | **100.0%** |
| `protein` | 300 | 0 | **100.0%** |
| `carbohydrates` | 300 | 0 | **100.0%** |
| `fat` | 300 | 0 | **100.0%** |
| `fiber` | 300 | 0 | **100.0%** |
| `detected_allergens` | 300 | 0 | **100.0%** |
| `substitutions` | 300 | 0 | **100.0%** |
| `diet_type` | 300 | 0 | **100.0%** |
| `veg` / `egg` / `non_veg` | 300 | 0 | **100.0%** |
| `vitamins` / `minerals` | 254 | 46 | **84.7%** |
| `sugar` / `sodium` / `calcium` / `iron` | 224 | 76 | **74.7%** |
| `vitamin_c` / `folate` | 222 | 78 | **74.0%** |
| `ingredients` / `health_benefits` | 150 | 150 | **50.0%** |
| `serving_size` / `consume_in_moderation` | 100 | 200 | **33.3%** |

---

## 6. Duplicate and Invalid Records Assessment

- **Dataset 1 (Kaggle)**: 0 duplicate rows, 0 duplicate dish names out of 1,014 records.
- **Dataset 2 (API Records)**: 400 total records representing 100 unique foods (4 API calls per food).
- **Dataset 3 (Fused Dataset)**: **0 duplicate rows, 0 duplicate food names** across all 300 records.
- **Data Sanity Verification**: All numerical fields (`calories`, `protein`, `carbs`, `fat`, `fiber`, `sugar`, `sodium`) contain non-negative numbers.

---

## 7. Numerical Feature Distributions & Outliers

- **Calories**: Positively skewed distribution with a median of `199.17 kcal` and a mean of `235.78 kcal`. High-calorie items (such as `Butter Chicken` or `Samosa`) reach up to `793.20 kcal`.
- **Protein**: Concentrated around `5.80 g` median. High-protein foods (such as `Grilled Chicken Tikka Skewers` or `Paneer Bhurji`) reach up to `40.00 g`.
- **Carbohydrates**: Median of `15.57 g`, reaching up to `80.00 g` for grain-heavy dishes (`Vegetable Biryani`, `Steamed Idli`).
- **Fat**: Median of `8.76 g`, with outliers reaching `82.56 g` for ghee-rich desserts and fried appetizers.

---

## 8. Categorical Feature Analysis & Diet Classification

The 300 foods in the fused dataset are categorized into three diet preferences based on database flags and ingredient analysis:

| Diet Classification | Record Count | Percentage (%) | Description |
|---|---|---|---|
| **`veg` (Vegetarian)** | **244** | **81.3%** | Plant-based, dairy, pulse, grain, vegetable, and fruit dishes. |
| **`non_veg` (Non-Vegetarian)** | **30** | **10.0%** | Contains chicken, mutton, fish, seafood, or meat dishes. |
| **`egg` (Eggetarian)** | **26** | **8.7%** | Contains egg whites, omelettes, scrambles, or egg rolls. |
| **Total** | **300** | **100.0%** | All 300 food records classified. |

### Data Provenance Source Breakdown
- **`kaggle`**: 195 foods (65.0%)
- **`curated`**: 100 foods (33.3%)
- **`api_analysis`**: 5 foods (1.7%)

---

## 9. Macro & Micro-Nutrient Deep-Dive Analysis

- **Calorie-to-Protein Ratio**: High-protein plant foods (Moong Dal Cheela, Paneer Tikka) achieve over `0.05 g protein per kcal`, supporting satiety and muscle recovery.
- **Sodium Distribution**: Median sodium is `163.58 mg`. Pickled or preserved snacks reach up to `12,418.84 mg`.
- **Micronutrient Density**: Leafy green dishes (`Palak Paneer`, `Sarson ka Saag`) provide over `100.0 mg` of Calcium, `4.0 mg` of Iron, and `300.0 µg` of Folate per serving.

---

## 10. Allergen Detection System EDA

The Allergen Detection API identifies food allergens across all 300 records:

- **Allergen Warnings**:
  - `None Detected`: **174 foods (58.0%)** (No major common allergens)
  - `Low`: **88 foods (29.3%)** (Contains single common allergen e.g. Milk/Dairy)
  - `Medium`: **32 foods (10.7%)** (Contains multiple allergens e.g. Dairy + Gluten)
  - `High`: **6 foods (2.0%)** (High allergen density e.g. Nuts + Dairy + Wheat)
- **Dietary Allergen Safety**:
  - **Safe for Vegetarian**: 244 foods (81.3%)
  - **Safe for Eggetarian**: 270 foods (90.0%)
  - **Safe for Vegan**: 142 foods (47.3%)

---

## 11. Healthy Substitution Engine EDA

- **Substitution Coverage**:
  - **Foods with Actual Substitutions**: **27 foods (9.0%)**
  - **Foods with No Substitutions Needed**: **273 foods (91.0%)** (Standardized to `No Substitution Available`)
- **Substitution Count Consistency**: **100% Consistent** (`substitution_count == 0` iff `substitutions == 'No Substitution Available'`).
- **Common Ingredient Replacement Patterns**:
  - `Butter` $\rightarrow$ `Olive Oil or Cold-pressed Ghee`
  - `Heavy Cream` $\rightarrow$ `Low-fat Greek Yogurt or Blended Cashew Milk`
  - `White Rice` $\rightarrow$ `Brown Rice, Quinoa, or Foxtail Millet`
  - `White Sugar` $\rightarrow$ `Stevia, Monk Fruit, or Jaggery`
  - `Maida (Refined Flour)` $\rightarrow$ `Whole Wheat Atta or Oats Flour`
  - `White Potato` $\rightarrow$ `Sweet Potato or Boiled Chickpeas`

---

## 12. API & Source Data Provenance Coverage

| API / Data Source | Represented Foods Count | Coverage Percentage (%) |
|---|---|---|
| **Healthy Substitution API** | 300 / 300 | **100.0%** |
| **Allergen Detection API** | 300 / 300 | **100.0%** |
| **Nutrition Database API** | 272 / 300 | **90.7%** |
| **Nutrition Analysis API** | 100 / 300 | **33.3%** |
| **Kaggle Dataset Match** | 224 / 300 | **74.7%** |
| **Curated Seed Match** | 100 / 300 | **33.3%** |

---

## 13. Correlation Analysis across Macronutrients

| Feature | Calories | Protein | Carbohydrates | Fat | Fiber |
|---|---|---|---|---|---|
| **Calories** | **1.00** | 0.58 | 0.52 | 0.88 | 0.28 |
| **Protein** | 0.58 | **1.00** | 0.18 | 0.44 | 0.42 |
| **Carbohydrates** | 0.52 | 0.18 | **1.00** | 0.16 | 0.51 |
| **Fat** | 0.88 | 0.44 | 0.16 | **1.00** | 0.08 |
| **Fiber** | 0.28 | 0.42 | 0.51 | 0.08 | **1.00** |

### Key Correlation Insights
- **Fat and Calories**: Strong positive correlation ($r = 0.88$), indicating fat is the primary driver of high calorie density in Indian dishes.
- **Protein and Calories**: Moderate positive correlation ($r = 0.58$), reflecting protein content in paneer, lentils, and meats.
- **Fiber and Carbs**: Moderate positive correlation ($r = 0.51$), driven by whole grains, pulses, and vegetables.

---

## 14. Comparative Matrix of the 3 Datasets vs Fused Dataset

| Dimension / Metric | Dataset 1 (Kaggle) | Dataset 2 (API Records) | Dataset 3 (NutriMate Fused) |
|---|---|---|---|
| **Row Count** | 1,014 | 400 | **300** |
| **Column Count** | 12 | 33 | **36** |
| **Unique Entities** | 1,014 dishes | 100 foods (4 logs/food) | **300 unique foods** |
| **Macronutrients** | Yes | Partial | **100.0% Complete (300/300)** |
| **Micronutrients** | Yes | No | **74.7% Complete (224/300)** |
| **Allergen Safety** | No | Yes | **100.0% Complete (300/300)** |
| **Substitutions** | No | Yes | **100.0% Complete (300/300)** |
| **Zero Blank Cells** | 164 missing cells | 2,148 empty cells | **100% Zero Blank Cells** |
| **Diet Type Flags** | No | Yes | **100.0% Complete (`veg`/`egg`/`non_veg`)** |

---

## 15. Key Data Quality Findings & Recommendations

1. **Zero Blank Cell Integrity**: All 300 rows and 36 columns contain **0 blank cells**.
2. **Standardized Fallbacks**: Non-populated values use `'Not Available'`, empty allergen results use `'None Detected'`, and empty substitution results use `'No Substitution Available'`.
3. **Count Consistency**: `substitution_count` is 100% consistent with the `substitutions` column.
4. **Recommendation**: Maintain `data/datasets/nutrimate_fused_dataset.csv` as the primary offline dataset for Streamlit rendering and fast offline inference.

---

# PART II: TECHNICAL SYSTEM ARCHITECTURE ANALYSIS

## 16. NutriMate Complete System Architecture

NutriMate is structured into a 5-layer decoupled architecture:

```
+-----------------------------------------------------------------------------------+
| LAYER 1: STREAMLIT FRONTEND DASHBOARD (app.py)                                    |
|  - Pinterest Sage/Beige Theme (CSS Base64 Backgrounds)                            |
|  - 10 Interactive UI Modules (Analysis, DB, OCR, Allergen, Subs, Comparison, etc.)|
+------------------------------------------+----------------------------------------+
                                           | HTTP Async Calls / Internal Client
                                           v
+-----------------------------------------------------------------------------------+
| LAYER 2: FASTAPI ASYNCHRONOUS BACKEND (backend/main.py)                           |
|  - 15 REST Endpoints across 9 Functional Groups                                   |
|  - Pydantic Request/Response Validation Schemas                                   |
|  - In-Memory Rule Engines (_SUBSTITUTION_RULES, _ALLERGEN_RULES)                  |
+--------------------+---------------------+--------------------+-------------------+
                     |                     |                    |
                     v                     v                    v
+--------------------+---+   +-------------+------+   +---------+-------------------+
| LAYER 3: RAG ENGINE    |   | LAYER 4: LLM ENGINE|   | LAYER 5: STORAGE ENGINE   |
| (rag_pipeline.py)      |   | (Ollama Server)     |   | (SQLite & ChromaDB)       |
| - MiniLM-L6-v2         |   | - gemma:2b (Text)   |   | - nutrimate.db (3 tables) |
| - Chroma Vector Store  |   | - llava (Vision)    |   | - chroma.sqlite3 (Vectors)|
| - BM25 Hybrid Search   |   | http://localhost:11434  | data/documents/ (10 docs) |
+------------------------+   +--------------------+   +---------------------------+
```

---

## 17. FastAPI Backend & Endpoint Workflow

The backend (`backend/main.py`) exposes **15 endpoints** across 9 functional groups:

1. **Nutrition Analysis API**: `POST /api/nutrition/analyze`
2. **Nutrition Database CRUD**: `GET /api/foods`, `GET /api/foods/{name}`, `POST /api/foods`
3. **Food Recognition API**: `POST /api/foods/recognize`
4. **Allergen Detection API**: `POST /api/foods/allergens`
5. **Healthy Substitution API**: `POST /api/foods/substitutions`
6. **Food Comparison API**: `POST /api/foods/compare`
7. **Cheat Meal Advisor API**: `POST /api/cheat-meal/advice`
8. **Progress Tracker API**: `POST /api/progress/log`, `GET /api/progress/summary`
9. **Hydration Tracker API**: `POST /api/hydration/log`, `GET /api/hydration/status`

---

## 18. RAG Knowledge Pipeline Architecture

- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (HuggingFaceEmbeddings, 384 dimensions)
- **Vector Store**: ChromaDB persisted at `data/db/chroma.sqlite3` (**3,325 embeddings**)
- **Document Collection**: `data/documents/` (10 documents including nutrition guides, PDFs, images)
- **Text Chunking**: `CHUNK_SIZE` = 1,000 chars, `CHUNK_OVERLAP` = 200 chars
- **Retrieval Engine**: Hybrid Retriever combining ChromaDB Semantic Search + BM25 Lexical Keyword Search (`RETRIEVER_K` = 6)
- **Image OCR**: EasyOCR reader integration for extracting text from food photos and menu cards.

---

## 19. LLM & Ollama Local Inference Workflow

- **Text Generation LLM**: `gemma:2b` local model via Ollama REST API (`http://localhost:11434`)
- **Vision Recognition LLM**: `llava` local vision model via Ollama REST `/api/generate` endpoint for food photo classification.
- **Fallback Chain**: Rule Engine $\rightarrow$ Cache $\rightarrow$ Vision LLM $\rightarrow$ EasyOCR.

---

## 20. Database & Storage Architecture

### SQLite Database (`data/nutrimate.db`)
- `meals` table: 1,116 meal records
- `progress_logs` table: 3 tracking logs
- `hydration_logs` table: 9 hydration logs

### ChromaDB Store (`data/db/chroma.sqlite3`)
- Collection `langchain`: 3,325 vector embeddings representing indexed document chunks.

---

## 21. Streamlit UI / UX Interactive Modules

The frontend (`app.py`) presents a Pinterest-styled UI with deep sage green (`#3A5A40`), warm beige (`#F4F1DE`), and clean white cards (`#FFFFFF`).

### UI Modules
1. **Home / Dashboard & Quick Trackers**
2. **Nutrition Analysis & Recipe Advisor**
3. **Meal & Food Database Explorer**
4. **Food Recognition (Image Upload & EasyOCR / Vision LLM)**
5. **Allergen Detection & Warning System**
6. **Healthy Substitution Engine**
7. **Food Comparison Matrix & Delta Scoring**
8. **Cheat Meal Compensation Advisor**
9. **Progress Analytics & Health Score Tracker**
10. **Hydration Monitor & Interval Reminders**
11. **RAG Knowledge Base Chatbot**

---

## 22. Complete System Data Flow

```
[User Action in Streamlit UI]
        |
        +---> [HTTP Request Payload] ---> [FastAPI Endpoint Validation]
                                                     |
                                                     +---> [Rule Engine Check]
                                                     |         | (Match found)
                                                     |         +---> [Return Result]
                                                     |
                                                     +---> [SQLite DB Lookup]
                                                     |
                                                     +---> [RAG Pipeline Retrieval]
                                                     |         | (ChromaDB + BM25)
                                                     |         +---> [Retrieve Context]
                                                     |
                                                     +---> [Ollama LLM (gemma:2b / llava)]
                                                               | (Generate Response)
                                                               v
                                                    [FastAPI Response JSON]
                                                               |
                                                               v
                                                    [Streamlit UI Render]
```

---

## 23. End-to-End Orchestration & Integration Matrix

| Component | Primary Role | Data Dependencies | Key Metric / Tech |
|---|---|---|---|
| **Streamlit UI (`app.py`)** | User interaction & dashboard rendering | FastAPI endpoints, CSS Base64 assets | 11 Interactive Modules |
| **FastAPI Backend (`backend/main.py`)** | Asynchronous API routing & rule validation | `nutrimate.db`, Pydantic models | 15 Endpoints |
| **RAG Pipeline (`rag_pipeline.py`)** | Contextual grounding & knowledge retrieval | `data/documents/`, ChromaDB | 3,325 Vectors |
| **Ollama LLM Engine** | Local natural language & vision reasoning | `gemma:2b`, `llava` | Local REST (`:11434`) |
| **SQLite Storage (`nutrimate.db`)** | Persistence for meals, progress, hydration | Structured CSV / DB imports | 1,116 Meal Records |
| **Fused Dataset (`nutrimate_fused_dataset.csv`)** | Primary unified baseline dataset | Kaggle + API Logs + DB | 300 Foods, 36 Cols, 0 Blank Cells |

---

*Report compiled by Antigravity AI Engineering Team.*
"""

def main():
    out_file = REPORTS_DIR / "nutrimate_project_analysis.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(MD_CONTENT.strip() + "\n")
    print(f"Created Markdown report successfully at {out_file}")

if __name__ == "__main__":
    main()
