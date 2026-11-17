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



(<img width="1919" height="893" alt="Screenshot 2026-08-18 022820" src="https://github.com/user-attachments/assets/a65d73de-b7de-4c4c-a4d4-04a8de3a93e0" />
(<img width="1901" height="846" alt="Screenshot 2026-08-18 022902" src="https://github.com/user-attachments/assets/6deef70a-9308-405b-8983-985b15789b48" />

<img width="1489" height="845" alt="Screenshot 2026-08-18 024106" src="https://github.com/user-attachments/assets/ab91fc01-eb08-4dcf-a027-042ede2f841d" />
<img width="1478" height="914" alt="Screenshot 2026-08-18 024249" src="https://github.com/user-attachments/assets/ef401884-b0db-4871-9187-5702e4cfc52d" />


<img width="1572" height="885" alt="Screenshot 2026-08-18 023115" src="https://github.com/user-attachments/assets/8760dd5c-ea60-4b46-9c55-42bd965bf638" />
<img width="1847" height="906" alt="Screenshot 2026-08-18 023038" src="https://github.com/user-attachments/assets/86cb8355-8f8c-45b6-af7d-119b66b2e957" />
<img width="1910" height="901" alt="Screenshot 2026-08-18 022917" src="https://github.com/user-attachments/assets/96cdfc78-abcc-4ba2-b8d3-da51293146ca" />
<img width="1494" height="878" alt="Screenshot 2026-08-18 024035" src="https://github.com/user-attachments/assets/bf7e9173-9296-435c-a175-a76ba99646b6" />
<img width="1504" height="858" alt="Screenshot 2026-08-18 023922" src="https://github.com/user-attachments/assets/593e9e9c-29bb-4333-a7b0-84a90efedc86" />
<img width="1477" height="674" alt="Screenshot 2026-08-18 023547" src="https://github.com/user-attachments/assets/f3daff8e-b7da-4bae-8b63-145ec113e487" />
<img width="1550" height="919" alt="Screenshot 2026-08-18 023532" src="https://github.com/user-attachments/assets/7d03e8fc-b42e-4c8f-a272-71392aa58162" />
<img width="1852" height="608" alt="Screenshot 2026-08-18 023438" src="https://github.com/user-attachments/assets/98c4a635-b69c-437e-9244-092fd76ceccb" />
<img width="1190" height="895" alt="Screenshot 2026-08-18 023323" src="https://github.com/user-attachments/assets/8b577e4f-65da-41f3-9ca6-0683c8f2b394" />


---

## 🚀 Future Scope

* 🥑 **Macronutrient Calculator**: Integrated macro tracker for automated daily calorie and protein estimation.
* 📊 **Diet Chart Export**: Automatic generation of weekly meal plans in downloadable PDF format.
* 🌐 **Multi-Language Support**: OCR and translation support for international nutrition labels.
* 🎙️ **Voice Query Support**: Speech-to-text input for enhanced accessibility.

---

## 👤 Author

* **Rudrani Chavan**
* **Project Type**: Academic MCA Major Project / Rudrani chavan
