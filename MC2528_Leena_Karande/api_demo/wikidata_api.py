"""
Wikidata API Demo
DanceCompass AI

Note: like the Wikipedia lookup, a bare-name search on Wikidata for
something like "Garba" or "Manipuri" often returns an unrelated entity
first (a given name, a language...) rather than the dance. We bias the
search query and the candidate ranking towards results whose
description actually mentions "dance".
"""

import requests


WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"

HEADERS = {
    "User-Agent": "DanceCompass-AI/1.0 (academic project)"
}


def _search(query: str) -> list:
    params = {
        "action": "wbsearchentities",
        "search": query,
        "language": "en",
        "uselang": "en",
        "type": "item",
        "limit": 5,
        "format": "json",
    }
    response = requests.get(WIKIDATA_API_URL, params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.json().get("search", [])


def search_wikidata(dance_name: str) -> dict | None:
    """Search Wikidata for a dance form and return the best matching item.

    Tries a dance-specific query first ("<name> dance"), then the bare
    name, and within each result set prefers an entity whose
    description mentions "dance" over the first raw hit.
    """

    for query in (f"{dance_name} dance", dance_name):
        results = _search(query)
        if not results:
            continue

        dance_related = [r for r in results if "dance" in (r.get("description") or "").lower()]
        if dance_related:
            return dance_related[0]

        exact_label = [r for r in results if r.get("label", "").lower() == dance_name.lower()]
        if exact_label and query == dance_name:
            return exact_label[0]

    # Fall back to the very first hit on the bare name, if anything came back.
    results = _search(dance_name)
    return results[0] if results else None


def get_wikidata_details(entity_id: str) -> dict:
    """Retrieve details for a Wikidata entity."""

    params = {
        "action": "wbgetentities",
        "ids": entity_id,
        "props": "labels|descriptions|sitelinks",
        "languages": "en",
        "format": "json",
        "formatversion": "2",
    }

    response = requests.get(
        WIKIDATA_API_URL,
        params=params,
        headers=HEADERS,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    entity = data.get("entities", {}).get(entity_id, {})

    labels = entity.get("labels", {})
    descriptions = entity.get("descriptions", {})
    sitelinks = entity.get("sitelinks", {})

    return {
        "wikidata_id": entity_id,
        "label": labels.get("en", {}).get("value"),
        "description": descriptions.get("en", {}).get("value"),
        "wikipedia_url": (
            f"https://en.wikipedia.org/wiki/"
            f"{sitelinks['enwiki']['title'].replace(' ', '_')}"
            if "enwiki" in sitelinks
            else None
        ),
        "wikidata_url": f"https://www.wikidata.org/wiki/{entity_id}",
    }


def enrich_dance(dance_name: str) -> dict:
    """Search and enrich a dance form using Wikidata."""

    result = search_wikidata(dance_name)

    if not result:
        return {
            "dance": dance_name,
            "found": False,
            "message": "No matching Wikidata entity found.",
        }

    entity_id = result.get("id")

    details = get_wikidata_details(entity_id)

    return {
        "dance": dance_name,
        "found": True,
        **details,
    }


if __name__ == "__main__":
    dance = input("Enter dance name: ").strip()

    result = enrich_dance(dance)

    print("\n--- Wikidata API Result ---")

    for key, value in result.items():
        print(f"{key}: {value}")
