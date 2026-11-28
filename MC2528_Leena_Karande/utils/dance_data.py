"""
Loads and formats the curated dance-forms dataset (data/dance_forms.json).
Used by: assistant (RAG corpus), explore (browsing/filtering), analytics
(stats), and recommender (quiz matching).
"""

import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "dance_forms.json")

# Rough numeric scale for matching against quiz answers
_ENERGY_SCALE = {"Low": 1, "Low-Medium": 2, "Medium": 3, "Medium-High": 4, "High": 5}


def load_dance_forms() -> list:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def profile_to_text(d: dict) -> str:
    """Formats one dance-form record as a labeled fact sheet (one field
    per line) rather than a run-on paragraph. This is what the RAG index
    embeds and what the LLM sees as context -- a clearly structured
    record is both easier to retrieve accurately and easier for the LLM
    to answer from in a well-organized way, instead of paraphrasing a
    wall of text."""
    return (
        f"## {d['name']} ({d['category']})\n"
        f"Origin: {d['origin_region']}\n"
        f"History: {d['era_origin']}\n"
        f"Music: {d['music_style']}, played on {', '.join(d['instruments'])}\n"
        f"Costume: {d['costume']}\n"
        f"Key movements: {d['key_movements']}\n"
        f"Energy level: {d['energy_level']}\n"
        f"Formation: {d['solo_or_partner']}\n"
        f"Style/mood: {', '.join(d['mood_style'])}\n"
        f"Learning difficulty: {d['learning_difficulty']}\n"
        f"Famous for: {d['famous_for']}\n"
        f"Fun fact: {d['fun_fact']}"
    )


def build_corpus_texts() -> list:
    """One formatted text block per dance form -- feed straight into
    rag_pipeline.build_index_from_texts()."""
    return [profile_to_text(d) for d in load_dance_forms()]


def build_enriched_corpus_texts() -> list:
    """Same as build_corpus_texts(), but each dance form's chunk is
    extended with API- and Kaggle-sourced facts (Wikipedia/Wikidata/Nominatim/
    Open Library/MusicBrainz/Kaggle) from data/dancecompass_final_fused_allsources.csv, when available.
    Falls back to the curated-only text for any form the merged dataset
    doesn't cover, and to build_corpus_texts() entirely if the merged
    dataset is missing -- so the RAG index still builds without it."""
    texts, _ = build_enriched_corpus_with_metadata()
    return texts


def build_enriched_corpus_with_metadata() -> tuple:
    """Returns (texts, metadata) -- one labeled fact-sheet chunk per dance
    form (curated data/dance_forms.json fields + API/Kaggle enrichment from
    data/dancecompass_final_fused_allsources.csv, when available), plus a parallel list
    of {"id", "name", "category", "has_enrichment"} dicts so retrieved
    context can be cited back to the person by name instead of shown as
    an anonymous text blob."""
    try:
        from utils.merged_data import enrichment_text, get_enrichment, merged_data_available
    except ImportError:
        merged_data_available = lambda: False  # noqa: E731

    forms = load_dance_forms()
    texts, metadata = [], []
    for d in forms:
        base = profile_to_text(d)
        extra = ""
        has_enrichment = False
        if merged_data_available():
            row = get_enrichment(d["id"])
            if row:
                extra = enrichment_text(row)
                has_enrichment = bool(extra)
        texts.append(f"{base}\n{extra}".strip() if extra else base)
        metadata.append({
            "id": d["id"],
            "name": d["name"],
            "category": d["category"],
            "has_enrichment": has_enrichment,
        })
    return texts, metadata


def categories(dance_forms: list = None) -> list:
    dance_forms = dance_forms or load_dance_forms()
    seen = []
    for d in dance_forms:
        if d["category"] not in seen:
            seen.append(d["category"])
    return seen


def filter_forms(dance_forms: list, category: str = None, energy: str = None,
                  solo_or_partner: str = None) -> list:
    result = dance_forms
    if category and category != "All":
        result = [d for d in result if d["category"] == category]
    if energy and energy != "All":
        result = [d for d in result if d["energy_level"] == energy]
    if solo_or_partner and solo_or_partner != "All":
        result = [d for d in result if solo_or_partner.lower() in d["solo_or_partner"].lower()]
    return result


def _energy_score(level: str) -> int:
    return _ENERGY_SCALE.get(level, 3)


def score_matches(dance_forms: list, desired_energy: int, wants_partner: bool,
                   wants_traditional: bool, wants_expressive: bool, top_n: int = 3) -> list:
    """Simple, transparent (non-LLM) scoring for the recommender quiz, so
    the "why this dance" explanation can be grounded in an auditable rule
    rather than an opaque model guess. The LLM is only used afterwards to
    phrase the explanation in natural language from the matched profiles."""
    scored = []
    for d in dance_forms:
        score = 0.0
        score += 3 - abs(_energy_score(d["energy_level"]) - desired_energy)

        is_partner = "partner" in d["solo_or_partner"].lower()
        if wants_partner == is_partner:
            score += 2

        traditional_categories = {"Indian Classical", "Indian Folk"}
        is_traditional = d["category"] in traditional_categories
        if wants_traditional == is_traditional:
            score += 2

        expressive_moods = {"expressive", "storytelling", "dramatic", "sensual", "romantic"}
        is_expressive = bool(expressive_moods.intersection(set(m.lower() for m in d["mood_style"])))
        if wants_expressive == is_expressive:
            score += 1.5

        scored.append((score, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:top_n]]
