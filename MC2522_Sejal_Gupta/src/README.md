# 🛡️ AI Social Media Content Moderator — Core Application

<p align="center">
  <b>A Multimodal AI-Powered Content Moderation and Toxicity Detection System combining Transformers, OCR, Multilingual Translation, Google Cloud Vision SafeSearch, and Google Gemini LLMs.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.30%2B-ff4b4b?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/Hugging%20Face-DeBERTa--v3-yellow?logo=huggingface" alt="Hugging Face">
  <img src="https://img.shields.io/badge/LLM-Google%20Gemini-orange?logo=google" alt="Google Gemini">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Modular Pipeline Breakdown](#-modular-pipeline-breakdown)
- [Project Directory Structure](#-project-directory-structure)
- [Installation & Setup](#-installation--setup)
- [Running the Application](#-running-the-application)
- [Testing Individual API Components](#-testing-individual-api-components)
- [Graceful Fallback Mechanism](#-graceful-fallback-mechanism)
- [Author & Academic Metadata](#-author--academic-metadata)

---

## 📖 Overview

The **AI Social Media Content Moderator** is an intelligent, multi-layered moderation pipeline engineered to identify toxic, obscene, threatening, insulting, and hateful social media comments. In addition to conventional text moderation, it natively accommodates:
- **Screenshot Ingestion**: Users can upload comment screenshots; the integrated OCR engine extracts embedded text automatically.
- **Visual Safety Verification**: Uploaded images are independently inspected for unsafe graphic content (adult, violence, racy, spoof) via Google Cloud Vision SafeSearch.
- **Multilingual Support**: Vernacular comments (Hindi, Gujarati) are automatically translated into English prior to deep transformer inference.
- **Dual-Engine Moderation**: Combining zero-shot DeBERTa classification with Gemini LLM contextual reasoning to eliminate false positives and provide human-readable justifications.
- **Auditory Reporting**: Audio summaries are synthesized on-the-fly using Google Text-to-Speech (gTTS).

---

## ✨ Key Features

1. **Multi-Input Ingestion**:
   - Plain text input via interactive text area.
   - Screenshot upload (`PNG`, `JPG`, `JPEG`) with automatic OCR text extraction.
2. **Visual Content Safety Inspection**:
   - Deep inspection using Google Vision SafeSearch across 5 distinct safety dimensions: *Adult*, *Violence*, *Racy*, *Medical*, and *Spoof*.
3. **Multilingual Translation**:
   - Integrated MyMemory API translates Hindi and Gujarati comments into English for consistent downstream analysis.
4. **Deep Transformer Moderation**:
   - Zero-shot classification powered by `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` via Hugging Face Inference API.
5. **Contextual LLM Reasoning**:
   - Google Gemini provides structured explanations, multi-category assignment, and granular risk level assessment (*Low*, *Medium*, *High*).
6. **Voice Synthesis**:
   - Audio moderation report generation enabling hands-free auditory review.
7. **Resilient Fallback**:
   - Keyword and heuristics safety fallback in the event of upstream API rate limits or quota exhaustion.

---

## 🏗️ System Architecture

```text
       ┌────────────────────────┐      ┌─────────────────────────┐
       │   Text Comment Input   │      │ Screenshot Image Upload │
       └───────────┬────────────┘      └────────────┬────────────┘
                   │                                │
                   │                     ┌──────────┴──────────┐
                   │                     ▼                     ▼
                   │              ┌──────────────┐      ┌──────────────┐
                   │              │   OCR API    │      │Google Vision │
                   │              │Text Extract  │      │  SafeSearch  │
                   │              └──────┬───────┘      └──────┬───────┘
                   │                     │                     │
                   ▼                     ▼                     │
       ┌────────────────────────────────────────┐              │
       │ Multilingual Detection & Translation   │              │
       │        (English / Hindi / Gujarati)    │              │
       └───────────────────┬────────────────────┘              │
                           │                                   │
                           ▼                                   │
       ┌────────────────────────────────────────┐              │
       │   Preprocessing & Text Sanitization    │              │
       └───────────────────┬────────────────────┘              │
                           │                                   │
               ┌───────────┴───────────┐                       │
               ▼                       ▼                       │
       ┌───────────────┐       ┌───────────────┐               │
       │ Hugging Face  │       │ Google Gemini │               │
       │ DeBERTa Model │       │  LLM Reasoner │               │
       └───────┬───────┘       └───────┬───────┘               │
               │                       │                       │
               └───────────┬───────────┘                       │
                           ▼                                   │
       ┌────────────────────────────────────────┐              │
       │     Unified Content Decision Engine    │◄─────────────┘
       └───────────────────┬────────────────────┘
                           │
               ┌───────────┴───────────┐
               ▼                       ▼
       ┌───────────────┐       ┌───────────────┐
       │Streamlit Cards│       │ gTTS Voice    │
       │  & Metrics    │       │ Audio Report  │
       └───────────────┘       └───────────────┘
```

---

## 🗂️ Project Directory Structure

```text
src/
├── app.py                      # Main Streamlit web application
├── requirements.txt            # Python dependencies
├── requirements_backup.txt     # Complete freeze of runtime dependencies
├── .env.example                # Sample environment configuration template
├── README.md                   # This documentation file
├── LICENSE                     # MIT Open Source License
│
├── api/                        # External API wrappers
│   ├── gemini_api.py           # Google Gemini generative language client
│   ├── ocr_api.py              # OCR text extraction engine
│   ├── translation_api.py      # MyMemory multilingual translation wrapper
│   └── vision_api.py           # Google Cloud Vision SafeSearch detector
│
├── models/                     # Model definitions and prompt pipelines
│   ├── gemini_model.py         # Gemini prompt formulation and response parsing
│   └── llm.py                  # High-level LLM abstraction interface
│
├── src/                        # Moderation core logic
│   └── moderator.py            # Hugging Face DeBERTa pipeline and classification logic
│
├── utils/                      # Helper utilities
│   └── preprocess.py           # Text cleaning, regex, and URL stripping
│
├── vectorstore/                # Vector store modules
│   └── faiss_store.py          # FAISS semantic vector retrieval helper
│
├── embeddings/                 # Sentence embedding wrappers
│   └── embedding_model.py      # Text embedding generation
│
└── tests/                      # Component verification test scripts
    ├── test_gemini.py          # Verifies Gemini LLM connectivity
    ├── test_huggingface.py     # Verifies Hugging Face DeBERTa inference
    ├── test_ocr.py             # Tests image OCR character extraction
    ├── test_translation.py     # Tests vernacular-to-English translation
    └── test_vision.py          # Tests Google Vision SafeSearch detection
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and configure your API tokens:
```bash
cp .env.example .env
```
Open `.env` in any text editor and supply:
```env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🚀 Running the Application

Launch the Streamlit web interface with:
```bash
streamlit run app.py
```
Open your browser and navigate to:
```
http://localhost:8501
```

---

## 🧪 Testing Individual API Components

The `src/` folder includes standalone test scripts to verify each integration independently:

```bash
# Test Hugging Face DeBERTa Moderation
python test_huggingface.py

# Test Google Gemini LLM API
python test_gemini.py

# Test Google Cloud Vision SafeSearch
python test_vision.py

# Test OCR Text Extraction
python test_ocr.py

# Test MyMemory Translation
python test_translation.py
```

---

## 🛡️ Graceful Fallback Mechanism

If upstream API rate limits are hit or the inference credit quota is exhausted, the application dynamically shifts to **Fallback Mode**:
- Retains full UI responsiveness.
- Activates heuristic token screening and regex keyword pattern matching.
- Clearly flags analysis results as `Fallback Analysis` to ensure complete operational transparency.

---

## 👩‍💻 Author & Academic Metadata

- **Student Name:** Sejal Gupta
- **Roll Number:** MC2522
- **Degree:** Master of Computer Applications (MCA) – Semester III
- **Course:** Data Science and Analytics
- **Faculty In-Charge:** Dr. Anita Chaware
- **Institution:** SNDT Women's University, Mumbai
