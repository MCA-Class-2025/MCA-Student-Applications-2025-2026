# ScamShield AI

LLM-based scam message detection and explanation system.

## Model
Gemini 2.5 Flash.

## Five data-collection APIs
1. Google Safe Browsing
2. VirusTotal
3. AbuseIPDB
4. PhishTank
5. URLhaus

## Dataset
Every analysis submitted from the frontend is automatically appended to:
`data/scamshield_dataset.xlsx`

## Setup

### Windows
Open Command Prompt in this folder:

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and add your API keys.

Then run:

```text
python app.py
```

Open:

`http://127.0.0.1:5000`

## Important
Never put API keys inside HTML or JavaScript. Keep them in `.env`.

For initial frontend testing, you can enter a message without a URL. URL-based APIs will show `not_checked`; once the keys are configured and a URL is supplied, the five API integrations can collect external evidence.
