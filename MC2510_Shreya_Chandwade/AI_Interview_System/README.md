# AI Interview System

AI-powered mock interview preparation app with user accounts, answer evaluation, performance dashboard, and personalized study plans.

## Features

- Mock interviews tailored to job role and skills
- 5 integrated OpenAI APIs with local fallbacks
- User registration and login
- Interview history and performance dashboard
- Personalized 7-day study plan
- Pre-interview skill gap analysis
- Post-interview AI feedback summary

## Three-Level Data Fusion

The RAG pipeline uses three executable fusion stages before its context is sent to the existing AI interview features:

1. **Data-Level Fusion** combines and cleans information from the database, knowledge base, question bank, and CSV datasets. It maps different column names to a common schema, fills missing fields, preserves source names, and removes duplicate questions.
2. **Feature-Level Fusion** combines multiple features describing each retrieved item: TF-IDF similarity, lexical overlap, category, skill, and difficulty similarity. Configurable weights produce one normalized feature-fusion score.
3. **Decision-Level Fusion** combines independent ranking decisions from TF-IDF, feature fusion, and source reliability. The resulting final score determines the ranked RAG context.

```text
Multiple Data Sources
	|
Data-Level Fusion
	|
Unified Data
	|
Feature Extraction
	|
Feature-Level Fusion
	|
Independent Decisions
	|
Decision-Level Fusion
	|
Final Ranked Result
	|
RAG / AI Interview System
```

Use `GET /fusion-status` to inspect source counts and confirm that all three stages are active.

## Requirements

- Python 3.11 or newer
- Optional: OpenAI API keys in `.env` for AI-powered features

## Setup

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your API keys:

```env
OPENAI_API_KEY=your_key_here
OPENAI_QUESTIONS_API_KEY=your_key_here
OPENAI_ANSWER_EVAL_API_KEY=your_key_here
OPENAI_FEEDBACK_API_KEY=your_key_here
OPENAI_SKILL_ANALYSIS_API_KEY=your_key_here
```

You can use the same OpenAI key for all five APIs.

## Run

**Windows:**

```bash
run.bat
```

**Manual:**

```bash
venv\Scripts\uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## Project Structure

```
AI_Interview_System/
├── backend/
│   ├── main.py          # FastAPI routes
│   ├── ai_service.py    # Question generation and evaluation
│   ├── api_config.py    # API key configuration (5 APIs)
│   ├── auth.py          # JWT authentication
│   ├── database.py      # SQLite database setup
│   └── models.py        # SQLAlchemy models
├── frontend/
│   ├── index.html       # Mock interview page
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── script.js
│   ├── dashboard.js
│   └── style.css
├── requirements.txt
└── run.bat
```

## Usage

1. Register an account at `/register`
2. Start a mock interview from the home page
3. Answer questions and review AI feedback
4. View your history and study plan on the dashboard

Interviews are saved automatically when you are logged in.
