"""
MovieMind AI
Recommendation Engine (template-based)

This intentionally does NOT use flan-t5 or any local LLM. Across many
attempts (flan-t5-base, flan-t5-large, greedy decoding, sampling, beam
search, and several layers of output validation), the model kept
producing repetition loops, echoing context back verbatim, or drifting
off-topic in new ways each time. Small local models are simply not
reliable enough for this multi-document synthesis task.

This version builds the same style of natural-sounding recommendation
deterministically from the actual movie data. It is always accurate,
instant (no model to load), and can never hallucinate or repeat.
"""

import re

LIGHT_GENRES = {"comedy", "animation", "family", "music"}
SERIOUS_GENRES = {"drama", "thriller", "horror", "war", "crime", "mystery"}


def _clean_topic(query: str) -> str:
    """Turns 'space movies' into 'space' for nicer phrasing."""
    topic = re.sub(r"\bmovies?\b", "", query, flags=re.IGNORECASE).strip()
    topic = topic.strip(" -,.")
    return topic if topic else query.strip()


def _genre_set(movie) -> set:
    genres = (movie.get("genres_clean") or "").lower()
    return {g.strip() for g in genres.split(",") if g.strip()}


def _categorize(movie) -> str:
    genres = _genre_set(movie)
    if genres & LIGHT_GENRES:
        return "light"
    if genres & SERIOUS_GENRES:
        return "serious"
    return "neutral"


def _join_titles(titles) -> str:
    titles = [t for t in titles if t]
    if not titles:
        return ""
    if len(titles) == 1:
        return titles[0]
    if len(titles) == 2:
        return f"{titles[0]} and {titles[1]}"
    return ", ".join(titles[:-1]) + f", and {titles[-1]}"


def generate_recommendation(query, movies):
    """
    Builds a structured, natural-sounding recommendation from the
    retrieved movies: an overview sentence, a theme sentence, and
    mood-based guidance (serious vs. lighter picks).
    """

    if not movies:
        return "I couldn't find any movies matching that query. Try a different search."

    top_movies = movies[:5]
    topic = _clean_topic(query)

    titles = [m.get("title", "Unknown") for m in top_movies]
    title_list = _join_titles(titles)

    all_genres = []
    for m in top_movies:
        for g in _genre_set(m):
            if g not in all_genres:
                all_genres.append(g)
    genre_list = _join_titles([g.title() for g in all_genres[:4]])

    serious_movies = [m for m in top_movies if _categorize(m) == "serious"]
    light_movies = [m for m in top_movies if _categorize(m) == "light"]

    sentences = [
        f"Based on your interest in {topic} movies, I recommend {title_list}."
    ]

    if genre_list:
        sentences.append(
            f"These movies explore different sides of {topic}, spanning {genre_list.lower()}."
        )

    if serious_movies:
        serious_titles = _join_titles([m.get("title", "Unknown") for m in serious_movies[:2]])
        sentences.append(
            f"If you're looking for a more serious {topic} story, start with {serious_titles}."
        )

    if light_movies:
        light_titles = _join_titles([m.get("title", "Unknown") for m in light_movies[:2]])
        verb = "are" if len(light_movies[:2]) > 1 else "is"
        sentences.append(
            f"If you prefer something lighter, {light_titles} {verb} a fun watch."
        )

    return " ".join(sentences)