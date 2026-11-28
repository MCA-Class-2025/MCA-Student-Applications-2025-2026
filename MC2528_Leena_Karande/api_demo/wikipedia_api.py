"""
Wikipedia / MediaWiki API Demo
DanceCompass AI

Purpose:
Fetch useful external information about a dance form
and combine it with our existing dance dataset.

Note: Many dance names are ambiguous English words (Salsa, Bhangra,
Garba, Manipuri, Breaking, Contemporary...). A single-shot lookup on
the bare name often lands on a Wikipedia *disambiguation* page (no
thumbnail, useless extract) or an unrelated article ("Contemporary"
-> "Contemporary history"). To fix that, we try a short list of more
specific candidate titles first and skip anything that comes back as
a disambiguation page.
"""

import requests


WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"

HEADERS = {"User-Agent": "DanceCompass-AI/1.0"}


def _is_disambiguation(data: dict) -> bool:
    if data.get("type") == "disambiguation":
        return True
    description = (data.get("description") or "").lower()
    return "topics referred to by the same term" in description


def _candidate_titles(dance_name: str, dance_id: str | None = None) -> list:
    """Ordered list of titles to try, most-specific first."""
    candidates = [dance_name]
    if "(" not in dance_name:
        candidates.append(f"{dance_name} (dance)")
        candidates.append(f"{dance_name} dance")
    if dance_id and dance_id.replace("_", " ").lower() != dance_name.lower():
        base = dance_id.replace("_", " ")
        candidates.append(f"{base} (dance)")
        candidates.append(f"{base} dance")
    # De-dupe while preserving order
    seen = set()
    ordered = []
    for c in candidates:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(c)
    return ordered


def search_wikipedia(dance_name: str, dance_id: str | None = None) -> dict:
    """
    Fetch a Wikipedia summary for a dance form, trying disambiguated
    candidate titles until one resolves to a real (non-disambiguation)
    article.
    """

    last_error = None
    for candidate in _candidate_titles(dance_name, dance_id):
        try:
            url = f"{WIKIPEDIA_API_URL}/{candidate.strip().replace(' ', '_')}"
            response = requests.get(url, headers=HEADERS, timeout=10)
        except requests.RequestException as e:
            last_error = str(e)
            continue

        if response.status_code != 200:
            last_error = f"HTTP {response.status_code}"
            continue

        data = response.json()
        if _is_disambiguation(data):
            continue

        thumbnail = data.get("thumbnail", {})
        return {
            "dance": dance_name,
            "found": True,
            "matched_title_query": candidate,
            "title": data.get("title"),
            "description": data.get("description"),
            "extract": data.get("extract"),
            "thumbnail_url": thumbnail.get("source"),
            "wikipedia_url": data.get("content_urls", {}).get("desktop", {}).get("page"),
        }

    return {
        "dance": dance_name,
        "found": False,
        "error": last_error or "No non-disambiguation Wikipedia page found.",
    }


def enrich_dance(dance_name: str, dance_id: str | None = None) -> dict:
    """
    Search Wikipedia and return enriched dance information.
    """

    return search_wikipedia(dance_name, dance_id)


if __name__ == "__main__":

    dance_name = input("Enter dance name: ")

    result = enrich_dance(dance_name)

    print("\n--- Wikipedia API Result ---")

    for key, value in result.items():
        print(f"{key}: {value}")
