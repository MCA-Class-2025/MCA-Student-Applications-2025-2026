# NutriMate – AI-Powered Nutrition Assistant using RAG

> **NutriMate** is a local, privacy-preserving Retrieval-Augmented Generation (RAG) system designed to deliver evidence-based dietary insights, nutritional facts, and food label analysis directly from user-uploaded PDFs and image files.

---

## 📌 Problem Statement

Navigating complex nutritional guidelines, diet charts, and food packaging labels can be overwhelming for individuals, dietitians, and students. Generic AI chatbots often produce unverified responses, hallucinate facts, or rely on outdated online sources without proper attribution. There is a critical need for an intelligent assistant that restricts its answers **strictly** to trusted, user-provided nutrition documents and provides verifiable page-level source citations.

---

## 🎯 Objectives

* **Evidence-Based Answers**: Ensure all AI responses are grounded strictly in uploaded documents without external hallucinations.
* **Multi-Format Processing**: Process both digital text documents (PDFs) and physical food label photographs (PNG/JPG/JPEG).
* **100% Local & Private Deployment**: Run the entire pipeline locally on CPU using open-source models, eliminating cloud API dependencies and API costs.
* **Transparent Attribution**: Output confidence scores, page numbers, and expandable retrieved text snippets for every claim.
* **User-Centric UI**: Deliver a modern, Pinterest-inspired interface featuring a soft pastel green and beige palette, sample question cards, and one-click answer downloads.

---

## ✨ Key Features

* 📄 **Multi-Format Ingestion**: Supports PDF documents via `PyPDFLoader` and images (PNG, JPG, JPEG) via local **EasyOCR** text extraction.
* 🧠 **Local Embedding & Vector Storage**: Utilizes `all-MiniLM-L6-v2` with **ChromaDB** for efficient semantic indexing and fast retrieval.
* 🤖 **Local LLM Generation**: Powered by local **Ollama** running `Gemma 2B`, enforcing zero data leakage and zero API costs.
* 📊 **Smart Confidence & Source Metrics**: Displays document name, page number, confidence percentage, and expandable context snippets for every response.
* 📥 **One-Click Response Download**: Export generated answers and citations directly as `.txt` files.
* 🎨 **Pinterest-Inspired Aesthetics**: Soft green/beige color theme, rounded card layouts, sample question cards, and custom user/assistant chat bubbles.
* ⚡ **Resource Caching**: Implements Streamlit `@st.cache_resource` and `@st.cache_data` for sub-second query rendering.

---

## 🛠️ Tech Stack

| Domain | Technology |
|---|---|
| **Frontend UI** | Streamlit, Custom Vanilla CSS |
| **Framework** | LangChain / LangChain Community |
| **OCR Engine** | EasyOCR (Local CPU Mode) |
| **Embedding Model** | HuggingFace (`sentence-transformers/all-MiniLM-L6-v2`) |
| **Vector Database** | ChromaDB (Persistent Disk Storage) |
| **Local LLM** | Ollama (`Gemma 2B`) |
| **Document Loaders** | PyPDFLoader & RecursiveCharacterTextSplitter |

---

## 🔄 RAG Pipeline Architecture

```
[ Upload PDF / Image ]
          │
          ├──► PDF parsing (PyPDFLoader) ───┐
          └──► Image OCR (EasyOCR) ─────────┴──► [ Document Chunks ] (1000 size, 200 overlap)
                                                         │
                                                         ▼
                                               [ HuggingFace Embeddings ]
                                               (all-MiniLM-L6-v2)
                                                         │
                                                         ▼
                                               [ Vector Database ]
                                               (ChromaDB Local Persist)
                                                         │
[ User Question ] ──────────────────────────────► [ Similarity Search ] (Top K=4)
                                                         │
                                                         ▼
                                               [ Context + Strict Prompt ]
                                                         │
                                                         ▼
                                               [ Ollama Gemma 2B LLM ]
                                                         │
                                                         ▼
                                               [ Response + Source Badges ]
```

---

## 📂 Folder Structure

```
nutrimate/
├── app.py                  # Main Streamlit UI, session state, and interaction handlers
├── rag_pipeline.py         # Ingestion, EasyOCR, ChromaDB vector store, and LLM chain
├── config.py               # Application settings, paths, model names, and color themes
├── styles.css              # Custom Pinterest-inspired CSS stylesheet
├── requirements.txt        # Python package dependencies
├── README.md               # Project documentation
└── data/                   # Data directory (automatically created)
    ├── db/                 # Persistent ChromaDB vector collections
    └── documents/          # Uploaded PDF and image files
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
* **Python**: Python 3.9, 3.10, or 3.11 installed.
* **Ollama**: Download and install Ollama from [ollama.com](https://ollama.com/).

### 2. Pull Local LLM Model
Open your terminal and pull the default Gemma model:
```bash
ollama pull gemma:2b
```

### 3. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/your-username/nutrimate.git
cd nutrimate

python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 How to Run

1. Make sure Ollama is running in the background.
2. Launch the Streamlit web app:
   ```bash
   streamlit run app.py
   ```
3. Open your browser at `http://localhost:8501`.
4. Upload your nutrition PDFs or food label photos in the sidebar.
5. Click a sample question or type your custom query!

---

## 📸 Screenshots

*(Add your application screenshots here when sharing on GitHub)*

| Main Landing Page | Chat & Source Attribution |
|:---:|:---:|
| ![Landing Page Placeholder](https://via.placeholder.com/600x350?text=NutriMate+Landing+Page) | ![Chat Interface Placeholder](https://via.placeholder.com/600x350?text=NutriMate+Chat+%26+Sources) |

---

## 🚀 Future Scope

* 🥑 **Macronutrient Calculator**: Integrated macro tracker for automated daily calorie and protein estimation.
* 📊 **Diet Chart Export**: Automatic generation of weekly meal plans in downloadable PDF format.
* 🌐 **Multi-Language Support**: OCR and translation support for international nutrition labels.
* 🎙️ **Voice Query Support**: Speech-to-text input for enhanced accessibility.

---

## 👤 Authors

* **NutriMate Development Team**
* **Project Type**: Academic MCA Major Project / Open Source Contribution
