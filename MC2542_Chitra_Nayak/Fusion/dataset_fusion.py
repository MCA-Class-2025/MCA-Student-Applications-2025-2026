from pathlib import Path
import pandas as pd
import re
import hashlib


# ============================================================
# PATHS
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BACKEND_DIR / "datasets"

# IMPORTANT:
# This is the ONLY output file created by this fusion script.
# dataset_fusion.csv is NEVER used as a source.
OUTPUT_FILE = DATASET_DIR / "dataset_fusion.csv"


# ============================================================
# SOURCE CSV FILES
# ============================================================

SOURCE_FILES = {
    "database": DATASET_DIR / "database.csv",
    "kaggle": DATASET_DIR / "kaggle_dataset_records.csv",
    "citations": DATASET_DIR / "opencitations_data.csv",
    "generation": DATASET_DIR / "research_paper_generation.csv",
    "advisor": DATASET_DIR / "research_project_advisor.csv",
    "research": DATASET_DIR / "research_results.csv",
}


# ============================================================
# FINAL CANONICAL DATASET COLUMNS
# ============================================================

CANONICAL_COLUMNS = [
    "Id",
    "title",
    "link",
    "year",
    "authors",
    "citations",
    "abstract",
    "doi",
    "eid",
    "source",
    "topic",
    "category",
    "publication_name",
    "document_type",
    "dataset_id",
    "dataset_title",
    "dataset_description",
    "dataset_url",
    "pdf_url",
    "pdf_path",
]


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(value):
    """
    Clean a single value.
    """

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    value = str(value)

    # Remove excessive whitespace
    value = re.sub(r"\s+", " ", value)

    return value.strip()


# ============================================================
# NORMALIZE TITLE
# ============================================================

def normalize_title(value):
    """
    Create a normalized title used to match
    records across different datasets.
    """

    value = clean_text(value).lower()

    # Remove punctuation
    value = re.sub(r"[^a-z0-9\s]", "", value)

    # Normalize spaces
    value = re.sub(r"\s+", " ", value)

    return value.strip()


# ============================================================
# CLEAN IDENTIFIERS
# ============================================================

def clean_identifier(value):
    """
    Clean DOI/EID identifiers.
    """

    value = clean_text(value).lower()

    if not value:
        return ""

    value = value.strip()

    # Remove common DOI prefixes
    value = value.replace(
        "https://doi.org/",
        ""
    )

    value = value.replace(
        "http://doi.org/",
        ""
    )

    value = value.replace(
        "doi:",
        ""
    )

    return value.strip()


# ============================================================
# DATAFRAME CLEANING
# ============================================================

def clean_dataframe(df):
    """
    Clean column names and string values.
    """

    # Clean column names
    df.columns = [
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        for column in df.columns
    ]

    # Clean object/string columns
    for column in df.columns:

        if df[column].dtype == "object":

            df[column] = df[column].apply(
                clean_text
            )

    return df


# ============================================================
# LOAD SOURCE DATASETS
# ============================================================

def load_sources():
    """
    Load ALL six source CSV files every time
    the fusion script runs.

    dataset_fusion.csv is intentionally NOT loaded.
    """

    datasets = {}

    print("\n" + "=" * 80)
    print("LOADING SOURCE DATASETS")
    print("=" * 80)

    for name, path in SOURCE_FILES.items():

        if not path.exists():

            print(
                f"\nWARNING: {path.name} not found."
            )

            continue

        try:

            df = pd.read_csv(
                path,
                low_memory=False
            )

            df = clean_dataframe(df)

            datasets[name] = df

            print(
                f"\n{name.upper():12} "
                f"{path.name:40} "
                f"Rows: {len(df):6}"
            )

            print(
                f"{'':12} "
                f"Columns: {len(df.columns):5}"
            )

        except Exception as error:

            print(
                f"\nERROR loading {path.name}: {error}"
            )

    return datasets


# ============================================================
# FIND FIRST NON-EMPTY VALUE
# ============================================================

def first_value(*values):
    """
    Return the first meaningful non-empty value.
    """

    for value in values:

        value = clean_text(value)

        if value:
            return value

    return ""


# ============================================================
# FIND ALL NON-EMPTY VALUES
# ============================================================

def combine_values(*values):
    """
    Combine multiple non-empty values without duplicates.
    """

    results = []

    for value in values:

        value = clean_text(value)

        if not value:
            continue

        if value not in results:
            results.append(value)

    return " | ".join(results)


# ============================================================
# CREATE CANONICAL PAPER ID
# ============================================================

def create_paper_id(
    doi="",
    eid="",
    title=""
):
    """
    Create a stable canonical identifier.

    Priority:
        1. DOI
        2. EID
        3. Normalized title
    """

    doi = clean_identifier(doi)
    eid = clean_identifier(eid)
    title_key = normalize_title(title)

    if doi:

        raw_key = "doi:" + doi

    elif eid:

        raw_key = "eid:" + eid

    elif title_key:

        raw_key = "title:" + title_key

    else:

        return ""

    digest = hashlib.sha256(
        raw_key.encode("utf-8")
    ).hexdigest()[:16]

    return "P" + digest


# ============================================================
# CREATE KAGGLE DATASET ID
# ============================================================

def create_dataset_id(
    dataset_id="",
    title=""
):
    """
    Create a stable identifier for a dataset.
    """

    dataset_id = clean_text(
        dataset_id
    )

    title_key = normalize_title(
        title
    )

    raw_key = (
        dataset_id
        if dataset_id
        else title_key
    )

    if not raw_key:
        return ""

    digest = hashlib.sha256(
        raw_key.encode("utf-8")
    ).hexdigest()[:16]

    return "D" + digest


# ============================================================
# PARSE YEAR
# ============================================================

def extract_year(value):
    """
    Extract a four-digit publication year.
    """

    value = clean_text(value)

    if not value:
        return ""

    match = re.search(
        r"\b(19|20)\d{2}\b",
        value
    )

    if match:
        return match.group(0)

    return ""


# ============================================================
# CREATE EMPTY RECORD
# ============================================================

def empty_record():
    """
    Create a record containing the canonical schema.
    """

    return {
        column: ""
        for column in CANONICAL_COLUMNS
    }


# ============================================================
# GET VALUE FROM POSSIBLE COLUMN NAMES
# ============================================================

def get_row_value(row, *column_names):
    """
    Retrieve the first non-empty value from several
    possible column names.
    """

    for column_name in column_names:

        value = row.get(
            column_name,
            ""
        )

        value = clean_text(value)

        if value:
            return value

    return ""


# ============================================================
# ADD ALL SOURCE-SPECIFIC COLUMNS
# ============================================================

def add_source_columns(
    record,
    row,
    excluded_columns=None
):
    """
    Preserve every original column from the source row.

    Canonical columns are handled separately.
    Every other source-specific column is retained.
    """

    if excluded_columns is None:
        excluded_columns = set()

    for column in row.index:

        if column in CANONICAL_COLUMNS:
            continue

        if column in excluded_columns:
            continue

        value = clean_text(
            row.get(
                column,
                ""
            )
        )

        if value:
            record[column] = value
        elif column not in record:
            record[column] = ""

    return record


# ============================================================
# FIND MATCHING RECORD
# ============================================================

def find_matching_record(
    records,
    doi="",
    eid="",
    title=""
):
    """
    Find an existing record using:

        1. DOI
        2. EID
        3. Normalized title
    """

    doi = clean_identifier(
        doi
    )

    eid = clean_identifier(
        eid
    )

    title_key = normalize_title(
        title
    )

    for record_id, record in records.items():

        existing_doi = clean_identifier(
            record.get(
                "doi",
                ""
            )
        )

        existing_eid = clean_identifier(
            record.get(
                "eid",
                ""
            )
        )

        existing_title = normalize_title(
            record.get(
                "title",
                ""
            )
        )

        if doi and existing_doi:

            if doi == existing_doi:
                return record_id

        if eid and existing_eid:

            if eid == existing_eid:
                return record_id

        if title_key and existing_title:

            if title_key == existing_title:
                return record_id

    return None


# ============================================================
# MERGE RECORDS
# ============================================================

def merge_record(
    records,
    record
):
    """
    Add a record to the fused dataset.

    If a matching record already exists, merge information
    from the new source into it.

    Source-specific columns are preserved as well.
    """

    paper_id = record.get(
        "Id",
        ""
    )

    if not paper_id:
        return

    existing_id = find_matching_record(
        records,
        doi=record.get(
            "doi",
            ""
        ),
        eid=record.get(
            "eid",
            ""
        ),
        title=record.get(
            "title",
            ""
        )
    )

    if existing_id is None:

        records[paper_id] = record

        return

    existing = records[
        existing_id
    ]

    # --------------------------------------------------------
    # Merge every field from the new source
    # --------------------------------------------------------

    for column, new_value in record.items():

        old_value = clean_text(
            existing.get(
                column,
                ""
            )
        )

        new_value = clean_text(
            new_value
        )

        # Fill missing information
        if not old_value and new_value:

            existing[column] = new_value

        # Preserve legitimate multiple values
        elif old_value and new_value:

            if column in [
                "authors",
                "citations",
                "source",
                "topic",
                "category",
                "publication_name",
                "document_type",
                "link",
                "pdf_url",
                "pdf_path"
            ]:

                existing[column] = combine_values(
                    old_value,
                    new_value
                )


# ============================================================
# PROCESS EXISTING DATABASE.CSV
# ============================================================

def process_database(
    df,
    records
):
    """
    Process the existing database.csv.

    Every usable database.csv record is retained.
    """

    if df is None:
        return

    print(
        "\nProcessing pre-existing database.csv..."
    )

    processed = 0

    for _, row in df.iterrows():

        title = get_row_value(
            row,
            "title",
            "paper_title",
            "name",
            "dataset_title"
        )

        dataset_id = get_row_value(
            row,
            "dataset_id",
            "id",
            "datasetid",
            "dataset_key"
        )

        doi = clean_identifier(
            get_row_value(
                row,
                "doi",
                "DOI"
            )
        )

        eid = clean_identifier(
            get_row_value(
                row,
                "eid",
                "EID",
                "scopus_eid"
            )
        )

        link = get_row_value(
            row,
            "link",
            "url",
            "paper_url",
            "source_url"
        )

        year = extract_year(
            get_row_value(
                row,
                "year",
                "publication_year",
                "published_year",
                "publication_date",
                "published_date"
            )
        )

        authors = get_row_value(
            row,
            "authors",
            "author",
            "author_names",
            "creator"
        )

        citations = get_row_value(
            row,
            "citations",
            "citation_count",
            "cited_by_count",
            "citation",
            "citations_count"
        )

        abstract = get_row_value(
            row,
            "abstract",
            "description",
            "summary",
            "text",
            "content"
        )

        source = get_row_value(
            row,
            "source",
            "provider",
            "database"
        )

        topic = get_row_value(
            row,
            "topic",
            "query",
            "research_topic",
            "subject"
        )

        category = get_row_value(
            row,
            "category",
            "field",
            "domain",
            "research_field"
        )

        publication_name = get_row_value(
            row,
            "publication_name",
            "journal",
            "journal_name",
            "venue",
            "publication"
        )

        document_type = get_row_value(
            row,
            "document_type",
            "type",
            "publication_type"
        )

        dataset_title = get_row_value(
            row,
            "dataset_title",
            "title"
        )

        dataset_description = get_row_value(
            row,
            "dataset_description",
            "description",
            "abstract"
        )

        dataset_url = get_row_value(
            row,
            "dataset_url",
            "url",
            "link"
        )

        pdf_url = get_row_value(
            row,
            "pdf_url",
            "pdf_link",
            "full_text_url"
        )

        pdf_path = get_row_value(
            row,
            "pdf_path",
            "filename",
            "file_path",
            "filepath"
        )

        # Skip completely unusable rows
        if (
            not title
            and not dataset_id
            and not doi
            and not eid
        ):
            continue

        looks_like_dataset = bool(
            dataset_id
            or dataset_title
            or dataset_description
        )

        if looks_like_dataset:

            record_id = create_dataset_id(
                dataset_id=dataset_id,
                title=title
            )

        else:

            record_id = create_paper_id(
                doi=doi,
                eid=eid,
                title=title
            )

        if not record_id:
            continue

        record = empty_record()

        record.update({

            "Id": record_id,

            "title": title,

            "link": link,

            "year": year,

            "authors": authors,

            "citations": citations,

            "abstract": abstract,

            "doi": doi,

            "eid": eid,

            "source": first_value(
                source,
                "database"
            ),

            "topic": topic,

            "category": category,

            "publication_name": first_value(
                publication_name,
                "Kaggle"
                if looks_like_dataset
                else ""
            ),

            "document_type": first_value(
                document_type,
                "dataset"
                if looks_like_dataset
                else ""
            ),

            "dataset_id": dataset_id,

            "dataset_title": dataset_title,

            "dataset_description": dataset_description,

            "dataset_url": dataset_url,

            "pdf_url": pdf_url,

            "pdf_path": pdf_path,
        })

        # Preserve all other database.csv columns
        record = add_source_columns(
            record,
            row
        )

        merge_record(
            records,
            record
        )

        processed += 1

    print(
        f"database.csv records processed: {processed}"
    )


# ============================================================
# PROCESS RESEARCH RESULTS
# ============================================================

def process_research_results(
    df,
    records
):

    if df is None:
        return

    for _, row in df.iterrows():

        title = first_value(
            row.get(
                "title",
                ""
            )
        )

        if not title:
            continue

        authors = first_value(
            row.get(
                "authors",
                ""
            )
        )

        abstract = first_value(
            row.get(
                "text",
                ""
            ),
            row.get(
                "result",
                ""
            ),
            row.get(
                "abstract",
                ""
            )
        )

        link = first_value(
            row.get(
                "url",
                ""
            ),
            row.get(
                "pdf_url",
                ""
            )
        )

        year = extract_year(
            first_value(
                row.get(
                    "published_date",
                    ""
                ),
                row.get(
                    "publication_date",
                    ""
                )
            )
        )

        source = first_value(
            row.get(
                "source",
                ""
            ),
            "research_results"
        )

        topic = first_value(
            row.get(
                "topic",
                ""
            )
        )

        category = first_value(
            row.get(
                "category",
                ""
            )
        )

        pdf_url = clean_text(
            row.get(
                "pdf_url",
                ""
            )
        )

        doi = clean_identifier(
            row.get(
                "doi",
                ""
            )
        )

        eid = clean_identifier(
            row.get(
                "eid",
                ""
            )
        )

        paper_id = create_paper_id(
            doi=doi,
            eid=eid,
            title=title
        )

        record = empty_record()

        record.update({

            "Id": paper_id,

            "title": title,

            "link": link,

            "year": year,

            "authors": authors,

            "citations": first_value(
                row.get(
                    "citations",
                    ""
                ),
                row.get(
                    "citation_count",
                    ""
                )
            ),

            "abstract": abstract,

            "doi": doi,

            "eid": eid,

            "source": source,

            "topic": topic,

            "category": category,

            "publication_name": first_value(
                row.get(
                    "publication_name",
                    ""
                ),
                row.get(
                    "journal",
                    ""
                )
            ),

            "document_type": first_value(
                row.get(
                    "document_type",
                    ""
                ),
                row.get(
                    "type",
                    ""
                )
            ),

            "dataset_id": "",

            "dataset_title": "",

            "dataset_description": "",

            "dataset_url": "",

            "pdf_url": pdf_url,

            "pdf_path": clean_text(
                row.get(
                    "pdf_path",
                    ""
                )
            ),
        })

        record = add_source_columns(
            record,
            row
        )

        merge_record(
            records,
            record
        )


# ============================================================
# PROCESS RESEARCH ADVISOR
# ============================================================

def process_advisor(
    df,
    records
):

    if df is None:
        return

    for _, row in df.iterrows():

        title = first_value(
            row.get(
                "title",
                ""
            )
        )

        if not title:
            continue

        doi = clean_identifier(
            row.get(
                "doi",
                ""
            )
        )

        eid = clean_identifier(
            row.get(
                "eid",
                ""
            )
        )

        authors = first_value(
            row.get(
                "authors",
                ""
            )
        )

        abstract = first_value(
            row.get(
                "abstract",
                ""
            ),
            row.get(
                "description",
                ""
            )
        )

        year = extract_year(
            first_value(
                row.get(
                    "publication_date",
                    ""
                ),
                row.get(
                    "year",
                    ""
                )
            )
        )

        paper_id = create_paper_id(
            doi=doi,
            eid=eid,
            title=title
        )

        record = empty_record()

        record.update({

            "Id": paper_id,

            "title": title,

            "link": first_value(
                row.get(
                    "url",
                    ""
                ),
                row.get(
                    "link",
                    ""
                )
            ),

            "year": year,

            "authors": authors,

            "citations": clean_text(
                row.get(
                    "cited_by_count",
                    ""
                )
            ),

            "abstract": abstract,

            "doi": doi,

            "eid": eid,

            "source": first_value(
                row.get(
                    "source",
                    ""
                ),
                "research_project_advisor"
            ),

            "topic": first_value(
                row.get(
                    "query",
                    ""
                ),
                row.get(
                    "research_field",
                    ""
                )
            ),

            "category": first_value(
                row.get(
                    "domain",
                    ""
                ),
                row.get(
                    "research_field",
                    ""
                )
            ),

            "publication_name": clean_text(
                row.get(
                    "publication_name",
                    ""
                )
            ),

            "document_type": clean_text(
                row.get(
                    "document_type",
                    ""
                )
            ),

            "dataset_id": "",

            "dataset_title": "",

            "dataset_description": "",

            "dataset_url": "",

            "pdf_url": first_value(
                row.get(
                    "pdf_url",
                    ""
                ),
                row.get(
                    "url",
                    ""
                )
            ),

            "pdf_path": "",
        })

        record = add_source_columns(
            record,
            row
        )

        merge_record(
            records,
            record
        )


# ============================================================
# PROCESS OPEN CITATIONS
# ============================================================

def process_citations(
    df,
    records
):

    if df is None:
        return

    for _, row in df.iterrows():

        title = first_value(
            row.get(
                "paper_title",
                ""
            ),
            row.get(
                "title",
                ""
            )
        )

        if not title:
            continue

        abstract = first_value(
            row.get(
                "abstract",
                ""
            ),
            row.get(
                "extracted_text",
                ""
            )
        )

        source = first_value(
            row.get(
                "source",
                ""
            ),
            "opencitations"
        )

        doi = clean_identifier(
            row.get(
                "doi",
                ""
            )
        )

        eid = clean_identifier(
            row.get(
                "eid",
                ""
            )
        )

        paper_id = create_paper_id(
            doi=doi,
            eid=eid,
            title=title
        )

        record = empty_record()

        record.update({

            "Id": paper_id,

            "title": title,

            "link": first_value(
                row.get(
                    "url",
                    ""
                ),
                row.get(
                    "link",
                    ""
                )
            ),

            "year": extract_year(
                first_value(
                    row.get(
                        "timestamp",
                        ""
                    ),
                    row.get(
                        "year",
                        ""
                    )
                )
            ),

            "authors": first_value(
                row.get(
                    "authors",
                    ""
                ),
                row.get(
                    "author",
                    ""
                )
            ),

            "citations": first_value(
                row.get(
                    "citations",
                    ""
                ),
                row.get(
                    "citation_count",
                    ""
                )
            ),

            "abstract": abstract,

            "doi": doi,

            "eid": eid,

            "source": source,

            "topic": first_value(
                row.get(
                    "user_question",
                    ""
                ),
                row.get(
                    "topic",
                    ""
                )
            ),

            "category": clean_text(
                row.get(
                    "category",
                    ""
                )
            ),

            "publication_name": first_value(
                row.get(
                    "publication_name",
                    ""
                ),
                row.get(
                    "journal",
                    ""
                )
            ),

            "document_type": clean_text(
                row.get(
                    "document_type",
                    ""
                )
            ),

            "dataset_id": "",

            "dataset_title": "",

            "dataset_description": "",

            "dataset_url": "",

            "pdf_url": clean_text(
                row.get(
                    "pdf_url",
                    ""
                )
            ),

            "pdf_path": clean_text(
                row.get(
                    "filename",
                    ""
                )
            ),
        })

        record = add_source_columns(
            record,
            row
        )

        merge_record(
            records,
            record
        )


# ============================================================
# PROCESS PAPER GENERATION
# ============================================================

def process_generation(
    df,
    records
):

    if df is None:
        return

    for _, row in df.iterrows():

        title = first_value(
            row.get(
                "title",
                ""
            )
        )

        if not title:
            continue

        doi = clean_identifier(
            row.get(
                "doi",
                ""
            )
        )

        eid = clean_identifier(
            row.get(
                "eid",
                ""
            )
        )

        paper_id = create_paper_id(
            doi=doi,
            eid=eid,
            title=title
        )

        record = empty_record()

        record.update({

            "Id": paper_id,

            "title": title,

            "link": first_value(
                row.get(
                    "link",
                    ""
                ),
                row.get(
                    "url",
                    ""
                ),
                row.get(
                    "pdf_url",
                    ""
                )
            ),

            "year": extract_year(
                row.get(
                    "timestamp",
                    ""
                )
            ),

            "authors": first_value(
                row.get(
                    "authors",
                    ""
                )
            ),

            "citations": first_value(
                row.get(
                    "citations",
                    ""
                )
            ),

            "abstract": first_value(
                row.get(
                    "abstract",
                    ""
                ),
                row.get(
                    "summary",
                    ""
                )
            ),

            "doi": doi,

            "eid": eid,

            "source": first_value(
                row.get(
                    "source",
                    ""
                ),
                "research_paper_generation"
            ),

            "topic": first_value(
                row.get(
                    "topic",
                    ""
                ),
                row.get(
                    "core_search_query",
                    ""
                )
            ),

            "category": first_value(
                row.get(
                    "category",
                    ""
                )
            ),

            "publication_name": first_value(
                row.get(
                    "publication_name",
                    ""
                )
            ),

            "document_type": first_value(
                row.get(
                    "document_type",
                    ""
                ),
                "generated_paper"
            ),

            "dataset_id": "",

            "dataset_title": "",

            "dataset_description": "",

            "dataset_url": "",

            "pdf_url": clean_text(
                row.get(
                    "pdf_url",
                    ""
                )
            ),

            "pdf_path": clean_text(
                row.get(
                    "pdf_path",
                    ""
                )
            ),
        })

        record = add_source_columns(
            record,
            row
        )

        merge_record(
            records,
            record
        )


# ============================================================
# PROCESS KAGGLE DATASETS
# ============================================================

def process_kaggle(
    df,
    records
):

    if df is None:
        return

    for _, row in df.iterrows():

        dataset_id = clean_text(
            row.get(
                "dataset_id",
                ""
            )
        )

        title = first_value(
            row.get(
                "title",
                ""
            ),
            row.get(
                "dataset_title",
                ""
            )
        )

        if not title and not dataset_id:
            continue

        record_id = create_dataset_id(
            dataset_id=dataset_id,
            title=title
        )

        description = clean_text(
            row.get(
                "description",
                ""
            )
        )

        dataset_url = first_value(
            row.get(
                "url",
                ""
            ),
            row.get(
                "dataset_url",
                ""
            )
        )

        record = empty_record()

        record.update({

            "Id": record_id,

            "title": title,

            "link": dataset_url,

            "year": extract_year(
                row.get(
                    "updated_date",
                    ""
                )
            ),

            "authors": clean_text(
                row.get(
                    "owner",
                    ""
                )
            ),

            "citations": clean_text(
                row.get(
                    "vote_count",
                    ""
                )
            ),

            "abstract": description,

            "doi": "",

            "eid": "",

            "source": "kaggle",

            "topic": clean_text(
                row.get(
                    "query",
                    ""
                )
            ),

            "category": clean_text(
                row.get(
                    "category",
                    ""
                )
            ),

            "publication_name": "Kaggle",

            "document_type": "dataset",

            "dataset_id": dataset_id,

            "dataset_title": title,

            "dataset_description": description,

            "dataset_url": dataset_url,

            "pdf_url": clean_text(
                row.get(
                    "pdf_url",
                    ""
                )
            ),

            "pdf_path": clean_text(
                row.get(
                    "pdf_path",
                    ""
                )
            ),
        })

        record = add_source_columns(
            record,
            row
        )

        merge_record(
            records,
            record
        )


# ============================================================
# DATASET FUSION
# ============================================================

def fuse_datasets(
    datasets
):

    print("\n" + "=" * 80)
    print("STARTING DATASET FUSION")
    print("=" * 80)

    records = {}

    # --------------------------------------------------------
    # PRE-EXISTING DATABASE
    # --------------------------------------------------------

    process_database(
        datasets.get("database"),
        records
    )

    # --------------------------------------------------------
    # Research results
    # --------------------------------------------------------

    process_research_results(
        datasets.get("research"),
        records
    )

    # --------------------------------------------------------
    # Research advisor
    # --------------------------------------------------------

    process_advisor(
        datasets.get("advisor"),
        records
    )

    # --------------------------------------------------------
    # OpenCitations
    # --------------------------------------------------------

    process_citations(
        datasets.get("citations"),
        records
    )

    # --------------------------------------------------------
    # Generated papers
    # --------------------------------------------------------

    process_generation(
        datasets.get("generation"),
        records
    )

    # --------------------------------------------------------
    # Kaggle API dataset records
    # --------------------------------------------------------

    process_kaggle(
        datasets.get("kaggle"),
        records
    )

    return records


# ============================================================
# CROSS-SOURCE DATA COMPLETION
# ============================================================

def complete_missing_information(
    df
):
    """
    Fill fields using equivalent information already
    present somewhere in the fused dataset.

    This does NOT invent data.
    """

    # --------------------------------------------------------
    # Clean all values first
    # --------------------------------------------------------

    for column in df.columns:

        if df[column].dtype == "object":

            df[column] = df[column].apply(
                clean_text
            )

    # --------------------------------------------------------
    # Create lookup tables
    # --------------------------------------------------------

    title_lookup = {}
    doi_lookup = {}
    eid_lookup = {}

    for _, row in df.iterrows():

        title_key = normalize_title(
            row.get(
                "title",
                ""
            )
        )

        doi_key = clean_identifier(
            row.get(
                "doi",
                ""
            )
        )

        eid_key = clean_identifier(
            row.get(
                "eid",
                ""
            )
        )

        if title_key:

            if title_key not in title_lookup:

                title_lookup[
                    title_key
                ] = row.to_dict()

        if doi_key:

            if doi_key not in doi_lookup:

                doi_lookup[
                    doi_key
                ] = row.to_dict()

        if eid_key:

            if eid_key not in eid_lookup:

                eid_lookup[
                    eid_key
                ] = row.to_dict()

    # --------------------------------------------------------
    # Complete records using matching records
    # --------------------------------------------------------

    for index in df.index:

        title_key = normalize_title(
            df.at[
                index,
                "title"
            ]
        )

        doi_key = clean_identifier(
            df.at[
                index,
                "doi"
            ]
        )

        eid_key = clean_identifier(
            df.at[
                index,
                "eid"
            ]
        )

        matching_records = []

        if (
            doi_key
            and doi_key in doi_lookup
        ):

            matching_records.append(
                doi_lookup[doi_key]
            )

        if (
            eid_key
            and eid_key in eid_lookup
        ):

            matching_records.append(
                eid_lookup[eid_key]
            )

        if (
            title_key
            and title_key in title_lookup
        ):

            matching_records.append(
                title_lookup[title_key]
            )

        # ----------------------------------------------------
        # Fill ALL missing fields
        # ----------------------------------------------------

        for column in df.columns:

            current_value = clean_text(
                df.at[
                    index,
                    column
                ]
            )

            if current_value:
                continue

            for matching_record in matching_records:

                candidate = clean_text(
                    matching_record.get(
                        column,
                        ""
                    )
                )

                if candidate:

                    df.at[
                        index,
                        column
                    ] = candidate

                    break

    return df


# ============================================================
# REMOVE RECORDS WITH NO USEFUL INFORMATION
# ============================================================

def remove_unusable_records(
    df
):
    """
    Remove records that contain no meaningful paper/dataset
    identity.

    Records are retained when they have at least one of:
        title
        dataset_id
        DOI
        EID
    """

    if df.empty:
        return df

    usable_mask = (
        df["title"]
        .astype(str)
        .str.strip()
        .ne("")
        |
        df["dataset_id"]
        .astype(str)
        .str.strip()
        .ne("")
        |
        df["doi"]
        .astype(str)
        .str.strip()
        .ne("")
        |
        df["eid"]
        .astype(str)
        .str.strip()
        .ne("")
    )

    before_count = len(df)

    df = df[
        usable_mask
    ].copy()

    removed_count = (
        before_count
        - len(df)
    )

    print(
        f"\nUnusable records removed: "
        f"{removed_count}"
    )

    return df


# ============================================================
# FINAL CLEANING
# ============================================================

def clean_final_dataframe(
    df
):

    # --------------------------------------------------------
    # Make sure all canonical columns exist
    # --------------------------------------------------------

    for column in CANONICAL_COLUMNS:

        if column not in df.columns:

            df[column] = ""

    # --------------------------------------------------------
    # Put canonical columns first
    # --------------------------------------------------------

    additional_columns = [
        column
        for column in df.columns
        if column not in CANONICAL_COLUMNS
    ]

    final_columns = (
        CANONICAL_COLUMNS
        + sorted(additional_columns)
    )

    df = df[
        final_columns
    ]

    # --------------------------------------------------------
    # Clean strings
    # --------------------------------------------------------

    for column in df.columns:

        if df[column].dtype == "object":

            df[column] = df[column].apply(
                clean_text
            )

    # --------------------------------------------------------
    # Remove exact duplicate rows
    # --------------------------------------------------------

    df = df.drop_duplicates()

    # --------------------------------------------------------
    # Remove records with no useful identity
    # --------------------------------------------------------

    df = remove_unusable_records(
        df
    )

    # --------------------------------------------------------
    # Ensure Id is unique
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=["Id"],
        keep="first"
    )

    # --------------------------------------------------------
    # Complete missing information
    # --------------------------------------------------------

    df = complete_missing_information(
        df
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # DO NOT replace blanks with "Not Available".
    #
    # Empty values remain empty because the information
    # genuinely does not exist in the source datasets.
    # --------------------------------------------------------

    for column in df.columns:

        if df[column].dtype == "object":

            df[column] = df[column].apply(
                clean_text
            )

    # --------------------------------------------------------
    # Sort for consistency
    # --------------------------------------------------------

    df = df.sort_values(
        by=[
            "title",
            "Id"
        ],
        na_position="last"
    )

    # --------------------------------------------------------
    # Reset index
    # --------------------------------------------------------

    df = df.reset_index(
        drop=True
    )

    return df


# ============================================================
# VALIDATION
# ============================================================

def validate_fused_dataset(
    df
):

    print("\n" + "=" * 80)
    print("FUSED DATASET VALIDATION")
    print("=" * 80)

    print(
        f"\nFinal rows       : {len(df)}"
    )

    print(
        f"Final columns    : {len(df.columns)}"
    )

    # --------------------------------------------------------
    # Primary key validation
    # --------------------------------------------------------

    duplicate_ids = df[
        df["Id"].duplicated(
            keep=False
        )
    ]

    print(
        f"Duplicate Ids    : {len(duplicate_ids)}"
    )

    # --------------------------------------------------------
    # Missing IDs
    # --------------------------------------------------------

    missing_ids = df[
        (
            df["Id"]
            .astype(str)
            .str.strip()
            == ""
        )
    ]

    print(
        f"Missing Ids      : {len(missing_ids)}"
    )

    # --------------------------------------------------------
    # Missing titles
    # --------------------------------------------------------

    missing_titles = df[
        (
            df["title"]
            .astype(str)
            .str.strip()
            == ""
        )
    ]

    print(
        f"Missing titles   : {len(missing_titles)}"
    )

    # --------------------------------------------------------
    # Empty fields
    # --------------------------------------------------------

    print(
        "\nColumn completeness:"
    )

    for column in df.columns:

        empty_count = (
            df[column]
            .astype(str)
            .str.strip()
            .eq("")
            .sum()
        )

        available_count = (
            len(df)
            - empty_count
        )

        print(
            f"  {column:35} "
            f"Available: {available_count:6} "
            f"Empty: {empty_count:6}"
        )

    # --------------------------------------------------------
    # DOI statistics
    # --------------------------------------------------------

    doi_count = (
        ~df["doi"]
        .astype(str)
        .str.strip()
        .eq("")
    ).sum()

    print(
        f"\nRecords with DOI: {doi_count}"
    )

    # --------------------------------------------------------
    # EID statistics
    # --------------------------------------------------------

    eid_count = (
        ~df["eid"]
        .astype(str)
        .str.strip()
        .eq("")
    ).sum()

    print(
        f"Records with EID: {eid_count}"
    )

    # --------------------------------------------------------
    # Dataset statistics
    # --------------------------------------------------------

    dataset_count = (
        ~df["dataset_id"]
        .astype(str)
        .str.strip()
        .eq("")
    ).sum()

    print(
        f"Kaggle datasets : {dataset_count}"
    )

    # --------------------------------------------------------
    # Sources
    # --------------------------------------------------------

    print(
        "\nSource distribution:"
    )

    source_counts = (
        df["source"]
        .value_counts()
    )

    for source, count in source_counts.items():

        print(
            f"  {source:35} : {count}"
        )

    # --------------------------------------------------------
    # Final columns
    # --------------------------------------------------------

    print(
        "\nFinal columns:"
    )

    for column in df.columns:

        print(
            f"  ✓ {column}"
        )

    print(
        "\nValidation complete."
    )


# ============================================================
# SAVE FUSED DATASET
# ============================================================

def save_fused_dataset(
    df
):

    DATASET_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 80)
    print("FUSED DATASET CREATED")
    print("=" * 80)

    print(
        "\nOutput file:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        f"\nRows written: {len(df)}"
    )

    print(
        f"Columns written: {len(df.columns)}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")

    print("=" * 80)
    print("RESEARCHIQ DATASET FUSION")
    print("=" * 80)

    print(
        "\nIMPORTANT:"
    )

    print(
        "database.csv IS INCLUDED as a source dataset."
    )

    print(
        "database.csv is NOT modified."
    )

    print(
        "dataset_fusion.csv is the ONLY output file."
    )

    print(
        "\nAll six source CSV files are loaded dynamically "
        "every time this script runs."
    )

    print(
        "\nSource datasets:"
    )

    for name, path in SOURCE_FILES.items():

        print(
            f"  {name:12} -> {path.name}"
        )

    print(
        "\nOutput:"
    )

    print(
        f"  -> {OUTPUT_FILE.name}"
    )

    # --------------------------------------------------------
    # Load all six datasets
    # --------------------------------------------------------

    datasets = load_sources()

    if not datasets:

        print(
            "\nERROR: No source datasets were loaded."
        )

        return

    # --------------------------------------------------------
    # Show total source rows
    # --------------------------------------------------------

    total_source_rows = sum(
        len(df)
        for df in datasets.values()
    )

    print(
        "\n" + "-" * 80
    )

    print(
        f"TOTAL SOURCE ROWS LOADED: "
        f"{total_source_rows}"
    )

    print(
        "-" * 80
    )

    # --------------------------------------------------------
    # Show source columns
    # --------------------------------------------------------

    print(
        "\nSOURCE COLUMNS:"
    )

    for name, df in datasets.items():

        print(
            f"\n{name.upper()}:"
        )

        for column in df.columns:

            print(
                f"  - {column}"
            )

    # --------------------------------------------------------
    # Fuse datasets
    # --------------------------------------------------------

    records = fuse_datasets(
        datasets
    )

    # --------------------------------------------------------
    # Check records
    # --------------------------------------------------------

    if not records:

        print(
            "\nERROR: No records were created."
        )

        return

    # --------------------------------------------------------
    # Convert to dataframe
    # --------------------------------------------------------

    fused_df = pd.DataFrame(
        list(records.values())
    )

    # --------------------------------------------------------
    # Clean and complete
    # --------------------------------------------------------

    fused_df = clean_final_dataframe(
        fused_df
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validate_fused_dataset(
        fused_df
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_fused_dataset(
        fused_df
    )

    print(
        "\n" + "=" * 80
    )

    print(
        "DATASET FUSION FINISHED SUCCESSFULLY"
    )

    print(
        "=" * 80
    )

    print(
        "\nThe fused dataset is:"
    )

    print(
        OUTPUT_FILE
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
