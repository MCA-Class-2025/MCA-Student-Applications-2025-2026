@'
# ResearchIQ – AI-Powered Research Intelligence Platform

ResearchIQ is an AI-powered research platform that integrates research data, external APIs, data fusion, exploratory data analysis, machine learning and LLM-based research assistance.

## Project Repository

| Module | Description |
|---|---|
| [Dashboard](./Dashboard) | Dashboard source code and visualizations |
| [Dashboard Screenshots](./Dashboard/screenshots) | Dashboard and Data Explorer outputs |
| [LLM](./LLM) | LLM integration and research services |
| [EDA](./EDA) | Exploratory data analysis and practical notebooks |
| [Fusion](./Fusion) | Dataset integration and validation |
| [Datasets](./Datasets) | Original, API-collected and fused datasets |
| [Documents](./documents) | Phase 1 and Phase 2 project reports |
| [Algorithms](./algorithms) | Machine learning and sorting algorithms |
| [Backend](./backend) | Flask backend |
| [Frontend](./frontend) | React frontend |

## Project Features

- Research Paper Discovery
- Research Paper Comparison
- Dataset Discovery
- Research Project Advisor
- Research Paper Generator
- Citation Analysis and PDF Question Answering
- Data Explorer
- DSAA Analytics Dashboard
- Data Fusion and Quality Assessment

## Technology Stack

- Python
- Flask
- React.js
- Pandas and NumPy
- Scikit-learn
- Ollama
- Recharts

## Running the Application

Start Ollama:

    ollama serve

Start the backend in a separate terminal:

    cd backend
    python app.py

Start the frontend in another terminal:

    cd frontend
    npm install
    npm run dev

## Repository Organization

The categorized folders contain source code copies, datasets, notebooks and screenshots for academic review. The original executable application remains within the backend and frontend directories.

## Academic Project

Master of Computer Applications (MCA)
SNDT Women's University
Academic Year 2026-2027
'@ | Set-Content README.md -Encoding UTF8