import os
import csv
import re
import json
from xml.sax.saxutils import escape
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER


# ============================================================
# LOAD ENVIRONMENT
# ============================================================
load_dotenv()


# ============================================================
# STANDALONE FLASK APPLICATION
# ============================================================
app = Flask(__name__)


# ============================================================
# CORS CONFIGURATION
# ============================================================
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ],
            "methods": [
                "GET",
                "POST",
                "OPTIONS",
            ],
            "allow_headers": [
                "Content-Type",
                "Authorization",
            ],
        }
    },
    supports_credentials=False,
)


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    allowed_origins = {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }

    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization"
        )
        response.headers["Access-Control-Max-Age"] = "3600"

    return response


# ============================================================
# EXPLICIT CORS PREFLIGHT HANDLING
# ============================================================
@app.before_request
def handle_cors_preflight():
    if request.method == "OPTIONS":
        response = jsonify({
            "success": True
        })

        origin = request.headers.get("Origin")

        allowed_origins = {
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        }

        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization"
            )

        return response, 200


# ============================================================
# CONFIGURATION
# ============================================================
CORE_API_KEY = os.getenv("CORE_API_KEY")
OLLAMA_MODEL = "qwen2.5:1.5b"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
CORE_BASE_URL = "https://api.core.ac.uk/v3"


# ============================================================
# ROUTES
# ============================================================
CORE_SEARCH_ROUTE = "/api/core/search"
PAPER_GENERATION_ROUTE = "/api/core/generate-paper"
PAPER_DOWNLOAD_ROUTE = "/api/core/download/<path:filename>"


# ============================================================
# DIRECTORIES
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "datasets"
PAPER_DIR = DATASET_DIR / "generated_papers"
CSV_FILE = DATASET_DIR / "research_paper_generation.csv"

DATASET_DIR.mkdir(
    parents=True,
    exist_ok=True
)

PAPER_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# PAPER MODULES
# ============================================================
PAPER_MODULES = {
    "abstract": {
        "title": "Abstract & Executive Summary",
        "description": (
            "Summarize the research problem, approach, "
            "key findings and significance."
        ),
    },
    "introduction": {
        "title": "Introduction",
        "description": (
            "Introduce the research area, background, "
            "problem and motivation."
        ),
    },
    "objectives": {
        "title": "Research Objectives",
        "description": (
            "Define the major objectives and goals "
            "of the proposed research."
        ),
    },
    "literature_review": {
        "title": "Literature Review",
        "description": (
            "Analyze existing research, approaches, "
            "findings and research gaps."
        ),
    },
    "methodology": {
        "title": "Methodology",
        "description": (
            "Describe the proposed research methodology, "
            "techniques and workflow."
        ),
    },
    "architecture": {
        "title": "System Architecture",
        "description": (
            "Explain the system design, components, "
            "data flow and architecture."
        ),
    },
    "results_discussion": {
        "title": "Results & Discussion",
        "description": (
            "Present expected or available results "
            "and discuss their significance."
        ),
    },
    "challenges": {
        "title": "Challenges & Limitations",
        "description": (
            "Discuss technical challenges, limitations "
            "and research constraints."
        ),
    },
    "future_scope": {
        "title": "Future Scope",
        "description": (
            "Explain possible improvements, extensions "
            "and future research directions."
        ),
    },
    "conclusion_references": {
        "title": "Conclusion & References",
        "description": (
            "Conclude the research and provide properly "
            "structured references."
        ),
    },
}


# ============================================================
# CSV COLUMNS
# ============================================================
CSV_COLUMNS = [
    "timestamp",
    "action",
    "topic",
    "supporting_paper_count",
    "supporting_papers",
    "title",
    "core_search_success",
    "core_search_query",
    "pdf_path",
]


# ============================================================
# CSV STORAGE
# ============================================================
def _csv_value(value):
    """
    Convert any Python value into a safe CSV string.

    Strings/numbers/bools are stored normally.

    Lists/dictionaries are stored as JSON.
    """
    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        try:
            return json.dumps(
                value,
                ensure_ascii=False
            )
        except (TypeError, ValueError):
            return str(value)

    return str(value)


def ensure_csv():
    """
    Make sure the dataset directory, paper directory,
    and CSV file exist.

    If the CSV does not exist, create it with CSV_COLUMNS.
    """
    DATASET_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    PAPER_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if not CSV_FILE.exists():
        with open(
            CSV_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=CSV_COLUMNS
            )
            writer.writeheader()


def _read_csv_data():
    """
    Read the existing CSV.
    """
    ensure_csv()

    if CSV_FILE.stat().st_size == 0:
        return [], CSV_COLUMNS

    with open(
        CSV_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:
        reader = csv.DictReader(file)
        rows = []

        for row in reader:
            rows.append(dict(row))

        return rows, reader.fieldnames or CSV_COLUMNS


def append_csv_row(**values):
    """
    Append one generated-paper record to the CSV.

    Only columns defined in CSV_COLUMNS are stored.
    """
    ensure_csv()

    rows, fieldnames = _read_csv_data()

    new_row = {
        column: ""
        for column in CSV_COLUMNS
    }

    for key, value in values.items():
        if key in CSV_COLUMNS:
            new_row[key] = _csv_value(value)

    rows.append(new_row)

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSV_COLUMNS,
            extrasaction="ignore"
        )

        writer.writeheader()

        for row in rows:
            writer.writerow({
                column: _csv_value(
                    row.get(column, "")
                )
                for column in CSV_COLUMNS
            })


# ============================================================
# CSV CLEANING
# ============================================================
def clean_csv():
    """
    Clean the existing CSV.

    Duplicate rows are removed while preserving CSV_COLUMNS.
    """
    ensure_csv()

    rows, _ = _read_csv_data()

    if not rows:
        return

    cleaned_rows = []
    seen = set()

    for row in rows:
        cleaned = {
            column: _clean_text(
                row.get(column, "")
            )
            for column in CSV_COLUMNS
        }

        key = tuple(
            cleaned.get(column, "")
            for column in CSV_COLUMNS
        )

        if key not in seen:
            seen.add(key)
            cleaned_rows.append(cleaned)

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSV_COLUMNS,
            extrasaction="ignore"
        )

        writer.writeheader()

        for row in cleaned_rows:
            writer.writerow(row)


# ============================================================
# TEXT HELPERS
# ============================================================
def _clean_text(value):
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value)
    ).strip()


def _list_to_csv(values):
    if not values:
        return ""

    cleaned_values = []

    for value in values:
        if isinstance(value, dict):
            value = (
                value.get("id")
                or value.get("title")
                or ""
            )

        clean_value = _clean_text(value)

        if clean_value:
            cleaned_values.append(clean_value)

    return "; ".join(cleaned_values)


# ============================================================
# SAVE CORE SEARCH RESULTS
# ============================================================
def save_search_results(
    results,
    topic
):
    timestamp = datetime.now().isoformat()

    for paper in results:
        row_data = {
            "timestamp": timestamp,
            "action": "supporting_literature_search",
            "topic": topic,
            "technology": "",
            "prompt": "",
            "modules": "",
            "selected_module_ids": "",
            "supporting_paper_count": 1,
            "supporting_papers": paper,
            "title": "",
            "paper": "",
            "output_format": "",
            "status": "success",
            "pdf_download_url": "",
            "docx_download_url": "",
            "pdf_path": "",
            "docx_path": "",
            "core_search_success": True,
            "core_search_query": topic,
            "core_error": "",
            "error": "",
        }

        append_csv_row(
            **row_data
        )


# ============================================================
# SAVE PAPER GENERATION
# ============================================================
def log_paper_generation(
    topic="",
    modules=None,
    supporting_papers=None,
    title="",
    output_format="pdf",
    status="success",
    pdf_download_url="",
    docx_download_url="",
    error="",
    prompt="",
    technology="",
    paper="",
    selected_module_ids=None,
    core_search_success="",
    core_search_query="",
    core_error="",
    docx_path="",
    pdf_path="",
):
    modules = modules or []

    supporting_papers = (
        supporting_papers or []
    )

    selected_module_ids = (
        selected_module_ids or []
    )

    row_data = {
        "timestamp": datetime.now().isoformat(),
        "action": "generate_research_paper",
        "topic": topic,
        "technology": technology,
        "prompt": prompt,
        "modules": modules,
        "selected_module_ids": selected_module_ids,
        "supporting_paper_count": len(
            supporting_papers
        ),
        "supporting_papers": supporting_papers,
        "title": title,
        "paper": paper,
        "output_format": output_format,
        "status": status,
        "pdf_download_url": pdf_download_url,
        "docx_download_url": docx_download_url,
        "pdf_path": pdf_path,
        "docx_path": docx_path,
        "core_search_success": core_search_success,
        "core_search_query": core_search_query,
        "core_error": core_error,
        "error": error,
    }

    append_csv_row(
        **row_data
    )


# ============================================================
# TOPIC RESOLUTION
# ============================================================
def resolve_topic(
    topic=None,
    advisor_topic=None,
    research_topic=None,
    selected_topic=None,
    generated_topic=None,
):
    possible_topics = [
        topic,
        advisor_topic,
        research_topic,
        selected_topic,
        generated_topic,
    ]

    for value in possible_topics:
        if isinstance(
            value,
            str
        ):
            value = value.strip()

            if value:
                return value

        if isinstance(
            value,
            dict
        ):
            for key in (
                "topic",
                "title",
                "research_topic",
                "selected_topic"
            ):
                nested = value.get(key)

                if (
                    isinstance(
                        nested,
                        str
                    )
                    and nested.strip()
                ):
                    return nested.strip()

    return ""


# ============================================================
# MODULE VALIDATION
# ============================================================
def normalize_modules(modules):
    if not isinstance(
        modules,
        list
    ):
        raise ValueError(
            "Research paper modules must be provided as a list of objects."
        )

    normalized = []

    for module in modules:
        if isinstance(
            module,
            dict
        ):
            module_id = _clean_text(
                module.get(
                    "id",
                    ""
                )
            )

            if not module_id:
                continue

        elif isinstance(
            module,
            str
        ):
            module_id = module.strip()

        else:
            continue

        if module_id not in PAPER_MODULES:
            raise ValueError(
                f"Invalid research paper module: {module_id}"
            )

        if module_id not in normalized:
            normalized.append(
                module_id
            )

    if not normalized:
        raise ValueError(
            "At least one research paper module is required."
        )

    return normalized


def module_details(module_ids):
    return [
        {
            "id": module_id,
            "title": PAPER_MODULES[
                module_id
            ]["title"],
            "description": PAPER_MODULES[
                module_id
            ]["description"],
        }
        for module_id in module_ids
    ]


# ============================================================
# SUPPORTING PAPER VALIDATION
# ============================================================
def normalize_supporting_papers(papers):
    if papers is None:
        return []

    if not isinstance(
        papers,
        list
    ):
        raise ValueError(
            "supporting_papers must be a list of objects."
        )

    normalized = []
    seen = set()

    for paper in papers:
        if not isinstance(
            paper,
            dict
        ):
            continue

        core_id = _clean_text(
            paper.get(
                "core_id",
                ""
            )
        )

        doi = _clean_text(
            paper.get(
                "doi",
                ""
            )
        )

        title = _clean_text(
            paper.get(
                "title",
                ""
            )
        )

        identity = (
            core_id
            or doi
            or title
        )

        if (
            not identity
            or identity in seen
        ):
            continue

        seen.add(identity)

        authors = paper.get(
            "authors",
            []
        )

        if not isinstance(
            authors,
            list
        ):
            authors = (
                [authors]
                if authors
                else []
            )

        normalized.append({
            "title": title,
            "authors": [
                _clean_text(author)
                for author in authors
                if _clean_text(author)
            ],
            "doi": doi,
            "core_id": core_id,
            "publication_year": _clean_text(
                paper.get(
                    "publication_year",
                    ""
                )
            ),
            "journal": _clean_text(
                paper.get(
                    "journal",
                    ""
                )
            ),
            "abstract": _clean_text(
                paper.get(
                    "abstract",
                    ""
                )
            ),
            "download_url": _clean_text(
                paper.get(
                    "download_url",
                    ""
                )
            ),
        })

    return normalized


# ============================================================
# API HEADERS
# ============================================================
def get_core_headers():
    headers = {
        "Accept": "application/json"
    }

    if CORE_API_KEY:
        headers["Authorization"] = (
            f"Bearer {CORE_API_KEY}"
        )

    return headers


def get_ollama_headers():
    return {
        "Content-Type": "application/json"
    }


# ============================================================
# API STATUS
# ============================================================
def check_api_keys():
    return {
        "core": bool(
            CORE_API_KEY
        ),
        "ollama": bool(
            OLLAMA_MODEL
        ),
        "success": bool(
            OLLAMA_MODEL
        ),
    }


# ============================================================
# CORE PAPER FORMATTER
# ============================================================
def format_paper(
    item,
    query="",
    technology=""
):
    authors = []

    raw_authors = item.get(
        "authors",
        []
    )

    if isinstance(
        raw_authors,
        list
    ):
        for author in raw_authors:
            if isinstance(
                author,
                dict
            ):
                name = (
                    author.get("name")
                    or author.get("displayName")
                    or ""
                )
            else:
                name = str(
                    author
                )

            if name:
                authors.append(
                    name.strip()
                )

    publication_year = (
        item.get(
            "yearPublished"
        )
        or item.get(
            "publicationYear"
        )
        or ""
    )

    journal = ""

    journals = item.get(
        "journals",
        []
    )

    if (
        isinstance(
            journals,
            list
        )
        and journals
    ):
        first = journals[0]

        if isinstance(
            first,
            dict
        ):
            journal = (
                first.get("title")
                or first.get("name")
                or ""
            )

    source = ""

    sources = item.get(
        "sources",
        []
    )

    if (
        isinstance(
            sources,
            list
        )
        and sources
    ):
        first = sources[0]

        if isinstance(
            first,
            dict
        ):
            source = first.get(
                "name",
                ""
            )

    return {
        "query": query,
        "technology": technology,
        "title": item.get(
            "title",
            ""
        ),
        "doi": item.get(
            "doi",
            ""
        ),
        "core_id": item.get(
            "id",
            ""
        ),
        "authors": authors,
        "publication_year": publication_year,
        "publisher": item.get(
            "publisher",
            ""
        ),
        "journal": journal,
        "abstract": (
            item.get(
                "abstract",
                ""
            )
            or ""
        ),
        "download_url": item.get(
            "downloadUrl",
            ""
        ),
        "source": source,
        "type": item.get(
            "documentType",
            ""
        ),
    }


# ============================================================
# CORE SUPPORTING LITERATURE SEARCH
# ============================================================
def search_core(
    query,
    limit=10,
    offset=0,
    technology=""
):
    query = _clean_text(
        query
    )

    if not query:
        return {
            "success": False,
            "error": "CORE search query is required.",
            "results": [],
        }

    if not CORE_API_KEY:
        return {
            "success": False,
            "error": (
                "CORE_API_KEY is missing from the .env file."
            ),
            "results": [],
        }

    try:
        limit = max(
            1,
            min(
                int(limit),
                20
            )
        )
    except (
        TypeError,
        ValueError
    ):
        limit = 10

    try:
        offset = max(
            0,
            int(offset)
        )
    except (
        TypeError,
        ValueError
    ):
        offset = 0

    url = (
        f"{CORE_BASE_URL}/search/works"
    )

    params = {
        "q": query,
        "limit": limit,
        "offset": offset,
    }

    response = None

    try:
        response = requests.get(
            url,
            headers=get_core_headers(),
            params=params,
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        results = [
            format_paper(
                item,
                query=query,
                technology=technology,
            )
            for item in data.get(
                "results",
                []
            )
        ]

        if results:
            save_search_results(
                results,
                topic=query,
            )

        return {
            "success": True,
            "query": query,
            "total_results": data.get(
                "totalHits",
                0
            ),
            "limit": limit,
            "offset": offset,
            "results": results,
        }

    except requests.exceptions.HTTPError as exc:
        status_code = (
            response.status_code
            if response is not None
            else "unknown"
        )

        return {
            "success": False,
            "error": (
                f"CORE API HTTP error "
                f"{status_code}: {exc}"
            ),
            "results": [],
        }

    except requests.exceptions.RequestException as exc:
        return {
            "success": False,
            "error": (
                f"CORE API request failed: {exc}"
            ),
            "results": [],
        }

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "results": [],
        }


# ============================================================
# SUPPORTING LITERATURE
# ============================================================
def search_supporting_literature(
    topic,
    technology="",
    limit=8
):
    topic = resolve_topic(
        topic=topic
    )

    if not topic:
        return {
            "success": False,
            "error": (
                "No research topic was received."
            ),
            "results": [],
        }

    query_parts = [
        topic
    ]

    if _clean_text(
        technology
    ):
        query_parts.append(
            _clean_text(
                technology
            )
        )

    query = " ".join(
        query_parts
    ).strip()

    return search_core(
        query=query,
        limit=limit,
        technology=technology,
    )


# ============================================================
# LITERATURE CONTEXT
# ============================================================
def build_literature_context(
    papers
):
    if not papers:
        return (
            "No supporting papers were retrieved from CORE. "
            "Do not invent references."
        )

    context_parts = []

    for index, paper in enumerate(
        papers,
        start=1
    ):
        authors = ", ".join(
            paper.get(
                "authors",
                []
            )
        )

        context_parts.append(
            f"""
SOURCE {index}

Title:

{paper.get('title', '')}

Authors:

{authors}

Year:

{paper.get('publication_year', '')}

Journal:

{paper.get('journal', '')}

DOI:

{paper.get('doi', '')}

Abstract:

{paper.get('abstract', '')}

CORE ID:

{paper.get('core_id', '')}
""".strip()
        )

    return "\n\n".join(
        context_parts
    )


# ============================================================
# MODULE INSTRUCTIONS
# ============================================================
def build_module_instructions(
    module_ids
):
    details = module_details(
        module_ids
    )

    blocks = []

    for index, module in enumerate(
        details,
        start=1
    ):
        blocks.append(
            f"{index}. {module['title']}\n"
            f"   ID: {module['id']}\n"
            f"   Purpose: {module['description']}"
        )

    return "\n\n".join(
        blocks
    )


# ============================================================
# SELECTED STRUCTURE
# ============================================================
def build_selected_structure(
    module_ids
):
    structures = {
        "abstract":
            "ABSTRACT & EXECUTIVE SUMMARY",

        "introduction":
            "INTRODUCTION",

        "objectives":
            "RESEARCH OBJECTIVES",

        "literature_review":
            "LITERATURE REVIEW",

        "methodology":
            "METHODOLOGY",

        "architecture":
            "SYSTEM ARCHITECTURE",

        "results_discussion":
            "RESULTS & DISCUSSION",

        "challenges":
            "CHALLENGES & LIMITATIONS",

        "future_scope":
            "FUTURE SCOPE",

        "conclusion_references":
            "CONCLUSION & REFERENCES",
    }

    return "\n".join(
        f"{index}. {structures[module_id]}"
        for index, module_id
        in enumerate(
            module_ids,
            start=1
        )
    )


# ============================================================
# OLLAMA RESEARCH PAPER GENERATION
# ============================================================
def generate_research_paper(
    topic,
    modules,
    prompt="",
    technology="",
    papers=None
):
    topic = resolve_topic(
        topic=topic
    )

    if not topic:
        raise ValueError(
            "Research topic is required."
        )

    module_ids = normalize_modules(
        modules
    )

    papers = normalize_supporting_papers(
        papers
    )

    literature_context = (
        build_literature_context(
            papers
        )
    )

    module_instructions = (
        build_module_instructions(
            module_ids
        )
    )

    selected_structure = (
        build_selected_structure(
            module_ids
        )
    )

    user_prompt = f"""
Create the selected sections of a professional academic research paper.

The research topic below is the topic selected for the Research Paper
Generation page and MUST remain the central subject of every generated section.

============================================================
RESEARCH TOPIC
============================================================

{topic}

============================================================
TECHNOLOGY / METHOD
============================================================

{technology or "Not specified"}

============================================================
SELECTED PAPER MODULES
============================================================

{module_instructions}

============================================================
REQUIRED OUTPUT STRUCTURE
============================================================

{selected_structure}

============================================================
USER INSTRUCTIONS
============================================================

{prompt or "Generate academically appropriate content for the selected modules."}

============================================================
SUPPORTING LITERATURE SUPPLIED BY CORE
============================================================

{literature_context}

============================================================
ACADEMIC RULES
============================================================

1. Generate ONLY the selected modules listed above.

2. Do not generate unselected modules as separate sections.

3. Keep every section specifically connected to the supplied research topic.

4. Use the supplied CORE papers as supporting evidence when relevant.

5. Do not copy sentences from CORE papers.

6. Cite sources only when a supplied CORE paper supports the statement.

7. Never invent papers, authors, journals, DOIs or CORE IDs.

8. If no supporting literature is supplied, do not invent references.

9. For Conclusion & References, include references only if that module was selected.

10. For Methodology, include a topic-specific workflow when that module was selected.

11. For System Architecture, describe the topic-specific architecture/data flow when selected.

12. For Results & Discussion, clearly distinguish expected/proposed findings from measured findings.

13. Keep the writing suitable for an MCA/student academic research project.

14. Produce actual academic research-paper content rather than a generic research-topic explanation.

15. Return ONLY the generated academic content.

16. Do not mention the first-page Research Generator.

17. Do not add an introduction such as "Here is your paper".
""".strip()

    payload = {
        "model": OLLAMA_MODEL,

        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an academic research paper writing assistant "
                    "for a dedicated Research Paper Generation system. "
                    "Produce structured, original, topic-specific academic "
                    "content and obey the selected-module contract exactly."
                ),
            },
            {
                "role": "user",
                "content": user_prompt
            },
        ],

        "stream": False,

        "options": {
            "temperature": 0.3,
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            headers=get_ollama_headers(),
            json=payload,
            timeout=600,
        )

        response.raise_for_status()

        data = response.json()

        message = data.get(
            "message"
        ) or {}

        raw_content = message.get(
            "content"
        ) or ""

        content = str(
            raw_content
        ).strip()

        if not content:
            raise RuntimeError(
                "Ollama returned no generated content. "
                f"Response received: {data}"
            )

        return {
            "success": True,
            "paper": content,
            "modules": module_ids,
        }

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            f"Research paper generation failed: {exc}"
        ) from exc


# ============================================================
# FILE HELPERS
# ============================================================
def safe_filename(
    text,
    max_length=80
):
    text = re.sub(
        r"[^a-zA-Z0-9\s\_-]",
        "",
        str(text)
    )

    text = re.sub(
        r"\s+",
        "_",
        text
    )

    return (
        text[:max_length]
        .strip("_")
        or "research_paper"
    )


def relative_web_path(path):
    if not path:
        return ""

    try:
        return str(
            Path(path).relative_to(
                BASE_DIR
            )
        ).replace(
            os.sep,
            "/"
        )

    except ValueError:
        return str(
            Path(path)
        ).replace(
            os.sep,
            "/"
        )


# ============================================================
# HEADING DETECTION
# ============================================================
def _is_heading(
    line,
    module_ids
):
    upper = line.upper().strip()

    selected_titles = {
        PAPER_MODULES[
            module_id
        ]["title"].upper()
        for module_id in module_ids
    }

    generic = {
        "ABSTRACT",
        "ABSTRACT & EXECUTIVE SUMMARY",
        "KEYWORDS",
        "INTRODUCTION",
        "RESEARCH OBJECTIVES",
        "LITERATURE REVIEW",
        "METHODOLOGY",
        "SYSTEM ARCHITECTURE",
        "RESULTS & DISCUSSION",
        "CHALLENGES & LIMITATIONS",
        "FUTURE SCOPE",
        "CONCLUSION & REFERENCES",
        "REFERENCES",
    }

    numbered_heading = bool(
        re.match(
            r"^\d+(?:\.\d+)?\.?\s+",
            upper
        )
    )

    return (
        upper in selected_titles
        or upper in generic
        or numbered_heading
    )


# ============================================================
# CREATE DOCX
# ============================================================
def create_docx(
    title,
    paper_text,
    filename,
    module_ids
):
    path = PAPER_DIR / filename

    document = Document()

    heading = document.add_heading(
        title,
        0
    )

    heading.alignment = 1

    document.add_paragraph(
        f"Generated by Research IQ\n"
        f"{datetime.now().strftime('%d %B %Y')}"
    )

    document.add_page_break()

    for line in paper_text.splitlines():
        line = line.strip()

        if not line:
            continue

        if _is_heading(
            line,
            module_ids
        ):
            document.add_heading(
                line,
                level=1
            )

        else:
            document.add_paragraph(
                line
            )

    document.save(path)

    return str(path)


# ============================================================
# CREATE PDF
# ============================================================
def create_pdf(
    title,
    paper_text,
    filename,
    module_ids
):
    path = PAPER_DIR / filename

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER

    heading_style = styles["Heading1"]

    body_style = styles["BodyText"]
    body_style.leading = 15

    document = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    elements = [
        Paragraph(
            escape(title),
            title_style
        ),

        Spacer(
            1,
            20
        ),

        Paragraph(
            "Generated by Research IQ",
            body_style
        ),

        Spacer(
            1,
            20
        ),
    ]

    for line in paper_text.splitlines():
        line = line.strip()

        if not line:
            elements.append(
                Spacer(
                    1,
                    8
                )
            )
            continue

        safe_line = escape(
            line
        )

        if _is_heading(
            line,
            module_ids
        ):
            elements.append(
                Paragraph(
                    safe_line,
                    heading_style
                )
            )

        else:
            elements.append(
                Paragraph(
                    safe_line,
                    body_style
                )
            )

    document.build(
        elements
    )

    return str(path)


# ============================================================
# MAIN PAPER GENERATION WORKFLOW
# ============================================================
def generate_research_paper_files(
    topic=None,
    prompt="",
    technology="",
    modules=None,
    supporting_papers=None,
    output_format="pdf",
    literature_limit=8,
    advisor_topic=None,
    research_topic=None,
    selected_topic=None,
    generated_topic=None,
):
    ensure_csv()

    resolved_topic = resolve_topic(
        topic=topic,
        advisor_topic=advisor_topic,
        research_topic=research_topic,
        selected_topic=selected_topic,
        generated_topic=generated_topic,
    )

    if not resolved_topic:
        raise ValueError(
            "Research topic is required. "
            "No topic was received for the Research Paper Generation page."
        )

    module_ids = normalize_modules(
        modules or []
    )

    selected_papers = (
        normalize_supporting_papers(
            supporting_papers
        )
    )

    output_format = (
        _clean_text(
            output_format
        ).lower()
        or "pdf"
    )

    if output_format not in {
        "pdf",
        "docx",
        "both"
    }:
        raise ValueError(
            "output_format must be 'pdf', 'docx', or 'both'."
        )

    # ========================================================
    # SUPPORTING LITERATURE
    # ========================================================
    literature = {
        "success": False,
        "results": [],
        "error": "",
        "query": resolved_topic,
    }

    if selected_papers:
        papers = selected_papers

        literature["success"] = True
        literature["results"] = papers
        literature["query"] = resolved_topic

    elif CORE_API_KEY:
        literature = (
            search_supporting_literature(
                topic=resolved_topic,
                technology=technology,
                limit=literature_limit,
            )
        )

        papers = literature.get(
            "results",
            []
        )

    else:
        papers = []

        literature["error"] = (
            "CORE_API_KEY is missing. "
            "Paper will be generated without CORE literature."
        )

    core_error = literature.get(
        "error",
        ""
    )

    # ========================================================
    # GENERATE PAPER
    # ========================================================
    generated = generate_research_paper(
        topic=resolved_topic,
        modules=module_ids,
        prompt=prompt,
        technology=technology,
        papers=papers,
    )

    paper_text = generated[
        "paper"
    ]

    title = resolved_topic.strip()

    base_name = (
        safe_filename(
            resolved_topic
        )
        + "_Research_Paper_"
        + datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
    )

    docx_path = ""
    pdf_path = ""

    # ========================================================
    # DOCX
    # ========================================================
    if output_format in {
        "docx",
        "both"
    }:
        docx_path = create_docx(
            title=title,
            paper_text=paper_text,
            filename=(
                base_name
                + ".docx"
            ),
            module_ids=module_ids,
        )

    # ========================================================
    # PDF
    # ========================================================
    if output_format in {
        "pdf",
        "both"
    }:
        pdf_path = create_pdf(
            title=title,
            paper_text=paper_text,
            filename=(
                base_name
                + ".pdf"
            ),
            module_ids=module_ids,
        )

    # ========================================================
    # DOWNLOAD INFORMATION
    # ========================================================
    pdf_filename = (
        Path(pdf_path).name
        if pdf_path
        else ""
    )

    docx_filename = (
        Path(docx_path).name
        if docx_path
        else ""
    )

    pdf_download_url = (
        f"/api/core/download/{pdf_filename}"
        if pdf_filename
        else ""
    )

    docx_download_url = (
        f"/api/core/download/{docx_filename}"
        if docx_filename
        else ""
    )

    # ========================================================
    # DATASET LOGGING
    # ========================================================
    generation_error = ""

    if core_error:
        generation_error = (
            f"CORE literature warning: "
            f"{core_error}"
        )

    log_paper_generation(
        topic=resolved_topic,

        modules=module_details(
            module_ids
        ),

        selected_module_ids=module_ids,

        supporting_papers=papers,

        title=title,

        prompt=prompt,

        technology=technology,

        paper=paper_text,

        output_format=output_format,

        status="success",

        pdf_download_url=pdf_download_url,

        docx_download_url=docx_download_url,

        pdf_path=relative_web_path(
            pdf_path
        ),

        docx_path=relative_web_path(
            docx_path
        ),

        core_search_success=literature.get(
            "success",
            False
        ),

        core_search_query=literature.get(
            "query",
            resolved_topic
        ),

        core_error=core_error,

        error=generation_error,
    )

    # ========================================================
    # RETURN RESULT
    # ========================================================
    return {
        "success": True,

        "feature":
            "research_paper_generation",

        "route":
            PAPER_GENERATION_ROUTE,

        "topic":
            resolved_topic,

        "title":
            title,

        "prompt":
            prompt,

        "technology":
            technology,

        "modules":
            module_details(
                module_ids
            ),

        "selected_module_ids":
            module_ids,

        "paper":
            paper_text,

        "supporting_papers":
            papers,

        "supporting_paper_count":
            len(papers),

        "core_search_success":
            literature.get(
                "success",
                False
            ),

        "core_search_query":
            literature.get(
                "query",
                resolved_topic
            ),

        "core_error":
            core_error,

        "output_format":
            output_format,

        "docx_path":
            relative_web_path(
                docx_path
            ),

        "pdf_path":
            relative_web_path(
                pdf_path
            ),

        "download_url":
            pdf_download_url,

        "pdf_download_url":
            pdf_download_url,

        "docx_download_url":
            docx_download_url,

        "dataset_path":
            relative_web_path(
                str(CSV_FILE)
            ),
    }


# ============================================================
# GENERATION ENTRY POINTS
# ============================================================
def generate_from_advisor(
    advisor_topic,
    advisor_technology="",
    user_prompt="",
    modules=None,
    supporting_papers=None,
    output_format="pdf",
):
    return generate_research_paper_files(
        topic=advisor_topic,
        technology=advisor_technology,
        prompt=user_prompt,
        modules=modules,
        supporting_papers=supporting_papers,
        output_format=output_format,
        literature_limit=8,
    )


def generate_from_topic_signal(
    topic=None,
    technology="",
    prompt="",
    modules=None,
    supporting_papers=None,
    output_format="pdf",
):
    return generate_research_paper_files(
        topic=topic,
        technology=technology,
        prompt=prompt,
        modules=modules,
        supporting_papers=supporting_papers,
        output_format=output_format,
        literature_limit=8,
    )


# ============================================================
# GENERATED PAPER FILE ACCESS
# ============================================================
def get_generated_paper_path(
    filename
):
    if not filename:
        raise ValueError(
            "Filename is required."
        )

    # Prevent directory traversal.
    safe_name = os.path.basename(
        filename
    )

    path = PAPER_DIR / safe_name

    if not path.exists():
        raise FileNotFoundError(
            f"Generated paper was not found: {safe_name}"
        )

    return str(path)


# ============================================================
# API ROUTE 1
# CORE SEARCH
# ============================================================
@app.route(
    "/api/core/search",
    methods=["POST"]
)
def core_search_api():
    try:
        data = request.get_json(
            silent=True
        ) or {}

        query = (
            data.get("query")
            or data.get("topic")
            or data.get("search")
            or ""
        )

        technology = data.get(
            "technology",
            ""
        )

        limit = data.get(
            "limit",
            10
        )

        offset = data.get(
            "offset",
            0
        )

        result = search_core(
            query=query,
            limit=limit,
            offset=offset,
            technology=technology,
        )

        return jsonify(
            result
        )

    except Exception as exc:
        print(
            "[CORE SEARCH ERROR]",
            repr(exc)
        )

        return jsonify({
            "success": False,
            "error": str(exc),
            "results": [],
        }), 500


# ============================================================
# API ROUTE 2
# GENERATE RESEARCH PAPER
# ============================================================
@app.route(
    "/api/core/generate-paper",
    methods=["POST", "OPTIONS"]
)
def generate_paper_api():

    # Explicit OPTIONS response for CORS.
    if request.method == "OPTIONS":
        response = jsonify({
            "success": True
        })

        origin = request.headers.get(
            "Origin"
        )

        if origin in {
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        }:
            response.headers["Access-Control-Allow-Origin"] = origin

            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, OPTIONS"
            )

            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization"
            )

        return response, 200

    try:
        print(
            "\n[Research IQ] POST /api/core/generate-paper"
        )

        data = request.get_json(
            silent=True
        ) or {}

        print(
            "[Research IQ] Request received."
        )

        # ----------------------------------------------------
        # TOPIC
        # ----------------------------------------------------
        topic = resolve_topic(
            topic=data.get(
                "topic"
            ),

            advisor_topic=data.get(
                "advisor_topic"
            ),

            research_topic=data.get(
                "research_topic"
            ),

            selected_topic=data.get(
                "selected_topic"
            ),

            generated_topic=data.get(
                "generated_topic"
            ),
        )

        print(
            "[Research IQ] Topic:",
            topic
        )

        # ----------------------------------------------------
        # BASIC DATA
        # ----------------------------------------------------
        prompt = data.get(
            "prompt",
            ""
        )

        technology = data.get(
            "technology",
            ""
        )

        modules = data.get(
            "modules",
            []
        )

        supporting_papers = data.get(
            "supporting_papers",
            []
        )

        output_format = data.get(
            "output_format",
            "pdf"
        )

        literature_limit = data.get(
            "literature_limit",
            8
        )

        print(
            "[Research IQ] Modules:",
            modules
        )

        print(
            "[Research IQ] Output format:",
            output_format
        )

        # ----------------------------------------------------
        # GENERATE EVERYTHING HERE
        # ----------------------------------------------------
        result = generate_research_paper_files(
            topic=topic,

            prompt=prompt,

            technology=technology,

            modules=modules,

            supporting_papers=supporting_papers,

            output_format=output_format,

            literature_limit=literature_limit,

            advisor_topic=data.get(
                "advisor_topic"
            ),

            research_topic=data.get(
                "research_topic"
            ),

            selected_topic=data.get(
                "selected_topic"
            ),

            generated_topic=data.get(
                "generated_topic"
            ),
        )

        # ----------------------------------------------------
        # ADD FULL LOCAL DOWNLOAD URLS
        # ----------------------------------------------------
        host_url = request.host_url.rstrip("/")

        if result.get(
            "pdf_download_url"
        ):
            result["pdf_download_url"] = (
                host_url
                + result[
                    "pdf_download_url"
                ]
            )

        if result.get(
            "docx_download_url"
        ):
            result["docx_download_url"] = (
                host_url
                + result[
                    "docx_download_url"
                ]
            )

        if result.get(
            "download_url"
        ):
            result["download_url"] = (
                host_url
                + result[
                    "download_url"
                ]
            )

        print(
            "[Research IQ] Paper generation completed."
        )

        print(
            "[Research IQ] PDF:",
            result.get(
                "pdf_download_url"
            )
        )

        return jsonify(
            result
        ), 200

    except ValueError as exc:
        print(
            "[Research IQ] VALIDATION ERROR:",
            repr(exc)
        )

        return jsonify({
            "success": False,
            "error": str(exc),
        }), 400

    except Exception as exc:
        print(
            "[Research IQ] GENERATION ERROR:",
            repr(exc)
        )

        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# API ROUTE 3
# DOWNLOAD GENERATED PAPER
# ============================================================
@app.route(
    "/api/core/download/<path:filename>",
    methods=["GET"]
)
def download_generated_paper(
    filename
):
    try:
        file_path = (
            get_generated_paper_path(
                filename
            )
        )

        return send_file(
            file_path,
            as_attachment=True,
            download_name=Path(
                file_path
            ).name
        )

    except FileNotFoundError:
        return jsonify({
            "success": False,
            "error": (
                "Generated paper was not found."
            )
        }), 404

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": str(exc)
        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================
@app.route(
    "/api/core/health",
    methods=["GET"]
)
def health_check():
    status = check_api_keys()

    return jsonify({
        "success": True,

        "service": (
            "Research IQ "
            "Research Paper Generation"
        ),

        "core_api": (
            "configured"
            if status["core"]
            else "missing"
        ),

        "ollama": (
            "configured"
            if status["ollama"]
            else "missing"
        ),

        "ollama_model":
            OLLAMA_MODEL,

        "ollama_url":
            OLLAMA_URL,

        "paper_directory":
            str(PAPER_DIR),

        "dataset":
            str(CSV_FILE),

        "routes": {
            "search":
                CORE_SEARCH_ROUTE,

            "generate":
                PAPER_GENERATION_ROUTE,

            "download":
                PAPER_DOWNLOAD_ROUTE,

            "health":
                "/api/core/health",
        }
    })


# ============================================================
# ROUTE INFORMATION
# ============================================================
def get_paper_generation_routes():
    return {
        "search":
            CORE_SEARCH_ROUTE,

        "generate":
            PAPER_GENERATION_ROUTE,

        "download":
            PAPER_DOWNLOAD_ROUTE,

        "health":
            "/api/core/health",
    }


# ============================================================
# START SERVER
# ============================================================
if __name__ == "__main__":

    print(
        "\n=============================================="
    )

    print(
        "       RESEARCH IQ PAPER GENERATOR"
    )

    print(
        "       STANDALONE BACKEND"
    )

    print(
        "==============================================\n"
    )

    try:
        ensure_csv()

        status = check_api_keys()

        print(
            "CORE API:",
            "OK"
            if status["core"]
            else "MISSING"
        )

        print(
            "Ollama:",
            "OK"
            if status["ollama"]
            else "MISSING"
        )

        print(
            "Ollama Model:",
            OLLAMA_MODEL
        )

        print(
            "Ollama URL:",
            OLLAMA_URL
        )

        print(
            "\nRoutes:"
        )

        print(
            "CORE Search:",
            CORE_SEARCH_ROUTE
        )

        print(
            "Generate Paper:",
            PAPER_GENERATION_ROUTE
        )

        print(
            "Download:",
            PAPER_DOWNLOAD_ROUTE
        )

        print(
            "Health:",
            "/api/core/health"
        )

        print(
            "\nDirectories:"
        )

        print(
            "Generated Papers:",
            PAPER_DIR
        )

        print(
            "Dataset:",
            CSV_FILE
        )

        print(
            "\n=============================================="
        )

        print(
            "Starting standalone Flask backend..."
        )

        print(
            "Backend URL:"
        )

        print(
            "http://127.0.0.1:5000"
        )

        print(
            "http://localhost:5000"
        )

        print(
            "==============================================\n"
        )

        app.run(
            host="0.0.0.0",
            port=5000,
            debug=True,
        )

    except Exception as exc:

        print(
            "\n=============================================="
        )

        print(
            "BACKEND STARTUP ERROR"
        )

        print(
            "=============================================="
        )

        print(
            repr(exc)
        )

        print(
            "==============================================\n"
        )

        raise