# 🌿 NutriCare AI

### An Intelligent Multilingual AI-Powered Nutrition & Diet Assistant for Cancer Patients using RAG and LLMs

> **Supporting better nutrition, better recovery, better lives.**

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)](https://streamlit.io/)
[![FAISS](https://img.shields.io/badge/Vector%20DB-FAISS-orange)](https://faiss.ai/)
[![LLM](https://img.shields.io/badge/LLM-Llama%203.3%2070B-purple)](https://www.llama.com/)
[![License](https://img.shields.io/badge/Project-Academic%20Prototype-green)](#)



**NutriCare AI** is a multimodal, multilingual AI-powered nutrition assistant designed to provide evidence-based dietary guidance for cancer patients, caregivers, and healthcare-support contexts.

The application combines **Retrieval-Augmented Generation (RAG)**, **semantic search**, **FAISS vector retrieval**, **LLM-based response generation**, **multilingual translation**, **text-to-speech**, nutrition databases, and external APIs through an interactive **Streamlit** interface.

---

## 🌐 Live Demo

🚀 **Try NutriCare AI:**
**https://nutricare-ai-llm.streamlit.app/**

> The live application may have limited functionality depending on API availability and deployment resources.
## 📸 Dashboard

![NutriCare AI Dashboard](images/dashboard.png)


---

## ✨ Key Features

### 💬 Medical Chat

Ask nutrition-related questions and receive context-aware responses based on the project's curated medical knowledge base.

### 🩺 Symptom Diet Assistant

Provides dietary guidance for treatment-related symptoms such as:

* Nausea
* Constipation
* Loss of appetite
* Taste changes
* Mouth sores
* Fatigue
* Dehydration

### 💉 Treatment Diet Assistant

Provides nutrition guidance based on treatment context, including:

* Chemotherapy
* Radiation therapy
* Surgery
* Recovery

### 🍽️ Personalized Meal Planner

Generates meal plans based on user-provided information such as:

* Age
* Gender
* Dietary preference
* Treatment
* Symptoms
* Cuisine
* Number of meals

### 🥘 AI Recipe Generator

Generates recipes based on available ingredients and provides nutritional information and cooking instructions.

Recipe-related video recommendations can also be obtained using the YouTube Data API.

### 🥦 Nutrient Lookup

Search nutritional information for **2,110+ Indian foods** using the project's nutrition database.

### 📊 Food Comparison

Compare two foods based on nutrients such as:

* Energy
* Protein
* Fat
* Carbohydrates
* Fiber
* Calcium
* Iron

### 🌿 Ayurvedic Remedies

Allows users to search traditional Ayurvedic resources and upload relevant PDF documents for retrieval-based querying.

### 🗂️ Chat History

Conversation history is stored using SQLite and can be viewed through a conversational interface.

### 🌐 Multilingual Support

Supports:

* 🇬🇧 English
* 🇮🇳 Hindi
* 🇮🇳 Marathi

Translation is handled using Google Translate integration.

### 🔊 Text-to-Speech

Responses can be converted to speech using **gTTS** and played through the application.

---

# 🧠 How NutriCare AI Works

NutriCare AI follows a Retrieval-Augmented Generation pipeline.

```text
                User Question
                     │
                     ▼
             Language Detection
                     │
                     ▼
             Query Processing
                     │
                     ▼
        Sentence Transformer Model
          all-MiniLM-L6-v2
                     │
                     ▼
              FAISS Search
             Top-K Retrieval
                     │
                     ▼
          Metadata Filtering
           Module-specific
                     │
                     ▼
             Context Building
                     │
                     ▼
            Prompt Construction
       Context + History + Query
                     │
                     ▼
          Llama 3.3 70B via Groq
                     │
                     ▼
           Generated Response
                     │
              ┌──────┴──────┐
              ▼             ▼
        Translation       Source
              │         Attribution
              ▼
          Final Answer
              │
       ┌──────┴────────┐
       ▼               ▼
   Text Display      Text-to-Speech
```

---

# 📚 Knowledge Base & Datasets

## 🏥 Medical Knowledge Base

The project contains a curated medical knowledge base covering topics such as:

* Cancer nutrition
* Treatment-based nutrition
* Symptom management
* Nutrients
* Food safety
* Meal planning
* Recipe guidelines
* FAQs
* Medical glossary

The documents are converted into chunks and indexed using FAISS for semantic retrieval.

**Current scale:**

* 80+ curated medical documents
* 1,406 indexed chunks
* 500-character chunk size
* 50-character overlap
* Metadata attached to each chunk

Sources include reputable organisations such as:

* National Cancer Institute (NCI)
* American Cancer Society (ACS)
* World Health Organization (WHO)
* Mayo Clinic
* ICMR
* National Institute of Nutrition (NIN)

---

## 🥗 Indian Food Nutrition Database

The project includes a CSV-based Indian food nutrition database containing **2,110+ food items**.

Example nutritional attributes include:

* Energy
* Protein
* Fat
* Carbohydrates
* Fiber
* Calcium
* Iron
* Vitamins
* Other nutritional values

This database powers the **Nutrient Lookup** and **Food Comparison** modules.

---

## 🍛 Recipe Database

The project contains **100+ Indian recipes** with information such as:

* Recipe name
* Cuisine
* Ingredients
* Cooking instructions
* Cooking time
* Calories
* Protein
* Carbohydrates

---

# 🛠️ Technology Stack

| Category             | Technology                         |
| -------------------- | ---------------------------------- |
| Programming Language | Python                             |
| Frontend             | Streamlit                          |
| LLM                  | Llama 3.3 70B via Groq             |
| Embeddings           | Sentence Transformers              |
| Embedding Model      | all-MiniLM-L6-v2                   |
| Vector Database      | FAISS                              |
| Translation          | Google Translate / deep-translator |
| Text-to-Speech       | gTTS + pygame                      |
| Image Understanding  | CLIP                               |
| Database             | SQLite                             |
| PDF Processing       | PyPDF2                             |
| PDF Generation       | ReportLab                          |
| Data Processing      | Pandas                             |
| Visualization        | Altair                             |
| Recipe Videos        | YouTube Data API                   |
| Nutrition API        | Spoonacular                        |
| Book Search          | Google Custom Search               |

---

# 🔌 External APIs

NutriCare AI integrates multiple external services:

### 1. Groq

Used for LLM-based response generation.

### 2. Google Translate

Used for multilingual response translation.

### 3. YouTube Data API

Used to search for recipe-related videos.

### 4. Spoonacular API

Used to obtain additional nutrition and food information.

### 5. Google Custom Search API

Used for searching Ayurvedic book and resource information.

> API keys are stored locally using environment variables and are **not included in the repository**.

---

# 🚀 Quick Start

## 1. Clone the Repository

```bash
git clone https://github.com/DimpalTamta/NutriCare-AI.git
cd NutriCare-AI
```

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure API Keys

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key
YOUTUBE_API_KEY=your_youtube_api_key
SPOONACULAR_API_KEY=your_spoonacular_api_key
GOOGLE_CUSTOM_SEARCH_API_KEY=your_google_custom_search_api_key
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_search_engine_id
```

**Never commit the `.env` file to GitHub.**

The repository should contain a `.gitignore` entry such as:

```gitignore
.env
*.db
__pycache__/
.venv/
venv/
```

---

# 📦 Build the FAISS Index

If the FAISS index is not already included in the repository, build it using the project's indexing script.

For example:

```bash
python build_index.py
```

> Use the actual index-building script/file name present in this repository. Avoid copying a command here that does not exactly match the current project structure.

The resulting index contains the embedded knowledge-base chunks used during retrieval.

---

# ▶️ Run the Application

```bash
streamlit run app.py
```

The application will open in your browser.

Default local address:

```text
http://localhost:8501
```

---

# 📁 Project Structure

```text
NutriCare-AI/
│
├── app.py
│
├── rag/
│   ├── load_documents.py
│   ├── chunking.py
│   ├── vector_store.py
│   └── ...
│
├── llm/
│   └── ...
│
├── memory/
│   └── ...
│
├── voice/
│   └── ...
│
├── nutrition/
│   └── ...
│
├── recipe/
│   └── ...
│
├── utils/
│   └── ...
│
├── knowledge_base/
│   └── ...
│
├── data/
│   ├── indian_food_database.csv
│   └── recipes.csv
│
├── requirements.txt
├── .gitignore
└── README.md
```

> Adjust this tree to exactly match your repository. Do not list folders that do not actually exist.

---

# 📊 RAG Configuration

| Component         | Configuration       |
| ----------------- | ------------------- |
| Embedding Model   | all-MiniLM-L6-v2    |
| Vector Database   | FAISS               |
| Vector Dimension  | 384                 |
| Chunk Size        | 500 characters      |
| Chunk Overlap     | 50 characters       |
| Retrieved Results | Top 5               |
| Retrieval Method  | Semantic Similarity |
| Filtering         | Metadata-based      |
| Generation Model  | Llama 3.3 70B       |

---

# 🧩 Application Modules

```text
NutriCare AI
│
├── Medical Chat
├── Symptom Diet Assistant
├── Treatment Diet Assistant
├── Personalized Meal Planner
├── AI Recipe Generator
├── Nutrient Lookup
├── Food Comparison
├── Ayurvedic Remedies
├── Chat History
└── About Us
```

---

# 📸 Screenshots

Add screenshots of the **actual running application** here.

Recommended screenshots:

| Module              | Screenshot                     |
| ------------------- | ------------------------------ |
| Dashboard           | `screenshots/dashboard.png`    |
| Medical Chat        | `screenshots/medical-chat.png` |
| Symptom Assistant   | `screenshots/symptom.png`      |
| Treatment Assistant | `screenshots/treatment.png`    |
| Meal Planner        | `screenshots/meal-planner.png` |
| Recipe Generator    | `screenshots/recipe.png`       |
| Nutrient Lookup     | `screenshots/nutrient.png`     |
| Food Comparison     | `screenshots/comparison.png`   |
| Ayurvedic Remedies  | `screenshots/ayurvedic.png`    |
| Chat History        | `screenshots/history.png`      |

Example:

```markdown
![NutriCare AI Dashboard](screenshots/dashboard.png)
```

---

# 🔐 Security

API credentials are loaded through environment variables.

Sensitive files such as:

```text
.env
*.db
```

should not be committed to the repository.

Before publishing the repository, verify that no API keys or other credentials exist in:

* Source code
* Git history
* `.env` files
* Configuration files
* Notebook outputs

---

# ⚠️ Medical Disclaimer

NutriCare AI is an **academic AI project and educational prototype**.

The information provided by the application is not a substitute for professional medical diagnosis, treatment, or personalised advice from a qualified oncologist, registered dietitian, or other healthcare professional.

Patients should consult their healthcare provider before making significant dietary or treatment-related decisions.

---

# 🎓 Academic Information

**Project:** NutriCare AI

**Course:** Large Language Models (LLM)

**Programme:** MCA – Semester III

**Department:** P.G. Department of Computer Science

**University:** SNDT Women's University

**Academic Year:** 2026–27

**Student:** Dimpal Tamta

**Roll No.:** MC2561

**Faculty:** Sarita Chauhan

---

# 👨‍💻 Developer

**Dimpal Tamta**

MCA Student | AI • Machine Learning • Data Science

GitHub: **[@DimpalTamta](https://github.com/DimpalTamta)**

---

# 🙏 Acknowledgements

This project uses information and resources from reputable organisations and datasets, including:

* National Cancer Institute (NCI)
* American Cancer Society (ACS)
* World Health Organization (WHO)
* Mayo Clinic
* Indian Council of Medical Research (ICMR)
* National Institute of Nutrition (NIN)

The project also uses open-source technologies and libraries including Streamlit, FAISS, Sentence Transformers, PyTorch, Pandas, and related Python packages.

---

# 📌 Project Status

**Status:** Completed Academic Prototype

NutriCare AI demonstrates the integration of:

* Retrieval-Augmented Generation
* Large Language Models
* Semantic Search
* Vector Databases
* Multilingual AI
* Nutrition Data Processing
* Voice Interaction
* External APIs
* Persistent Chat History
* Streamlit Application Development

---

## 📜 License

This project was developed for academic and educational purposes.


---



<h1 align="center">🥗 API Fused Dataset Analytics – Food, Nutrition &amp; Production Dashboard</h1>

<p align="center">
  An interactive 6-page Streamlit dashboard that shows <b>what is in our foods</b>,
  <b>how healthy and processed they are</b>, and <b>where they are produced in the world and in India</b>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Streamlit-dashboard-ff4b4b" alt="Streamlit">
  <img src="https://img.shields.io/badge/Plotly-interactive%20charts-3f4f75" alt="Plotly">
  <img src="https://img.shields.io/badge/Data-API%20Fused%20Dataset-2e7d32" alt="API Fused Dataset">
</p>

---

## Contents

- [About Project](#about-project)
- [Highlights](#highlights)
- [Pages, one by one](#pages-one-by-one)
- [Quick start](#quick-start)
- [How the data is handled](#how-the-data-is-handled)
- [Themes and filters](#themes-and-filters)
- [Project structure](#project-structure)
- [Known limitations](#known-limitations)
- [Data source](#data-source)

---

## About Project

`API_Fusion_Dataset.csv` combines several food data sources into one table of
**8,779 foods × 26 columns**: nutrition values per 100 g, Nutri-Score, NOVA processing group,
global and Indian production, Hindi and Marathi names, food photos and a cancer-related classification.

This dashboard turns that table into a clear story that anyone can follow:

1. **What** is in the food? (calories, protein, carbs, fat, fibre, minerals, vitamin C)
2. **How good and how processed is it?** (Nutri-Score A–E, NOVA groups 1–4)
3. **Where is it grown?** (top producing countries and Indian states on maps)
4. **What can I download?** (searchable data explorer, CSV / Excel export)

Everything is calculated from the file. **No data is invented.**

## Highlights

- **6 linked pages** with one shared filter bar (food name, Hindi/Marathi name, Nutri-Score, NOVA, cancer risk, support category, country, state).
- **Selected Food Profile** with photo, Hindi/Marathi names, nutrients, Nutri-Score, NOVA and classification.
- **Interactive World and India maps** that zoom to the top-3 producers of the selected food.
- **Top navigation bar, no sidebar**, so the full screen is used for charts.
- **8 colour themes** that change every chart and card.
- **Missing values are never turned into 0**; duplicates are reported, not removed.
- **Statistics page** with correlation, z-score box plot, outliers, validation report and export.
- **CSV and Excel download** of the filtered data on every page.

---

## Pages, one by one

### 1 · Main Dashboard

<!-- Main dashboard screenshots: images/222.png → images/888.png (one full page, split in 7 parts, top to bottom) -->
<p align="center">
  <img src="images/222.png" alt="Main Dashboard – part 1" width="100%">
  <img src="images/333.png" alt="Main Dashboard – part 2" width="100%">
  <img src="images/444.png" alt="Main Dashboard – part 3" width="100%">
  <img src="images/555.png" alt="Main Dashboard – part 4" width="100%">
  <img src="images/666.png" alt="Main Dashboard – part 5" width="100%">
  <img src="images/777.png" alt="Main Dashboard – part 6" width="100%">
  <img src="images/888.png" alt="Main Dashboard – part 7" width="100%">
</p>

<p align="center"><i>Page 1 – Main Dashboard: KPIs, food profile, Nutri-Score, NOVA, production charts, maps, nutrient charts and the dataset explorer in one screen.</i></p>

The one-page summary of the whole dataset. It answers *"what is in this dataset?"* in about ten seconds.

| Visual | What it tells you |
|---|---|
| **KPI cards** | Total foods, countries covered, Indian states covered, NOVA groups |
| **Selected Food Profile** | Photo (from `Image URL`), Hindi and Marathi names, nutrients, Nutri-Score, NOVA group and cancer classification of one chosen food |
| **Nutri-Score Distribution** | Donut chart: count and % of foods in each grade A–E |
| **Food Distribution by NOVA Group** | Treemap: bigger tile = more foods in that processing group |
| **Top Producing Countries / Indian States** | Bar charts with names on the bars, based on each food's top-3 producers |
| **Interactive Production Map** | Switch between 🌍 World and 🇮🇳 India; the map zooms to the top-3 producers of the selected food |
| **Nutrient Composition** | Choose a nutrient and see the top foods plus the selected food |
| **Calories vs Protein** | Scatter plot, point size = fibre, ★ = selected food |
| **Cancer Classification** | Stacked bar: Risk Group × Cancer Patient Support Category |
| **Global / Indian Production** | Production in tonnes (log scale), selected food in red |
| **API Fused Dataset Explorer** | All columns, search, sort, CSV / Excel download |

### 2 · Nutrition

Compares the nutrients of foods and food groups.

- **Macronutrient comparison** – Protein, Carbs, Fat, Fibre by Nutri-Score, NOVA, Risk Group or Support Category.
- **Micronutrient comparison** – Calcium, Iron, Potassium, Sodium, Vitamin C (log scale).
- **Calories vs Protein scatter** – with up to 4 comparison foods.
- **Food comparison table** and **nutrient statistics**.
- **Searchable food table** with Hindi and Marathi names.

### 3 · Food Quality

Shows how healthy and how processed the foods are.

- **Nutri-Score pie** (grades A–E, "-" = not scored).
- **NOVA group treemap** (groups 1–4).
- **Nutri-Score vs NOVA heatmap** – number of foods for each combination.
- **Counts and percentage tables** with average nutrients per Nutri-Score grade.

### 4 · Cancer Classification

Shows the dataset's own cancer-related classifications.

- **Cancer Risk Classification** – top 15 categories.
- **Cancer Patient Support Category** – donut chart.
- **Nutrition across classifications** – mean nutrients per group.
- **Category-wise food list** – filter by support category and risk group.

> These are the dataset's own classifications, **not medical advice**.

### 5 · Production &amp; Maps

Shows **where** foods are produced.

- **Interactive World map** and **India map** – show the selected food's top producers, or the number of foods per place.
- **Top producing countries / states** (choose Top N).
- **Global vs Indian production** (log scale) and **India's share** in global production.
- **Production table** sorted by global production.

### 6 · Statistics &amp; Data

The technical page for checking the data.

| Tab | What it shows |
|---|---|
| **Charts** | Nutrient correlation heatmap, z-score box plot, missing values chart |
| **Descriptive statistics** | Count, mean, std, min, max for all nutrients |
| **Dataset summary** | Column names and data types |
| **Complete dataset** | Searchable full table |
| **Duplicate records** | Fully duplicated rows and repeated food names |
| **Outliers** | Values beyond a chosen |z| threshold |
| **Validation report** | Data-quality checks and missing-value table |
| **Export** | Download CSV, Excel or statistics CSV |

---

## Quick start

```bash
# 1. get the code
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>/API_Fused_Dataset_Analytics

# 2. create a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. install the requirements
pip install -r requirements.txt

# 4. start the dashboard
streamlit run app.py
```

Streamlit opens the dashboard in your browser (normally <http://localhost:8501>).
The data file is already included in `data/`, so no extra download is needed.

## How the data is handled

- Every number is calculated from `data/API_Fusion_Dataset.csv`; **nothing is invented**.
- **Missing nutrient values stay blank**, they are never replaced with 0.
- **Duplicates are reported, not removed.**
- `Cancer_Risk_Classification` has about 1,400 different text values, so charts group it by the text before " - "
  (*Risk factor / Protective / Neutral / Limit or avoid*). The full text is shown in the food profile and tables.
- Maps colour the **top-3 producers** (Rank 1–3) of the selected food. The Production page colours every place by number of foods.
  "Unknown" and "Not produced in India" are left off the maps.
- The box plot uses **z-scores**, so nutrients with different units share one axis. The micronutrient chart uses a **log axis**.

## Themes and filters

- Choose from **8 colour themes** in the header.
- The horizontal **filter bar** (Food / Hindi / Marathi name, Nutri-Score, NOVA, cancer risk, support category, country, state) has **Apply** and **Clear** buttons.
- Filters, themes, the data-quality **Info** panel and the **CSV download** button work on every page.

## Project structure

```text
API_Fused_Dataset_Analytics/
├── app.py                          # main dashboard (page 1)
├── requirements.txt
├── .streamlit/config.toml          # hides default sidebar navigation
├── pages/
│   ├── 1_Nutrition_Analysis.py
│   ├── 2_Food_Quality_Processing.py
│   ├── 3_Cancer_Classification.py
│   ├── 4_Production_Geographic.py
│   └── 5_Statistics_Data_Explorer.py
├── modules/
│   ├── theme.py                    # 8 colour themes
│   ├── data.py                     # loading, parsing, filtering, CSV/Excel export
│   ├── stats.py                    # descriptive stats, missing values, duplicates, quality report
│   ├── images.py                   # food photo from Image URL + placeholder
│   ├── charts.py                   # main-dashboard charts and both maps
│   ├── pagecharts.py               # charts for the supporting pages
│   ├── shell.py                    # header, theme, navigation, global filters
│   └── ui.py                       # CSS and HTML snippets
├── data/
│   ├── API_Fusion_Dataset.csv      # the fused dataset
│   └── india_states.geojson        # India state boundaries
└── images/                         # screenshots used in this README
```

## Known limitations

- The bundled `india_states.geojson` is an older, simplified file **without Telangana** (it is drawn inside Andhra Pradesh).
- Food photos load in your browser from the `Image URL` column; a placeholder is shown if a link is missing or broken.
- The dataset has no per-country or per-state tonnage, so maps highlight places by **rank or food count**, not by amount.
- Cancer-related columns are dataset classifications and are **not medically verified**.

## Data source

`API_Fusion_Dataset.csv` – a fused dataset of food nutrition, Nutri-Score, NOVA processing group,
global and Indian crop production, and cancer-related food classification.
