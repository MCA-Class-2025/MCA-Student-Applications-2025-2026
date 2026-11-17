"""
MovieMind AI
Watchmode API Integration

Provides streaming availability for movies in India.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

WATCHMODE_API_KEY = os.getenv("WATCHMODE_API_KEY")

BASE_URL = "https://api.watchmode.com/v1"


def clean_streaming_sources(sources):
    """
    Remove duplicate streaming entries and combine
    different video qualities for the same platform.
    """

    platforms = {}

    for source in sources:

        name = source.get("name", "Unknown")
        source_type = source.get("type", "Unknown")
        quality = source.get("format")
        price = source.get("price")
        url = source.get("web_url")

        # Group by platform + type
        key = (name, source_type)

        if key not in platforms:
            platforms[key] = {
                "name": name,
                "type": source_type,
                "price": price,
                "qualities": [],
                "url": url
            }

        # Add quality only once
        if quality and quality not in platforms[key]["qualities"]:
            platforms[key]["qualities"].append(quality)

        # Keep price if the first entry didn't have one
        if platforms[key]["price"] is None and price is not None:
            platforms[key]["price"] = price

    return list(platforms.values())


def search_watchmode_movie(title, country="IN"):
    """
    Search for a movie on Watchmode and return
    streaming availability for the selected country.

    Default country: India (IN)
    """

    if not WATCHMODE_API_KEY:
        print("Watchmode API key not found.")
        return None

    # ---------------------------------------
    # Step 1: Search for the movie
    # ---------------------------------------

    search_url = f"{BASE_URL}/search/"

    search_params = {
        "apiKey": WATCHMODE_API_KEY,
        "search_field": "name",
        "search_value": title
    }

    try:

        response = requests.get(
            search_url,
            params=search_params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("title_results", [])

        if not results:
            print(f"Movie not found on Watchmode: {title}")
            return None

        movie = results[0]

        title_id = movie.get("id")

        if not title_id:
            print("Watchmode title ID not found.")
            return None

        # ---------------------------------------
        # Step 2: Get streaming sources
        # ---------------------------------------

        sources_url = f"{BASE_URL}/title/{title_id}/sources/"

        source_params = {
            "apiKey": WATCHMODE_API_KEY,
            "regions": country
        }

        source_response = requests.get(
            sources_url,
            params=source_params,
            timeout=10
        )

        source_response.raise_for_status()

        sources = source_response.json()

        # ---------------------------------------
        # Step 3: Clean duplicate sources
        # ---------------------------------------

        cleaned_sources = clean_streaming_sources(sources)

        # ---------------------------------------
        # Step 4: Return useful data
        # ---------------------------------------

        return {
            "title_id": title_id,
            "title": movie.get("name"),
            "sources": cleaned_sources
        }

    except requests.RequestException as e:

        print("Watchmode API Error:", e)

        return None