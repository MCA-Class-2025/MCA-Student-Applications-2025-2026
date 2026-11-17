# SnapKnow

**Upload a photo, get a caption, a name, a confidence score and verified facts.**
SnapKnow is a Streamlit app that asks a vision LLM (Gemini, Claude, or a local Ollama model) what is in a
photo, then enriches the answer with live data from public APIs. Every analysis is saved to a history file,
so you can also ask follow-up questions about anything you have photographed before.

The full evaluation of the API-fusion and RAG work is in [`docs/SnapKnow_Full_Report.docx`](docs/SnapKnow_Full_Report.docx).

## Contents

1. [Features](#features)
2. [Quick start](#quick-start)
3. [API keys](#api-keys)
4. [Using the app](#using-the-app)
5. [Project structure](#project-structure)
6. [REST API](#rest-api)
7. [ML dataset and notebook](#ml-dataset-and-notebook)
8. [RAG knowledge base](#rag-knowledge-base)
9. [Troubleshooting](#troubleshooting)

## Features

**Image analysis**
- Caption, category, name, confidence, description, detailed facts and a fun fact for any photo.
- Three providers: Google Gemini, Anthropic Claude, or a local Ollama model.
- Output in English, Hindi, Marathi, Spanish or French. Changing the language re-explains the current photo.
- Persistent history in `snapknow_history.json`, plus bulk import of many images or a `.zip` of folders.

**Voice and export**
- Read-aloud (text-to-speech) and voice follow-up questions (speech-to-text).
- PDF report per image (with a QR code), or one combined PDF of your whole history.
- One-click ML-ready CSV export with text statistics and 23 numeric image features.

**Data enrichment (API fusion)**

| API | Gives you | Key needed? |
|---|---|---|
| Wikipedia | Summary and source link | No |
| USDA FoodData Central | Calories, protein, carbs, fat | Optional |
| GBIF | Scientific name, taxonomy, conservation status | No |
| TheMealDB | Recipe ingredients and instructions | No |
| OpenWeatherMap | Current weather for places | Optional |
| Unsplash | Reference photos | Optional |
| iNaturalist | Species profile and photo | No |
| OpenStreetMap (Nominatim) | Coordinates, address, map | No |
| REST Countries | Capital, population, currency, flag | No |
| Open Food Facts | Nutri-Score, NOVA group, allergens | No |
| Wikidata | Structured facts for any subject | No |

Only the APIs that make sense for a category are called (nutrition for Food, species data for Animal and
Flower, weather for Place, and so on).

## Quick start

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your keys (see "API keys" below)
cp .env.example .env              # Windows: copy .env.example .env

# 4. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

> **Audio note:** `gTTS` and `SpeechRecognition` call free Google web services, so they need an internet
> connection. Speech-to-text uses your browser microphone through `st.audio_input` (Streamlit 1.38 or newer),
> so allow microphone access when prompted.

## API keys

Put keys in `.env` (copied from `.env.example`) or paste them into the app sidebar. The sidebar overrides `.env`.
The variable names are **case-sensitive on macOS and Linux**, so keep them exactly as in `.env.example`.

| Variable | Used for | Where to get it |
|---|---|---|
| `GEMINI_API_KEY` | Gemini vision (free tier, recommended to start) | https://aistudio.google.com/apikey |
| `ANTHROPIC_API_KEY` | Claude vision (paid) | https://console.anthropic.com/ |
| `OLLAMA_BASE_URL`, `OLLAMA_VISION_MODEL` | Local vision model | https://ollama.com |
| `USDA_API_KEY` | USDA nutrition (blank falls back to the shared `DEMO_KEY`) | https://fdc.nal.usda.gov/api-key-signup |
| `UNSPLASH_ACCESS_KEY` | Reference photos | https://unsplash.com/developers |
| `OPENWEATHER_API_KEY` | Weather for places | https://openweathermap.org/api |

Every key is optional. Features whose key is blank are simply skipped. `.env` is git-ignored, so it never gets
committed. **Never share or upload your `.env` file.**

**Gemini notes:** the free tier is rate-limited, not unlimited. If you get a `429` error, wait and retry. If you
get `404 NOT_FOUND "model ... no longer available"`, Google has retired that model ID. Check
https://ai.google.dev/gemini-api/docs/models and update the model list in `app.py`.

## Using the app

1. Pick a provider and model in the sidebar and enter its key (or load it from `.env`).
2. Upload a photo and click **Analyze Image**.
3. Read the caption, category, name, confidence, description, facts and API enrichment.
4. Click **Read Aloud** to hear the result, or record a voice question and click **Transcribe & Ask**.
5. Download the PDF report, or open **Bulk Import** and **Collection Gallery** to work with many images.

## Project structure

```
SnapKnow/
├── app.py                        Streamlit app: UI, voice, PDF, history, API fusion
├── core.py                       Shared analysis logic (prompting, parsing, resizing, translation)
├── extra_apis.py                 iNaturalist, OpenStreetMap, REST Countries, Open Food Facts, Wikidata
├── rag.py                        TF-IDF retrieval over the fused data (no extra setup)
├── rag_engine.py                 Chroma + Ollama retrieval (needs a local Ollama server)
├── api_server.py                 Standalone FastAPI REST API
├── build_ml_dataset.py           Builds the ML-ready CSV from history or a folder of images
├── download_sample_images.py     Downloads ~50 free Wikimedia Commons photos for bulk import
├── snapknow_ml_starter.ipynb     Jupyter starter notebook (EDA, classification, clustering)
├── snapknow_history.json         Saved analyses (generated by the app)
├── snapknow_images/              Saved copies of analyzed photos
├── snapknow_knowledge_base.json  RAG documents built from API results
├── snapknow_ml_dataset.csv       Example ML-ready export
├── docs/                         Project report
├── .env.example                  Template for your API keys
├── requirements.txt              Python dependencies, grouped by purpose
└── pyproject.toml                Formatter and linter settings
```

`app.py` and `api_server.py` both import their core logic from `core.py`, so the web UI and the REST API share
exactly one implementation and cannot drift apart.

## REST API

```bash
uvicorn api_server:app --reload
```

Open http://127.0.0.1:8000/docs for interactive Swagger documentation.

| Endpoint | Purpose |
|---|---|
| `POST /analyze` | Upload an image (`file`) with `provider`, `model_name`, `api_key` and optional `language`, `question`. Returns the parsed result as JSON. |
| `POST /translate` | Translate an already-analyzed `result` into a `target_language` without re-uploading. |
| `GET /health` | Health check, returns `{"status": "ok"}`. |

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -F "file=@/path/to/photo.jpg" \
  -F "provider=gemini" \
  -F "model_name=gemini-3.6-flash" \
  -F "api_key=YOUR_GEMINI_API_KEY"
```

## ML dataset and notebook

**In the app (easiest):** open **Bulk Import**, upload images (or a `.zip` of folders) and click
**Analyze all & add to history**. Then open **Collection Gallery** and **Prepare ML-ready CSV**. The file is
downloadable and also saved as `snapknow_ml_dataset.csv`. Free API tiers are rate-limited, so start with 25 to 50
images per run and keep the delay at 3 seconds or more.

**Need photos fast?** `python download_sample_images.py` downloads about 50 freely licensed photos from Wikimedia
Commons into `sample_images.zip`, with a `CREDITS.csv` of authors and licences. Keep `CREDITS.csv` with your
project because the licences require attribution.

**From the command line:**

```bash
python build_ml_dataset.py                                       # from saved history (offline)
python build_ml_dataset.py --folder my_images --provider gemini  # label a whole folder in bulk
python build_ml_dataset.py --folder my_images --enrich           # add iNaturalist / Open Food Facts / geo columns
```

If `my_images` has sub-folders named after the true class (`Animal/`, `Food/`, ...), the CSV also gets a
`true_label` column and an `ai_correct` column. Then run `jupyter notebook` and open
`snapknow_ml_starter.ipynb`.

## RAG knowledge base

- **`rag.py`** builds a small knowledge base from the Wikipedia, USDA, GBIF, TheMealDB and weather results, and
  retrieves facts with TF-IDF and cosine similarity. It needs no extra API key or model download.
- **`rag_engine.py`** is a heavier option: a Chroma vector store over your history using Ollama
  (`nomic-embed-text` and `llama3.2`). It needs a running local Ollama server.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Error calling API" | Check the key is correct and has credit or quota. |
| Key in `.env` is not picked up | Variable names are case-sensitive. Use the exact names from `.env.example`. |
| Microphone recorder missing | Upgrade Streamlit: `pip install -U streamlit`. |
| Speech-to-text fails | It needs internet access. For offline use, swap in `openai-whisper`. |
| PDF shows garbled characters | `fpdf2` built-in fonts are Latin-1 only. Add a Unicode TTF font with `pdf.add_font(...)`. |
| RAG with Ollama fails | Start the Ollama server and pull the models (`ollama pull nomic-embed-text llama3.2`). |
