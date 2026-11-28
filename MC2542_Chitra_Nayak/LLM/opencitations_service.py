import os
import csv
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

OPENCITATIONS_TOKEN = os.getenv(
    "OPENCITATIONS_API_KEY"
)

BASE_URL = (
    "https://api.opencitations.net/index/v2"
)


# ============================================================
# OLLAMA CONFIGURATION
# ============================================================

OLLAMA_MODEL = "qwen2.5:1.5b"

OLLAMA_URL = (
    "http://127.0.0.1:11434/api/chat"
)


# ============================================================
# FLASK BLUEPRINT
# ============================================================

opencitations_bp = Blueprint(
    "opencitations",
    __name__,
    url_prefix="/api/opencitations"
)


# ============================================================
# DATASET DIRECTORY
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent.parent

# IMPORTANT:
# Dataset is stored in datasets, not dataSets/data.

DATASETS_DIR = (
    BASE_DIR / "datasets"
)

CSV_FILE = (
    DATASETS_DIR / "opencitations_data.csv"
)

DATASETS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# DATASET COLUMNS
# ============================================================

CSV_HEADERS = [

    # --------------------------------------------------------
    # Interaction
    # --------------------------------------------------------

    "timestamp",
    "operation",

    # --------------------------------------------------------
    # Uploaded / selected paper
    # --------------------------------------------------------

    "filename",
    "paper_title",
    "doi",
    "paper_identifier",
    "authors",
    "publication_name",
    "publication_date",
    "document_type",
    "abstract",
    "extracted_text",

    # --------------------------------------------------------
    # User interaction
    # --------------------------------------------------------

    "user_question",

    # --------------------------------------------------------
    # AI response
    # --------------------------------------------------------

    "answer",
    "answer_lines",
    "answer_format",

    # --------------------------------------------------------
    # Citation information
    # --------------------------------------------------------

    "citation_count",
    "reference_count",
    "incoming_citation_count",
    "outgoing_reference_count",
    "incoming_citation_identifiers",
    "outgoing_reference_identifiers",

    # --------------------------------------------------------
    # Dataset/source information
    # --------------------------------------------------------

    "source",
    "status"
]


# ============================================================
# DEFAULT VALUES
# ============================================================

DEFAULT_TEXT = "Not available"
DEFAULT_NUMBER = 0


# ============================================================
# CSV CLEANING HELPERS
# ============================================================

def clean_text(
    value,
    default=DEFAULT_TEXT
):
    """
    Converts a value into clean, non-empty text.
    """

    if value is None:
        return default

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return default

        return value

    if isinstance(value, list):
        cleaned_items = []

        for item in value:
            item_text = clean_text(
                item,
                ""
            )

            if item_text:
                cleaned_items.append(
                    item_text
                )

        if cleaned_items:
            return ", ".join(
                cleaned_items
            )

        return default

    value = str(value).strip()

    if not value:
        return default

    return value


def clean_number(
    value
):
    """
    Converts numeric values into clean integers.
    """

    if value is None:
        return DEFAULT_NUMBER

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return DEFAULT_NUMBER

        try:
            return int(value)

        except (
            ValueError,
            TypeError
        ):
            return DEFAULT_NUMBER

    try:
        return int(value)

    except (
        ValueError,
        TypeError
    ):
        return DEFAULT_NUMBER


def clean_list(
    value
):
    """
    Converts citation/reference lists into
    clean semicolon-separated text.
    """

    if value is None:
        return DEFAULT_TEXT

    if not isinstance(
        value,
        list
    ):
        return clean_text(value)

    cleaned = []

    for item in value:

        if isinstance(
            item,
            dict
        ):

            identifier = (
                item.get("id")
                or item.get("cited")
                or item.get("citing")
                or item.get("doi")
                or item.get("identifier")
            )

            if identifier:

                cleaned.append(
                    clean_text(
                        identifier,
                        ""
                    )
                )

            else:

                try:

                    item_json = json.dumps(
                        item,
                        ensure_ascii=False,
                        sort_keys=True
                    )

                    if item_json.strip():

                        cleaned.append(
                            item_json
                        )

                except Exception:
                    continue

        else:

            item_text = clean_text(
                item,
                ""
            )

            if item_text:
                cleaned.append(
                    item_text
                )

    if not cleaned:
        return DEFAULT_TEXT

    return " | ".join(
        cleaned
    )


# ============================================================
# CLEAN DATASET ROW
# ============================================================

def clean_dataset_row(
    row
):
    """
    Ensures every dataset cell contains
    a meaningful value.
    No blank cells are allowed.
    """

    cleaned = {}

    # --------------------------------------------------------
    # Text columns
    # --------------------------------------------------------

    text_columns = [

        "timestamp",
        "operation",
        "filename",
        "paper_title",
        "doi",
        "paper_identifier",
        "authors",
        "publication_name",
        "publication_date",
        "document_type",
        "abstract",
        "extracted_text",
        "user_question",
        "answer",
        "answer_format",
        "incoming_citation_identifiers",
        "outgoing_reference_identifiers",
        "source",
        "status"
    ]

    for column in text_columns:

        cleaned[column] = clean_text(
            row.get(column)
        )

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [

        "answer_lines",
        "citation_count",
        "reference_count",
        "incoming_citation_count",
        "outgoing_reference_count"
    ]

    for column in numeric_columns:

        cleaned[column] = clean_number(
            row.get(column)
        )

    return cleaned


# ============================================================
# DETERMINE WHETHER A COLUMN HAS REAL DATA
# ============================================================

def column_has_real_data(
    rows,
    column
):
    """
    Determines whether a column contains
    actual information anywhere in the dataset.
    """

    if not rows:
        return False

    for row in rows:

        value = row.get(
            column,
            ""
        )

        if value is None:
            continue

        if isinstance(
            value,
            (int, float)
        ):

            if value != 0:
                return True

        else:

            text = str(
                value
            ).strip()

            if text and text not in [
                "Not available",
                "No answer generated"
            ]:
                return True

    return False


# ============================================================
# GET ACTIVE DATASET COLUMNS
# ============================================================

def get_active_columns(
    rows
):
    """
    Keeps only columns that have actual data.

    Core interaction columns remain available whenever
    records exist.
    """

    if not rows:
        return []

    active_columns = []

    for column in CSV_HEADERS:

        if column_has_real_data(
            rows,
            column
        ):

            active_columns.append(
                column
            )

    return active_columns


# ============================================================
# READ EXISTING DATASET
# ============================================================

def read_existing_rows():
    """
    Reads existing CSV rows safely.
    """

    if not CSV_FILE.exists():
        return []

    try:

        with open(
            CSV_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(
                file
            )

            rows = list(
                reader
            )

        cleaned_rows = []

        for row in rows:

            if not row:
                continue

            meaningful_values = [

                str(value).strip()

                for value in row.values()

                if value is not None
                and str(value).strip()
            ]

            if not meaningful_values:
                continue

            cleaned_rows.append(
                clean_dataset_row(
                    row
                )
            )

        return cleaned_rows

    except Exception as error:

        print(
            "Dataset read failed:",
            error
        )

        return []


# ============================================================
# REWRITE CLEAN DATASET
# ============================================================

def rewrite_dataset(
    rows
):
    """
    Rebuilds the CSV from clean records.

    This ensures:
      - CSV format
      - no blank cells
      - no empty columns
      - no malformed rows
      - consistent headers
    """

    if not rows:
        return

    cleaned_rows = []

    for row in rows:

        cleaned_row = clean_dataset_row(
            row
        )

        cleaned_rows.append(
            cleaned_row
        )

    active_columns = get_active_columns(
        cleaned_rows
    )

    if not active_columns:
        return

    try:

        with open(
            CSV_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=active_columns,
                extrasaction="ignore"
            )

            writer.writeheader()

            for row in cleaned_rows:

                output_row = {}

                for column in active_columns:

                    value = row.get(
                        column
                    )

                    if value is None:

                        if column in [
                            "answer_lines",
                            "citation_count",
                            "reference_count",
                            "incoming_citation_count",
                            "outgoing_reference_count"
                        ]:

                            value = 0

                        else:

                            value = DEFAULT_TEXT

                    if isinstance(
                        value,
                        str
                    ) and not value.strip():

                        value = DEFAULT_TEXT

                    output_row[column] = value

                writer.writerow(
                    output_row
                )

    except Exception as error:

        print(
            "Dataset rewrite failed:",
            error
        )


# ============================================================
# CLEAN EXISTING CSV
# ============================================================

def clean_existing_csv():

    if not CSV_FILE.exists():
        return

    rows = read_existing_rows()

    if rows:

        rewrite_dataset(
            rows
        )


# ============================================================
# INITIALIZE CSV
# ============================================================

def initialize_csv():

    DATASETS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if CSV_FILE.exists():

        clean_existing_csv()

    # Do NOT create a header-only dataset.
    #
    # The CSV is created when the first actual
    # record is saved.
    #
    # This prevents an empty dataset containing
    # only columns.

    return


# ============================================================
# SAVE COMPLETE PAPER / QA RECORD
# ============================================================

def save_to_csv(
    paper,
    operation,
    user_question="",
    answer="",
    citation_count="",
    reference_count="",
    incoming_citation_count="",
    outgoing_reference_count="",
    incoming_citations=None,
    outgoing_references=None,
    filename="",
    extracted_text="",
    status="success"
):
    """
    Saves one complete ResearchIQ interaction.
    """

    initialize_csv()

    paper = paper or {}

    # --------------------------------------------------------
    # Authors
    # --------------------------------------------------------

    authors = paper.get(
        "authors",
        []
    )

    if isinstance(
        authors,
        list
    ):

        author_values = []

        for author in authors:

            author_text = clean_text(
                author,
                ""
            )

            if author_text:

                author_values.append(
                    author_text
                )

        authors = ", ".join(
            author_values
        )

    authors = clean_text(
        authors
    )

    # --------------------------------------------------------
    # Answer line count
    # --------------------------------------------------------

    answer_lines = 0

    if answer:

        answer_lines = len(
            [
                line
                for line in str(
                    answer
                ).splitlines()
                if line.strip()
            ]
        )

    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    timestamp = datetime.now().isoformat()

    # --------------------------------------------------------
    # Citation/reference identifiers
    # --------------------------------------------------------

    incoming_identifiers = clean_list(
        incoming_citations
    )

    outgoing_identifiers = clean_list(
        outgoing_references
    )

    # --------------------------------------------------------
    # Build complete record
    # --------------------------------------------------------

    row = {

        "timestamp":
            timestamp,

        "operation":
            operation,

        "filename":
            filename
            or paper.get(
                "filename",
                ""
            ),

        "paper_title":
            paper.get(
                "title",
                ""
            ),

        "doi":
            paper.get(
                "doi",
                ""
            ),

        "paper_identifier":
            paper.get(
                "identifier",
                ""
            ),

        "authors":
            authors,

        "publication_name":
            paper.get(
                "publication_name",
                ""
            ),

        "publication_date":
            paper.get(
                "publication_date",
                ""
            ),

        "document_type":
            paper.get(
                "document_type",
                ""
            ),

        "abstract":
            paper.get(
                "abstract",
                ""
            ),

        "extracted_text":
            extracted_text
            or paper.get(
                "extracted_text",
                ""
            ),

        "user_question":
            user_question,

        "answer":
            answer,

        "answer_lines":
            answer_lines,

        "answer_format":
            "5 lines",

        "citation_count":
            citation_count,

        "reference_count":
            reference_count,

        "incoming_citation_count":
            incoming_citation_count,

        "outgoing_reference_count":
            outgoing_reference_count,

        "incoming_citation_identifiers":
            incoming_identifiers,

        "outgoing_reference_identifiers":
            outgoing_identifiers,

        "source":
            "OpenCitations + Research IQ",

        "status":
            status
    }

    cleaned_row = clean_dataset_row(
        row
    )

    # --------------------------------------------------------
    # Read existing records
    # --------------------------------------------------------

    existing_rows = read_existing_rows()

    # --------------------------------------------------------
    # Add the new actual record
    # --------------------------------------------------------

    existing_rows.append(
        cleaned_row
    )

    # --------------------------------------------------------
    # Rewrite complete clean CSV
    # --------------------------------------------------------

    rewrite_dataset(
        existing_rows
    )


# ============================================================
# HEADERS
# ============================================================

def get_headers():

    headers = {
        "Accept": "application/json"
    }

    if OPENCITATIONS_TOKEN:

        headers[
            "authorization"
        ] = OPENCITATIONS_TOKEN

    return headers


# ============================================================
# GENERIC OPENCITATIONS REQUEST
# ============================================================

def make_request(
    endpoint
):

    url = (
        f"{BASE_URL}/{endpoint}"
    )

    try:

        response = requests.get(
            url,
            headers=get_headers(),
            timeout=20
        )

        if response.status_code == 200:

            return response.json()

        print(
            "OpenCitations API error:",
            response.status_code,
            response.text
        )

        return None

    except requests.exceptions.RequestException as error:

        print(
            "OpenCitations request failed:",
            error
        )

        return None


# ============================================================
# CITATION COUNT
# ============================================================

def get_citation_count(
    identifier
):

    if not identifier:

        return {
            "citation_count": 0
        }

    endpoint = (
        f"citation-count/"
        f"{identifier}"
    )

    result = make_request(
        endpoint
    )

    if result:

        try:

            count = int(
                result[0].get(
                    "count",
                    0
                )
            )

        except (
            ValueError,
            TypeError,
            IndexError
        ):

            count = 0

        return {
            "citation_count": count
        }

    return {
        "citation_count": 0
    }


# ============================================================
# REFERENCE COUNT
# ============================================================

def get_reference_count(
    identifier
):

    if not identifier:

        return {
            "reference_count": 0
        }

    endpoint = (
        f"reference-count/"
        f"{identifier}"
    )

    result = make_request(
        endpoint
    )

    if result:

        try:

            count = int(
                result[0].get(
                    "count",
                    0
                )
            )

        except (
            ValueError,
            TypeError,
            IndexError
        ):

            count = 0

        return {
            "reference_count": count
        }

    return {
        "reference_count": 0
    }


# ============================================================
# INCOMING CITATIONS
# ============================================================

def get_citations(
    identifier
):

    if not identifier:
        return []

    endpoint = (
        f"citations/"
        f"{identifier}"
    )

    result = make_request(
        endpoint
    )

    if result is None:
        return []

    return result


# ============================================================
# OUTGOING REFERENCES
# ============================================================

def get_references(
    identifier
):

    if not identifier:
        return []

    endpoint = (
        f"references/"
        f"{identifier}"
    )

    result = make_request(
        endpoint
    )

    if result is None:
        return []

    return result


# ============================================================
# COMPLETE CITATION INFORMATION
# ============================================================

def get_citation_information(
    identifier
):

    citation_data = (
        get_citation_count(
            identifier
        )
    )

    reference_data = (
        get_reference_count(
            identifier
        )
    )

    citations = (
        get_citations(
            identifier
        )
    )

    references = (
        get_references(
            identifier
        )
    )

    return {

        "citation_count":
            citation_data.get(
                "citation_count",
                0
            ),

        "reference_count":
            reference_data.get(
                "reference_count",
                0
            ),

        "incoming_citations":
            citations,

        "outgoing_references":
            references,

        "incoming_citation_count":
            len(citations),

        "outgoing_reference_count":
            len(references)
    }


# ============================================================
# PREPARE PAPER CONTEXT
# ============================================================

def build_paper_context(
    paper,
    citation_information
):

    authors = paper.get(
        "authors",
        []
    )

    if isinstance(
        authors,
        list
    ):

        authors = ", ".join(
            str(author)
            for author in authors
        )

    context = f"""

RESEARCH PAPER

Title:

{paper.get("title", "Unknown")}

Authors:

{authors or "Unknown"}

Publication:

{paper.get("publication_name", "Unknown")}

Published:

{paper.get("publication_date", "Unknown")}

DOI:

{paper.get("doi", "Unknown")}

Document Type:

{paper.get("document_type", "Research Paper")}

Abstract:

{paper.get("abstract", "No abstract provided.")}

CITATION INFORMATION

Citation Count:

{citation_information.get("citation_count", 0)}

Reference Count:

{citation_information.get("reference_count", 0)}

Incoming Citations:

{citation_information.get("incoming_citation_count", 0)}

Outgoing References:

{citation_information.get("outgoing_reference_count", 0)}

"""

    return context


# ============================================================
# FORCE FIVE-LINE ANSWER
# ============================================================

def normalize_answer(
    answer
):

    if not answer:
        return ""

    lines = [

        line.strip()

        for line in answer.splitlines()

        if line.strip()
    ]

    cleaned = []

    for line in lines:

        if line.startswith(
            (
                "1.",
                "2.",
                "3.",
                "4.",
                "5."
            )
        ):

            line = line[2:].strip()

        cleaned.append(
            line
        )

    if len(cleaned) > 5:

        cleaned = cleaned[:5]

    while len(cleaned) < 5:

        cleaned.append("")

    return "\n".join(
        cleaned[:5]
    )


# ============================================================
# AI QUESTION ANSWERING
# ============================================================

def ask_ai_about_paper(
    paper,
    question,
    citation_information
):

    if not question:

        return {
            "success": False,
            "error": "Question is required.",
            "answer": ""
        }

    paper_context = build_paper_context(
        paper,
        citation_information
    )

    prompt = f"""

You are the ResearchIQ research-paper assistant.

Answer the user's question using ONLY the research paper

content supplied below.

IMPORTANT:

- Give a concise answer.

- Normally answer in 3 to 4 short lines.

- If the question requires detailed explanation, use at most 7 short lines.

- Do not give a huge paragraph.

- Do not repeat the entire paper.

- Do not invent information.

- Do not fabricate citations.

- Do not use markdown headings.

- Answer the question directly.

- Keep the answer academically useful and easy to understand.

If the requested information is not available in the paper,

say that the paper does not provide enough information.

RESEARCH PAPER:

{paper_context}

USER QUESTION:

{question}

Return ONLY the answer.

"""

    try:

        payload = {

            "model":
                OLLAMA_MODEL,

            "messages": [

                {
                    "role": "system",
                    "content": (
                        "You are an academic "
                        "research-paper question "
                        "answering assistant. "
                        "Use only the supplied "
                        "paper content."
                    )
                },

                {
                    "role": "user",
                    "content": prompt
                }
            ],

            "stream": False,

            "options": {
                "temperature": 0.2
            }
        }

        print(
            "\n========== OLLAMA REQUEST =========="
        )

        print(
            "URL:",
            OLLAMA_URL
        )

        print(
            "MODEL:",
            OLLAMA_MODEL
        )

        print(
            "====================================\n"
        )

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )

        if response.status_code != 200:

            print(
                "\n========== OLLAMA ERROR =========="
            )

            print(
                "STATUS:",
                response.status_code
            )

            print(
                "RESPONSE:",
                response.text
            )

            print(
                "==================================\n"
            )

            return {

                "success": False,

                "error": (
                    f"Ollama API error "
                    f"{response.status_code}: "
                    f"{response.text}"
                ),

                "answer": ""
            }

        data = response.json()

        answer = (
            data
            .get("message", {})
            .get("content", "")
        )

        answer = answer.strip()

        if not answer:

            return {

                "success": False,

                "error":
                    "Ollama returned an empty answer.",

                "answer": ""
            }

        return {

            "success": True,

            "answer": answer
        }

    except requests.exceptions.RequestException as error:

        print(
            "\nOllama request failed:",
            error
        )

        return {

            "success": False,

            "error":
                f"AI request failed: {str(error)}",

            "answer": ""
        }

    except Exception as error:

        print(
            "\nUnexpected Ollama error:",
            error
        )

        return {

            "success": False,

            "error":
                f"Unexpected AI error: {str(error)}",

            "answer": ""
        }


# ============================================================
# ASK QUESTION ABOUT A PAPER
# ============================================================

def ask_question(
    paper,
    question
):

    if not paper:

        return {

            "success": False,

            "error":
                "Research paper is required."
        }

    if not question:

        return {

            "success": False,

            "error":
                "Question is required."
        }

    identifier = (
        paper.get("identifier")
        or paper.get("doi")
        or ""
    )

    # --------------------------------------------------------
    # Get citation information
    # --------------------------------------------------------

    citation_information = (
        get_citation_information(
            identifier
        )
    )

    # --------------------------------------------------------
    # Ask AI
    # --------------------------------------------------------

    ai_result = ask_ai_about_paper(
        paper=paper,
        question=question,
        citation_information=
            citation_information
    )

    # --------------------------------------------------------
    # Failed AI response
    # --------------------------------------------------------

    if not ai_result["success"]:

        save_to_csv(
            paper=paper,
            operation=
                "paper_question",
            user_question=
                question,
            citation_count=
                citation_information.get(
                    "citation_count",
                    0
                ),
            reference_count=
                citation_information.get(
                    "reference_count",
                    0
                ),
            incoming_citation_count=
                citation_information.get(
                    "incoming_citation_count",
                    0
                ),
            outgoing_reference_count=
                citation_information.get(
                    "outgoing_reference_count",
                    0
                ),
            incoming_citations=
                citation_information.get(
                    "incoming_citations",
                    []
                ),
            outgoing_references=
                citation_information.get(
                    "outgoing_references",
                    []
                ),
            answer=
                "No answer generated",
            filename=
                paper.get(
                    "filename",
                    ""
                ),
            extracted_text=
                paper.get(
                    "extracted_text",
                    paper.get(
                        "abstract",
                        ""
                    )
                ),
            status="failed"
        )

        return ai_result

    # --------------------------------------------------------
    # Get answer
    # --------------------------------------------------------

    answer = ai_result[
        "answer"
    ]

    # --------------------------------------------------------
    # Save EVERYTHING related to the QA interaction
    # --------------------------------------------------------

    save_to_csv(
        paper=paper,
        operation=
            "paper_question",
        user_question=
            question,
        answer=
            answer,
        citation_count=
            citation_information.get(
                "citation_count",
                0
            ),
        reference_count=
            citation_information.get(
                "reference_count",
                0
            ),
        incoming_citation_count=
            citation_information.get(
                "incoming_citation_count",
                0
            ),
        outgoing_reference_count=
            citation_information.get(
                "outgoing_reference_count",
                0
            ),
        incoming_citations=
            citation_information.get(
                "incoming_citations",
                []
            ),
        outgoing_references=
            citation_information.get(
                "outgoing_references",
                []
            ),
        filename=
            paper.get(
                "filename",
                ""
            ),
        extracted_text=
            paper.get(
                "extracted_text",
                paper.get(
                    "abstract",
                    ""
                )
            ),
        status="success"
    )

    # --------------------------------------------------------
    # Return complete response to frontend
    # --------------------------------------------------------

    return {

        "success": True,

        "question":
            question,

        "answer":
            answer,

        # Paper information

        "paper": {

            "title":
                paper.get(
                    "title",
                    ""
                ),

            "authors":
                paper.get(
                    "authors",
                    []
                ),

            "publication_name":
                paper.get(
                    "publication_name",
                    ""
                ),

            "publication_date":
                paper.get(
                    "publication_date",
                    ""
                ),

            "doi":
                paper.get(
                    "doi",
                    ""
                ),

            "document_type":
                paper.get(
                    "document_type",
                    ""
                )
        },

        # Citation information

        "citation_information":
            citation_information,

        "source":
            "Research IQ",

        "answer_format":
            "5 lines",

        "timestamp":
            datetime.now().isoformat()
    }


# ============================================================
# PAPER ANALYSIS WITHOUT A QUESTION
# ============================================================

def summarize_paper(
    paper
):

    return ask_question(
        paper=paper,
        question=(
            "Give me a concise summary of this "
            "research project, including its "
            "problem, method, findings, significance "
            "and conclusion."
        )
    )


# ============================================================
# PAPER INFORMATION
# ============================================================

def get_paper_information(
    paper
):

    if not paper:

        return {

            "success": False,

            "error":
                "Research paper is required."
        }

    identifier = (
        paper.get("identifier")
        or paper.get("doi")
        or ""
    )

    citation_information = (
        get_citation_information(
            identifier
        )
    )

    # --------------------------------------------------------
    # Save metadata lookup
    # --------------------------------------------------------

    save_to_csv(
        paper=paper,
        operation=
            "paper_information",
        user_question=
            "Metadata lookup",
        answer=
            "Paper metadata and citation information retrieved.",
        citation_count=
            citation_information.get(
                "citation_count",
                0
            ),
        reference_count=
            citation_information.get(
                "reference_count",
                0
            ),
        incoming_citation_count=
            citation_information.get(
                "incoming_citation_count",
                0
            ),
        outgoing_reference_count=
            citation_information.get(
                "outgoing_reference_count",
                0
            ),
        incoming_citations=
            citation_information.get(
                "incoming_citations",
                []
            ),
        outgoing_references=
            citation_information.get(
                "outgoing_references",
                []
            ),
        filename=
            paper.get(
                "filename",
                ""
            ),
        extracted_text=
            paper.get(
                "extracted_text",
                paper.get(
                    "abstract",
                    ""
                )
            ),
        status="success"
    )

    return {

        "success": True,

        "paper":
            paper,

        "citation_information":
            citation_information,

        "source":
            "OpenCitations"
    }


# ============================================================
# UPLOADED PAPER PROCESSING
# ============================================================

def extract_uploaded_paper_data(
    uploaded_file
):

    if not uploaded_file:

        return {

            "success": False,

            "error":
                "Paper file is required."
        }

    filename = clean_text(
        uploaded_file.filename,
        "uploaded_paper.pdf"
    )

    # --------------------------------------------------------
    # Basic PDF validation
    # --------------------------------------------------------

    if not filename.lower().endswith(
        ".pdf"
    ):

        return {

            "success": False,

            "error":
                "Only PDF research papers are supported."
        }

    try:

        pdf_bytes = uploaded_file.read()

        if not pdf_bytes:

            return {

                "success": False,

                "error":
                    "The uploaded PDF is empty."
            }

        # ----------------------------------------------------
        # Attempt PDF text extraction
        # ----------------------------------------------------

        extracted_text = ""

        try:

            import io
            from pypdf import PdfReader

            reader = PdfReader(
                io.BytesIO(
                    pdf_bytes
                )
            )

            pages = []

            for page in reader.pages:

                page_text = (
                    page.extract_text()
                    or ""
                )

                if page_text.strip():

                    pages.append(
                        page_text.strip()
                    )

            extracted_text = "\n".join(
                pages
            )

        except Exception as error:

            print(
                "PDF text extraction warning:",
                error
            )

        # ----------------------------------------------------
        # Try to identify DOI
        # ----------------------------------------------------

        doi = ""

        if extracted_text:

            import re

            doi_match = re.search(
                r"(?:https?://doi\.org/|doi:\s*)?"
                r"(10\.\d{4,9}/[-._;()/:\w]+)",
                extracted_text,
                re.IGNORECASE
            )

            if doi_match:

                doi = (
                    doi_match.group(1)
                    .rstrip(
                        ".,;)"
                    )
                )

        # ----------------------------------------------------
        # Build paper object
        # ----------------------------------------------------

        paper = {

            "title":
                Path(filename).stem,

            "doi":
                doi,

            "identifier":
                f"doi:{doi}"
                if doi
                else "",

            "authors":
                [],

            "publication_name":
                "",

            "publication_date":
                "",

            "document_type":
                "Research Paper",

            "abstract":
                extracted_text[:12000]
                if extracted_text
                else
                "No extractable text was found in the uploaded PDF.",

            "extracted_text":
                extracted_text
                if extracted_text
                else
                "No extractable text was found in the uploaded PDF.",

            "filename":
                filename
        }

        return {

            "success":
                True,

            "paper":
                paper,

            "extracted_text":
                extracted_text,

            "filename":
                filename
        }

    except Exception as error:

        return {

            "success": False,

            "error":
                f"Failed to process uploaded paper: {str(error)}"
        }


# ============================================================
# UPLOAD PAPER
# ============================================================

def process_uploaded_paper(
    file
):

    try:

        if not file:

            return {

                "success": False,

                "error":
                    "No PDF file was uploaded. "
                    "Use the 'file' form field."
            }

        # ----------------------------------------------------
        # Use uploaded Flask file object directly
        # ----------------------------------------------------

        uploaded_result = (
            extract_uploaded_paper_data(
                file
            )
        )

        if not uploaded_result["success"]:

            return uploaded_result

        paper = uploaded_result[
            "paper"
        ]

        extracted_text = (
            uploaded_result.get(
                "extracted_text",
                ""
            )
        )

        filename = (
            uploaded_result.get(
                "filename",
                ""
            )
        )

        # ----------------------------------------------------
        # Get OpenCitations data when DOI exists
        # ----------------------------------------------------

        identifier = (
            paper.get("identifier")
            or paper.get("doi")
            or ""
        )

        citation_information = (
            get_citation_information(
                identifier
            )
            if identifier
            else {

                "citation_count":
                    0,

                "reference_count":
                    0,

                "incoming_citations":
                    [],

                "outgoing_references":
                    [],

                "incoming_citation_count":
                    0,

                "outgoing_reference_count":
                    0
            }
        )

        # ----------------------------------------------------
        # Save COMPLETE uploaded paper information
        # ----------------------------------------------------

        save_to_csv(
            paper=paper,
            operation=
                "paper_upload",
            user_question=
                "Paper uploaded",
            answer=
                "Research paper uploaded and processed.",
            citation_count=
                citation_information.get(
                    "citation_count",
                    0
                ),
            reference_count=
                citation_information.get(
                    "reference_count",
                    0
                ),
            incoming_citation_count=
                citation_information.get(
                    "incoming_citation_count",
                    0
                ),
            outgoing_reference_count=
                citation_information.get(
                    "outgoing_reference_count",
                    0
                ),
            incoming_citations=
                citation_information.get(
                    "incoming_citations",
                    []
                ),
            outgoing_references=
                citation_information.get(
                    "outgoing_references",
                    []
                ),
            filename=
                filename,
            extracted_text=
                extracted_text,
            status="success"
        )

        return {

            "success":
                True,

            "message":
                "Research paper uploaded successfully.",

            "paper":
                paper,

            "citation_information":
                citation_information,

            "extracted_text":
                extracted_text,

            "source":
                "OpenCitations + Research IQ",

            "timestamp":
                datetime.now().isoformat()
        }

    except Exception as error:

        print(
            "OpenCitations upload error:",
            error
        )

        return {

            "success": False,

            "error":
                f"Failed to upload paper: {str(error)}"
        }


# ============================================================
# COMPATIBILITY FUNCTION FOR app.py
# ============================================================

#
# app.py imports:
#
# from services.opencitations_service import upload_paper
#
# The actual processing function above is named
# process_uploaded_paper().
#
# This wrapper keeps the existing processing logic unchanged
# while providing the function expected by app.py.
#
# ============================================================

def upload_paper(
    file=None
):

    if file is None:

        file = (
            request.files.get(
                "file"
            )
            or
            request.files.get(
                "paper"
            )
        )

    return process_uploaded_paper(
        file
    )


# ============================================================
# FLASK UPLOAD ENDPOINT
# ============================================================

@opencitations_bp.route(
    "/upload-paper",
    methods=["POST"]
)

def upload_paper_endpoint():

    uploaded_file = (
        request.files.get(
            "file"
        )
        or
        request.files.get(
            "paper"
        )
    )

    result = process_uploaded_paper(
        uploaded_file
    )

    if not result.get(
        "success"
    ):

        return jsonify(
            result
        ), 400

    return jsonify(
        result
    ), 200


# ============================================================
# GET SAVED PAPER
# ============================================================

@opencitations_bp.route(
    "/saved-paper",
    methods=["GET"]
)

def saved_paper_endpoint():

    try:

        rows = read_existing_rows()

        if not rows:

            return jsonify({

                "success": False,

                "error":
                    "No saved paper found."

            }), 404

        # Find the most recent uploaded paper

        uploaded_rows = [

            row

            for row in rows

            if row.get("operation") ==
            "paper_upload"
        ]

        if not uploaded_rows:

            return jsonify({

                "success": False,

                "error":
                    "No saved paper found."

            }), 404

        latest = uploaded_rows[-1]

        paper = {

            "title":
                latest.get(
                    "paper_title",
                    ""
                ),

            "doi":
                latest.get(
                    "doi",
                    ""
                ),

            "identifier":
                latest.get(
                    "paper_identifier",
                    ""
                ),

            "authors": (

                latest.get(
                    "authors",
                    ""
                ).split(", ")

                if latest.get("authors")
                and latest.get("authors")
                != "Not available"

                else []
            ),

            "publication_name":
                latest.get(
                    "publication_name",
                    ""
                ),

            "publication_date":
                latest.get(
                    "publication_date",
                    ""
                ),

            "document_type":
                latest.get(
                    "document_type",
                    ""
                ),

            "abstract":
                latest.get(
                    "abstract",
                    ""
                ),

            "extracted_text":
                latest.get(
                    "extracted_text",
                    ""
                ),

            "filename":
                latest.get(
                    "filename",
                    ""
                )
        }

        return jsonify({

            "success": True,

            "paper": paper,

            "citation_information": {

                "citation_count":
                    clean_number(
                        latest.get(
                            "citation_count",
                            0
                        )
                    ),

                "reference_count":
                    clean_number(
                        latest.get(
                            "reference_count",
                            0
                        )
                    ),

                "incoming_citation_count":
                    clean_number(
                        latest.get(
                            "incoming_citation_count",
                            0
                        )
                    ),

                "outgoing_reference_count":
                    clean_number(
                        latest.get(
                            "outgoing_reference_count",
                            0
                        )
                    )
            },

            "source":
                "OpenCitations + Research IQ"

        }), 200

    except Exception as error:

        print(
            "Saved paper error:",
            error
        )

        return jsonify({

            "success": False,

            "error":
                f"Failed to load saved paper: {str(error)}"

        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

def check_api():

    if not OPENCITATIONS_TOKEN:

        return {

            "status":
                "error",

            "message":
                "OpenCitations_API_KEY not found in .env"
        }

    try:

        response = requests.get(

            f"{BASE_URL}/citation-count/"
            "doi:10.1108/jd-12-2013-0166",

            headers=
                get_headers(),

            timeout=10
        )

        if response.status_code == 200:

            return {

                "status":
                    "ok",

                "message":
                    "OpenCitations API is working"
            }

        return {

            "status":
                "error",

            "message":
                f"API returned {response.status_code}"
        }

    except requests.exceptions.RequestException as error:

        return {

            "status":
                "error",

            "message":
                str(error)
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n======================================"
    )

    print(
        " Research IQ - OpenCitations Q&A"
    )

    print(
        "======================================\n"
    )

    health = check_api()

    print(
        "OpenCitations:",
        health
    )

    test_paper = {

        "title":
            "Example Research Paper",

        "doi":
            "doi:10.1108/jd-12-2013-0166",

        "identifier":
            "doi:10.1108/jd-12-2013-0166",

        "authors":
            ["Example Author"],

        "publication_name":
            "Example Journal",

        "publication_date":
            "2024-01-01",

        "document_type":
            "Article",

        "abstract":
            (
                "This is example paper content. "
                "Replace this with the abstract or "
                "extracted PDF text."
            ),

        "extracted_text":
            (
                "This is example paper content. "
                "Replace this with the abstract or "
                "extracted PDF text."
            ),

        "filename":
            "Example_Research_Paper.pdf"
    }

    print(
        "\nTesting paper information..."
    )

    information = get_paper_information(
        test_paper
    )

    print(
        json.dumps(
            information,
            indent=2
        )
    )

    print(
        "\nTesting Q&A..."
    )

    result = ask_question(
        paper=test_paper,
        question=(
            "Can I know something more "
            "about this project as a summary?"
        )
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )

    print(
        "\nCSV:"
    )

    print(
        CSV_FILE
    )