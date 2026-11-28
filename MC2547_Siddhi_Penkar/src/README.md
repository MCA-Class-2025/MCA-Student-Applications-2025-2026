# 🐞 BugAssist AI
### AI-Powered Bug Analysis and Management Platform

A multi-source software bug intelligence platform powered by Retrieval-Augmented Generation (RAG), Data Fusion, Semantic Search, FAISS and Large Language Models.

BugAssist AI is an academic Streamlit application designed to help developers analyze software bugs, explore enriched bug datasets, identify possible root causes, recommend fixes and generate bug-management payloads for external development tools.

**MCA Final Year Project — RAG Architecture and Data Fusion Demonstration**

---

## Project Overview

Software bug information is often scattered across PDF reports, technical documentation, error logs and structured datasets. Analyzing these sources manually can be time-consuming and makes it difficult to identify recurring issues and understand their root causes.

BugAssist AI brings these capabilities together in one platform. It combines PDF-based semantic search with an enriched bug dataset to provide AI-assisted bug analysis and interactive data exploration.

The application uses Sentence-Transformers to generate semantic embeddings, FAISS for vector similarity search and Qwen2.5-1.5B-Instruct for generating structured AI responses.

The platform is organized into three main modules:

- **PDF RAG:** Upload bug reports and documentation, create a searchable knowledge base and receive AI-generated bug analysis.
- **Bug Data Explorer:** Explore the fused dataset through filters, statistics, detailed records and interactive visualizations.
- **Bug Management:** Generate GitHub Issue, Jira Ticket and Slack Alert payload previews and obtain AI-powered bug triage recommendations.

## Key Features

| Feature | Description |
|---|---|
| Multi-PDF Upload | Upload multiple bug reports, technical documents and PDF logs |
| Text Extraction | Extracts PDF content using PyMuPDF |
| Text Preprocessing | Cleans and normalizes extracted document text |
| Document Chunking | Divides documents into smaller overlapping text chunks |
| Semantic Embeddings | Uses all-MiniLM-L6-v2 from Sentence-Transformers |
| FAISS Vector Search | Retrieves relevant information using semantic similarity |
| Dataset Integration | Loads an enriched bug dataset from Excel or CSV |
| Dataset Indexing | Builds a FAISS index for searching structured bug records |
| AI Bug Analysis | Uses Qwen2.5-1.5B-Instruct to generate bug analysis |
| Root Cause Analysis | Provides possible explanations for software defects |
| Fix Recommendations | Generates suggested solutions based on retrieved evidence |
| Bug Data Explorer | Provides dataset filtering, searching and detailed bug information |
| Bug Analytics | Displays priority, risk and confidence-related visualizations when the required columns are available |
| GitHub Issue Payload | Generates a formatted GitHub issue draft |
| Jira Ticket Payload | Generates a structured Jira ticket JSON preview |
| Slack Alert Payload | Generates a formatted Slack notification preview |
| AI Bug Triage | Recommends teams, urgency, next steps and estimated effort |
| Report Generation | Saves generated bug-analysis reports under the reports directory |
| Interactive Interface | Provides a multi-tab Streamlit application with Plotly visualizations |

## Application Modules

### 1. PDF RAG – Bug Analysis Assistant

The PDF RAG module allows users to upload one or more software bug reports, technical manuals and documentation files.

The uploaded documents pass through the following pipeline:

1. PDF text extraction using PyMuPDF.
2. Text cleaning and preprocessing.
3. Document chunking with overlap.
4. Embedding generation using Sentence-Transformers.
5. FAISS index creation and storage.
6. Semantic retrieval of the most relevant information.
7. AI response generation using Qwen2.5-1.5B-Instruct.

Users can enter natural-language questions such as:

- Why does the application crash when uploading large files?
- What could be the root cause of this error?
- What fix can be recommended for this issue?

The system retrieves relevant document chunks and uses them to generate structured bug analysis.

**AI response sections include:**
- Bug Summary
- Possible Root Cause
- Technical Explanation
- Recommended Fix
- Relevant Source Information

Generated reports are saved in the reports directory.

### 2. Bug Data Explorer – Fused Dataset Analysis

The Bug Data Explorer module provides an interactive interface for exploring the enriched software bug dataset.

The application searches the `data/` directory for Excel files, preferring filenames containing `FINAL` or `COMPLETE`. If an Excel file is unavailable or cannot be loaded, it attempts to load `bug_dataset_300.csv`.

The module also generates derived fields such as:

- `has_cve` – Identifies whether a bug record contains an associated CVE ID.
- `risk_level` – Derives a risk category using the available severity or priority information.

**Dataset exploration features:**

- Total number of bug records.
- Critical-risk bug count.
- High-priority bug count.
- CVE availability.
- Search by bug title or bug ID.
- Filter by priority and risk level.
- View complete details of individual bug records.
- Interactive priority distribution chart.
- Risk-level distribution chart.
- Confidence versus severity scatter plot, when the required columns are available.

The dataset is also used to build a separate FAISS index for semantic retrieval.

### 3. Bug Management – Developer Workflow

The Bug Management module demonstrates how a selected bug record can be transformed into different formats for software development and team communication platforms.

**GitHub Issue**

Generates a Markdown-formatted issue draft containing:
- Bug ID and title.
- Severity and priority.
- Technology stack and environment.
- Root cause information.
- Steps to reproduce.
- Expected and actual behaviour.

**Jira Ticket**

Generates a structured JSON payload containing:
- Project key.
- Bug summary.
- Description.
- Issue type.
- Priority.

**Slack Alert**

Generates a formatted notification containing:
- Bug ID and title.
- Severity and priority.
- Technology stack.
- Environment.
- Root cause.
- Risk level.

These three features currently generate payload previews for demonstration. Actual submission requires connecting the corresponding external API credentials and implementing the API requests.

**AI Triage Recommendation**

The module also uses Qwen2.5-1.5B-Instruct to analyze the selected bug and generate:

1. Recommended Team – Backend, Frontend, DevOps or another suitable team.
2. Urgency – Critical, High, Medium or Low.
3. Suggested Next Steps.
4. Estimated Effort – Small, Medium or Large.
5. Additional Notes.

A rule-based fallback recommendation is provided if LLM generation fails.

## Dataset and Data Integration

BugAssist AI combines document-based knowledge retrieval with structured software bug data.

The application supports an enriched dataset in Excel format and a CSV fallback.

The dataset contains software bug information such as:

- Bug ID
- Bug Title
- Bug Description
- Error Code
- Bug Category
- Technology Stack
- Severity
- Environment
- Developer Role
- Root Cause
- Suggested Fix
- Technical Explanation

Additional enrichment fields can provide information about priority recommendations, fix confidence, GitHub issues, CVE records and other external information.

The actual available fields depend on the loaded dataset.

The application uses the enriched dataset for interactive exploration and dataset-based semantic retrieval.

API Integration

BugAssist AI uses five external APIs and services during the dataset enrichment and data fusion process. These integrations collect additional information from multiple sources to make the software bug dataset more informative and useful for analysis.

APIs Integrated

API / Service

Integration Purpose

Mistral AI API

Generates AI-based root cause analysis and priority recommendations for individual bug records using bug titles and descriptions.

GitHub REST API

Retrieves GitHub-related information associated with the technology stack.

Stack Exchange API (Stack Overflow)

Retrieves relevant technical questions and discussions related to the technology stack.

National Vulnerability Database (NVD) API

Retrieves vulnerability information and associated CVE records.

NewsAPI

Retrieves relevant technology-related news information for additional dataset enrichment.

API Data Collection and Integration Workflow

The original bug dataset is loaded.

Mistral AI is used to generate additional AI-based analysis for bug records.

GitHub REST API retrieves relevant GitHub information.

Stack Exchange API collects relevant Stack Overflow discussions.

NVD API retrieves vulnerability and CVE-related information.

NewsAPI collects relevant news information.

API responses are processed and integrated with the original dataset using the relevant bug and technology-stack matching fields.

Caching is used for technology-stack-based API lookups to reduce repeated requests.

The enriched dataset is prepared for use in the Bug Data Explorer and dataset-based semantic retrieval.

Data Fusion

The API-generated information is combined with the original structured bug records to create an enriched dataset containing additional technical, vulnerability and AI-generated information.

This integration demonstrates how multiple external information sources can be combined with an existing dataset to improve the availability of information for software bug analysis.


## System Architecture and Workflow

### Overall Application Workflow

```text
                  BugAssist AI
                       |
             ---------------------
             |         |         |
             v         v         v
          PDF RAG   Data       Bug
                    Explorer  Management
             |         |         |
             v         v         v
         PDF Upload  Fused    Select Bug
             |       Dataset     |
             v         |         |
         PyMuPDF       v         v
             |     Data Index  GitHub/Jira/
             v         |       Slack Payloads
        Preprocessing  |
             |         |         |
             v         |         v
         Chunking      |      AI Triage
             |         |         |
             v         |         v
        Embeddings     |       Qwen LLM
             |         |
             v         |
         FAISS Index <-+
             |
             v
       Semantic Search
             |
             v
         Top-3 Results
             |
             v
        RAG Prompt
             |
             v
      Qwen2.5-1.5B
             |
             v
      AI Bug Analysis
             |
             v
      Report Generation
```

### PDF RAG Processing Pipeline

```text
PDF Bug Reports
      |
      v
PyMuPDF Text Extraction
      |
      v
Text Preprocessing
      |
      v
Document Chunking
      |
      v
Sentence-Transformer Embeddings
      |
      v
FAISS Vector Index
      |
      v
User Query
      |
      v
Semantic Search (Top-3)
      |
      v
Retrieved Context
      |
      v
RAG Prompt Construction
      |
      v
Qwen2.5-1.5B-Instruct
      |
      v
Structured AI Bug Analysis
      |
      v
Source Information + Saved Report
```

## Technology Stack

| Category | Technology |
|---|---|
| Programming Language | Python |
| Frontend and Application | Streamlit |
| Data Processing | Pandas, NumPy |
| Data Visualization | Plotly Express |
| PDF Processing | PyMuPDF |
| Text Preprocessing | Python |
| Text Embeddings | Sentence-Transformers |
| Embedding Model | all-MiniLM-L6-v2 |
| Large Language Model | Qwen/Qwen2.5-1.5B-Instruct |
| LLM Framework | Hugging Face Transformers |
| Deep Learning | PyTorch |
| Vector Database | FAISS |
| Dataset Formats | CSV, Excel |
| Storage | Local files and FAISS indexes |

## Project Structure

```text
BugAssist-AI/
│
├── app.py
│
├── src/
│   ├── __init__.py
│   ├── pdf_loader.py
│   ├── preprocessing.py
│   ├── chunking.py
│   ├── embedding.py
│   ├── vector_store.py
│   ├── search.py
│   ├── llm.py
│   ├── prompt.py
│   ├── ui.py
│   ├── utils.py
│   └── dataset_index.py
│
├── data/
│   ├── bug_dataset_300.csv
│   └── [enriched Excel dataset]
│
├── models/
│
├── reports/
│
├── requirements.txt
│
├── README.md
│
└── .gitignore
```

## Installation and Local Setup

### Prerequisites

- Python 3.10 or 3.11 recommended.
- Git.
- Internet connection for downloading models and installing dependencies.
- Sufficient RAM and disk space for the embedding model and LLM.
- Approximately 4 GB or more of free disk space is recommended, depending on model caching and installed dependencies.

### 1. Clone the Repository

```bash
git clone https://github.com/SiddhiPenkar/BugAssist-AI.git
```

Open the project directory:

```bash
cd BugAssist-AI
```

### 2. Create a Virtual Environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Make sure the required Excel-reading dependency, such as `openpyxl`, is included if you are using `.xlsx` files.

### 4. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser, normally at:

```text
http://localhost:8501
```

## First Run Notes

- The Sentence-Transformers embedding model is downloaded and cached when first required.
- Qwen2.5-1.5B-Instruct is loaded when AI generation is requested.
- The dataset FAISS index is built automatically when a dataset is loaded and an existing dataset index is not found.
- PDF knowledge-base indexing is performed after uploading PDFs and clicking **Create Knowledge Base**.
- Model loading and generation speed depend on available system memory and hardware.

## How to Use

### PDF RAG

1. Open the PDF RAG tab.
2. Upload one or more bug report PDFs.
3. Click **Create Knowledge Base**.
4. Enter a bug-related question.
5. Click **Search & Analyze**.
6. Review the generated AI analysis and retrieved source information.
7. Find the saved report in the reports directory.

### Bug Data Explorer

1. Open the Bug Data Explorer tab.
2. Ensure that the enriched Excel dataset or CSV fallback is available inside `data/`.
3. View the overview statistics.
4. Search for a bug using its title or ID.
5. Apply priority and risk-level filters.
6. Select a bug to view its complete record.
7. Explore the available interactive charts.

### Bug Management

1. Open the Bug Management tab.
2. Select a bug from the dataset.
3. Generate the GitHub Issue payload preview.
4. Generate the Jira Ticket JSON preview.
5. Generate the Slack Alert message preview.
6. Click **Get AI Triage for this bug** to obtain an AI-generated recommendation.

## Screenshots

| PDF RAG Interface 
<img width="959" height="503" alt="Screenshot 2026-08-05 044504" src="https://github.com/user-attachments/assets/32309c58-6587-40a8-83fc-91d346bf2498" />

| PDF upload and knowledge-base creation |
<img width="959" height="502" alt="Screenshot 2026-08-05 042941" src="https://github.com/user-attachments/assets/9efd99be-1160-4ea6-9251-77b18ea09546" />

| AI Bug Analysis 
<img width="1919" height="1005" alt="Screenshot 2026-08-18 050836" src="https://github.com/user-attachments/assets/ea60ca51-ef04-402a-a136-95cde7978e66" />

| Generated root cause and recommended fix |
<img width="959" height="505" alt="Screenshot 2026-08-05 043054" src="https://github.com/user-attachments/assets/e88f858f-b211-4396-83c8-168d32eea16c" />

| Retrieved Source Document |
<img width="1919" height="996" alt="Screenshot 2026-08-18 050852" src="https://github.com/user-attachments/assets/7accb28f-ce7f-4300-a55c-dc3080e2be24" />

<img width="951" height="502" alt="Screenshot 2026-08-05 034708" src="https://github.com/user-attachments/assets/b7a899b7-7e70-4890-8a72-ba4c68631ec0" />

| Bug Data Explorer 
<img width="1442" height="996" alt="Screenshot 2026-08-18 050220" src="https://github.com/user-attachments/assets/fdebcef9-ef74-4dab-af2b-4718ccd38775" />

| Dataset overview and filtering |
<img width="1919" height="995" alt="Screenshot 2026-08-18 051027" src="https://github.com/user-attachments/assets/8f6e7507-7908-4df0-8d87-85a8c49585a1" />

| Bug Details 
<img width="1919" height="1001" alt="Screenshot 2026-08-18 051051" src="https://github.com/user-attachments/assets/2c887183-24f5-4a39-a1fb-7ba6ff6ca056" />

| Bug Management 
<img width="1476" height="996" alt="Screenshot 2026-08-18 054728" src="https://github.com/user-attachments/assets/c5ad5dc6-5015-4d66-a66d-2bb2a73662ac" />

| GitHub, Jira and Slack payload previews |
<img width="1504" height="1005" alt="Screenshot 2026-08-18 054801" src="https://github.com/user-attachments/assets/66389b59-d196-47f4-80e6-5f5799d859fd" />
<img width="1484" height="1004" alt="Screenshot 2026-08-18 054826" src="https://github.com/user-attachments/assets/9fb9bb20-c7bc-443f-b984-6dc63a8ddc8d" />
<img width="1494" height="997" alt="Screenshot 2026-08-18 054848" src="https://github.com/user-attachments/assets/2578f9c6-a9f8-41f1-982c-d88e83ae21b3" />


| AI Triage and urgency recommendation
<img width="1473" height="877" alt="Screenshot 2026-08-18 053319" src="https://github.com/user-attachments/assets/417fa903-c5ca-4e9c-9165-a30e2bbdd125" />

## Limitations

- The quality of AI-generated analysis depends on the relevance and completeness of retrieved information.
- The application requires a valid PDF knowledge base or an available dataset for meaningful bug analysis.
- Excel and CSV datasets must contain the expected columns for all explorer features to work.
- Some analytics charts are displayed only when their required enriched columns are available.
- External dataset enrichment is performed separately; the current application loads the prepared dataset.
- GitHub, Jira and Slack functionality currently generates payload previews and does not automatically submit them to external services.
- AI triage depends on successful loading and execution of the local Qwen model.
- Model generation can be slower on CPU-based systems with limited memory.
- FAISS dataset indexes should be rebuilt when the underlying dataset changes.

## Future Enhancements

- Implement live GitHub Issue creation using the GitHub REST API.
- Connect Jira API for automatic ticket creation.
- Integrate Slack webhooks for real-time bug notifications.
- Improve AI response generation speed and efficiency.
- Add advanced bug classification and prediction models.
- Introduce additional dataset analytics and filtering options.
- Improve source-level evidence tracking and bug similarity analysis.

## Academic Disclaimer

BugAssist AI is an academic software engineering project developed for educational and research purposes. Its AI-generated root cause analysis, recommended fixes, priority suggestions and triage recommendations are intended to assist developers and should be verified before being used in real software development workflows.

---

**Developed as an MCA Final Year Project**

**GitHub Repository:** https://github.com/SiddhiPenkar/BugAssist-AI
