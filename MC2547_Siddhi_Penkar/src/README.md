# 🐞 BugAssist AI

**BugAssist AI** is a Retrieval Augmented Generation (RAG) based intelligent assistant for analyzing
software bug reports, logs, and technical documentation. Upload PDF bug reports/manuals, build a
searchable knowledge base, and ask natural-language questions to get structured, AI-generated bug
analysis with root causes and recommended fixes — grounded in your own documents.

> MCA Final Year Project — RAG Architecture Demonstration

---

## 📖 Project Description

Debugging often requires digging through scattered PDFs — crash logs, issue trackers exported as
PDF, API manuals, changelogs. BugAssist AI lets you upload these documents, automatically indexes
them using semantic embeddings and a FAISS vector database, and then answers your questions using
a local LLM (Qwen2.5-1.5B-Instruct) that is grounded strictly in the retrieved context — reducing
hallucination and keeping answers traceable to source documents.

---

## 🏗️ Architecture Explanation

```
                ┌─────────────────┐
                │   PDF Uploads    │
                └────────┬─────────┘
                         │  PyMuPDF
                         ▼
                ┌─────────────────┐
                │  Text Extraction │  (pdf_loader.py)
                └────────┬─────────┘
                         ▼
                ┌─────────────────┐
                │  Preprocessing   │  (preprocessing.py)
                │  clean/normalize │
                └────────┬─────────┘
                         ▼
                ┌─────────────────┐
                │     Chunking     │  (chunking.py)
                │  size + overlap  │
                └────────┬─────────┘
                         ▼
                ┌─────────────────┐
                │    Embeddings    │  (embedding.py)
                │ all-MiniLM-L6-v2 │
                └────────┬─────────┘
                         ▼
                ┌─────────────────┐
                │   FAISS Index    │  (vector_store.py)
                │  save / load     │
                └────────┬─────────┘
                         ▼
   User Query ──▶ ┌─────────────────┐
                  │ Semantic Search  │  (search.py) → Top-3 chunks
                  └────────┬─────────┘
                           ▼
                  ┌─────────────────┐
                  │   RAG Prompt     │  (prompt.py)
                  └────────┬─────────┘
                           ▼
                  ┌─────────────────┐
                  │  Qwen2.5-1.5B    │  (llm.py)
                  │  LLM Generation  │
                  └────────┬─────────┘
                           ▼
                  ┌─────────────────┐
                  │  Streamlit UI    │  (ui.py / app.py)
                  │  + Report saved  │
                  └─────────────────┘
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `app.py` | Streamlit entrypoint; wires the entire pipeline together |
| `src/pdf_loader.py` | Multi-PDF upload handling + text extraction (PyMuPDF) |
| `src/preprocessing.py` | Lowercasing, symbol removal, whitespace cleanup |
| `src/chunking.py` | Word-based chunking with configurable size/overlap |
| `src/embedding.py` | SentenceTransformer embeddings for docs & queries |
| `src/vector_store.py` | FAISS index build / save / load / search |
| `src/search.py` | High-level semantic search (query → top-k chunks) |
| `src/prompt.py` | RAG prompt template ("expert software debugging assistant") |
| `src/llm.py` | Qwen2.5-1.5B-Instruct loading & response generation |
| `src/ui.py` | Streamlit styling, sidebar, response/source rendering |
| `src/utils.py` | Paths, logging, report saving, shared helpers |

---

## 📁 Project Structure

```
BugAssist-AI/
├── app.py
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
│   └── utils.py
├── data/
│   ├── uploaded_pdfs/
│   ├── extracted_text/
│   └── faiss_index/
├── models/
├── reports/
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Installation Steps

### 1. Prerequisites
- Python 3.10 or 3.11 (recommended)
- ~4 GB free disk space (for cached embedding + LLM models on first run)
- Internet connection (first run only, to download models from HuggingFace)

### 2. Clone / Extract the Project
Extract `BugAssist-AI.zip` and open the folder in VS Code.

### 3. Create a Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> ⚠️ Note: `torch` may take a while to install. If you have a CUDA-capable GPU and want GPU
> acceleration, install the appropriate CUDA build of PyTorch from
> [pytorch.org](https://pytorch.org/get-started/locally/) instead of the default CPU build.

---

## ▶️ Running the Application

From the project root (with the virtual environment activated):

```bash
streamlit run app.py
```

Streamlit will start a local server and open the app in your browser, typically at:
```
http://localhost:8501
```

### First Run Notes
- The first time you build a knowledge base or ask a question, the embedding model
  (`all-MiniLM-L6-v2`) and the LLM (`Qwen/Qwen2.5-1.5B-Instruct`) will be downloaded automatically
  from HuggingFace and cached under `models/`. This may take several minutes depending on your
  connection speed.
- Subsequent runs will load the cached models and start much faster.

---

## 🚀 How to Use

1. **Upload PDFs** — Use the file uploader to select one or more bug report / log / manual PDFs.
2. **Create Knowledge Base** — Click the button to extract, clean, chunk, embed, and index your
   documents into FAISS.
3. **Ask a Question** — Type a natural-language question about a bug (e.g. *"Why does the app
   crash on large file uploads?"*).
4. **Search & Analyze** — Click to retrieve the most relevant chunks and generate a structured AI
   analysis: Bug Summary, Root Cause, Technical Explanation, Recommended Fix, and Source Info.
5. **Reports** — Every generated answer is automatically saved as a timestamped `.txt` file under
   `reports/`.

---

## ✨ Feature Highlights

- 📂 Multi-PDF upload with robust error handling for corrupt/invalid files
- 🧹 Text cleaning pipeline (lowercase, symbol removal, whitespace normalization)
- ✂️ Configurable chunking with overlap to preserve context across chunk boundaries
- 🧠 Semantic embeddings via `all-MiniLM-L6-v2` (SentenceTransformers)
- 🔍 FAISS vector similarity search (cosine similarity, top-3 retrieval with scores)
- 🤖 Local LLM generation via `Qwen2.5-1.5B-Instruct`, grounded in retrieved context
- 📝 Structured, professional bug-analysis output format
- 💾 Automatic report saving (`reports/`)
- 🎨 Modern dark, gradient Streamlit UI
- 🛡️ Error handling for missing index, empty uploads, invalid queries, and model load failures

---

## 🖼️ Screenshots

> _Add your own screenshots here after running the app._

| Home Page | Knowledge Base Built | AI Response |
|---|---|---|
| `screenshots/home.png` | `screenshots/kb_built.png` | `screenshots/response.png` |

---

## 🧩 Technology Stack

- **Language:** Python
- **Frontend:** Streamlit
- **Embeddings:** Sentence-Transformers (`all-MiniLM-L6-v2`)
- **LLM:** HuggingFace Transformers — `Qwen2.5-1.5B-Instruct`
- **Vector Database:** FAISS (`faiss-cpu`)
- **PDF Processing:** PyMuPDF
- **Numerical Utilities:** NumPy

---

## 🛠️ Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError` | Ensure the virtual environment is activated and `pip install -r requirements.txt` completed successfully. |
| Model download is slow/fails | Check your internet connection; models are cached in `models/` after first download. |
| Out of memory during LLM generation | Close other applications; consider running on a machine with more RAM, or reduce `max_new_tokens` in `src/llm.py`. |
| "No knowledge base found" error | Upload PDFs and click **Create Knowledge Base** before searching. |
| PDF text extraction returns empty | The PDF is likely scanned/image-only; use an OCR tool to convert it to text-based PDF first. |

---

## 📄 License

This project is provided for academic/educational purposes as part of an MCA final-year project.
