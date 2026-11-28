import os
import csv
import json
import re
import math
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# CORS
# ============================================================

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, Authorization"
    )
    response.headers["Access-Control-Allow-Methods"] = (
        "GET, POST, OPTIONS"
    )
    return response


# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/chat"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:1.5b"
)


# ============================================================
# RAG DATASET
# ============================================================

RAG_DATASET_FILE = (
    r"C:\Users\anita nayak\Documents\PROJECTS\DSA_PROJECT"
    r"\backend\datasets\database.csv"
)


# ============================================================
# DATASET / OUTPUT DIRECTORY
# ============================================================

DATA_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "datasets"
)

DATA_DIR = os.path.abspath(DATA_DIR)

COMPARISON_CSV_FILE = os.path.join(
    DATA_DIR,
    "study_comparisons.csv"
)

COMPARISON_COLUMNS = [
    "timestamp",
    "paper_1_title",
    "paper_1_authors",
    "paper_1_year",
    "paper_2_title",
    "paper_2_authors",
    "paper_2_year",
    "comparison"
]


# ============================================================
# RAG CONFIGURATION
# ============================================================

RAG_TOP_K = 5
MAX_RECORD_CHARS = 7000
MAX_RAG_CONTEXT_CHARS = 30000


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(value):

    if value is None:
        return ""

    if isinstance(value, (list, tuple)):

        value = ", ".join(
            str(item).strip()
            for item in value
            if item is not None
            and str(item).strip()
        )

    return " ".join(
        str(value)
        .replace("\r", " ")
        .replace("\n", " ")
        .split()
    ).strip()


# ============================================================
# PUBLICATION YEAR
# ============================================================

def get_publication_year(value):

    value = clean_text(value)

    if not value:
        return ""

    if len(value) >= 4 and value[:4].isdigit():

        year = value[:4]

        try:

            year_int = int(year)

            if 1000 <= year_int <= 9999:
                return year

        except (ValueError, TypeError):
            pass

    match = re.search(
        r"\b(19|20)\d{2}\b",
        value
    )

    if match:
        return match.group(0)

    return ""


# ============================================================
# CSV SETUP
# ============================================================

def ensure_csv():

    os.makedirs(
        DATA_DIR,
        exist_ok=True
    )

    if not os.path.exists(
        COMPARISON_CSV_FILE
    ):

        with open(
            COMPARISON_CSV_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=COMPARISON_COLUMNS
            )

            writer.writeheader()


# ============================================================
# RAG DATASET VALIDATION
# ============================================================

def check_rag_dataset():

    if not os.path.exists(
        RAG_DATASET_FILE
    ):

        return {
            "success": False,
            "error": (
                "RAG dataset was not found at: "
                f"{RAG_DATASET_FILE}"
            )
        }

    if not os.path.isfile(
        RAG_DATASET_FILE
    ):

        return {
            "success": False,
            "error": (
                "RAG dataset path is not a file: "
                f"{RAG_DATASET_FILE}"
            )
        }

    return {
        "success": True,
        "message": "RAG dataset is available.",
        "path": RAG_DATASET_FILE
    }


# ============================================================
# LOAD RAG DATASET
# ============================================================

def load_rag_dataset():

    dataset_status = check_rag_dataset()

    if not dataset_status["success"]:

        return {
            "success": False,
            "error": dataset_status["error"],
            "records": [],
            "columns": []
        }

    records = []

    try:

        with open(
            RAG_DATASET_FILE,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)

            columns = (
                reader.fieldnames
                or []
            )

            for row in reader:

                if not row:
                    continue

                cleaned_row = {}

                for key, value in row.items():

                    if key is None:
                        continue

                    cleaned_row[
                        clean_text(key)
                    ] = clean_text(value)

                if not any(
                    cleaned_row.values()
                ):
                    continue

                records.append(
                    cleaned_row
                )

        return {
            "success": True,
            "records": records,
            "columns": columns,
            "count": len(records)
        }

    except UnicodeDecodeError:

        try:

            records = []

            with open(
                RAG_DATASET_FILE,
                "r",
                newline="",
                encoding="cp1252"
            ) as file:

                reader = csv.DictReader(file)

                columns = (
                    reader.fieldnames
                    or []
                )

                for row in reader:

                    if not row:
                        continue

                    cleaned_row = {}

                    for key, value in row.items():

                        if key is None:
                            continue

                        cleaned_row[
                            clean_text(key)
                        ] = clean_text(value)

                    if not any(
                        cleaned_row.values()
                    ):
                        continue

                    records.append(
                        cleaned_row
                    )

            return {
                "success": True,
                "records": records,
                "columns": columns,
                "count": len(records)
            }

        except Exception as e:

            return {
                "success": False,
                "error": (
                    "Could not read the RAG dataset: "
                    f"{str(e)}"
                ),
                "records": [],
                "columns": []
            }

    except csv.Error as e:

        return {
            "success": False,
            "error": (
                "Invalid CSV dataset: "
                f"{str(e)}"
            ),
            "records": [],
            "columns": []
        }

    except OSError as e:

        return {
            "success": False,
            "error": (
                "Could not open the RAG dataset: "
                f"{str(e)}"
            ),
            "records": [],
            "columns": []
        }

    except Exception as e:

        return {
            "success": False,
            "error": (
                "Unexpected RAG dataset error: "
                f"{str(e)}"
            ),
            "records": [],
            "columns": []
        }


# ============================================================
# TOKENIZER
# ============================================================

def tokenize(text):

    text = clean_text(text).lower()

    return re.findall(
        r"[a-zA-Z0-9]+",
        text
    )


# ============================================================
# STOPWORDS
# ============================================================

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "using",
    "use",
    "based",
    "study",
    "research",
    "paper",
    "analysis",
    "method",
    "methods",
    "approach",
    "results",
    "system",
    "application",
    "applications",
    "new",
    "proposed",
    "data",
    "model",
    "models"
}


def meaningful_tokens(text):

    return [
        token
        for token in tokenize(text)
        if token not in STOPWORDS
        and len(token) > 2
    ]


# ============================================================
# BUILD SEARCHABLE RECORD
# ============================================================

def build_record_text(record):

    if not isinstance(
        record,
        dict
    ):
        return ""

    parts = []

    for key, value in record.items():

        key_clean = clean_text(key)
        value_clean = clean_text(value)

        if not value_clean:
            continue

        parts.append(
            f"{key_clean}: {value_clean}"
        )

    return "\n".join(parts)


# ============================================================
# TF-IDF HELPERS
# ============================================================

def build_term_frequency(tokens):

    frequencies = {}

    for token in tokens:

        frequencies[token] = (
            frequencies.get(token, 0) + 1
        )

    return frequencies


def build_idf(documents):

    document_frequency = {}

    total_documents = len(
        documents
    )

    if total_documents == 0:
        return {}

    for tokens in documents:

        unique_tokens = set(tokens)

        for token in unique_tokens:

            document_frequency[token] = (
                document_frequency.get(token, 0) + 1
            )

    idf = {}

    for token, frequency in document_frequency.items():

        idf[token] = (
            math.log(
                (total_documents + 1)
                /
                (frequency + 1)
            )
            + 1
        )

    return idf


def cosine_similarity(
    query_vector,
    document_vector
):

    if not query_vector or not document_vector:
        return 0.0

    common_terms = (
        set(query_vector.keys())
        &
        set(document_vector.keys())
    )

    if not common_terms:
        return 0.0

    dot_product = sum(
        query_vector[token]
        *
        document_vector[token]
        for token in common_terms
    )

    query_norm = math.sqrt(
        sum(
            value * value
            for value in query_vector.values()
        )
    )

    document_norm = math.sqrt(
        sum(
            value * value
            for value in document_vector.values()
        )
    )

    if (
        query_norm == 0
        or document_norm == 0
    ):
        return 0.0

    return (
        dot_product
        /
        (query_norm * document_norm)
    )


# ============================================================
# CREATE TF-IDF VECTOR
# ============================================================

def create_tfidf_vector(
    tokens,
    idf
):

    if not tokens:
        return {}

    term_frequency = (
        build_term_frequency(tokens)
    )

    total_terms = len(tokens)

    vector = {}

    for term, frequency in term_frequency.items():

        tf = (
            frequency
            /
            total_terms
        )

        vector[term] = (
            tf
            *
            idf.get(
                term,
                1.0
            )
        )

    return vector


# ============================================================
# RAG RETRIEVAL
# ============================================================

def retrieve_relevant_records(
    query,
    top_k=RAG_TOP_K
):

    query = clean_text(query)

    if not query:

        return {
            "success": False,
            "error": "RAG retrieval query is empty.",
            "records": []
        }

    dataset = load_rag_dataset()

    if not dataset["success"]:

        return {
            "success": False,
            "error": dataset["error"],
            "records": []
        }

    records = dataset["records"]

    if not records:

        return {
            "success": False,
            "error": "The RAG dataset contains no records.",
            "records": []
        }

    documents = []

    for record in records:

        record_text = (
            build_record_text(record)
        )

        documents.append(
            tokenize(record_text)
        )

    query_tokens = tokenize(query)

    if not query_tokens:

        return {
            "success": False,
            "error": "Could not extract searchable terms.",
            "records": []
        }

    idf = build_idf(
        documents
    )

    query_vector = (
        create_tfidf_vector(
            query_tokens,
            idf
        )
    )

    scored_records = []

    for index, record in enumerate(records):

        document_vector = (
            create_tfidf_vector(
                documents[index],
                idf
            )
        )

        score = cosine_similarity(
            query_vector,
            document_vector
        )

        scored_records.append(
            (
                score,
                index,
                record
            )
        )

    scored_records.sort(
        key=lambda item: item[0],
        reverse=True
    )

    selected = []

    for score, index, record in scored_records[:top_k]:

        selected.append({
            "score": round(
                float(score),
                6
            ),
            "record": record
        })

    return {
        "success": True,
        "query": query,
        "records": selected,
        "total_dataset_records": len(records)
    }


# ============================================================
# PAPER TEXT
# ============================================================

def build_paper_text(paper):

    if not isinstance(
        paper,
        dict
    ):
        return ""

    fields = [
        "title",
        "abstract",
        "authors",
        "publication_name",
        "publication_date",
        "doi",
        "keywords",
        "query",
        "research_topic",
        "topic",
        "domain"
    ]

    parts = []

    for field in fields:

        value = clean_text(
            paper.get(
                field,
                ""
            )
        )

        if value:

            parts.append(
                value
            )

    if not parts:

        for key, value in paper.items():

            value = clean_text(value)

            if value:
                parts.append(value)

    return " ".join(parts)


# ============================================================
# TOPIC RELEVANCE
#
# IMPORTANT:
# This is calculated from the actual paper information.
# RAG records are NOT used to decide whether the paper
# itself is related to the user's topic.
# ============================================================

def calculate_topic_relevance(
    paper,
    topic
):

    topic_tokens = set(
        meaningful_tokens(topic)
    )

    if not topic_tokens:

        return {
            "score": 0,
            "matched_terms": [],
            "title_matches": [],
            "abstract_matches": [],
            "level": "unknown"
        }

    title = clean_text(
        paper.get(
            "title",
            ""
        )
    )

    abstract = clean_text(
        paper.get(
            "abstract",
            ""
        )
    )

    paper_text = (
        f"{title} {abstract}"
    )

    paper_tokens = set(
        meaningful_tokens(
            paper_text
        )
    )

    title_tokens = set(
        meaningful_tokens(title)
    )

    abstract_tokens = set(
        meaningful_tokens(abstract)
    )

    matched_terms = sorted(
        topic_tokens & paper_tokens
    )

    title_matches = sorted(
        topic_tokens & title_tokens
    )

    abstract_matches = sorted(
        topic_tokens & abstract_tokens
    )

    coverage = (
        len(matched_terms)
        /
        len(topic_tokens)
    )

    title_coverage = (
        len(title_matches)
        /
        len(topic_tokens)
    )

    abstract_coverage = (
        len(abstract_matches)
        /
        len(topic_tokens)
    )

    # Title matches are intentionally weighted more strongly.
    raw_score = (
        (title_coverage * 0.60)
        +
        (abstract_coverage * 0.40)
    )

    score = round(
        min(raw_score * 100, 100),
        2
    )

    if score >= 60:

        level = "strong"

    elif score >= 30:

        level = "moderate"

    elif score > 0:

        level = "weak"

    else:

        level = "unrelated"

    return {
        "score": score,
        "matched_terms": matched_terms,
        "title_matches": title_matches,
        "abstract_matches": abstract_matches,
        "level": level
    }


# ============================================================
# BUILD PAPER RAG QUERY
#
# IMPORTANT:
# Do NOT put the user's topic into the paper retrieval query.
# Otherwise an unrelated paper can retrieve records about
# the topic and the LLM can incorrectly treat those records
# as evidence that the paper itself is about that topic.
# ============================================================

def build_paper_rag_query(
    paper,
    topic=""
):

    if not isinstance(
        paper,
        dict
    ):
        return ""

    important_fields = [
        "title",
        "abstract",
        "authors",
        "publication_name",
        "publication_date",
        "doi",
        "query",
        "research_topic",
        "topic",
        "domain"
    ]

    parts = []

    for field in important_fields:

        value = paper.get(
            field,
            ""
        )

        value = clean_text(
            value
        )

        if value:

            parts.append(
                value
            )

    if not parts:

        for key, value in paper.items():

            value = clean_text(value)

            if value:
                parts.append(value)

    return " ".join(parts)


# ============================================================
# RAG RETRIEVAL FOR ONE PAPER
# ============================================================

def retrieve_for_paper(
    paper,
    topic="",
    top_k=RAG_TOP_K
):

    query = build_paper_rag_query(
        paper,
        topic=topic
    )

    if not query:

        return {
            "success": False,
            "error": "Could not build RAG query for paper.",
            "records": []
        }

    return retrieve_relevant_records(
        query=query,
        top_k=top_k
    )


# ============================================================
# FORMAT RETRIEVED RAG CONTEXT
# ============================================================

def format_rag_record(
    record_number,
    score,
    record
):

    text = build_record_text(
        record
    )

    if len(text) > MAX_RECORD_CHARS:

        text = (
            text[:MAX_RECORD_CHARS]
            +
            "\n[Record truncated]"
        )

    return (
        f"RETRIEVED DATASET RECORD {record_number}\n"
        f"Relevance score: {score}\n"
        f"{text}\n"
    )


def build_rag_context(
    paper_1_results,
    paper_2_results
):

    sections = []

    sections.append(
        "===== SUPPORTING RAG CONTEXT FOR PAPER 1 ====="
    )

    paper_1_records = (
        paper_1_results.get(
            "records",
            []
        )
    )

    for index, item in enumerate(
        paper_1_records,
        start=1
    ):

        sections.append(
            format_rag_record(
                index,
                item.get(
                    "score",
                    0
                ),
                item.get(
                    "record",
                    {}
                )
            )
        )

    sections.append(
        "===== SUPPORTING RAG CONTEXT FOR PAPER 2 ====="
    )

    paper_2_records = (
        paper_2_results.get(
            "records",
            []
        )
    )

    for index, item in enumerate(
        paper_2_records,
        start=1
    ):

        sections.append(
            format_rag_record(
                index,
                item.get(
                    "score",
                    0
                ),
                item.get(
                    "record",
                    {}
                )
            )
        )

    context = "\n".join(
        sections
    )

    if len(context) > MAX_RAG_CONTEXT_CHARS:

        context = (
            context[:MAX_RAG_CONTEXT_CHARS]
            +
            "\n[Retrieved RAG context truncated]"
        )

    return context


# ============================================================
# OLLAMA HEADERS
# ============================================================

def get_ollama_headers():

    return {
        "Content-Type": "application/json"
    }


# ============================================================
# OLLAMA TAGS URL
# ============================================================

def get_ollama_tags_url():

    if "/api/chat" in OLLAMA_URL:

        return OLLAMA_URL.replace(
            "/api/chat",
            "/api/tags"
        )

    if OLLAMA_URL.endswith("/api"):

        return (
            OLLAMA_URL.rstrip("/")
            +
            "/tags"
        )

    return (
        OLLAMA_URL.rstrip("/")
        +
        "/api/tags"
    )


# ============================================================
# CHECK OLLAMA
# ============================================================

def check_ollama():

    try:

        response = requests.get(
            get_ollama_tags_url(),
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        models = data.get(
            "models",
            []
        )

        model_names = [
            model.get(
                "name",
                ""
            )
            for model in models
            if model.get("name")
        ]

        if not model_names:

            return {
                "success": False,
                "error": (
                    "Ollama is running, but no models "
                    "are installed."
                )
            }

        model_available = any(
            name == OLLAMA_MODEL
            or name.startswith(
                f"{OLLAMA_MODEL}:"
            )
            for name in model_names
        )

        if not model_available:

            return {
                "success": False,
                "error": (
                    f"Ollama model '{OLLAMA_MODEL}' "
                    "was not found. Installed models: "
                    f"{', '.join(model_names)}"
                )
            }

        return {
            "success": True,
            "message": (
                "Ollama is running and the configured "
                f"model '{OLLAMA_MODEL}' is available."
            ),
            "models": model_names
        }

    except requests.exceptions.ConnectionError:

        return {
            "success": False,
            "error": (
                "Could not connect to Ollama. "
                "Make sure Ollama is running."
            )
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "error": (
                f"Failed to connect to Ollama: {str(e)}"
            )
        }


# ============================================================
# BUILD RAG COMPARISON PROMPT
# ============================================================

def build_comparison_prompt(
    paper_1,
    paper_2,
    topic,
    rag_context,
    paper_1_relevance,
    paper_2_relevance
):

    authors_1 = clean_text(
        paper_1.get(
            "authors",
            []
        )
    )

    authors_2 = clean_text(
        paper_2.get(
            "authors",
            []
        )
    )

    topic = clean_text(topic)

    return f"""
You are an academic research paper comparison assistant.

Your ONLY job is to determine which of TWO supplied research
papers is a better academic fit for the USER'S RESEARCH TOPIC.

The user's research topic is the PRIMARY and FINAL decision
criterion.

============================================================
USER'S RESEARCH TOPIC
============================================================

{topic}

============================================================
CRITICAL RULE: PAPER IDENTITY
============================================================

The supplied Paper 1 and Paper 2 information is the ONLY
source that determines what each paper is about.

DO NOT infer that a paper discusses the user's topic merely
because a retrieved RAG dataset record discusses that topic.

DO NOT transfer facts from Paper 2 to Paper 1.

DO NOT transfer facts from Paper 1 to Paper 2.

DO NOT use retrieved RAG records as if they are the uploaded
papers.

The RAG records are ONLY supporting scholarly context.

If Paper 1 is about cloud computing and Paper 2 is about brain
disease, you MUST preserve that distinction.

An unrelated paper MUST NOT be described as being about the
user's topic.

============================================================
DETERMINISTIC TOPIC RELEVANCE
============================================================

The backend independently calculated topic relevance from the
actual supplied paper title and abstract.

Paper 1 relevance score:
{paper_1_relevance["score"]}/100

Paper 1 relevance level:
{paper_1_relevance["level"]}

Paper 1 matched topic terms:
{", ".join(paper_1_relevance["matched_terms"]) or "None"}

Paper 2 relevance score:
{paper_2_relevance["score"]}/100

Paper 2 relevance level:
{paper_2_relevance["level"]}

Paper 2 matched topic terms:
{", ".join(paper_2_relevance["matched_terms"]) or "None"}

These relevance results MUST be respected.

If a paper has a relevance level of "unrelated", do NOT
describe that paper as directly relevant to the topic.

If both papers are unrelated or only weakly related, you may
conclude that neither is a strong match.

============================================================
IMPORTANT DECISION RULES
============================================================

1. Compare BOTH papers specifically against:
   "{topic}"

2. Direct subject/topic relevance is more important than
   general academic quality.

3. Do NOT select a paper simply because it sounds technical.

4. Do NOT select a paper simply because it has a stronger
   methodology if its subject is unrelated to the topic.

5. A paper about cloud computing, Python, networking, generic
   computer science, or another unrelated area must NOT be
   treated as a brain-disease paper merely because RAG context
   contains brain-related information.

6. A paper about brain diseases, neurological disorders,
   biomarkers, brain imaging, diagnosis of brain disorders, or
   closely related brain-disease research should receive strong
   relevance when supported by its own title/abstract.

7. If one paper is clearly relevant and the other is clearly
   unrelated, the relevant paper should be the better fit.

8. If neither paper is sufficiently relevant, say:
   "Neither paper is a strong match for the entered research topic."

9. Never invent facts.

============================================================
RAG RULES
============================================================

1. The RAG context is supporting scholarly context only.

2. RAG records MUST NOT redefine either supplied paper.

3. Do NOT claim that a supplied paper contains information
   merely because a RAG record contains that information.

4. Do NOT invent methodologies, experiments, datasets,
   findings, limitations, research gaps, or results.

5. If the supplied paper information does not provide something,
   write:
   "Not available from the provided information."

6. Do not use outside knowledge.

============================================================
PAPER 1
============================================================

Title:
{clean_text(paper_1.get("title", ""))}

Authors:
{authors_1}

Publication:
{clean_text(paper_1.get("publication_name", ""))}

Publication Date:
{clean_text(paper_1.get("publication_date", ""))}

DOI:
{clean_text(paper_1.get("doi", ""))}

Citations:
{clean_text(paper_1.get("cited_by_count", 0))}

Abstract:
{clean_text(paper_1.get("abstract", ""))}

============================================================
PAPER 2
============================================================

Title:
{clean_text(paper_2.get("title", ""))}

Authors:
{authors_2}

Publication:
{clean_text(paper_2.get("publication_name", ""))}

Publication Date:
{clean_text(paper_2.get("publication_date", ""))}

DOI:
{clean_text(paper_2.get("doi", ""))}

Citations:
{clean_text(paper_2.get("cited_by_count", 0))}

Abstract:
{clean_text(paper_2.get("abstract", ""))}

============================================================
SUPPORTING RAG CONTEXT
============================================================

{rag_context}

============================================================
TASK
============================================================

Compare Paper 1 and Paper 2 specifically for:

"{topic}"

For EACH paper determine:

- How directly it relates to the topic
- Whether its research problem is useful for the topic
- Whether its methodology is applicable to the topic
- Whether its findings are useful for the topic
- What research gap it may help address
- Its technical depth
- Its strengths for the user's topic
- Its limitations for the user's topic

IMPORTANT:

When information is not present in the supplied paper
information, say:

"Not available from the provided information."

Do not fill missing information using assumptions.

============================================================
FINAL DECISION
============================================================

The final winner MUST be based primarily on direct relevance
to:

"{topic}"

The reason MUST explicitly explain the connection between the
selected paper and "{topic}".

If one paper is unrelated, clearly say so.

If neither paper is sufficiently relevant, say:

"Neither paper is a strong match for the entered research topic."

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

Use exactly this structure:

{{
    "overview": "Short overall comparison specifically against the entered research topic",

    "research_problem": {{
        "paper_1": "...",
        "paper_2": "...",
        "comparison": "..."
    }},

    "methodology": {{
        "paper_1": "...",
        "paper_2": "...",
        "comparison": "..."
    }},

    "findings": {{
        "paper_1": "...",
        "paper_2": "...",
        "comparison": "..."
    }},

    "strengths": {{
        "paper_1": [
            "...",
            "..."
        ],
        "paper_2": [
            "...",
            "..."
        ]
    }},

    "limitations": {{
        "paper_1": [
            "...",
            "..."
        ],
        "paper_2": [
            "...",
            "..."
        ]
    }},

    "similarities": [
        "...",
        "..."
    ],

    "differences": [
        "...",
        "..."
    ],

    "research_relevance": {{
        "paper_1": "...",
        "paper_2": "..."
    }},

    "overall_assessment": "...",

    "which_paper_is_more_suitable": "...",

    "reason": "Explain specifically why the selected paper is more or less suitable for the entered research topic."
}}

============================================================
FINAL VALIDATION
============================================================

Before returning JSON verify:

- Did you use the exact user's research topic?
- Did you evaluate Paper 1 independently?
- Did you evaluate Paper 2 independently?
- Did you preserve the actual identity of both papers?
- Did you avoid transferring RAG information between papers?
- Did you avoid treating unrelated papers as relevant?
- Is the winner actually the paper with stronger topic relevance?
- Does the reason explicitly mention the user's topic?
- If neither paper matches, did you say so?
- Did you avoid inventing information?
- Is the response valid JSON only?

Return valid JSON only.
"""


# ============================================================
# SAVE COMPARISON
# ============================================================

def save_comparison_to_csv(
    paper_1,
    paper_2,
    comparison
):

    ensure_csv()

    paper_1_title = clean_text(
        paper_1.get(
            "title",
            ""
        )
    )

    paper_2_title = clean_text(
        paper_2.get(
            "title",
            ""
        )
    )

    paper_1_authors = clean_text(
        paper_1.get(
            "authors",
            []
        )
    )

    paper_2_authors = clean_text(
        paper_2.get(
            "authors",
            []
        )
    )

    paper_1_year = get_publication_year(
        paper_1.get(
            "publication_date",
            ""
        )
    )

    paper_2_year = get_publication_year(
        paper_2.get(
            "publication_date",
            ""
        )
    )

    if not paper_1_title or not paper_2_title:
        return

    try:

        with open(
            COMPARISON_CSV_FILE,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=COMPARISON_COLUMNS
            )

            writer.writerow({

                "timestamp":
                    datetime.now().isoformat(),

                "paper_1_title":
                    paper_1_title,

                "paper_1_authors":
                    paper_1_authors,

                "paper_1_year":
                    paper_1_year,

                "paper_2_title":
                    paper_2_title,

                "paper_2_authors":
                    paper_2_authors,

                "paper_2_year":
                    paper_2_year,

                "comparison":
                    json.dumps(
                        comparison,
                        ensure_ascii=False
                    )
            })

    except OSError:
        pass


# ============================================================
# PARSE OLLAMA JSON
# ============================================================

def parse_ollama_json(
    content
):

    if not content:
        return None

    content = content.strip()

    # --------------------------------------------------------
    # Direct JSON
    # --------------------------------------------------------

    try:

        return json.loads(
            content
        )

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Remove markdown fences
    # --------------------------------------------------------

    if content.startswith(
        "```json"
    ):

        content = content[7:]

        if content.endswith(
            "```"
        ):

            content = content[:-3]

        content = content.strip()

    elif content.startswith(
        "```"
    ):

        content = content[3:]

        if content.endswith(
            "```"
        ):

            content = content[:-3]

        content = content.strip()

    try:

        return json.loads(
            content
        )

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Final fallback:
    # locate outermost JSON object
    # --------------------------------------------------------

    start = content.find(
        "{"
    )

    end = content.rfind(
        "}"
    )

    if (
        start != -1
        and end != -1
        and end > start
    ):

        candidate = content[
            start:end + 1
        ]

        try:

            return json.loads(
                candidate
            )

        except json.JSONDecodeError:

            return None

    return None


# ============================================================
# COMPARE TWO PAPERS USING RAG
# ============================================================

def compare_papers(
    paper_1,
    paper_2,
    topic
):

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not isinstance(
        paper_1,
        dict
    ):

        return {
            "success": False,
            "error": "Paper 1 is invalid."
        }

    if not isinstance(
        paper_2,
        dict
    ):

        return {
            "success": False,
            "error": "Paper 2 is invalid."
        }

    # --------------------------------------------------------
    # VALIDATE RESEARCH TOPIC
    # --------------------------------------------------------

    topic = clean_text(
        topic
    )

    if not topic:

        return {
            "success": False,
            "error": (
                "Research topic is required for paper comparison."
            )
        }

    title_1 = clean_text(
        paper_1.get(
            "title",
            ""
        )
    )

    title_2 = clean_text(
        paper_2.get(
            "title",
            ""
        )
    )

    if not title_1:

        return {
            "success": False,
            "error": "Paper 1 title is missing."
        }

    if not title_2:

        return {
            "success": False,
            "error": "Paper 2 title is missing."
        }

    # --------------------------------------------------------
    # PREVENT SAME PAPER
    # --------------------------------------------------------

    eid_1 = clean_text(
        paper_1.get(
            "eid",
            ""
        )
    )

    eid_2 = clean_text(
        paper_2.get(
            "eid",
            ""
        )
    )

    doi_1 = clean_text(
        paper_1.get(
            "doi",
            ""
        )
    )

    doi_2 = clean_text(
        paper_2.get(
            "doi",
            ""
        )
    )

    if (
        eid_1
        and eid_2
        and eid_1 == eid_2
    ):

        return {
            "success": False,
            "error": (
                "Please select two different papers."
            )
        }

    if (
        doi_1
        and doi_2
        and doi_1.lower()
        == doi_2.lower()
    ):

        return {
            "success": False,
            "error": (
                "Please select two different papers."
            )
        }

    # --------------------------------------------------------
    # CALCULATE DIRECT PAPER-TO-TOPIC RELEVANCE
    #
    # IMPORTANT:
    # This happens BEFORE RAG.
    #
    # The actual supplied paper title/abstract determines
    # whether the paper relates to the user's topic.
    # --------------------------------------------------------

    paper_1_relevance = calculate_topic_relevance(
        paper_1,
        topic
    )

    paper_2_relevance = calculate_topic_relevance(
        paper_2,
        topic
    )

    # --------------------------------------------------------
    # CHECK RAG DATASET
    # --------------------------------------------------------

    dataset_status = (
        check_rag_dataset()
    )

    if not dataset_status["success"]:

        return {
            "success": False,
            "error": dataset_status["error"]
        }

    # --------------------------------------------------------
    # RETRIEVE PAPER 1 CONTEXT
    #
    # IMPORTANT:
    # The user's topic is NOT added to this query.
    # This prevents the topic from pulling unrelated
    # topic records into Paper 1's context.
    # --------------------------------------------------------

    paper_1_rag = retrieve_for_paper(
        paper_1,
        topic="",
        top_k=RAG_TOP_K
    )

    if not paper_1_rag["success"]:

        return {
            "success": False,
            "error": (
                "RAG retrieval failed for Paper 1: "
                f"{paper_1_rag['error']}"
            )
        }

    # --------------------------------------------------------
    # RETRIEVE PAPER 2 CONTEXT
    #
    # IMPORTANT:
    # Paper 2 is retrieved independently.
    # --------------------------------------------------------

    paper_2_rag = retrieve_for_paper(
        paper_2,
        topic="",
        top_k=RAG_TOP_K
    )

    if not paper_2_rag["success"]:

        return {
            "success": False,
            "error": (
                "RAG retrieval failed for Paper 2: "
                f"{paper_2_rag['error']}"
            )
        }

    # --------------------------------------------------------
    # BUILD RAG CONTEXT
    # --------------------------------------------------------

    rag_context = build_rag_context(
        paper_1_rag,
        paper_2_rag
    )

    if not rag_context.strip():

        return {
            "success": False,
            "error": (
                "No relevant information was retrieved "
                "from the RAG dataset."
            )
        }

    # --------------------------------------------------------
    # CHECK OLLAMA
    # --------------------------------------------------------

    ollama_status = check_ollama()

    if not ollama_status["success"]:

        return {
            "success": False,
            "error": ollama_status["error"]
        }

    # --------------------------------------------------------
    # BUILD TOPIC-AWARE RAG PROMPT
    # --------------------------------------------------------

    prompt = build_comparison_prompt(
        paper_1,
        paper_2,
        topic,
        rag_context,
        paper_1_relevance,
        paper_2_relevance
    )

    # --------------------------------------------------------
    # OLLAMA PAYLOAD
    # --------------------------------------------------------

    payload = {

        "model": OLLAMA_MODEL,

        "messages": [

            {
                "role": "system",

                "content": (
                    "You are an academic research paper "
                    "comparison assistant. "

                    "The user's research topic is the PRIMARY "
                    "criterion for deciding which paper is "
                    "more suitable. "

                    "Evaluate each supplied paper independently. "

                    "Never transfer information from one paper "
                    "to the other. "

                    "Never treat supporting RAG records as "
                    "the content or identity of the supplied "
                    "papers. "

                    "An unrelated paper must remain unrelated "
                    "even if the RAG dataset contains records "
                    "about the user's topic. "

                    "Use only the supplied paper information, "
                    "backend relevance analysis, and supporting "
                    "RAG context. "

                    "Do not invent facts. "

                    "Return valid JSON only."
                )
            },

            {
                "role": "user",
                "content": prompt
            }
        ],

        "stream": False,

        "format": "json",

        "options": {
            "temperature": 0.1
        }
    }

    # --------------------------------------------------------
    # CALL OLLAMA
    # --------------------------------------------------------

    response = None

    try:

        response = requests.post(
            OLLAMA_URL,
            headers=get_ollama_headers(),
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        message = data.get(
            "message",
            {}
        )

        content = message.get(
            "content",
            ""
        )

        if not content:

            return {
                "success": False,
                "error": (
                    "Ollama returned an empty comparison."
                )
            }

        # ----------------------------------------------------
        # PARSE JSON
        # ----------------------------------------------------

        comparison = parse_ollama_json(
            content
        )

        if comparison is None:

            return {
                "success": False,
                "error": (
                    "Ollama returned an invalid "
                    "comparison format."
                )
            }

        # ----------------------------------------------------
        # SAFETY NORMALIZATION
        #
        # If the model somehow produces an obviously
        # contradictory winner, backend relevance takes
        # priority.
        # ----------------------------------------------------

        if (
            paper_1_relevance["score"] == 0
            and
            paper_2_relevance["score"] > 0
        ):

            comparison[
                "which_paper_is_more_suitable"
            ] = "Paper 2"

            comparison[
                "reason"
            ] = (
                f"Paper 2 is more suitable for the research "
                f"topic '{topic}' because Paper 1 has no direct "
                f"topic-term match in its supplied title or "
                f"abstract, while Paper 2 has stronger direct "
                f"topic relevance."
            )

            comparison[
                "research_relevance"
            ] = {

                "paper_1":
                    (
                        f"Paper 1 is unrelated to '{topic}' "
                        f"based on the supplied paper information."
                    ),

                "paper_2":
                    (
                        f"Paper 2 has stronger direct relevance "
                        f"to '{topic}'."
                    )
            }

        elif (
            paper_2_relevance["score"] == 0
            and
            paper_1_relevance["score"] > 0
        ):

            comparison[
                "which_paper_is_more_suitable"
            ] = "Paper 1"

            comparison[
                "reason"
            ] = (
                f"Paper 1 is more suitable for the research "
                f"topic '{topic}' because Paper 2 has no direct "
                f"topic-term match in its supplied title or "
                f"abstract, while Paper 1 has stronger direct "
                f"topic relevance."
            )

            comparison[
                "research_relevance"
            ] = {

                "paper_1":
                    (
                        f"Paper 1 has stronger direct relevance "
                        f"to '{topic}'."
                    ),

                "paper_2":
                    (
                        f"Paper 2 is unrelated to '{topic}' "
                        f"based on the supplied paper information."
                    )
            }

        elif (
            paper_1_relevance["score"] == 0
            and
            paper_2_relevance["score"] == 0
        ):

            comparison[
                "which_paper_is_more_suitable"
            ] = "Neither"

            comparison[
                "reason"
            ] = (
                f"Neither paper is a strong match for the "
                f"entered research topic '{topic}'."
            )

            comparison[
                "overall_assessment"
            ] = (
                "Neither paper is a strong match for the "
                "entered research topic."
            )

        # ----------------------------------------------------
        # SAVE COMPARISON HISTORY
        # ----------------------------------------------------

        save_comparison_to_csv(
            paper_1,
            paper_2,
            comparison
        )

        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return {

            "success": True,

            "topic":
                topic,

            "paper_1":
                paper_1,

            "paper_2":
                paper_2,

            "comparison":
                comparison,

            "rag": {

                "dataset":
                    RAG_DATASET_FILE,

                "query":
                    topic,

                "paper_1_query":
                    build_paper_rag_query(
                        paper_1
                    ),

                "paper_2_query":
                    build_paper_rag_query(
                        paper_2
                    ),

                "paper_1_relevance":
                    paper_1_relevance,

                "paper_2_relevance":
                    paper_2_relevance,

                "paper_1_retrieved":
                    len(
                        paper_1_rag.get(
                            "records",
                            []
                        )
                    ),

                "paper_2_retrieved":
                    len(
                        paper_2_rag.get(
                            "records",
                            []
                        )
                    )
            }
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error": (
                "Ollama comparison request timed out."
            )
        }

    except requests.exceptions.HTTPError as e:

        status_code = (
            response.status_code
            if response is not None
            else None
        )

        try:

            error_data = response.json()

        except Exception:

            error_data = {}

        return {
            "success": False,
            "error": (
                f"AI comparison failed "
                f"({status_code}): "
                f"{error_data or str(e)}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "success": False,
            "error": (
                "Could not connect to Ollama. "
                "Make sure Ollama is running on "
                f"{OLLAMA_URL}."
            )
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "error": (
                f"AI comparison request failed: "
                f"{str(e)}"
            )
        }

    except Exception as e:

        return {
            "success": False,
            "error": (
                f"Unexpected comparison error: "
                f"{str(e)}"
            )
        }


# ============================================================
# LOCAL RAG SEARCH
# ============================================================

def search_rag(
    query,
    count=10
):

    result = retrieve_relevant_records(
        query=query,
        top_k=count
    )

    if not result["success"]:

        return {
            "success": False,
            "error": result["error"],
            "results": []
        }

    formatted_results = []

    for item in result["records"]:

        record = item.get(
            "record",
            {}
        )

        formatted_results.append({

            **record,

            "_rag_score": item.get(
                "score",
                0
            )
        })

    return {
        "success": True,
        "query": query,
        "total_results":
            len(formatted_results),
        "results":
            formatted_results
    }


# ============================================================
# RESEARCH IQ SEARCH
# ============================================================

def research_iq_search(
    technology,
    domain=None,
    count=10,
    languages=None,
    field="",
    interests="",
    methodology="",
    experience_level=""
):

    query_parts = []

    if technology:

        query_parts.append(
            clean_text(technology)
        )

    if domain:

        query_parts.append(
            clean_text(domain)
        )

    if field:

        query_parts.append(
            clean_text(field)
        )

    if interests:

        query_parts.append(
            clean_text(interests)
        )

    if methodology:

        query_parts.append(
            clean_text(methodology)
        )

    query = " ".join(
        part
        for part in query_parts
        if part
    )

    if not query:

        return {
            "success": False,
            "error": "Search query is required.",
            "results": []
        }

    return search_rag(
        query=query,
        count=count
    )


# ============================================================
# SEARCH BY TECHNOLOGY
# ============================================================

def search_by_technology(
    technology,
    domain=None,
    count=10,
    languages=None,
    field="",
    interests="",
    methodology="",
    experience_level=""
):

    return research_iq_search(
        technology=technology,
        domain=domain,
        count=count,
        languages=languages,
        field=field,
        interests=interests,
        methodology=methodology,
        experience_level=experience_level
    )


# ============================================================
# SEARCH BY TOPIC
# ============================================================

def search_by_topic(
    topic,
    count=10,
    languages=None,
    field="",
    domain="",
    interests="",
    methodology="",
    experience_level=""
):

    if not topic:

        return {
            "success": False,
            "error": "Research topic is required.",
            "results": []
        }

    return search_rag(
        query=topic,
        count=count
    )


# ============================================================
# SEARCH BY AUTHOR
# ============================================================

def search_by_author(
    author_name,
    count=10
):

    if not author_name:

        return {
            "success": False,
            "error": "Author name is required.",
            "results": []
        }

    return search_rag(
        query=author_name,
        count=count
    )


# ============================================================
# GET PAPER BY ID
# ============================================================

def get_paper_by_eid(
    eid
):

    if not eid:

        return {
            "success": False,
            "error": "EID is required."
        }

    dataset = load_rag_dataset()

    if not dataset["success"]:

        return {
            "success": False,
            "error": dataset["error"]
        }

    eid_clean = clean_text(
        eid
    ).lower()

    for record in dataset["records"]:

        for key, value in record.items():

            if key.lower() in (
                "eid",
                "id",
                "paper_id"
            ):

                if (
                    clean_text(value).lower()
                    ==
                    eid_clean
                ):

                    return {
                        "success": True,
                        "result": record
                    }

    return {
        "success": False,
        "error": (
            "Paper was not found in the RAG dataset."
        )
    }


# ============================================================
# CHECK DATASET
# ============================================================

def check_dataset():

    return check_rag_dataset()


# ============================================================
# FLASK API: HEALTH CHECK
# ============================================================

@app.route(
    "/api/elsevier/compare",
    methods=["OPTIONS"]
)
def compare_options():

    return jsonify({
        "success": True
    }), 200


# ============================================================
# FLASK API: RAG PAPER COMPARISON
# ============================================================

@app.route(
    "/api/elsevier/compare",
    methods=["POST"]
)
def api_compare_papers():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "success": False,
                "error": (
                    "Request body must contain valid JSON."
                )
            }), 400

        # ----------------------------------------------------
        # GET RESEARCH TOPIC
        #
        # Expected frontend request:
        #
        # {
        #     "topic": "brain",
        #     "paper_1": {...},
        #     "paper_2": {...}
        # }
        # ----------------------------------------------------

        topic = clean_text(
            data.get(
                "topic",
                ""
            )
        )

        if not topic:

            return jsonify({
                "success": False,
                "error": (
                    "Research topic is required for "
                    "paper comparison."
                )
            }), 400

        # ----------------------------------------------------
        # ACCEPT PAPER FORMAT
        # ----------------------------------------------------

        paper_1 = data.get(
            "paper_1"
        )

        paper_2 = data.get(
            "paper_2"
        )

        if paper_1 is None:

            paper_1 = data.get(
                "paper1"
            )

        if paper_2 is None:

            paper_2 = data.get(
                "paper2"
            )

        # ----------------------------------------------------
        # VALIDATE PAPERS
        # ----------------------------------------------------

        if not isinstance(
            paper_1,
            dict
        ):

            return jsonify({
                "success": False,
                "error": (
                    "Paper 1 is missing or invalid."
                )
            }), 400

        if not isinstance(
            paper_2,
            dict
        ):

            return jsonify({
                "success": False,
                "error": (
                    "Paper 2 is missing or invalid."
                )
            }), 400

        # ----------------------------------------------------
        # RUN TOPIC-AWARE RAG COMPARISON
        # ----------------------------------------------------

        result = compare_papers(
            paper_1,
            paper_2,
            topic
        )

        # ----------------------------------------------------
        # RETURN APPROPRIATE HTTP STATUS
        # ----------------------------------------------------

        if result.get("success"):

            return jsonify(
                result
            ), 200

        return jsonify(
            result
        ), 400

    except Exception as e:

        return jsonify({
            "success": False,
            "error": (
                "Unexpected API error: "
                f"{str(e)}"
            )
        }), 500


# ============================================================
# FLASK API: RAG SEARCH
# ============================================================

@app.route(
    "/api/rag/search",
    methods=["POST"]
)
def api_rag_search():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "success": False,
                "error": "Invalid JSON request."
            }), 400

        query = clean_text(
            data.get(
                "query",
                ""
            )
        )

        count = data.get(
            "count",
            10
        )

        try:

            count = int(count)

        except (ValueError, TypeError):

            count = 10

        result = search_rag(
            query=query,
            count=count
        )

        if result.get("success"):

            return jsonify(
                result
            ), 200

        return jsonify(
            result
        ), 400

    except Exception as e:

        return jsonify({
            "success": False,
            "error": (
                f"Unexpected RAG search error: {str(e)}"
            )
        }), 500


# ============================================================
# FLASK API: DATASET STATUS
# ============================================================

@app.route(
    "/api/rag/dataset",
    methods=["GET"]
)
def api_rag_dataset():

    try:

        result = check_rag_dataset()

        if result.get("success"):

            return jsonify(
                result
            ), 200

        return jsonify(
            result
        ), 404

    except Exception as e:

        return jsonify({
            "success": False,
            "error": (
                f"Unexpected dataset error: {str(e)}"
            )
        }), 500


# ============================================================
# FLASK API: OLLAMA STATUS
# ============================================================

@app.route(
    "/api/rag/ollama",
    methods=["GET"]
)
def api_ollama_status():

    try:

        result = check_ollama()

        if result.get("success"):

            return jsonify(
                result
            ), 200

        return jsonify(
            result
        ), 503

    except Exception as e:

        return jsonify({
            "success": False,
            "error": (
                f"Unexpected Ollama error: {str(e)}"
            )
        }), 500


# ============================================================
# TEST / RUN BACKEND
# ============================================================

if __name__ == "__main__":

    print(
        "\n======================================"
    )

    print(
        "   RESEARCHIQ RAG STUDY COMPARISON"
    )

    print(
        "======================================\n"
    )

    # --------------------------------------------------------
    # Dataset check
    # --------------------------------------------------------

    dataset_status = (
        check_rag_dataset()
    )

    if dataset_status["success"]:

        print(
            "RAG dataset loaded:"
        )

        print(
            RAG_DATASET_FILE
        )

    else:

        print(
            "RAG DATASET ERROR:",
            dataset_status["error"]
        )

    # --------------------------------------------------------
    # Dataset information
    # --------------------------------------------------------

    dataset = load_rag_dataset()

    if dataset["success"]:

        print(
            f"Dataset records: "
            f"{dataset['count']}"
        )

        print(
            "Dataset columns:"
        )

        print(
            ", ".join(
                dataset["columns"]
            )
        )

    # --------------------------------------------------------
    # Ollama check
    # --------------------------------------------------------

    ollama_status = check_ollama()

    if ollama_status["success"]:

        print(
            "\nOllama loaded successfully."
        )

        print(
            f"Model: {OLLAMA_MODEL}"
        )

    else:

        print(
            "\nOLLAMA ERROR:",
            ollama_status["error"]
        )

    # --------------------------------------------------------
    # Local RAG test
    # --------------------------------------------------------

    result = search_rag(
        query="machine learning healthcare",
        count=5
    )

    if result["success"]:

        print(
            f"\nRAG retrieved "
            f"{result['total_results']} records."
        )

        for index, paper in enumerate(
            result["results"],
            start=1
        ):

            print(
                f"\n{index}."
            )

            print(
                json.dumps(
                    paper,
                    indent=2,
                    ensure_ascii=False
                )
            )

    else:

        print(
            "\nRAG SEARCH ERROR:",
            result["error"]
        )

    # --------------------------------------------------------
    # START FLASK SERVER
    # --------------------------------------------------------

    print(
        "\n======================================"
    )

    print(
        "ResearchIQ Flask backend starting..."
    )

    print(
        "Comparison API:"
    )

    print(
        "POST http://127.0.0.1:5000/api/elsevier/compare"
    )

    print(
        "======================================\n"
    )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )