# 🚀 PrepGenius AI

> An AI-powered Smart Learning & Revision Assistant built using **React, FastAPI, Ollama (Qwen2.5), FAISS, and SQLite**.

![License](https://img.shields.io/badge/License-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.11-yellow)
![React](https://img.shields.io/badge/React-18-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Ollama](https://img.shields.io/badge/Ollama-Qwen2.5-purple)

---

# 📖 Overview

PrepGenius AI is an intelligent study assistant that helps students learn faster using Large Language Models (LLMs).

The application allows students to upload study material, generate summaries, create flashcards, generate MCQs, plan study schedules, and chat with an AI tutor.

The project works completely offline using Ollama and FAISS.

---

# ✨ Features

- 📚 AI Tutor Chat
- 📝 Smart AI Summarizer
- 🎴 Flashcard Generator
- ❓ MCQ Quiz Generator
- 📅 AI Study Planner
- 📊 Study Analytics
- 🌐 Multilingual Summaries (English, Hindi, Marathi)
- 🔊 Text-to-Speech Audio Reader
- 📄 PDF Export
- 🔐 JWT Authentication

---

# 🛠 Tech Stack

## Frontend

- React
- TypeScript
- Tailwind CSS
- Vite
- Framer Motion

## Backend

- FastAPI
- SQLAlchemy
- SQLite
- JWT Authentication

## AI

- Ollama
- Qwen2.5:3B
- Sentence Transformers
- FAISS

---

# 📂 Project Structure

```text
PrepGenius AI
│
├── backend
│   ├── app
│   ├── uploads
│   ├── requirements.txt
│   └── .env
│
├── frontend
│   ├── src
│   ├── public
│   ├── package.json
│   └── vite.config.ts
│
├── screenshots
│
├── sample_dataset
│
└── README.md
```

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/kinju22/PrepGenius-AI.git

cd PrepGenius-AI
```

---

## Backend

```bash
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend runs on

```
http://localhost:8000
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend runs on

```
http://localhost:5173
```

---

# 🤖 Run Ollama

Start Ollama

```bash
ollama serve
```

Download the model

```bash
ollama pull qwen2.5:3b
```

---

# 📸 Screenshots

## Dashboard

![Dashboard](screenshots/dashboard.png)

---

## AI Tutor Chat

![Chat](screenshots/chat.png)

---

## Smart Summarizer

![Summarizer](screenshots/summarizer.png)

---

## Flashcards

![Flashcards](screenshots/flashcards.png)

---

## MCQ Generator

![MCQ](screenshots/mcq.png)

---

## Study Planner

![Planner](screenshots/planner.png)

---

## Study Analytics

![Analytics](screenshots/analytics.png)

---

# 📁 Sample Dataset

The repository contains sample study notes inside the **sample_dataset** folder.

Supported formats

- PDF
- DOCX
- TXT

---

# 🔮 Future Scope

- Voice Chat
- OCR Support
- Mobile Application
- Cloud Sync
- AI Exam Predictor
- Personalized Learning
- Multi-Model Support

---

# 👨‍💻 Author

**Kinjal Gauda**

MCA Student

SNDT Women's University

GitHub: https://github.com/kinju22

---

# ⭐ If you like this project

Please give this repository a ⭐ on GitHub.