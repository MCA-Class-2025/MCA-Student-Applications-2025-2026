# DocuMind AI – Intelligent Document Question Answering System

## Overview

DocuMind AI is a Retrieval-Augmented Generation (RAG) application that allows users to upload PDF documents and ask natural language questions. The system retrieves relevant information from the uploaded documents using FAISS vector search and generates accurate answers using the FLAN-T5 Large language model through Hugging Face.

## Features

* Multi-PDF upload
* Semantic document search
* Conversational question answering
* Source document retrieval
* FAISS vector database
* Streamlit web interface
* Hugging Face LLM integration

## Technology Stack

* Python
* Streamlit
* LangChain
* FAISS
* Sentence Transformers (all-MiniLM-L6-v2)
* Hugging Face (FLAN-T5 Large)

## Project Structure

```text
PDF_QA_Chatbot/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── dataset/
├── faiss_index/
└── src/
```

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file:

```env
HUGGINGFACEHUB_API_TOKEN=YOUR_HUGGING_FACE_TOKEN
```

## Run the Application

```bash
streamlit run app.py
```

## RAG Pipeline

Document Upload → Text Extraction → Chunking → Embedding Generation → FAISS Vector Database → Retrieval → FLAN-T5 Large → Answer Generation

## Embedding Model

`sentence-transformers/all-MiniLM-L6-v2`

## Vector Database

FAISS

## Language Model

`google/flan-t5-large`

## Author

Shruti Ingle
