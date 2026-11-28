"""
Loads the fully fused dataset (data/dancecompass_final_fused_allsources.csv:
curated + 5-API enrichment + Kaggle "Dance Styles & Genres" enrichment) and
the precomputed EDA outputs (data/eda/*.csv, data/eda/*.png).

This sits ALONGSIDE utils/dance_data.py, which stays the source of truth for
the curated dance_forms.json fields (name, category, costume, etc.). This
module only ever adds: enrichment from Wikidata / Wikipedia / Nominatim /
Open Library / MusicBrainz / Kaggle, plus text-analysis and EDA fields
computed on top of the curated data. The original JSON is never modified
and nothing here overwrites it -- explore.py, analytics.py, and the RAG
corpus builder merge the two by dance-form `id`.

Missing values in this file are real NaN (not text labels) on purpose --
_clean() below depends on that to correctly skip absent fields instead of
treating a placeholder string as real content.

Used by: analytics (unified charts + EDA), explore (API enrichment panel),
dance_data / app.py (enriched RAG corpus).
"""

import os

import pandas as pd
import streamlit as st

_MERGED_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "dancecompass_final_fused_allsources.csv")
_EDA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "eda")

EDA_TABLE_FILES = {
    "summary": "eda_summary.csv",
    "api_coverage": "api_coverage.csv",
    "category": "category_summary.csv",
    "difficulty": "difficulty_summary.csv",
    "energy": "energy_summary.csv",
    "country": "country_summary.csv",
}

EDA_CHART_FILES = {
    "category": "01_category_distribution.png",
    "difficulty": "02_learning_difficulty.png",
    "energy": "03_energy_level.png",
    "country": "04_country_distribution.png",
    "text_length": "05_text_word_count.png",
    "api_coverage": "06_api_coverage.png",
}

API_SOURCES = {
    "Wikidata": "wikidata_found",
    "Wikipedia": "wikipedia_found",
    "Nominatim": "location_found",
    "Open Library": "openlibrary_found",
    "MusicBrainz": "musicbrainz_found",
    "Kaggle (Dance Styles & Genres)": "kaggle_matched",
}


def merged_data_available() -> bool:
    return os.path.exists(_MERGED_CSV_PATH)


@st.cache_data(show_spinner=False)
def load_merged_df() -> pd.DataFrame:
    """The full fused table: 20 dance forms x curated + text-analysis +
    API-enrichment columns. Cached for the session; reload happens only
    when Streamlit's cache is cleared."""
    if not merged_data_available():
        return pd.DataFrame()
    return pd.read_csv(_MERGED_CSV_PATH)


def get_enrichment(dance_id: str) -> dict:
    """API-enriched + text-analysis fields for one dance form id, or {}
    if the merged dataset isn't present or the id isn't found."""
    df = load_merged_df()
    if df.empty:
        return {}
    row = df[df["id"] == dance_id]
    if row.empty:
        return {}
    return row.iloc[0].to_dict()


@st.cache_data(show_spinner=False)
def load_eda_tables() -> dict:
    """Precomputed EDA summary CSVs (produced by eda.py), keyed by short name."""
    tables = {}
    for key, fname in EDA_TABLE_FILES.items():
        path = os.path.join(_EDA_DIR, fname)
        if os.path.exists(path):
            tables[key] = pd.read_csv(path)
    return tables


def eda_chart_path(key: str):
    """Absolute path to a precomputed EDA chart PNG, or None if missing."""
    fname = EDA_CHART_FILES.get(key)
    if not fname:
        return None
    path = os.path.join(_EDA_DIR, fname)
    return path if os.path.exists(path) else None


def api_coverage_summary() -> dict:
    """{source_name: (found_count, total_count)} computed live from the
    merged dataset, so it stays correct even if the dataset grows beyond
    the 20 forms the precomputed eda.py charts were built from."""
    df = load_merged_df()
    if df.empty:
        return {}
    total = len(df)
    coverage = {}
    for label, col in API_SOURCES.items():
        if col in df.columns:
            found = int(df[col].fillna(False).astype(bool).sum())
            coverage[label] = (found, total)
    return coverage


def _clean(value) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def openlibrary_link(row: dict, i: int) -> str:
    """Prefer the exact work URL (added by scripts/refresh_enrichment.py);
    fall back to an Open Library search link built from title/author,
    which needs no extra API call and still lands on the right book."""
    direct = _clean(row.get(f"book_{i}_url"))
    if direct:
        return direct
    title, author = _clean(row.get(f"book_{i}_title")), _clean(row.get(f"book_{i}_author"))
    if not title:
        return ""
    from urllib.parse import quote_plus
    return f"https://openlibrary.org/search?q={quote_plus(f'{title} {author}'.strip())}"


def musicbrainz_link(row: dict, i: int) -> str:
    direct = _clean(row.get(f"music_recording_{i}_url"))
    if direct:
        return direct
    mbid = _clean(row.get(f"music_recording_{i}_id"))
    return f"https://musicbrainz.org/recording/{mbid}" if mbid else ""


def youtube_link(row: dict, i: int) -> str:
    direct = _clean(row.get(f"music_recording_{i}_youtube_url"))
    if direct:
        return direct
    title, artist = _clean(row.get(f"music_recording_{i}_title")), _clean(row.get(f"music_recording_{i}_artist"))
    if not title:
        return ""
    from urllib.parse import quote_plus
    return f"https://www.youtube.com/results?search_query={quote_plus(f'{title} {artist}'.strip())}"


def enrichment_text(row: dict) -> str:
    """Formats one merged-CSV row's API-sourced fields into a labeled
    block for the RAG corpus -- appended to (not replacing) the curated
    profile text in dance_data.profile_to_text(), in the same one-field-
    per-line style, so retrieval can surface facts that only came from
    Wikipedia/Wikidata/Nominatim/OpenLibrary/MusicBrainz and the LLM can
    tell curated facts and open-data facts apart. Books and recordings
    include their real markdown links so the LLM can pass them straight
    through into its answer instead of citing a title with no way to
    click through to it."""
    lines = []

    extract = _clean(row.get("wikipedia_extract"))
    if extract:
        lines.append(f"Wikipedia summary: {extract}")

    wd_desc = _clean(row.get("wikidata_description"))
    if wd_desc:
        lines.append(f"Wikidata summary: {wd_desc}")

    loc_bits = [b for b in (_clean(row.get("location_display_name")), _clean(row.get("country"))) if b]
    if loc_bits:
        lines.append("Geographic reference: " + ", ".join(dict.fromkeys(loc_bits)))

    books = []
    for i in (1, 2, 3):
        title = _clean(row.get(f"book_{i}_title"))
        if title:
            author = _clean(row.get(f"book_{i}_author"))
            label = f"{title}" + (f" by {author}" if author else "")
            link = openlibrary_link(row, i)
            books.append(f"[{label}]({link})" if link else label)
    if books:
        lines.append("Recommended reading (markdown links, use them as-is): " + "; ".join(books))

    tracks = []
    for i in (1, 2, 3):
        title = _clean(row.get(f"music_recording_{i}_title"))
        if title:
            artist = _clean(row.get(f"music_recording_{i}_artist"))
            label = f"{title}" + (f" by {artist}" if artist else "")
            mb_link, yt_link = musicbrainz_link(row, i), youtube_link(row, i)
            link_bits = []
            if yt_link:
                link_bits.append(f"[listen on YouTube]({yt_link})")
            if mb_link:
                link_bits.append(f"[MusicBrainz]({mb_link})")
            tracks.append(f"{label} ({', '.join(link_bits)})" if link_bits else label)
    if tracks:
        lines.append("Reference recordings (markdown links, use them as-is): " + "; ".join(tracks))

    return "\n".join(lines)
