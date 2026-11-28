"""
Kaggle Dataset Service - ResearchIQ

Responsibilities

----------------

1. Search Kaggle datasets using a free-form research query.

2. Support category, sorting and result-limit filters.

3. Calculate a simple query relevance score.

4. Return clean dataset metadata for the frontend.

5. Store returned Kaggle dataset metadata as structured CSV records.

6. Download selected Kaggle datasets.

7. Keep Kaggle credentials in .env.

8. Prepare clean data for future dataset fusion.

Architecture

------------

React Frontend

        ↓

Flask Route

        ↓

Kaggle Service

        ↓

Kaggle API

        ↓

Clean Dataset Records

        ↓

kaggle_dataset_records.csv
"""

import csv
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from dotenv import load_dotenv

try:
    from kaggle.api.kaggle_api_extended import KaggleApi
except ImportError:
    KaggleApi = None


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

# Kaggle package v2 uses KAGGLE_API_TOKEN
KAGGLE_API_TOKEN = os.getenv("KAGGLE_API_TOKEN")

BASE_DIR = Path(__file__).resolve().parent.parent

# Store persistent CSV files inside backend/datasets
# alongside the existing RAG dataset (database.csv).
DATA_DIR = BASE_DIR / "datasets"
DOWNLOAD_DIR = BASE_DIR / "data" / "kaggle_downloads"

DATASET_CSV_FILE = DATA_DIR / "kaggle_dataset_records.csv"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DOWNLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CSV COLUMNS
# ============================================================

# These are the selected Kaggle dataset attributes that are
# stored as actual CSV columns and populated with records.
#
# created_date has intentionally been removed.

DATASET_CSV_COLUMNS = [
    "query",
    "category",
    "sort_by",
    "limit",
    "title",
    "description",
    "owner",
    "dataset_id",
    "size",
    "file_count",
    "vote_count",
    "download_count",
    "usability",
    "updated_date",
    "url"
]


# ============================================================
# KAGGLE CLIENT
# ============================================================

_kaggle_api = None


def get_kaggle_api() -> KaggleApi:
    """
    Create and authenticate the Kaggle API client.

    Authentication uses KAGGLE_API_TOKEN from .env.
    """

    global _kaggle_api

    if _kaggle_api is not None:
        return _kaggle_api

    if KaggleApi is None:
        raise RuntimeError(
            "Kaggle package is not installed. "
            "Run: pip install kaggle"
        )

    # Check KAGGLE_API_TOKEN instead of KAGGLE_API_KEY
    if not KAGGLE_API_TOKEN:
        raise RuntimeError(
            "KAGGLE_API_TOKEN is missing from the .env file."
        )

    # Kaggle's current client reads this environment variable.
    os.environ["KAGGLE_API_TOKEN"] = KAGGLE_API_TOKEN

    api = KaggleApi()
    api.authenticate()

    _kaggle_api = api

    return api


# ============================================================
# UTILITY - SAFE VALUE
# ============================================================

def safe_value(
    value: Any,
    default: Any = ""
) -> Any:
    """
    Return a default value instead of None.
    """

    if value is None:
        return default

    return value


# ============================================================
# UTILITY - CLEAN TEXT
# ============================================================

def clean_text(
    value: Any
) -> str:
    """
    Convert any value into clean single-line text.
    """

    if value is None:
        return ""

    text = str(value)

    text = text.replace("\n", " ")
    text = text.replace("\r", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(
    text: Any
) -> str:
    """
    Normalize text for relevance calculation.
    """

    if text is None:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"[^a-zA-Z0-9\s\-]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(
    text: str
) -> Set[str]:
    """
    Convert text into meaningful search tokens.
    """

    normalized = normalize_text(text)

    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "using",
        "use",
        "data",
        "dataset",
        "datasets",
        "based",
        "model",
        "models",
        "of",
        "in",
        "on",
        "to",
        "a",
        "an",
        "is",
        "are",
        "this",
        "that",
        "by",
        "into",
        "about"
    }

    return {
        word
        for word in normalized.split()
        if len(word) > 2
        and word not in stop_words
    }


# ============================================================
# RELEVANCE SCORE
# ============================================================

def calculate_relevance_score(
    query: str,
    dataset_title: str,
    dataset_description: str = "",
    dataset_tags: Optional[List[str]] = None
) -> float:
    """
    Calculate a simple relevance score from 0-100.

    Weighting:
        Title       = 60%
        Tags        = 25%
        Description = 15%
    """

    query_words = tokenize(query)

    if not query_words:
        return 0.0

    title_words = tokenize(
        dataset_title
    )

    description_words = tokenize(
        dataset_description
    )

    tag_words: Set[str] = set()

    if dataset_tags:
        for tag in dataset_tags:
            tag_words.update(
                tokenize(tag)
            )

    title_matches = (
        query_words.intersection(
            title_words
        )
    )

    tag_matches = (
        query_words.intersection(
            tag_words
        )
    )

    description_matches = (
        query_words.intersection(
            description_words
        )
    )

    title_score = (
        len(title_matches)
        / len(query_words)
    ) * 60

    tag_score = (
        len(tag_matches)
        / len(query_words)
    ) * 25

    description_score = (
        len(description_matches)
        / len(query_words)
    ) * 15

    final_score = (
        title_score
        + tag_score
        + description_score
    )

    return round(
        min(final_score, 100.0),
        2
    )


# ============================================================
# RECORD ID
# ============================================================

def create_record_id(
    dataset_ref: str,
    search_query: str,
    position: int
) -> str:
    """
    Create a unique readable record ID.

    Used internally for processing purposes.

    It is NOT stored as a dataset CSV column.
    """

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%d%H%M%S%f"
    )

    safe_ref = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        dataset_ref
    ).strip("_")

    return (
        f"KAGGLE_"
        f"{timestamp}_"
        f"{position}_"
        f"{safe_ref}"
    )


# ============================================================
# CSV - ENSURE DATASET FILE
# ============================================================

def ensure_dataset_csv_exists() -> None:
    """
    Create the dataset CSV with the selected headers
    if it does not exist.

    The CSV is persistent inside the datasets folder.

    New searches append records to this same file.
    """

    if DATASET_CSV_FILE.exists():
        return

    with open(
        DATASET_CSV_FILE,
        mode="w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=DATASET_CSV_COLUMNS
        )

        writer.writeheader()


# ============================================================
# CSV - SAVE DATASET RECORD
# ============================================================

def save_dataset_record(
    record: Dict[str, Any]
) -> None:
    """
    Save one clean Kaggle dataset record.

    The record is APPENDED to the existing persistent
    kaggle_dataset_records.csv file.

    Only the selected dataset attributes are written.

    Lists are converted to:

        value1 | value2 | value3

    Missing/unavailable values are stored as blank.
    """

    ensure_dataset_csv_exists()

    clean_record: Dict[str, Any] = {}

    for column in DATASET_CSV_COLUMNS:

        value = record.get(
            column,
            ""
        )

        if isinstance(value, list):
            value = " | ".join(
                clean_text(item)
                for item in value
            )

        clean_record[column] = clean_text(
            value
        )

    # Append to the same CSV file.
    with open(
        DATASET_CSV_FILE,
        mode="a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=DATASET_CSV_COLUMNS
        )

        writer.writerow(
            clean_record
        )


# ============================================================
# DATASET ATTRIBUTE HELPER
# ============================================================

def get_first_attribute(
    obj: Any,
    attributes: List[str],
    default: Any = ""
) -> Any:
    """
    Return the first non-empty attribute from an object.
    """

    for attribute in attributes:

        try:
            value = getattr(
                obj,
                attribute,
                None
            )

        except Exception:
            value = None

        if value not in (
            None,
            ""
        ):
            return value

    return default


# ============================================================
# TAG CLEANING
# ============================================================

def clean_dataset_tags(
    tags: Any
) -> List[str]:
    """
    Normalize Kaggle tag objects into strings.

    Tags are still used internally for relevance scoring,
    but are not stored as CSV columns.
    """

    if tags is None:
        return []

    if not isinstance(tags, list):
        tags = [tags]

    cleaned_tags = []

    for tag in tags:

        if isinstance(tag, dict):

            tag_name = (
                tag.get("name")
                or tag.get("displayName")
                or tag.get("display_name")
                or ""
            )

            if tag_name:
                cleaned_tags.append(
                    clean_text(tag_name)
                )

        else:

            tag_text = clean_text(tag)

            if tag_text:
                cleaned_tags.append(
                    tag_text
                )

    return cleaned_tags


# ============================================================
# DATASET SERIALIZATION
# ============================================================

def dataset_to_dict(
    dataset: Any,
    query: str = ""
) -> Dict[str, Any]:
    """
    Convert a Kaggle Dataset object into
    frontend-friendly JSON metadata.

    Kaggle API versions can expose different
    attribute names, so multiple names are checked.
    """

    # --------------------------------------------------------
    # REFERENCE
    # --------------------------------------------------------

    dataset_ref = get_first_attribute(
        dataset,
        [
            "ref",
            "dataset_ref",
            "id"
        ],
        ""
    )

    dataset_ref = clean_text(
        dataset_ref
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = get_first_attribute(
        dataset,
        [
            "title",
            "name"
        ],
        ""
    )

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = get_first_attribute(
        dataset,
        [
            "description",
            "subtitle"
        ],
        ""
    )

    # --------------------------------------------------------
    # OWNER
    # --------------------------------------------------------

    owner = get_first_attribute(
        dataset,
        [
            "owner_name",
            "creator_name",
            "creatorName",
            "owner"
        ],
        ""
    )

    # --------------------------------------------------------
    # SIZE
    # --------------------------------------------------------

    size_bytes = get_first_attribute(
        dataset,
        [
            "total_bytes",
            "totalBytes",
            "size"
        ],
        ""
    )

    # --------------------------------------------------------
    # FILE COUNT
    # --------------------------------------------------------

    file_count = get_first_attribute(
        dataset,
        [
            "file_count",
            "fileCount"
        ],
        None
    )

    if file_count is None:

        files = getattr(
            dataset,
            "files",
            None
        )

        if isinstance(files, list):
            file_count = len(files)

        else:
            file_count = ""

    # --------------------------------------------------------
    # VOTES
    # --------------------------------------------------------

    vote_count = get_first_attribute(
        dataset,
        [
            "votes",
            "vote_count",
            "voteCount"
        ],
        ""
    )

    # --------------------------------------------------------
    # DOWNLOADS
    # --------------------------------------------------------

    download_count = get_first_attribute(
        dataset,
        [
            "download_count",
            "downloadCount"
        ],
        ""
    )

    # --------------------------------------------------------
    # VIEWS
    # --------------------------------------------------------

    # Kept internally for compatibility with the Kaggle
    # metadata response, but it is NOT saved to the dataset CSV.

    view_count = get_first_attribute(
        dataset,
        [
            "view_count",
            "viewCount"
        ],
        ""
    )

    # --------------------------------------------------------
    # USABILITY
    # --------------------------------------------------------

    usability = get_first_attribute(
        dataset,
        [
            "usability_rating",
            "usabilityRating",
            "usability"
        ],
        ""
    )

    # --------------------------------------------------------
    # TAGS
    # --------------------------------------------------------

    tags = get_first_attribute(
        dataset,
        [
            "tags"
        ],
        []
    )

    clean_tags = clean_dataset_tags(
        tags
    )

    # --------------------------------------------------------
    # UPDATED DATE
    # --------------------------------------------------------

    updated_date = get_first_attribute(
        dataset,
        [
            "last_updated",
            "lastUpdated",
            "updated"
        ],
        ""
    )

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    dataset_url = ""

    if dataset_ref:

        dataset_url = (
            "https://www.kaggle.com/datasets/"
            + dataset_ref
        )

    # --------------------------------------------------------
    # RELEVANCE
    # --------------------------------------------------------

    relevance_score = calculate_relevance_score(
        query=query,
        dataset_title=clean_text(title),
        dataset_description=clean_text(description),
        dataset_tags=clean_tags
    )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "dataset_id":
            dataset_ref,

        "dataset_ref":
            dataset_ref,

        "title":
            clean_text(title),

        "description":
            clean_text(description),

        "owner":
            clean_text(owner),

        "url":
            dataset_url,

        "size":
            clean_text(size_bytes),

        "size_bytes":
            size_bytes,

        "file_count":
            file_count,

        "vote_count":
            vote_count,

        "download_count":
            download_count,

        "view_count":
            view_count,

        "usability":
            usability,

        "usability_rating":
            usability,

        "tags":
            clean_tags,

        "updated_date":
            clean_text(updated_date),

        "last_updated":
            clean_text(updated_date),

        "relevance_score":
            relevance_score
    }


# ============================================================
# SEARCH DATASETS
# ============================================================

def search_datasets(
    query: str,
    category: str = "All",
    sort_by: str = "hottest",
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search Kaggle datasets.
    """

    query = (
        query or ""
    ).strip()

    category = (
        category or "All"
    ).strip()

    sort_by = (
        sort_by or "hottest"
    ).strip().lower()

    # --------------------------------------------------------
    # VALIDATE QUERY
    # --------------------------------------------------------

    if not query:
        raise ValueError(
            "Search query is required."
        )

    # --------------------------------------------------------
    # VALIDATE LIMIT
    # --------------------------------------------------------

    try:
        limit = int(limit)

    except (
        TypeError,
        ValueError
    ):
        limit = 10

    limit = max(
        1,
        min(limit, 100)
    )

    # --------------------------------------------------------
    # VALID SORT VALUES
    # --------------------------------------------------------

    allowed_sort_values = {
        "hottest": "hottest",
        "votes": "votes",
        "updated": "updated",
        "active": "active",
        "published": "published"
    }

    kaggle_sort = allowed_sort_values.get(
        sort_by,
        "hottest"
    )

    # --------------------------------------------------------
    # BUILD SEARCH QUERY
    # --------------------------------------------------------

    search_query = query

    if (
        category
        and category.lower() != "all"
    ):

        search_query = (
            f"{query} {category}"
        ).strip()

    try:

        # ----------------------------------------------------
        # GET KAGGLE CLIENT
        # ----------------------------------------------------

        api = get_kaggle_api()

        # ----------------------------------------------------
        # SEARCH KAGGLE
        # ----------------------------------------------------

        datasets = api.dataset_list(
            search=search_query,
            sort_by=kaggle_sort
        )

        # ----------------------------------------------------
        # SAFELY LIMIT RESULTS
        # ----------------------------------------------------

        datasets = list(
            datasets or []
        )

        datasets = datasets[:limit]

        results: List[Dict[str, Any]] = []

        # ----------------------------------------------------
        # SERIALIZE RESULTS
        # ----------------------------------------------------

        for position, dataset in enumerate(
            datasets,
            start=1
        ):

            dataset_data = dataset_to_dict(
                dataset,
                query=query
            )

            dataset_data[
                "search_query"
            ] = query

            dataset_data[
                "search_category"
            ] = category

            dataset_data[
                "sort_by"
            ] = sort_by

            dataset_data[
                "result_limit"
            ] = limit

            dataset_data[
                "result_position"
            ] = position

            results.append(
                dataset_data
            )

        # ----------------------------------------------------
        # SORT BY OUR RELEVANCE SCORE
        # ----------------------------------------------------

        results.sort(
            key=lambda item: item.get(
                "relevance_score",
                0
            ),
            reverse=True
        )

        # ----------------------------------------------------
        # REASSIGN RESULT POSITION
        # AFTER RELEVANCE SORTING
        # ----------------------------------------------------

        for position, result in enumerate(
            results,
            start=1
        ):

            result[
                "result_position"
            ] = position

        # ----------------------------------------------------
        # SAVE DATASET RECORDS
        # ----------------------------------------------------

        for position, result in enumerate(
            results,
            start=1
        ):

            record_id = create_record_id(
                dataset_ref=result.get(
                    "dataset_ref",
                    ""
                ),
                search_query=query,
                position=position
            )

            # ------------------------------------------------
            # CLEAN DATASET CSV RECORD
            # ------------------------------------------------
            #
            # Only the selected attributes are saved.
            #
            # query
            # category
            # sort_by
            # limit
            # title
            # description
            # owner
            # dataset_id
            # size
            # file_count
            # vote_count
            # download_count
            # usability
            # updated_date
            # url
            #
            # created_date has intentionally been removed.
            #
            # record_id, tags, view_count, relevance_score,
            # dataset_ref, etc. are NOT stored as CSV columns.
            # ------------------------------------------------

            dataset_record = {

                "query":
                    query,

                "category":
                    category,

                "sort_by":
                    sort_by,

                "limit":
                    limit,

                "title":
                    result.get(
                        "title",
                        ""
                    ),

                "description":
                    result.get(
                        "description",
                        ""
                    ),

                "owner":
                    result.get(
                        "owner",
                        ""
                    ),

                "dataset_id":
                    result.get(
                        "dataset_id",
                        ""
                    ),

                "size":
                    result.get(
                        "size",
                        ""
                    ),

                "file_count":
                    result.get(
                        "file_count",
                        ""
                    ),

                "vote_count":
                    result.get(
                        "vote_count",
                        ""
                    ),

                "download_count":
                    result.get(
                        "download_count",
                        ""
                    ),

                "usability":
                    result.get(
                        "usability",
                        ""
                    ),

                "updated_date":
                    result.get(
                        "updated_date",
                        ""
                    ),

                "url":
                    result.get(
                        "url",
                        ""
                    )
            }

            # This appends the record to the SAME
            # persistent CSV in backend/datasets/.

            save_dataset_record(
                dataset_record
            )

        # ----------------------------------------------------
        # RETURN FRONTEND RESPONSE
        # ----------------------------------------------------

        return {
            "success":
                True,

            "query":
                query,

            "category":
                category,

            "sort_by":
                sort_by,

            "limit":
                limit,

            "count":
                len(results),

            "datasets":
                results
        }

    except Exception as exc:

        raise RuntimeError(
            "Kaggle dataset search failed: "
            f"{exc}"
        ) from exc


# ============================================================
# GET DATASET DETAILS
# ============================================================

def get_dataset_details(
    dataset_ref: str
) -> Dict[str, Any]:
    """
    Retrieve detailed information about
    one Kaggle dataset.
    """

    dataset_ref = (
        dataset_ref or ""
    ).strip()

    if not dataset_ref:
        raise ValueError(
            "dataset_ref is required."
        )

    try:

        api = get_kaggle_api()

        dataset = api.dataset_view(
            dataset_ref
        )

        result = dataset_to_dict(
            dataset
        )

        return result

    except Exception as exc:

        raise RuntimeError(
            "Could not retrieve Kaggle "
            f"dataset details: {exc}"
        ) from exc


# ============================================================
# DOWNLOAD DATASET
# ============================================================

def download_dataset(
    dataset_ref: str,
    extract: bool = True
) -> Dict[str, Any]:
    """
    Download a selected Kaggle dataset.

    Downloads are stored inside:

        backend/data/kaggle_downloads/
    """

    dataset_ref = (
        dataset_ref or ""
    ).strip()

    if not dataset_ref:
        raise ValueError(
            "dataset_ref is required."
        )

    # --------------------------------------------------------
    # SAFE DIRECTORY NAME
    # --------------------------------------------------------

    safe_name = re.sub(
        r"[^a-zA-Z0-9_\-]+",
        "_",
        dataset_ref
    ).strip("_")

    dataset_folder = (
        DOWNLOAD_DIR / safe_name
    )

    dataset_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    dataset_url = (
        "https://www.kaggle.com/datasets/"
        + dataset_ref
    )

    try:

        api = get_kaggle_api()

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        api.dataset_download_files(
            dataset_ref,
            path=str(dataset_folder),
            unzip=extract
        )

        # ----------------------------------------------------
        # COLLECT DOWNLOADED FILES
        # ----------------------------------------------------

        files: List[str] = []

        for file_path in dataset_folder.rglob("*"):

            if file_path.is_file():

                files.append(
                    str(
                        file_path.relative_to(
                            BASE_DIR
                        )
                    )
                )

        relative_download_path = str(
            dataset_folder.relative_to(
                BASE_DIR
            )
        )

        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return {
            "success":
                True,

            "dataset_ref":
                dataset_ref,

            "dataset_url":
                dataset_url,

            "download_directory":
                relative_download_path,

            "files":
                files,

            "file_count":
                len(files)
        }

    except Exception as exc:

        raise RuntimeError(
            "Kaggle dataset download failed: "
            f"{exc}"
        ) from exc


# ============================================================
# CSV LOCATION
# ============================================================

def get_dataset_csv_path() -> str:
    """
    Return the dataset CSV path
    relative to the backend directory.
    """

    ensure_dataset_csv_exists()

    return str(
        DATASET_CSV_FILE.relative_to(
            BASE_DIR
        )
    )


# ============================================================
# SERVICE HEALTH CHECK
# ============================================================

def test_kaggle_connection() -> Dict[str, Any]:
    """
    Test Kaggle API authentication and connectivity.
    """

    try:

        api = get_kaggle_api()

        datasets = api.dataset_list(
            search="machine learning"
        )

        return {
            "success":
                True,

            "message":
                "Kaggle API connection successful.",

            "sample_results":
                len(datasets),

            "dataset_csv":
                get_dataset_csv_path()
        }

    except Exception as exc:

        return {
            "success":
                False,

            "message":
                "Kaggle API connection failed.",

            "error":
                str(exc)
        }


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "ResearchIQ - Kaggle Service Test"
    )

    print("=" * 60)

    result = test_kaggle_connection()

    print(result)

    print()

    print(
        "Dataset CSV:",
        get_dataset_csv_path()
    )