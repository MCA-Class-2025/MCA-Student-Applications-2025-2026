# 🛡️ SecureSense AI
### ML-Based Threat Detection & RAG-Powered Cybersecurity Assistant

SecureSense AI is an AI-powered cybersecurity application that combines **Machine Learning** and **Large Language Models (LLMs)** to detect network anomalies and provide intelligent cybersecurity assistance through **Retrieval-Augmented Generation (RAG)**.

This project extends the research work:

> **ML-Based Anomaly Detection for Zero Trust Network Access (ZTNA)**

by integrating a Retrieval-Augmented Generation (RAG) pipeline with a Large Language Model to create an interactive cybersecurity knowledge assistant.

---

# 🚀 Features

## 🔍 Machine Learning Threat Detection

- Detect anomalous network traffic
- Isolation Forest based anomaly detection
- NSL-KDD dataset support
- CSV upload
- Prediction visualization
- Download prediction results

---

## 🤖 AI Threat Analysis Assistant

- Retrieval-Augmented Generation (RAG)
- Context-aware cybersecurity question answering
- Uses uploaded research papers
- Conversation history
- Supports Zero Trust and Network Security concepts

---

## 📚 Knowledge Base Management

Administrator Features

- Upload PDF/DOCX research papers
- Replace existing documents
- Delete documents
- Rebuild Knowledge Base
- View uploaded documents

---

## 📄 Research Assistant

- Research paper support
- Technical document understanding
- AI-assisted cybersecurity learning

---

## 🖥 Professional Streamlit Interface

- Dashboard
- Threat Detection
- Threat Analysis Assistant
- Knowledge Base
- Research Assistant
- About Page

---

# 🏗 System Architecture

```text
                    Research Papers (PDF/DOCX)
                              │
                              ▼
                     Document Loader
                              │
                              ▼
                       Text Extraction
                              │
                              ▼
                          Chunking
                              │
                              ▼
                  Sentence Embeddings
                              │
                              ▼
                     FAISS Vector Database
                              │
                    User Question
                              │
                              ▼
                         Retriever
                              │
                              ▼
                      Prompt Template
                              │
                ┌─────────────┴──────────────┐
                │                            │
                ▼                            ▼
         Ollama (Local)              Groq API (Cloud)
                │                            │
                └─────────────┬──────────────┘
                              ▼
                    AI Generated Response
```

---

# 🧠 Technologies Used

## Programming Language

- Python 3.12

## Frontend

- Streamlit

## Machine Learning

- Scikit-learn
- Isolation Forest

## Large Language Model

### Local

- Ollama
- Gemma 3 1B

### Cloud

- Groq API
- Llama 3.1 8B Instant (or any supported Groq model)

## Embedding Model

- all-MiniLM-L6-v2
- Sentence Transformers

## Vector Database

- FAISS

## PDF Processing

- PyPDF
- python-docx

---

# 📂 Project Structure

```text
SecureSense_AI_LLM/

│
├── app.py
│
├── app_pages/
│   ├── dashboard.py
│   ├── threat_detection.py
│   ├── threat_analysis.py
│   ├── knowledge_base.py
│   ├── research_assistant.py
│   └── about.py
│
├── modules/
│   ├── anomaly_detection/
│   ├── llm/
│   └── rag/
│
├── data/
│   ├── documents/
│   └── datasets/
│
├── models/
│
├── requirements.txt
│
└── README.md
```

---

# ⚙ Installation

Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/SecureSense_AI_LLM.git
```

Go to project folder

```bash
cd SecureSense_AI_LLM
```

Create Virtual Environment

Windows

```bash
python -m venv .venv
```

Activate

```bash
.venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# ▶ Running the Application

## Local Version (Ollama)

Start Ollama

```bash
ollama serve
```

Download the model

```bash
ollama pull gemma3:1b
```

Run Streamlit

```bash
streamlit run app.py
```

---

## Cloud Version (Groq)

Configure the following secret:

```text
GROQ_API_KEY=YOUR_API_KEY
LLM_PROVIDER=groq
```

Deploy using Streamlit Community Cloud.

---

# 📚 Dataset

## Machine Learning

- NSL-KDD Dataset

Used for

- Network intrusion detection
- Anomaly detection
- Isolation Forest training

## RAG Knowledge Base

Research papers related to

- Zero Trust Architecture
- Zero Trust Network Access (ZTNA)
- Intrusion Detection Systems
- NSL-KDD
- AI-based Cybersecurity

---

# 🔄 RAG Pipeline

```text
Research Papers
        │
        ▼
Document Loader
        │
        ▼
Text Extraction
        │
        ▼
Chunking
        │
        ▼
Sentence Embeddings
        │
        ▼
FAISS Vector Database
        │
        ▼
Retriever
        │
        ▼
Prompt Template
        │
        ▼
LLM
        │
        ▼
Generated Response
```

---

# 📊 Machine Learning Pipeline

```text
CSV Dataset
      │
      ▼
Data Preprocessing
      │
      ▼
Isolation Forest
      │
      ▼
Prediction
      │
      ▼
Threat Detection Results
```

---

# 📷 Screenshots

Add screenshots here after deployment.

Suggested screenshots:

- Dashboard
- Threat Detection
- Threat Analysis Assistant
- Knowledge Base
- Research Assistant
- About Page

---

# 🎯 Future Scope

- Voice-enabled Cybersecurity Assistant
- Real-time Network Monitoring
- Live Packet Capture Integration
- SIEM Integration
- Threat Intelligence APIs
- Multi-user Authentication
- Cloud Vector Database
- Hybrid Search
- PDF Summarization
- Automatic Knowledge Base Synchronization

---

# 📄 Research Work

This project extends the research:

**ML-Based Anomaly Detection for Zero Trust Network Access (ZTNA)**

The original research focuses on Machine Learning-based anomaly detection.

This application extends that work by integrating:

- Retrieval-Augmented Generation (RAG)
- Large Language Models
- Cybersecurity Knowledge Base
- Interactive Threat Analysis Assistant

---

# 👨‍💻 Author

**Asmi Raut**

Master of Computer Applications (MCA)

---

# 📜 License

This project is developed for academic and educational purposes.