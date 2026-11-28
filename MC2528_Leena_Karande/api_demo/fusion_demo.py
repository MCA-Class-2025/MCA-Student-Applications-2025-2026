"""
DanceCompass AI - Final API Data Fusion

Purpose:
    1. Read the original DanceCompass JSON dataset.
    2. Perform basic text EDA.
    3. Enrich every dance using five external APIs.
    4. Keep the original JSON dataset untouched.
    5. Create ONE merged CSV file for EDA and UI visualization.

APIs:
    1. Wikidata
    2. Wikipedia
    3. Nominatim
    4. Open Library
    5. MusicBrainz
"""

import json
import re
import time
from collections import Counter
from pathlib import Path

import pandas as pd

from wikidata_api import search_wikidata
from wikipedia_api import search_wikipedia
from nominatim_api import geocode_location
from openlibrary_api import search_openlibrary
from musicbrainz_api import search_musicbrainz


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = PROJECT_ROOT / "data" / "dance_forms.json"

OUTPUT_DIR = PROJECT_ROOT / "data"
OUTPUT_CSV = OUTPUT_DIR / "dancecompass_merged.csv"


# ============================================================
# SETTINGS
# ============================================================

TOP_BOOKS = 3
TOP_ARTISTS = 3

# Small delays to be respectful to public APIs.
NOMINATIM_DELAY = 1.1
MUSICBRAINZ_DELAY = 1.1

# ============================================================
# API SEARCH NAME NORMALIZATION
# ============================================================

def get_api_search_name(dance: dict) -> str:
    """
    Return a cleaner search term for knowledge APIs.

    The original dance name is never modified.
    """

    name = str(
        dance.get("name", "")
    ).strip()

    aliases = {
        "Breaking (Breakdance)": "Breaking",
    }

    return aliases.get(
        name,
        name
    )

# ============================================================
# LOAD ORIGINAL DATASET
# ============================================================

def load_dataset() -> list:
    """Load the original DanceCompass JSON dataset."""

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "dance_forms.json must contain a list of dance records."
        )

    return data


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def list_to_text(value) -> str:
    """
    Convert list values into CSV-friendly text.

    Example:
        ["Tabla", "Sarangi"]
        ->
        "Tabla; Sarangi"
    """

    if isinstance(value, list):
        return "; ".join(str(item) for item in value)

    if value is None:
        return ""

    return str(value)


def clean_text(text: str) -> str:
    """Basic text cleaning for EDA."""

    text = str(text).lower()

    text = re.sub(r"[^a-z0-9\s]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def count_words(text: str) -> int:
    """Count words in a text string."""

    return len(re.findall(r"\b\w+\b", str(text)))


def count_sentences(text: str) -> int:
    """Estimate sentence count."""

    sentences = re.findall(
        r"[^.!?]+[.!?]+",
        str(text)
    )

    if sentences:
        return len(sentences)

    return 1 if str(text).strip() else 0


def average_word_length(text: str) -> float:
    """Calculate average word length."""

    words = re.findall(r"\b[a-zA-Z]+\b", str(text))

    if not words:
        return 0.0

    return round(
        sum(len(word) for word in words) / len(words),
        2
    )


# ============================================================
# SIMPLE TEXT KEYWORD EXTRACTION
# ============================================================

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
    "that",
    "are",
    "was",
    "were",
    "has",
    "have",
    "its",
    "into",
    "their",
    "they",
    "which",
    "also",
    "been",
    "than",
    "one",
    "two",
    "used",
    "use",
    "known",
    "often",
    "through",
    "over",
    "during",
    "where",
    "when",
    "such",
    "many",
    "more",
    "very",
    "a",
    "an",
    "in",
    "of",
    "to",
    "on",
    "is",
    "as",
    "by",
    "or",
    "at",
    "it"
}


def extract_top_keywords(text: str, top_n: int = 10) -> str:
    """Extract frequent meaningful words from the text."""

    cleaned = clean_text(text)

    words = re.findall(
        r"\b[a-z]{3,}\b",
        cleaned
    )

    words = [
        word
        for word in words
        if word not in STOPWORDS
    ]

    counts = Counter(words)

    keywords = [
        word
        for word, _ in counts.most_common(top_n)
    ]

    return "; ".join(keywords)


# ============================================================
# CREATE COMBINED TEXT
# ============================================================

def create_combined_text(dance: dict) -> str:
    """
    Combine the important textual fields from the original
    DanceCompass dataset.
    """

    fields = [
        "name",
        "category",
        "origin_region",
        "era_origin",
        "music_style",
        "instruments",
        "costume",
        "key_movements",
        "mood_style",
        "learning_difficulty",
        "famous_for",
        "fun_fact",
    ]

    parts = []

    for field in fields:
        value = dance.get(field)

        if isinstance(value, list):
            value = list_to_text(value)

        if value:
            parts.append(str(value))

    return " ".join(parts)


# ============================================================
# TEXT EDA
# ============================================================

def generate_text_eda(dance: dict) -> dict:
    """Generate basic text-analysis features."""

    combined_text = create_combined_text(dance)

    cleaned_text = clean_text(combined_text)

    return {
        "combined_text": combined_text,
        "cleaned_text": cleaned_text,
        "word_count": count_words(combined_text),
        "character_count": len(combined_text),
        "sentence_count": count_sentences(combined_text),
        "average_word_length": average_word_length(combined_text),
        "top_keywords": extract_top_keywords(combined_text),
    }


# ============================================================
# WIKIDATA NORMALIZATION
# ============================================================

def normalize_wikidata(data: dict | None) -> dict:

    if not data:
        return {
            "wikidata_found": False,
            "wikidata_id": "",
            "wikidata_label": "",
            "wikidata_description": "",
            "wikidata_url": "",
        }

    display = data.get("display", {})

    label = display.get("label", {})
    description = display.get("description", {})

    return {
        "wikidata_found": True,
        "wikidata_id": data.get("id", ""),
        "wikidata_label": (
            label.get("value", "")
            if isinstance(label, dict)
            else str(label)
        ),
        "wikidata_description": (
            description.get("value", "")
            if isinstance(description, dict)
            else str(description)
        ),
        "wikidata_url": data.get("url", ""),
    }


# ============================================================
# WIKIPEDIA NORMALIZATION
# ============================================================

def normalize_wikipedia(data: dict | None) -> dict:

    if not data:
        return {
            "wikipedia_found": False,
            "wikipedia_title": "",
            "wikipedia_description": "",
            "wikipedia_extract": "",
            "wikipedia_thumbnail_url": "",
            "wikipedia_url": "",
        }

    return {
        "wikipedia_found": data.get("found", False),
        "wikipedia_title": data.get("title", ""),
        "wikipedia_description": data.get(
            "description",
            ""
        ),
        "wikipedia_extract": data.get(
            "extract",
            ""
        ),
        "wikipedia_thumbnail_url": data.get(
            "thumbnail_url",
            ""
        ),
        "wikipedia_url": data.get(
            "wikipedia_url",
            ""
        ),
    }


# ============================================================
# NOMINATIM NORMALIZATION
# ============================================================

def normalize_nominatim(data: dict | None) -> dict:

    if not data:
        return {
            "location_found": False,
            "geographic_query": "",
            "location_display_name": "",
            "latitude": "",
            "longitude": "",
            "country": "",
            "country_code": "",
            "state": "",
            "region": "",
        }

    return {
        "location_found": data.get(
            "found",
            False
        ),
        "geographic_query": data.get(
            "geographic_query",
            ""
        ),
        "location_display_name": data.get(
            "display_name",
            ""
        ),
        "latitude": data.get(
            "latitude",
            ""
        ),
        "longitude": data.get(
            "longitude",
            ""
        ),
        "country": data.get(
            "country",
            ""
        ),
        "country_code": data.get(
            "country_code",
            ""
        ),
        "state": data.get(
            "state",
            ""
        ),
        "region": data.get(
            "region",
            ""
        ),
    }


# ============================================================
# OPEN LIBRARY NORMALIZATION
# ============================================================

def normalize_openlibrary(data: dict | None) -> dict:

    result = {
        "openlibrary_found": False,
        "openlibrary_total_results": 0,
        "book_count_selected": 0,

        "book_1_title": "",
        "book_1_author": "",
        "book_1_year": "",

        "book_2_title": "",
        "book_2_author": "",
        "book_2_year": "",

        "book_3_title": "",
        "book_3_author": "",
        "book_3_year": "",
    }

    if not data:
        return result

    books = data.get("books", [])

    result["openlibrary_found"] = data.get(
        "found",
        False
    )

    result["openlibrary_total_results"] = data.get(
        "total_results",
        0
    )

    selected_books = books[:TOP_BOOKS]

    result["book_count_selected"] = len(
        selected_books
    )

    for index, book in enumerate(
        selected_books,
        start=1
    ):

        authors = book.get(
            "authors",
            []
        )

        if isinstance(authors, list):
            author_text = "; ".join(
                str(author)
                for author in authors
            )
        else:
            author_text = str(authors)

        result[f"book_{index}_title"] = (
            book.get("title", "")
        )

        result[f"book_{index}_author"] = (
            author_text
        )

        result[f"book_{index}_year"] = (
            book.get(
                "first_publish_year",
                ""
            )
        )

    return result


# ============================================================
# MUSICBRAINZ NORMALIZATION
# ============================================================

def normalize_musicbrainz(data: dict | None) -> dict:
    """
    Normalize MusicBrainz recording results for the merged dataset.

    MusicBrainz is now queried using the recording endpoint,
    so the output contains music recordings rather than
    artist-name matches.
    """

    result = {
        "musicbrainz_found": False,
        "musicbrainz_query": "",
        "musicbrainz_total_results": 0,
        "music_recording_count_selected": 0,

        "music_recording_1_title": "",
        "music_recording_1_artist": "",
        "music_recording_1_id": "",
        "music_recording_1_length_ms": "",
        "music_recording_1_score": "",

        "music_recording_2_title": "",
        "music_recording_2_artist": "",
        "music_recording_2_id": "",
        "music_recording_2_length_ms": "",
        "music_recording_2_score": "",

        "music_recording_3_title": "",
        "music_recording_3_artist": "",
        "music_recording_3_id": "",
        "music_recording_3_length_ms": "",
        "music_recording_3_score": "",
    }

    if not data:
        return result

    recordings = data.get("recordings", [])

    result["musicbrainz_found"] = data.get(
        "found",
        False
    )

    result["musicbrainz_query"] = data.get(
        "query",
        ""
    )

    result["musicbrainz_total_results"] = data.get(
        "total_results",
        0
    )

    selected_recordings = recordings[:3]

    result["music_recording_count_selected"] = len(
        selected_recordings
    )

    for index, recording in enumerate(
        selected_recordings,
        start=1
    ):
        result[f"music_recording_{index}_title"] = (
            recording.get("title", "")
        )

        result[f"music_recording_{index}_artist"] = (
            recording.get("artist", "")
        )

        result[f"music_recording_{index}_id"] = (
            recording.get("musicbrainz_id", "")
        )

        result[f"music_recording_{index}_length_ms"] = (
            recording.get("length_ms", "")
        )

        result[f"music_recording_{index}_score"] = (
            recording.get("score", "")
        )

    return result

# ============================================================
# GEOGRAPHIC QUERY CLEANING
# ============================================================

def get_geographic_query(dance: dict) -> str:
    """
    Convert the dataset's origin_region into a cleaner
    geographic query for Nominatim.

    The original origin_region is never modified.
    """

    name = str(
        dance.get("name", "")
    ).strip().lower()

    origin = str(
        dance.get("origin_region", "")
    ).strip()

    geographic_queries = {
        "ballet": "Italy",
        "salsa": "Cuba",
        "flamenco": "Andalusia, Spain",
        "hip-hop": "New York City, United States",
        "tango": "Argentina",
        "contemporary": "United States",
        "belly dance": "Egypt",
        "tap dance": "United States",
        "breaking (breakdance)": "New York City, United States",
        "waltz": "Austria",
    }

    if name in geographic_queries:
        return geographic_queries[name]

    return origin
# ============================================================
# API ENRICHMENT
# ============================================================

def enrich_dance(dance: dict, index: int, total: int) -> dict:

    dance_name = str(
        dance.get("name", "")
    ).strip()

    api_search_name = get_api_search_name(
    dance
    )

    origin = str(
        dance.get(
            "origin_region",
            ""
        )
    ).strip()

    print("\n" + "=" * 70)
    print(
        f"[{index}/{total}] Processing: {dance_name}"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # ORIGINAL DATA
    # --------------------------------------------------------

    merged_record = {}

    for key, value in dance.items():
        merged_record[key] = list_to_text(value)

    # --------------------------------------------------------
    # TEXT EDA
    # --------------------------------------------------------

    print("Generating text EDA...")

    eda_result = generate_text_eda(
        dance
    )

    merged_record.update(
        eda_result
    )

    # --------------------------------------------------------
    # WIKIDATA
    # --------------------------------------------------------

    print("1/5 Wikidata...")

    try:
        wikidata_raw = search_wikidata(
            api_search_name
        )

        merged_record.update(
            normalize_wikidata(
                wikidata_raw
            )
        )

    except Exception as error:

        print(
            f"Wikidata error: {error}"
        )

        merged_record.update(
            normalize_wikidata(None)
        )

    # --------------------------------------------------------
    # WIKIPEDIA
    # --------------------------------------------------------

    print("2/5 Wikipedia...")

    try:
        wikipedia_raw = search_wikipedia(
            api_search_name
        )

        merged_record.update(
            normalize_wikipedia(
                wikipedia_raw
            )
        )

    except Exception as error:

        print(
            f"Wikipedia error: {error}"
        )

        merged_record.update(
            normalize_wikipedia(None)
        )

    # --------------------------------------------------------
    # NOMINATIM
    # --------------------------------------------------------

    print("3/5 Nominatim...")

    try:

        geographic_query = get_geographic_query(
            dance
        )

        if geographic_query:

            nominatim_raw = geocode_location(
                geographic_query
            )

            merged_record.update(
                normalize_nominatim(
                    nominatim_raw
                )
            )

            # Store the actual query used by Nominatim
            merged_record["geographic_query"] = (
                geographic_query
            )

        else:

            merged_record.update(
                normalize_nominatim(None)
            )

            merged_record["geographic_query"] = ""

        # Respect public geocoding service usage.
        time.sleep(
            NOMINATIM_DELAY
            )

    except Exception as error:

        print(
            f"Nominatim error: {error}"
        )

        merged_record.update(
            normalize_nominatim(None)
        )

        merged_record["geographic_query"] = ""
    # --------------------------------------------------------
    # OPEN LIBRARY
    # --------------------------------------------------------

    print("4/5 Open Library...")

    try:

        openlibrary_raw = search_openlibrary(
            dance_name
        )

        merged_record.update(
            normalize_openlibrary(
                openlibrary_raw
            )
        )

    except Exception as error:

        print(
            f"Open Library error: {error}"
        )

        merged_record.update(
            normalize_openlibrary(None)
        )

    # --------------------------------------------------------
    # MUSICBRAINZ
    # --------------------------------------------------------

    print("5/5 MusicBrainz...")

    try:

        musicbrainz_raw = search_musicbrainz(
            dance_name
        )

        merged_record.update(
            normalize_musicbrainz(
                musicbrainz_raw
            )
        )

        # MusicBrainz public API usage requires
        # requests to be rate controlled.
        time.sleep(
            MUSICBRAINZ_DELAY
        )

    except Exception as error:

        print(
            f"MusicBrainz error: {error}"
        )

        merged_record.update(
            normalize_musicbrainz(None)
        )

    return merged_record


# ============================================================
# MAIN FUSION PROCESS
# ============================================================

def build_merged_dataset():

    print("=" * 70)
    print("        DANCECOMPASS AI - DATA FUSION")
    print("=" * 70)

    print(
        f"\nOriginal dataset:"
        f"\n{DATASET_PATH}"
    )

    # --------------------------------------------------------
    # LOAD ORIGINAL DATASET
    # --------------------------------------------------------

    dances = load_dataset()

    total_dances = len(dances)

    print(
        f"\nLoaded {total_dances} dance records."
    )

    print(
        "\nOriginal JSON will NOT be modified."
    )

    # --------------------------------------------------------
    # PROCESS ALL DANCES
    # --------------------------------------------------------

    merged_records = []

    for index, dance in enumerate(
        dances,
        start=1
    ):

        try:

            merged_record = enrich_dance(
                dance,
                index,
                total_dances
            )

            merged_records.append(
                merged_record
            )

        except Exception as error:

            print(
                f"\nERROR processing "
                f"{dance.get('name', 'Unknown')}:"
            )

            print(error)

    # --------------------------------------------------------
    # CREATE DATAFRAME
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "Creating final merged DataFrame..."
    )

    dataframe = pd.DataFrame(
        merged_records
    )

    # --------------------------------------------------------
    # ENSURE OUTPUT DIRECTORY EXISTS
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # SAVE ONE MERGED CSV
    # --------------------------------------------------------

    dataframe.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "DATA FUSION COMPLETED"
    )

    print(
        "=" * 70
    )

    print(
        f"\nOriginal records : {total_dances}"
    )

    print(
        f"Merged records   : {len(dataframe)}"
    )

    print(
        f"Final columns    : {len(dataframe.columns)}"
    )

    print(
        f"\nMerged CSV saved to:"
    )

    print(
        OUTPUT_CSV
    )

    print(
        "\nOriginal JSON remains untouched."
    )

    print(
        "\nPreview:"
    )

    print(
        dataframe[
            [
                "id",
                "name",
                "category",
                "origin_region",
                "wikidata_found",
                "wikipedia_found",
                "location_found",
                "openlibrary_found",
                "musicbrainz_found",
            ]
        ].to_string(
            index=False
        )
    )

    return dataframe


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        build_merged_dataset()

    except Exception as error:

        print(
            "\nERROR:"
        )

        print(error)