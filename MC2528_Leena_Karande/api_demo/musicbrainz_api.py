"""
MusicBrainz API Demo
DanceCompass AI

Purpose:
    Retrieve music/recording metadata related to a dance form.

MusicBrainz API:
    https://musicbrainz.org/ws/2/

No API key is required for the public API.
"""

import time
import requests


MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2/recording"

HEADERS = {
    "User-Agent": (
        "DanceCompassAI/1.0 "
        "(educational project; contact: leekarande@gmail.com)"
    ),
    "Accept": "application/json",
}


def search_musicbrainz(query: str) -> dict:
    """
    Search MusicBrainz recordings related to a dance/music query.

    Returns structured recording information including:
    - recording title
    - artist/artist credit
    - MusicBrainz recording ID
    - match score
    """

    query = query.strip()

    if not query:
        return {
            "found": False,
            "query": query,
            "error": "Search query cannot be empty.",
        }

    params = {
        "query": query,
        "fmt": "json",
        "limit": 5,
    }

    max_retries = 3

    for attempt in range(max_retries):

        try:

            # MusicBrainz requires clients to stay at or below
            # one request per second.
            time.sleep(1.2)

            response = requests.get(
                MUSICBRAINZ_URL,
                params=params,
                headers=HEADERS,
                timeout=30,
            )

            # --------------------------------------------------
            # SUCCESS
            # --------------------------------------------------

            if response.status_code == 200:

                data = response.json()

                recordings = []

                for recording in data.get(
                    "recordings",
                    []
                ):

                    # ------------------------------------------
                    # Extract artist credits
                    # ------------------------------------------

                    artist_names = []

                    for credit in recording.get(
                        "artist-credit",
                        []
                    ):

                        if isinstance(credit, dict):

                            artist = credit.get(
                                "artist",
                                {}
                            )

                            if artist.get("name"):
                                artist_names.append(
                                    artist.get("name")
                                )

                    recordings.append(
                        {
                            "title": recording.get(
                                "title"
                            ),

                            "artist": "; ".join(
                                artist_names
                            ),

                            "musicbrainz_id": recording.get(
                                "id"
                            ),

                            "length_ms": recording.get(
                                "length"
                            ),

                            "score": recording.get(
                                "score"
                            ),
                        }
                    )

                return {
                    "found": len(recordings) > 0,
                    "query": query,
                    "total_results": data.get(
                        "count",
                        0
                    ),
                    "recordings": recordings,
                }

            # --------------------------------------------------
            # TEMPORARY SERVER ERROR
            # --------------------------------------------------

            elif response.status_code in (
                502,
                503,
                504,
            ):

                if attempt < max_retries - 1:

                    retry_delay = 2 ** (
                        attempt + 1
                    )

                    print(
                        "MusicBrainz temporarily "
                        f"unavailable "
                        f"(HTTP {response.status_code}). "
                        f"Waiting {retry_delay} seconds..."
                    )

                    time.sleep(
                        retry_delay
                    )

                    continue

                return {
                    "found": False,
                    "query": query,
                    "error": (
                        "MusicBrainz service unavailable "
                        f"(HTTP {response.status_code}) "
                        f"after {max_retries} attempts."
                    ),
                }

            # --------------------------------------------------
            # RATE LIMIT
            # --------------------------------------------------

            elif response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After",
                    "5",
                )

                try:
                    retry_seconds = int(
                        retry_after
                    )
                except ValueError:
                    retry_seconds = 5

                if attempt < max_retries - 1:

                    print(
                        "MusicBrainz rate limit reached. "
                        f"Waiting {retry_seconds} seconds..."
                    )

                    time.sleep(
                        retry_seconds
                    )

                    continue

                return {
                    "found": False,
                    "query": query,
                    "error": (
                        "MusicBrainz rate limit reached. "
                        "Please try again later."
                    ),
                }

            # --------------------------------------------------
            # OTHER HTTP ERRORS
            # --------------------------------------------------

            else:

                return {
                    "found": False,
                    "query": query,
                    "error": (
                        "MusicBrainz returned "
                        f"HTTP {response.status_code}."
                    ),
                }

        # ------------------------------------------------------
        # TIMEOUT
        # ------------------------------------------------------

        except requests.Timeout:

            if attempt < max_retries - 1:

                print(
                    "MusicBrainz request timed out. "
                    "Retrying..."
                )

                time.sleep(2)

                continue

            return {
                "found": False,
                "query": query,
                "error": (
                    "MusicBrainz request timed out."
                ),
            }

        # ------------------------------------------------------
        # NETWORK ERROR
        # ------------------------------------------------------

        except requests.RequestException as error:

            if attempt < max_retries - 1:

                print(
                    "Network error while contacting "
                    "MusicBrainz. Retrying..."
                )

                time.sleep(2)

                continue

            return {
                "found": False,
                "query": query,
                "error": str(error),
            }

        # ------------------------------------------------------
        # INVALID JSON
        # ------------------------------------------------------

        except ValueError:

            return {
                "found": False,
                "query": query,
                "error": (
                    "MusicBrainz returned an invalid "
                    "JSON response."
                ),
            }

    return {
        "found": False,
        "query": query,
        "error": "Unknown MusicBrainz API error.",
    }


def print_result(result: dict) -> None:
    """
    Display the MusicBrainz recording results.
    """

    print("\n--- MusicBrainz API Result ---")

    print(
        f"Query: {result.get('query')}"
    )

    print(
        f"Found: {result.get('found')}"
    )

    if "error" in result:

        print(
            f"Error: {result['error']}"
        )

        return

    print(
        f"Total results: "
        f"{result.get('total_results', 0)}"
    )

    recordings = result.get(
        "recordings",
        []
    )

    if not recordings:

        print(
            "\nNo matching music recordings found."
        )

        return

    print(
        "\nRelated Music Recordings:\n"
    )

    for index, recording in enumerate(
        recordings,
        start=1
    ):

        print(
            f"Recording {index}"
        )

        print(
            f"Title: "
            f"{recording.get('title')}"
        )

        print(
            f"Artist: "
            f"{recording.get('artist')}"
        )

        print(
            f"MusicBrainz ID: "
            f"{recording.get('musicbrainz_id')}"
        )

        print(
            f"Length (ms): "
            f"{recording.get('length_ms')}"
        )

        print(
            f"Match Score: "
            f"{recording.get('score')}"
        )

        print(
            "-" * 50
        )


def main():

    print("=" * 60)

    print(
        "        MusicBrainz API Demo"
    )

    print(
        "             DanceCompass AI"
    )

    print("=" * 60)

    query = input(
        "\nEnter dance/music-related search: "
    ).strip()

    result = search_musicbrainz(
        query
    )

    print_result(
        result
    )


if __name__ == "__main__":

    main()