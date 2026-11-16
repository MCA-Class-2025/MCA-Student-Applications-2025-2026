# 🛡️ SecureSense AI - LLM & RAG-Based PDF Question Answering	
### ML-Based Threat Detection & RAG-Powered Cybersecurity Assistant

SecureSense AI is an AI-powered cybersecurity application that combines **Machine Learning** and **Large Language Models (LLMs)** to detect network anomalies and provide intelligent cybersecurity assistance through **Retrieval-Augmented Generation (RAG)**.

This project extends the research work:

> **ML-Based Anomaly Detection for Zero Trust Network Access (ZTNA)**

by integrating a Retrieval-Augmented Generation (RAG) pipeline with a Large Language Model to create an interactive cybersecurity knowledge assistant.

---

**Live Demo:** 🌐 https://securesense-ai.streamlit.app


## 🖥Streamlit Interface


- Dashboard
<img width="1277" height="533" alt="image" src="https://github.com/user-attachments/assets/c2fd871f-bc5d-4aed-af68-7450f53f7f3f" />

- Threat Detection
<img width="1279" height="549" alt="image" src="https://github.com/user-attachments/assets/0fd2fe95-c90c-44bd-998b-af7342a71f0b" />

- Threat Analysis Assistant
<img width="1271" height="505" alt="image" src="https://github.com/user-attachments/assets/170de4d3-76f0-4991-88b6-1e19fbe0e367" />

- Knowledge Base
<img width="1279" height="553" alt="image" src="https://github.com/user-attachments/assets/eeac7f22-6677-49da-952d-2a88d5dee2ec" />

<img width="1279" height="558" alt="image" src="https://github.com/user-attachments/assets/1669252f-dfe7-4a4d-a242-18bcd33e222a" />

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

