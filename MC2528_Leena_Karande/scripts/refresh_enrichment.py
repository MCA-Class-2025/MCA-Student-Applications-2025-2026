"""
Refresh API enrichment in data/dancecompass_merged.csv.

Run this locally (needs real internet access to wikipedia.org,
wikidata.org, openlibrary.org, musicbrainz.org):

    python scripts/refresh_enrichment.py

What it does:
  - Re-runs the Wikidata + Wikipedia lookups using the disambiguation-safe
    logic in api_demo/wikidata_api.py and api_demo/wikipedia_api.py, so
    entries like Manipuri, Bhangra, Garba, Salsa, Breaking, and
    Contemporary get their real dance article (and a real thumbnail)
    instead of a disambiguation page.
  - Re-runs the Open Library lookup and additionally stores each book's
    `openlibrary_key` (e.g. "/works/OL12345W") as book_i_url, so the
    Explore page can link straight to the book instead of a search page.
  - Adds music_recording_i_url (MusicBrainz page) and
    music_recording_i_youtube_url (YouTube search) columns from the
    MusicBrainz IDs already in the CSV -- no MusicBrainz re-fetch needed.
  - Leaves every curated (data/dance_forms.json) and EDA/text-analysis
    column untouched. Only overwrites the API-enrichment columns.

Safe to re-run any time; it always starts from the current
data/dancecompass_merged.csv and only replaces the columns above.
"""

import os
import sys
import time
from urllib.parse import quote_plus

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_demo.wikidata_api import enrich_dance as enrich_wikidata
from api_demo.wikipedia_api import enrich_dance as enrich_wikipedia
from api_demo.openlibrary_api import search_openlibrary
from api_demo.musicbrainz_api import search_musicbrainz

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "dancecompass_merged.csv")


def refresh_wikidata_wikipedia(df: pd.DataFrame) -> pd.DataFrame:
    for idx, row in df.iterrows():
        name, dance_id = row["name"], row["id"]
        print(f"[{idx + 1}/{len(df)}] {name} ...", end=" ")

        wd = enrich_wikidata(name)
        df.at[idx, "wikidata_found"] = wd.get("found", False)
        df.at[idx, "wikidata_id"] = wd.get("wikidata_id")
        df.at[idx, "wikidata_label"] = wd.get("label")
        df.at[idx, "wikidata_description"] = wd.get("description")
        df.at[idx, "wikidata_url"] = wd.get("wikidata_url")

        wp = enrich_wikipedia(name, dance_id)
        df.at[idx, "wikipedia_found"] = wp.get("found", False)
        df.at[idx, "wikipedia_title"] = wp.get("title")
        df.at[idx, "wikipedia_description"] = wp.get("description")
        df.at[idx, "wikipedia_extract"] = wp.get("extract")
        df.at[idx, "wikipedia_thumbnail_url"] = wp.get("thumbnail_url")
        df.at[idx, "wikipedia_url"] = wp.get("wikipedia_url")

        print("ok" if wp.get("found") else f"NO WIKIPEDIA MATCH ({wp.get('error')})")
        time.sleep(0.3)  # be polite to the public APIs
    return df


def refresh_book_urls(df: pd.DataFrame) -> pd.DataFrame:
    for idx, row in df.iterrows():
        name = row["name"]
        result = search_openlibrary(name)
        books = result.get("books", [])[:3]
        print(f"[{idx + 1}/{len(df)}] {name}: {len(books)} book(s)")
        for i in range(1, 4):
            df.at[idx, f"book_{i}_url"] = None
        for i, book in enumerate(books, start=1):
            key = book.get("openlibrary_key")
            df.at[idx, f"book_{i}_url"] = f"https://openlibrary.org{key}" if key else None
        time.sleep(0.5)
    return df


def add_music_links(df: pd.DataFrame) -> pd.DataFrame:
    for i in (1, 2, 3):
        id_col, title_col, artist_col = f"music_recording_{i}_id", f"music_recording_{i}_title", f"music_recording_{i}_artist"
        if id_col not in df.columns:
            continue
        df[f"music_recording_{i}_url"] = df[id_col].apply(lambda mbid: f"https://musicbrainz.org/recording/{mbid}" if isinstance(mbid, str) and mbid else None)

        def yt_link(row, title_col=title_col, artist_col=artist_col):
            title, artist = row.get(title_col), row.get(artist_col)
            if not isinstance(title, str) or not title:
                return None
            q = f"{title} {artist}" if isinstance(artist, str) and artist else title
            return f"https://www.youtube.com/results?search_query={quote_plus(q)}"

        df[f"music_recording_{i}_youtube_url"] = df.apply(yt_link, axis=1)
    return df


def main():
    print(f"Loading {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    print("\n--- Refreshing Wikidata + Wikipedia (disambiguation-safe) ---")
    df = refresh_wikidata_wikipedia(df)

    print("\n--- Refreshing Open Library book links ---")
    df = refresh_book_urls(df)

    print("\n--- Adding MusicBrainz / YouTube links ---")
    df = add_music_links(df)

    df.to_csv(CSV_PATH, index=False)
    print(f"\nDone. Wrote {len(df)} rows back to {CSV_PATH}")
    print("Restart the Streamlit app (or clear its cache) to see the refreshed data.")


if __name__ == "__main__":
    main()
