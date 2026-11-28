import os
import requests
import pandas as pd
import xml.etree.ElementTree as ET

from datetime import datetime, timezone
from urllib.parse import quote

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# CONFIGURATION
# ============================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)

DATASET_DIR = os.path.join(
    BACKEND_DIR,
    "datasets"
)

# ============================================================
# CSV OUTPUT FILE
# ============================================================

CSV_FILE = os.path.join(
    DATASET_DIR,
    "research_results.csv"
)


# ============================================================
# ARXIV API CONFIGURATION
# ============================================================

# arXiv is used directly.
# No local arXiv CSV dataset is required.

ARXIV_API_URL = (
    "https://export.arxiv.org/api/query"
)

# Number of papers requested from arXiv.
#
# We retrieve more than TOP_K so that papers with inactive
# links can be removed while still trying to return TOP_K.
#
ARXIV_SEARCH_SIZE = 50


# ============================================================
# OLLAMA CONFIGURATION
# ============================================================

# Ollama runs locally.
OLLAMA_URL = "http://localhost:11434/api/chat"

# Make sure this model is installed using:
#
# ollama pull qwen2.5:1.5b
#
OLLAMA_MODEL = "qwen2.5:1.5b"


# ============================================================
# RAG CONFIGURATION
# ============================================================

# Number of papers finally retrieved.
TOP_K = 11

# Retrieve more candidates internally so inactive papers
# can be removed while still returning up to TOP_K valid papers.
CANDIDATE_K = TOP_K * 5


# ============================================================
# LINK VALIDATION CONFIGURATION
# ============================================================

REQUEST_TIMEOUT = 10

REQUEST_HEADERS = {
    "User-Agent": (
        "ResearchIQ/1.0 "
        "(Research Paper Retrieval System; "
        "mailto:researchiq@example.com)"
    )
}


# ============================================================
# CSV COLUMNS
# ============================================================

# These columns are based on the actual response attributes
# produced by the research pipeline.
#
# One CSV row represents one retrieved research paper.
#
CSV_COLUMNS = [
    "timestamp",
    "topic",
    "result",
    "retrieved_paper_count",
    "paper_rank",
    "source",
    "title",
    "authors",
    "category",
    "published_date",
    "similarity_score",
    "url",
    "pdf_url",
    "text"
]


# ============================================================
# 1. ENSURE CSV FILE EXISTS
# ============================================================

def ensure_csv():
    """
    Create the datasets directory and CSV file if they
    do not already exist.

    The CSV is created with clean, meaningful columns.

    No empty seed rows are created.
    """

    os.makedirs(
        DATASET_DIR,
        exist_ok=True
    )

    if not os.path.exists(CSV_FILE):

        empty_df = pd.DataFrame(
            columns=CSV_COLUMNS
        )

        empty_df.to_csv(
            CSV_FILE,
            index=False,
            encoding="utf-8-sig"
        )

        print(
            f"Created CSV file:\n{CSV_FILE}"
        )


# ============================================================
# 2. CHECK WHETHER A LINK IS ACTIVE
# ============================================================

def is_active_url(url):
    """
    Check whether a URL is actually reachable.

    HEAD is attempted first because it is lightweight.
    If HEAD is rejected by the server, a GET request
    is attempted as a fallback.

    Returns:
        True  -> URL is reachable
        False -> URL is unavailable
    """

    if not url:
        return False

    url = str(url).strip()

    if not url:
        return False

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):
        return False

    try:

        response = requests.head(
            url,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )

        if 200 <= response.status_code < 400:

            return True

    except requests.RequestException:

        pass

    # --------------------------------------------------------
    # Some research websites reject HEAD requests.
    # Try GET as fallback.
    # --------------------------------------------------------

    try:

        response = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            stream=True
        )

        active = (
            200 <= response.status_code < 400
        )

        response.close()

        return active

    except requests.RequestException:

        return False


# ============================================================
# 3. CHECK PAPER VIEW + PDF LINKS
# ============================================================

def validate_paper_links(document):
    """
    A paper is considered recommendable ONLY when:

        1. View/site URL exists and works.
        2. PDF/download URL exists and works.

    Papers failing either check are rejected.
    """

    view_url = str(
        document.get(
            "url",
            ""
        )
    ).strip()

    pdf_url = str(
        document.get(
            "pdf_url",
            ""
        )
    ).strip()

    if not view_url:
        return False

    if not pdf_url:
        return False

    # --------------------------------------------------------
    # Check View Site
    # --------------------------------------------------------

    if not is_active_url(
        view_url
    ):

        print(
            f"   ✗ Inactive view link: "
            f"{document.get('title', '')}"
        )

        return False

    # --------------------------------------------------------
    # Check PDF
    # --------------------------------------------------------

    if not is_active_url(
        pdf_url
    ):

        print(
            f"   ✗ Inactive PDF link: "
            f"{document.get('title', '')}"
        )

        return False

    return True


# ============================================================
# 4. NORMALIZE ARXIV ID
# ============================================================

def normalize_arxiv_id(arxiv_id):
    """
    Normalize an arXiv identifier before constructing URLs.

    Examples:

        http://arxiv.org/abs/2505.15946
            -> 2505.15946

        https://arxiv.org/pdf/2505.15946
            -> 2505.15946

        2505.15946v3
            -> 2505.15946v3
    """

    if not arxiv_id:
        return ""

    arxiv_id = str(
        arxiv_id
    ).strip()

    # --------------------------------------------------------
    # Handle complete URLs.
    # --------------------------------------------------------

    if "arxiv.org/" in arxiv_id:

        arxiv_id = (
            arxiv_id
            .split(
                "arxiv.org/",
                1
            )[1]
        )

        if arxiv_id.startswith(
            "abs/"
        ):

            arxiv_id = arxiv_id[
                4:
            ]

        elif arxiv_id.startswith(
            "pdf/"
        ):

            arxiv_id = arxiv_id[
                4:
            ]

    # --------------------------------------------------------
    # Remove malformed abs- prefix.
    # --------------------------------------------------------

    if arxiv_id.startswith(
        "abs-"
    ):

        arxiv_id = arxiv_id[
            4:
        ]

    # --------------------------------------------------------
    # Remove leading/trailing slashes.
    # --------------------------------------------------------

    arxiv_id = arxiv_id.strip(
        "/"
    )

    return arxiv_id


# ============================================================
# 5. SEARCH ARXIV DIRECTLY
# ============================================================

def search_arxiv(
    topic,
    max_results=ARXIV_SEARCH_SIZE
):
    """
    Search arXiv directly using the live arXiv API.

    No local arXiv CSV dataset is required.

    The arXiv API returns:
        - title
        - authors
        - abstract/summary
        - category
        - published date
        - arXiv ID
        - paper URL
    """

    print(
        "\n===== SEARCHING ARXIV ====="
    )

    print(
        f"Topic: {topic}"
    )

    # --------------------------------------------------------
    # URL-encode the research topic.
    #
    # all:"topic" searches the topic across the searchable
    # arXiv metadata.
    # --------------------------------------------------------

    encoded_topic = quote(
        f'all:"{topic}"'
    )

    api_url = (
        f"{ARXIV_API_URL}"
        f"?search_query={encoded_topic}"
        f"&start=0"
        f"&max_results={max_results}"
        f"&sortBy=relevance"
        f"&sortOrder=descending"
    )

    print(
        f"arXiv API request:\n{api_url}"
    )

    try:

        response = requests.get(
            api_url,
            headers=REQUEST_HEADERS,
            timeout=30
        )

    except requests.ConnectionError:

        raise RuntimeError(
            "\nCould not connect to the arXiv API.\n"
            "Please check your internet connection."
        )

    except requests.Timeout:

        raise RuntimeError(
            "\narXiv API request timed out."
        )

    except requests.RequestException as e:

        raise RuntimeError(
            f"\nUnable to connect to arXiv:\n{e}"
        )

    print(
        f"arXiv status: "
        f"{response.status_code}"
    )

    if response.status_code != 200:

        raise RuntimeError(
            "arXiv API request failed: "
            f"{response.status_code}\n"
            f"{response.text}"
        )

    # --------------------------------------------------------
    # Parse Atom XML response.
    # --------------------------------------------------------

    try:

        root = ET.fromstring(
            response.text
        )

    except ET.ParseError as e:

        raise RuntimeError(
            f"Unable to parse arXiv response:\n{e}"
        )

    # --------------------------------------------------------
    # arXiv Atom namespace.
    # --------------------------------------------------------

    namespace = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom"
    }

    entries = root.findall(
        "atom:entry",
        namespace
    )

    if not entries:

        print(
            "No papers found on arXiv."
        )

        return []

    documents = []

    # --------------------------------------------------------
    # Convert each arXiv entry into the same document
    # structure used by the existing RAG pipeline.
    # --------------------------------------------------------

    for entry in entries:

        # ----------------------------------------------------
        # ID
        # ----------------------------------------------------

        id_element = entry.find(
            "atom:id",
            namespace
        )

        raw_id = ""

        if id_element is not None:

            raw_id = (
                id_element.text
                or ""
            ).strip()

        arxiv_id = normalize_arxiv_id(
            raw_id
        )

        if not arxiv_id:
            continue

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        title_element = entry.find(
            "atom:title",
            namespace
        )

        title = ""

        if title_element is not None:

            title = (
                title_element.text
                or ""
            ).strip()

            title = " ".join(
                title.split()
            )

        # ----------------------------------------------------
        # Summary / abstract
        # ----------------------------------------------------

        summary_element = entry.find(
            "atom:summary",
            namespace
        )

        summary = ""

        if summary_element is not None:

            summary = (
                summary_element.text
                or ""
            ).strip()

            summary = " ".join(
                summary.split()
            )

        # ----------------------------------------------------
        # Authors
        # ----------------------------------------------------

        authors = []

        for author in entry.findall(
            "atom:author",
            namespace
        ):

            name_element = author.find(
                "atom:name",
                namespace
            )

            if name_element is not None:

                name = (
                    name_element.text
                    or ""
                ).strip()

                if name:

                    authors.append(
                        name
                    )

        authors_text = ", ".join(
            authors
        )

        # ----------------------------------------------------
        # Published date
        # ----------------------------------------------------

        published_element = entry.find(
            "atom:published",
            namespace
        )

        published_date = ""

        if published_element is not None:

            published_date = (
                published_element.text
                or ""
            ).strip()

        # ----------------------------------------------------
        # Category
        # ----------------------------------------------------

        categories = []

        for category in entry.findall(
            "atom:category",
            namespace
        ):

            term = (
                category.attrib.get(
                    "term",
                    ""
                )
                .strip()
            )

            if term:

                categories.append(
                    term
                )

        category_text = ", ".join(
            categories
        )

        # ----------------------------------------------------
        # Construct arXiv URLs directly.
        # ----------------------------------------------------

        view_url = (
            "https://arxiv.org/abs/"
            f"{arxiv_id}"
        )

        pdf_url = (
            "https://arxiv.org/pdf/"
            f"{arxiv_id}"
        )

        # ----------------------------------------------------
        # Build searchable research text.
        # ----------------------------------------------------

        text = f"""
Title: {title}
Authors: {authors_text}
Category: {category_text}
Published: {published_date}
Summary: {summary}
""".strip()

        documents.append(
            {
                "source": "arXiv",
                "title": title,
                "authors": authors_text,
                "category": category_text,
                "published_date": published_date,
                "text": text,
                "url": view_url,
                "pdf_url": pdf_url
            }
        )

    print(
        f"arXiv papers received: "
        f"{len(documents)}"
    )

    return documents


# ============================================================
# 6. PREPARE RESEARCH DATA
# ============================================================

def prepare_research_data(
    topic
):
    """
    Retrieve research documents directly from arXiv.

    No local datasets are used.

    arXiv
       ↓
    Live research papers
       ↓
    Searchable research documents
    """

    print(
        "\n===== PREPARING RESEARCH TEXT ====="
    )

    documents = search_arxiv(
        topic,
        max_results=ARXIV_SEARCH_SIZE
    )

    print(
        f"Total documents available for RAG: "
        f"{len(documents)}"
    )

    return documents


# ============================================================
# 7. BUILD RAG RETRIEVER
# ============================================================

def build_rag_index(
    documents
):
    """
    Build a lightweight TF-IDF retrieval index.

    TF-IDF converts each research paper into a numerical
    vector based on the importance of words and phrases.
    """

    print(
        "\n===== BUILDING RAG INDEX ====="
    )

    if not documents:

        raise RuntimeError(
            "No research papers were found on arXiv."
        )

    texts = [
        document["text"]
        for document in documents
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=30000,
        ngram_range=(1, 2)
    )

    document_vectors = (
        vectorizer.fit_transform(
            texts
        )
    )

    print(
        f"RAG index created: "
        f"{document_vectors.shape[0]} documents x "
        f"{document_vectors.shape[1]} features"
    )

    return (
        vectorizer,
        document_vectors
    )


# ============================================================
# 8. RETRIEVE RELEVANT PAPERS
# ============================================================

def retrieve_relevant_documents(
    query,
    documents,
    vectorizer,
    document_vectors,
    top_k=TOP_K
):
    """
    Retrieve the most relevant research papers using
    cosine similarity.

    IMPORTANT:

    Papers are ranked first, but only papers with BOTH
    active View and active PDF links are returned.

    More candidates are checked internally so inactive
    papers do not simply reduce the final recommendation
    count.
    """

    print(
        "\n===== RAG RETRIEVAL ====="
    )

    print(
        f"Query: {query}"
    )

    # --------------------------------------------------------
    # Convert user query into TF-IDF vector.
    # --------------------------------------------------------

    query_vector = vectorizer.transform(
        [query]
    )

    # --------------------------------------------------------
    # Calculate cosine similarity.
    # --------------------------------------------------------

    similarities = cosine_similarity(
        query_vector,
        document_vectors
    ).flatten()

    # --------------------------------------------------------
    # Get more candidates than TOP_K.
    # --------------------------------------------------------

    candidate_count = min(
        CANDIDATE_K,
        len(documents)
    )

    candidate_indices = (
        similarities
        .argsort()[
            -candidate_count:
        ][::-1]
    )

    retrieved = []

    print(
        "\n===== CHECKING PAPER LINKS ====="
    )

    # --------------------------------------------------------
    # Validate papers in relevance order.
    # --------------------------------------------------------

    for index in candidate_indices:

        if len(retrieved) >= top_k:

            break

        score = float(
            similarities[index]
        )

        document = documents[
            index
        ].copy()

        document[
            "similarity_score"
        ] = round(
            score,
            4
        )

        # ----------------------------------------------------
        # Skip paper completely if either View or PDF link
        # is inactive.
        # ----------------------------------------------------

        if not validate_paper_links(
            document
        ):

            print(
                f"   Skipping paper: "
                f"{document['title']}"
            )

            continue

        retrieved.append(
            document
        )

        print(
            f"   ✓ Valid paper: "
            f"{document['title']}"
        )

    print(
        f"\nRetrieved {len(retrieved)} "
        f"valid research documents."
    )

    # --------------------------------------------------------
    # Display retrieved papers.
    # --------------------------------------------------------

    for i, document in enumerate(
        retrieved,
        start=1
    ):

        print(
            f"{i}. "
            f"[{document['source']}] "
            f"{document['title']} "
            f"(score="
            f"{document['similarity_score']}"
            f")"
        )

        print(
            f"   View: "
            f"{document['url']}"
        )

        print(
            f"   PDF: "
            f"{document['pdf_url']}"
        )

    return retrieved


# ============================================================
# 9. BUILD LLM CONTEXT
# ============================================================

def build_context(
    retrieved_documents
):
    """
    Convert the retrieved research papers into context
    supplied to the local Ollama LLM.
    """

    context_parts = []

    for i, document in enumerate(
        retrieved_documents,
        start=1
    ):

        context_parts.append(
            f"""
RESEARCH PAPER {i}

Source:
{document['source']}

Title:
{document['title']}

Authors:
{document.get('authors', '')}

Category:
{document.get('category', '')}

Published:
{document.get('published_date', '')}

Similarity Score:
{document['similarity_score']}

Research Content:
{document['text']}
""".strip()
        )

    return (
        "\n\n"
        "-----------------------------"
        "\n\n"
    ).join(
        context_parts
    )


# ============================================================
# 10. CALL OLLAMA
# ============================================================

def call_llm(
    context,
    topic
):
    """
    Send the retrieved research papers to a local
    Ollama model.

    Ollama runs locally, so no Groq API key is required.

    The generated research response is normal readable text.
    """

    print(
        "\n===== CALLING OLLAMA ====="
    )

    print(
        f"Model: {OLLAMA_MODEL}"
    )

    print(
        f"URL: {OLLAMA_URL}"
    )

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = f"""
You are ResearchIQ, an intelligent research assistant.

The user entered this research topic:

{topic}

A research retrieval system searched the live arXiv
research database and retrieved the most relevant
research papers.

Use ONLY the supplied research papers as the primary
factual basis for your response.

Your task is to help the user understand the research
available for their topic.

IMPORTANT RULES:

1. Use the supplied research papers as your primary source.

2. Do not invent research findings.

3. Do not create fake citations.

4. Mention the actual paper titles when referring to papers.

5. Explain important findings from the retrieved papers.

6. Identify common methodologies used in the papers.

7. Identify important observations.

8. Identify potential research gaps.

9. Keep the response focused on the user's research topic.

10. Do NOT return JSON.

11. Do NOT use JSON formatting.

12. Do NOT use markdown code fences.

13. Return normal readable research text.

14. Do not claim that a paper says something if that
    information is not present in the supplied context.

Structure your response using these headings:

Research Overview

Key Findings

Methodologies

Important Observations

Research Gaps

Retrieved Research Papers

Under "Retrieved Research Papers", mention the actual
paper titles supplied in the context.

============================================================
RETRIEVED RESEARCH CONTEXT
============================================================

{context}
"""

    # ========================================================
    # OLLAMA REQUEST
    # ========================================================

    payload = {
        "model": OLLAMA_MODEL,

        "messages": [
            {
                "role": "system",
                "content": (
                    "You are ResearchIQ, an expert "
                    "research assistant. "
                    "Use the supplied research context "
                    "as the primary factual source. "
                    "Return normal readable text. "
                    "Never return JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        "stream": False,

        "options": {
            "temperature": 0.3
        }
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=300
        )

    except requests.ConnectionError:

        raise RuntimeError(
            "\nCould not connect to Ollama.\n\n"
            "Make sure Ollama is running.\n"
            "Then check it with:\n\n"
            "ollama list\n"
        )

    except requests.Timeout:

        raise RuntimeError(
            "\nOllama took too long to respond."
        )

    except requests.RequestException as e:

        raise RuntimeError(
            f"Unable to connect to Ollama:\n{e}"
        )

    print(
        f"Ollama status: "
        f"{response.status_code}"
    )

    # ========================================================
    # HANDLE API ERROR
    # ========================================================

    if response.status_code != 200:

        print(
            "\nOllama response:"
        )

        print(
            response.text
        )

        raise RuntimeError(
            "Ollama request failed: "
            f"{response.status_code}\n"
            f"{response.text}"
        )

    # ========================================================
    # READ OLLAMA RESPONSE
    # ========================================================

    try:

        result = response.json()

    except ValueError:

        raise RuntimeError(
            "Ollama returned an invalid API response."
        )

    try:

        content = (
            result[
                "message"
            ][
                "content"
            ]
        )

    except (
        KeyError,
        TypeError
    ):

        raise RuntimeError(
            "Unexpected response format from Ollama.\n"
            f"Response:\n{result}"
        )

    if not content:

        raise RuntimeError(
            "Ollama returned an empty response."
        )

    print(
        "Ollama response received successfully."
    )

    return content.strip()


# ============================================================
# 11. SAVE RESEARCH RESPONSE TO CSV
# ============================================================

def save_research_response_to_csv(
    topic,
    result,
    retrieved_documents
):
    """
    Save the actual generated response and retrieved paper
    attributes into a clean CSV.

    IMPORTANT:

    One row = one retrieved research paper.

    Every row contains all CSV_COLUMNS in the exact
    correct order.

    Missing values are replaced with "N/A" so that
    records do not contain empty fields.

    Existing CSV records are also normalized to the
    exact same column structure.
    """

    ensure_csv()

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    rows = []

    retrieved_count = len(
        retrieved_documents
    )

    # --------------------------------------------------------
    # Create one actual CSV record for every retrieved paper.
    # --------------------------------------------------------

    for paper_rank, document in enumerate(
        retrieved_documents,
        start=1
    ):

        row = {
            "timestamp": timestamp,

            "topic": topic,

            "result": result,

            "retrieved_paper_count": retrieved_count,

            "paper_rank": paper_rank,

            "source": document.get(
                "source",
                "N/A"
            ),

            "title": document.get(
                "title",
                "N/A"
            ),

            "authors": document.get(
                "authors",
                "N/A"
            ),

            "category": document.get(
                "category",
                "N/A"
            ),

            "published_date": document.get(
                "published_date",
                "N/A"
            ),

            "similarity_score": document.get(
                "similarity_score",
                "N/A"
            ),

            "url": document.get(
                "url",
                "N/A"
            ),

            "pdf_url": document.get(
                "pdf_url",
                "N/A"
            ),

            "text": document.get(
                "text",
                "N/A"
            )
        }

        # ----------------------------------------------------
        # Make sure blank values are also stored as N/A.
        # ----------------------------------------------------

        for column in CSV_COLUMNS:

            value = row.get(
                column,
                "N/A"
            )

            if pd.isna(value):

                row[column] = "N/A"

            elif isinstance(
                value,
                str
            ) and not value.strip():

                row[column] = "N/A"

        rows.append(
            row
        )

    # --------------------------------------------------------
    # If no papers were retrieved, do NOT create an empty
    # fake research record.
    #
    # Instead, the CSV remains clean with no meaningless row.
    # --------------------------------------------------------

    if not rows:

        print(
            "\nNo retrieved papers available."
        )

        print(
            "No empty/fake CSV record was created."
        )

        return

    # --------------------------------------------------------
    # Convert records into DataFrame.
    #
    # Explicitly use CSV_COLUMNS so every value is placed
    # under the correct header.
    # --------------------------------------------------------

    new_df = pd.DataFrame(
        rows
    )

    new_df = new_df.reindex(
        columns=CSV_COLUMNS
    )

    # --------------------------------------------------------
    # Replace any remaining missing values.
    # --------------------------------------------------------

    new_df = new_df.fillna(
        "N/A"
    )

    # --------------------------------------------------------
    # Replace empty strings as well.
    # --------------------------------------------------------

    new_df = new_df.replace(
        r"^\s*$",
        "N/A",
        regex=True
    )

    # --------------------------------------------------------
    # Read existing CSV.
    # --------------------------------------------------------

    if os.path.exists(
        CSV_FILE
    ):

        try:

            existing_df = pd.read_csv(
                CSV_FILE,
                dtype=str
            )

        except (
            pd.errors.EmptyDataError,
            pd.errors.ParserError
        ):

            existing_df = pd.DataFrame(
                columns=CSV_COLUMNS
            )

    else:

        existing_df = pd.DataFrame(
            columns=CSV_COLUMNS
        )

    # --------------------------------------------------------
    # Make sure existing CSV has every required column.
    # --------------------------------------------------------

    for column in CSV_COLUMNS:

        if column not in existing_df.columns:

            existing_df[
                column
            ] = "N/A"

    # --------------------------------------------------------
    # Keep ONLY the required columns and place them in
    # the exact required order.
    # --------------------------------------------------------

    existing_df = existing_df[
        CSV_COLUMNS
    ]

    # --------------------------------------------------------
    # Replace missing values in existing records.
    # --------------------------------------------------------

    existing_df = existing_df.fillna(
        "N/A"
    )

    # --------------------------------------------------------
    # Replace empty strings in existing records.
    # --------------------------------------------------------

    existing_df = existing_df.replace(
        r"^\s*$",
        "N/A",
        regex=True
    )

    # --------------------------------------------------------
    # Append new actual records.
    # --------------------------------------------------------

    final_df = pd.concat(
        [
            existing_df,
            new_df
        ],
        ignore_index=True
    )

    # --------------------------------------------------------
    # Ensure final DataFrame ALWAYS has the exact required
    # columns in the exact required order.
    # --------------------------------------------------------

    final_df = final_df.reindex(
        columns=CSV_COLUMNS
    )

    # --------------------------------------------------------
    # Make absolutely sure there are no blank values.
    # --------------------------------------------------------

    final_df = final_df.fillna(
        "N/A"
    )

    final_df = final_df.replace(
        r"^\s*$",
        "N/A",
        regex=True
    )

    # --------------------------------------------------------
    # Remove completely empty rows.
    # --------------------------------------------------------

    final_df = final_df.dropna(
        how="all"
    )

    # --------------------------------------------------------
    # Remove accidental duplicate rows.
    # --------------------------------------------------------

    final_df = final_df.drop_duplicates(
        keep="last"
    )

    # --------------------------------------------------------
    # Save clean CSV.
    # --------------------------------------------------------

    final_df.to_csv(
        CSV_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        "\n===== CSV SAVED ====="
    )

    print(
        f"CSV file: {CSV_FILE}"
    )

    print(
        f"Records currently stored: "
        f"{len(final_df)}"
    )

    print(
        f"Columns stored: "
        f"{len(final_df.columns)}"
    )

    print(
        "CSV columns:"
    )

    for column in final_df.columns:

        print(
            f"   ✓ {column}"
        )


# ============================================================
# 12. COMPLETE RAG + OLLAMA PIPELINE
# ============================================================

def generate_research_response(
    topic
):
    """
    Complete ResearchIQ pipeline:

    User Topic
          ↓
    Live arXiv API
          ↓
    arXiv research papers
          ↓
    Research documents
          ↓
    TF-IDF
          ↓
    Cosine similarity
          ↓
    Candidate papers
          ↓
    Active View + PDF link validation
          ↓
    Top 11 valid papers
          ↓
    Research context
          ↓
    Ollama local API
          ↓
    Local LLM
          ↓
    Research explanation
          ↓
    Clean CSV record storage
    """

    # --------------------------------------------------------
    # Validate topic.
    # --------------------------------------------------------

    topic = str(
        topic
    ).strip()

    if not topic:

        raise ValueError(
            "Research topic cannot be empty."
        )

    # --------------------------------------------------------
    # STEP 1:
    # Search live arXiv.
    # --------------------------------------------------------

    documents = (
        prepare_research_data(
            topic
        )
    )

    if not documents:

        raise RuntimeError(
            "No relevant research papers were found on arXiv "
            f"for topic: {topic}"
        )

    # --------------------------------------------------------
    # STEP 2:
    # Build TF-IDF index.
    # --------------------------------------------------------

    vectorizer, document_vectors = (
        build_rag_index(
            documents
        )
    )

    # --------------------------------------------------------
    # STEP 3:
    # Retrieve TOP 11 VALID papers.
    #
    # Invalid View/PDF links are automatically skipped.
    # --------------------------------------------------------

    retrieved_documents = (
        retrieve_relevant_documents(
            topic,
            documents,
            vectorizer,
            document_vectors,
            top_k=TOP_K
        )
    )

    if not retrieved_documents:

        raise RuntimeError(
            "No valid research papers with active View and "
            "PDF links were found for this topic."
        )

    # --------------------------------------------------------
    # STEP 4:
    # Build LLM context.
    # --------------------------------------------------------

    context = build_context(
        retrieved_documents
    )

    # --------------------------------------------------------
    # STEP 5:
    # Send context to Ollama.
    # --------------------------------------------------------

    result = call_llm(
        context,
        topic
    )

    # --------------------------------------------------------
    # STEP 6:
    # Save actual response attributes to CSV.
    # --------------------------------------------------------

    save_research_response_to_csv(
        topic,
        result,
        retrieved_documents
    )

    # --------------------------------------------------------
    # STEP 7:
    # Return result.
    #
    # This Python dictionary is ONLY for communication
    # between this service and your Flask backend.
    #
    # It does NOT mean the research output is stored as JSON.
    # The actual persistent dataset is CSV.
    # --------------------------------------------------------

    return {
        "result": result,
        "retrieved_documents": retrieved_documents
    }


# ============================================================
# 13. DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("\n")

    print(
        "=" * 60
    )

    print(
        "RESEARCHIQ RAG GENERATOR"
    )

    print(
        "Live arXiv + TF-IDF + "
        "Cosine Similarity + Ollama"
    )

    print(
        "=" * 60
    )

    print(
        f"\nOllama model: {OLLAMA_MODEL}"
    )

    print(
        f"CSV file: {CSV_FILE}"
    )

    topic = input(
        "\nEnter a research topic: "
    ).strip()

    if not topic:

        print(
            "No topic entered."
        )

        exit()

    try:

        output = (
            generate_research_response(
                topic
            )
        )

        # ====================================================
        # GENERATED RESEARCH RESPONSE
        # ====================================================

        print("\n")

        print(
            "=" * 60
        )

        print(
            "GENERATED RESEARCH RESPONSE"
        )

        print(
            "=" * 60
        )

        print(
            output["result"]
        )

        # ====================================================
        # RETRIEVED PAPERS
        # ====================================================

        print("\n")

        print(
            "=" * 60
        )

        print(
            "RETRIEVED RESEARCH PAPERS"
        )

        print(
            "=" * 60
        )

        for i, document in enumerate(
            output[
                "retrieved_documents"
            ],
            start=1
        ):

            print(
                f"\n{i}. "
                f"[{document['source']}] "
                f"{document['title']}"
            )

            print(
                f"   Authors: "
                f"{document.get('authors', '')}"
            )

            print(
                f"   Category: "
                f"{document.get('category', '')}"
            )

            print(
                f"   Published: "
                f"{document.get('published_date', '')}"
            )

            print(
                f"   Similarity Score: "
                f"{document['similarity_score']}"
            )

            print(
                f"   View URL: "
                f"{document['url']}"
            )

            print(
                f"   PDF URL: "
                f"{document['pdf_url']}"
            )

        # ====================================================
        # CSV CONFIRMATION
        # ====================================================

        print("\n")

        print(
            "=" * 60
        )

        print(
            "CSV DATASET"
        )

        print(
            "=" * 60
        )

        print(
            f"Saved to:\n{CSV_FILE}"
        )

    except Exception as e:

        print(
            "\nERROR:"
        )

        print(
            str(e)
        )