# Responsible AI-Based Risk Assessment System

## Overview

The Responsible AI-Based Risk Assessment System is an AI-powered cybersecurity application developed to assist administrators in analyzing user security risks within the SecureShare platform.

The system combines a Large Language Model (LLM), Retrieval-Augmented Generation (RAG), and a rule-based knowledge base to generate human-readable explanations and security recommendations based on real-time user risk assessment data.

---

## Features

- AI-powered Security Assistant
- User Risk Analysis
- Risk Explanation Generation
- Security Policy Retrieval (RAG)
- High Risk Users
- Medium Risk Users
- Low Risk Users
- Blocked Users
- Failed Login Summary
- Overall Risk Summary
- Integration with SecureShare

---

## Technologies Used

### Frontend
- PHP
- HTML
- CSS
- JavaScript

### Backend
- Python
- Flask

### Database
- MySQL

### AI Components
- Qwen 2.5-1.5B Instruct
- Retrieval-Augmented Generation (RAG)
- Rule-Based Knowledge Base

---

## Project Structure

```
Responsible_AI_Risk_Assessment/
│
├── config/
├── data/
├── knowledge_base/
│   ├── blocked_user_policy.txt
│   ├── failed_login_policy.txt
│   ├── high_risk_policy.txt
│   ├── low_risk_policy.txt
│   ├── medium_risk_policy.txt
│   ├── long_session_policy.txt
│   └── recommendation_policy.txt
│
├── src/
│   ├── app.py
│   ├── chatbot.py
│   ├── database.py
│   ├── rag_engine.py
│   ├── llm_engine.py
│   ├── risk_engine.py
│   ├── risk_assessment.py
│   └── utils.py
│
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Working

1. Administrator enters a query through the AI Security Assistant.
2. The chatbot detects the user's intent.
3. Relevant user information is retrieved from the MySQL database.
4. The appropriate security policy is retrieved from the knowledge base.
5. The retrieved information is combined into a prompt.
6. The Qwen Large Language Model generates a security explanation and recommendation.
7. The response is displayed in the chatbot.

---

## Example Queries

- Explain Rahul's risk
- Explain Mariam's risk
- Show high risk users
- Show medium risk users
- Show low risk users
- Show blocked users
- Show failed login attempts
- Risk summary

---

## Installation

### Clone the repository

git clone https://github.com/MCA-Class-2025/MCA-Student-Applications-2025-2026.git

cd MCA-Student-Applications-2025-2026/MC2503_Ansari_Shara

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure Database

- Import the `zero_trust_system.sql` database into MySQL.
- Update the MySQL connection details in `src/database.py`.

```python
host = "localhost"
user = "root"
password = ""
database = "zero_trust_system"
```

### Run the Application

```bash
python src/app.py
```

The Flask API will start on:

```
http://127.0.0.1:5000
```

---

## Future Scope

- Add semantic document retrieval using embedding models.
- Integrate vector databases such as FAISS or ChromaDB.
- Cloud deployment.
- Voice-enabled AI assistant.
- Real-time threat monitoring.

---

## Author

**Shara Ansari**

Master of Computer Applications (MCA)

SNDT Women's University

## GitHub Repository

[Responsible AI-Based Risk Assessment System](https://github.com/MCA-Class-2025/MCA-Student-Applications-2025-2026/tree/main/MC2503_Ansari_Shara)