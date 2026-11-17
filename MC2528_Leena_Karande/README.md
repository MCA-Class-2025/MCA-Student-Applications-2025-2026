# DanceCompass AI — Cultural Heritage, Reimagined

DanceCompass AI is a Streamlit application for exploring a curated collection of dance traditions. It brings together structured dance profiles, open-data enrichment, exploratory data analysis (EDA), semantic retrieval, and optional Gemini-powered features in one interactive interface.

The project is designed to help users discover dance forms, compare their characteristics, explore related cultural references, and learn from a knowledge base grounded in the project's curated and enriched data.

## Features

- **Home dashboard** — introduces the platform and highlights selected dance traditions.
- **Explore Dance Forms** — browse and filter the collection by category, energy level, and solo/partner format; expand profiles to view origin, history, music, instruments, costume, movements, difficulty, and other details.
- **Dataset Insights** — interactive, filter-responsive charts and summary indicators for dance categories, energy, formation, learning difficulty, API enrichment coverage, profile text, and geographic origins.
- **AI Dance Guide** — ask questions about the dance collection using retrieval-augmented generation (RAG). Retrieved profile context is prepared locally using sentence-transformer embeddings and FAISS; Gemini is used to generate answers when an API key is configured.
- **Dance Recommender** — answer preference questions and receive ranked matches using a transparent rule-based scoring function. Gemini can optionally provide a natural-language explanation of the matches.
- **Dance Recognition / Image Guide** — upload an image and ask for a description of visible details such as costume, pose, instruments, or setting. This feature is a visual description assistant, not an automated dance-form or identity recognition system; it requires Gemini.
- **Upload Knowledge** — upload a PDF, extract its text, and add the extracted content to the session's searchable AI knowledge base.
- **Quiz** — answer questions based on the curated dance collection.
- **About** — overview of the platform and its approach.
- **Language selection and read-aloud** — supported answer-language translation uses Gemini; browser text-to-speech is used for read-aloud where available.

Some AI features require a Gemini API key. Browsing, filtering, the rule-based recommendation matches, quiz, and dataset analytics are designed to work from the local project data without Gemini generation.

## Data and API integration

The application uses a curated dataset of **20 dance forms** stored in `data/dance_forms.json`. Enrichment data is stored locally so the application can load the fused profiles without calling all external services every time it starts.

The five open-data services used by the API enrichment pipeline are:

| Source | Use in the project | Official service |
|---|---|---|
| Wikidata | Structured knowledge and entity references | [Wikidata API](https://www.wikidata.org/w/api.php) |
| Wikipedia | Summaries, extracts, thumbnails, and article links | [Wikipedia REST API](https://en.wikipedia.org/api/rest_v1/) |
| Nominatim / OpenStreetMap | Geocoding dance-origin locations | [Nominatim Search API](https://nominatim.org/release-docs/latest/api/Search/) |
| Open Library | Related book and literature references | [Open Library Search API](https://openlibrary.org/dev/docs/api/search) |
| MusicBrainz | Related music recordings and artist references | [MusicBrainz Web Service](https://musicbrainz.org/doc/MusicBrainz_API) |

The project also incorporates supplementary fields from the Kaggle **Dance Styles & Genres** dataset: [Kaggle dataset](https://www.kaggle.com/datasets/melissamonfared/dances). The fusion script uses a hand-reviewed alias map and carries selected supplementary fields such as tempo, hardness ratio, formation, learning difficulty, associated genre, and health benefits.

**Data-quality note:** the Kaggle source's `Origin` and `Dance Type` fields were found to contain unreliable values for some records. The project retains these as explicitly named raw/unverified fields and does not use them to overwrite the curated origin or category fields. See `kaggle_data/qa_findings.csv` and `kaggle_data/fuse_kaggle_dataset.py` for the documented checks and handling.

### Dataset files

| File | Description |
|---|---|
| `data/dance_forms.json` | Curated base collection of 20 dance-form profiles |
| `data/dancecompass_merged.csv` | Curated data enriched with text-analysis fields and five-API results (20 rows × 73 columns) |
| `data/dancecompass_final_fused_allsources.csv` | Final fused dataset, including supplementary Kaggle fields (20 rows × 83 columns) |
| `kaggle_data/dance_styles_kaggle.csv` | Local source copy of the Kaggle dataset |
| `kaggle_data/dancecompass_kaggle_fused.csv` | Kaggle enrichment matched to the curated dance forms |
| `kaggle_data/qa_findings.csv` | Data-quality findings for selected Kaggle fields |

The application reads the curated profiles and the final fused CSV when the corresponding files are available. It can fall back to curated profile content when enrichment data is unavailable.

## Exploratory Data Analysis

The repository contains EDA scripts and saved outputs for three stages of the data pipeline:

1. **Original curated dataset** — analysis of the 20 × 15 base dataset.
2. **Five-API enriched dataset** — data-quality checks, univariate, bivariate, and multivariate analysis of the 20 × 73 dataset.
3. **Final fused dataset** — analysis of the 20 × 83 dataset, including Kaggle-derived numeric fields.

Run the scripts from the project root:

```bash
python eda_1_original_curated/run_eda.py
python phase1_eda/run_eda.py
python eda_3_final_fused/run_eda.py
```

The scripts write summary tables and visualizations into their respective `outputs` folders. The repository also includes the earlier `eda.py` script and its saved outputs under `data/eda/`.

## Technology stack

- **Application:** Python, Streamlit, Streamlit Option Menu
- **Data processing:** Pandas, NumPy
- **Visualization:** Plotly, Matplotlib
- **Semantic retrieval:** Sentence Transformers, FAISS CPU
- **Generative AI:** Google Gemini via the `google-genai` SDK (optional; requires an API key)
- **PDF processing:** PyMuPDF, pypdf
- **Image handling:** Pillow
- **HTTP/API requests:** Requests

## Project structure

```text
DanceCompass/
├── app.py                         # Streamlit application entry point
├── requirements.txt               # Python dependencies
├── README.md
├── .env.example                   # Example environment-variable file
├── .gitignore
├── assets/                        # Application assets
├── data/
│   ├── dance_forms.json           # Curated dance-form profiles
│   ├── dancecompass_merged.csv    # Five-API enriched dataset
│   ├── dancecompass_final_fused_allsources.csv
│   └── eda/                       # Earlier EDA outputs
├── modules/                       # Streamlit page modules
├── utils/                         # Data, RAG, Gemini, translation, audio, and styling helpers
├── api_demo/                      # Individual API examples and fusion demonstration
├── scripts/                       # Data-enrichment refresh utility
├── kaggle_data/                   # Kaggle source, fusion, QA, and workbook scripts
├── eda_1_original_curated/        # EDA for the original curated dataset
├── phase1_eda/                    # EDA for the five-API dataset
├── eda_3_final_fused/             # EDA for the final fused dataset
└── build_final_fused_dataset.py   # Final fused-dataset build utility
```

## Setup and installation

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_PROJECT_FOLDER>
```

If you are downloading the project as a ZIP instead, extract it and open the extracted project folder in VS Code.

### 2. Create a virtual environment

Python **3.11** is recommended for the tested local setup.

**Windows (Command Prompt):**

```cmd
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Gemini (optional)

A Gemini API key is needed for AI-generated guide responses, generated recommendation explanations, image descriptions, and Gemini-based translation.

For local Streamlit configuration, create `.streamlit/secrets.toml` in the project root:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Alternatively, set the `GEMINI_API_KEY` environment variable before starting the app. Never commit your real API key, `.env`, or `.streamlit/secrets.toml` to GitHub. The repository's `.gitignore` is configured to exclude local secrets and the virtual environment.

### 5. Run the application

From the project root, with the virtual environment activated:

```bash
python -m streamlit run app.py
```

Open the local URL printed in the terminal (normally `http://localhost:8501`).

## API enrichment scripts

The API client examples are in `api_demo/`. The combined enrichment demonstration is in `api_demo/fusion_demo.py`. The refresh utility for the existing enrichment data is `scripts/refresh_enrichment.py`.

These scripts make requests to third-party public services. Their availability, response contents, rate limits, and usage policies are controlled by the respective providers. In particular, follow the Nominatim usage policy and avoid sending frequent or bulk requests from an unapproved client.

## Security and responsible use

- Keep API keys and other credentials out of source control.
- Do not upload `.env`, `.streamlit/secrets.toml`, or `.venv/` to GitHub.
- External API results can be incomplete, ambiguous, or unavailable; treat them as supplementary references and verify important cultural or historical claims.
- The image guide is intended to describe visible image content. It should not be used to infer a person's identity or sensitive personal attributes, or to claim that an image definitively identifies a dance form.
- Respect the terms, attribution requirements, and rate limits of each external data provider and dataset.

## Current scope and limitations

- The curated collection contains 20 dance forms; it is not intended to represent every dance tradition worldwide.
- External enrichment coverage varies by dance form and source.
- Gemini-dependent features are unavailable until a valid API key is configured and the service is reachable.
- PDF knowledge added through the upload page is added to the current application session's index; it is not a permanent replacement for the repository's source dataset.
- Browser text-to-speech availability depends on the user's browser and installed voices.

## Acknowledgements

DanceCompass AI uses information and services from Wikidata, Wikipedia, OpenStreetMap/Nominatim, Open Library, MusicBrainz, and the Kaggle Dance Styles & Genres dataset. Please consult each provider's documentation and terms for details on data use and attribution.

---

**Project:** DanceCompass AI  
**Application framework:** Streamlit  
**Primary language:** Python
