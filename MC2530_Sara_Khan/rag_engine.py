"""Country-aware hybrid RAG and analytics for the Travel Destination Intelligence System."""

from pathlib import Path
import json
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
INDEX = DATA / "faiss_attractions.index"
META = DATA / "rag_documents.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_MODEL = "qwen2.5:3b"


def load_source():
    """Load the enriched dataset, falling back to the original dataset/workbook."""
    enriched = DATA / "travel_attractions_enriched.csv"
    original = DATA / "travel_attractions_1500.csv"
    master = DATA / "travel_attractions_master.xlsx"

    if enriched.exists():
        df = pd.read_csv(enriched)
        if not df.empty:
            return df

    if master.exists():
        try:
            df = pd.read_excel(master, sheet_name="Attractions")
            if not df.empty:
                return df
        except Exception:
            pass

    if original.exists():
        return pd.read_csv(original)

    raise FileNotFoundError(
        "Dataset not found. Expected travel_attractions_enriched.csv, "
        "travel_attractions_master.xlsx, or travel_attractions_1500.csv "
        "inside the data folder."
    )


def row_to_text(row):
    fields = [
        "name_en", "city_en", "country_en", "category",
        "wikipedia_summary", "wikidata_description",
        "inception_date", "official_website",
        "forecast_avg_max_temp_c", "forecast_avg_min_temp_c",
        "past_30d_avg_temp_c", "currency_code",
        "currency_inr_per_unit", "next_public_holiday",
        "next_public_holiday_date",
    ]

    parts = []
    for field in fields:
        if field in row.index:
            value = row.get(field)
            if pd.notna(value) and str(value).strip():
                parts.append(f"{field.replace('_', ' ')}: {value}")

    return " | ".join(parts)


def build_index():
    """Build a FAISS index and matching metadata for all usable attraction rows."""
    from sentence_transformers import SentenceTransformer
    import faiss

    df = load_source()
    records = []

    for _, row in df.iterrows():
        text = row_to_text(row)
        if not text.strip():
            continue

        records.append({
            "text": text,
            "country": str(row.get("country_en", "")).strip(),
            "city": str(row.get("city_en", "")).strip(),
            "name": str(row.get("name_en", "")).strip(),
        })

    if not records:
        raise ValueError("No valid attraction records found.")

    print(f"Creating embeddings for {len(records)} records...")
    model = SentenceTransformer(MODEL_NAME)
    vectors = model.encode(
        [record["text"] for record in records],
        normalize_embeddings=True,
        show_progress_bar=True,
    ).astype("float32")

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    DATA.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX))
    META.write_text(
        json.dumps({"records": records}, ensure_ascii=False),
        encoding="utf-8",
    )

    print("FAISS index created successfully.")
    return len(records)


def load_index_data():
    """Load the index and rebuild it if its metadata format/count is outdated."""
    import faiss

    if not INDEX.exists() or not META.exists():
        build_index()

    data = json.loads(META.read_text(encoding="utf-8"))

    # The earlier version stored only {"documents": [...]}.
    if "records" not in data:
        build_index()
        data = json.loads(META.read_text(encoding="utf-8"))

    records = data["records"]
    index = faiss.read_index(str(INDEX))

    if index.ntotal != len(records):
        build_index()
        data = json.loads(META.read_text(encoding="utf-8"))
        records = data["records"]
        index = faiss.read_index(str(INDEX))

    return index, records


def detect_country(question, records):
    """Detect a country explicitly mentioned in the question."""
    countries = sorted(
        {
            str(record.get("country", "")).strip()
            for record in records
            if str(record.get("country", "")).strip()
            and str(record.get("country", "")).lower() != "nan"
        },
        key=len,
        reverse=True,
    )

    aliases = {
        "india": ["india", "indian"],
        "united states": ["usa", "u.s.a.", "united states", "america"],
        "united kingdom": ["uk", "u.k.", "united kingdom", "britain"],
        "united arab emirates": ["uae", "united arab emirates"],
    }

    question_lower = question.lower()

    for country in countries:
        terms = aliases.get(country.lower(), [country])
        for term in terms:
            pattern = r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)"
            if re.search(pattern, question_lower):
                return country

    return None


def retrieve(question, k=5):
    """Retrieve relevant records, filtering to a named country when present."""
    from sentence_transformers import SentenceTransformer

    index, records = load_index_data()
    country = detect_country(question, records)

    if country:
        candidate_ids = [
            i for i, record in enumerate(records)
            if str(record.get("country", "")).strip().lower() == country.lower()
        ]
        if not candidate_ids:
            return []
        print(f"Country filter applied: {country}")
    else:
        candidate_ids = list(range(len(records)))

    model = SentenceTransformer(MODEL_NAME)
    query_vector = model.encode(
        [question],
        normalize_embeddings=True,
    ).astype("float32")[0]

    # Apply country filtering before semantic ranking.
    all_vectors = index.reconstruct_n(0, index.ntotal)
    candidate_vectors = all_vectors[candidate_ids]
    scores = np.dot(candidate_vectors, query_vector)
    best_positions = np.argsort(scores)[::-1][:min(k, len(candidate_ids))]

    selected_ids = [candidate_ids[position] for position in best_positions]
    return [records[i]["text"] for i in selected_ids]


def answer_analytics(question):
    """Calculate country rankings from every row in the loaded dataset."""
    df = load_source()

    if "country_en" not in df.columns:
        return "Country information is unavailable in the loaded dataset."

    # Normalize whitespace and exclude only missing/blank country values.
    country_values = df["country_en"].astype("string").str.strip()
    country_values = country_values[
        country_values.notna() & country_values.ne("")
    ]

    counts = country_values.value_counts()

    if counts.empty:
        return "No country information was found in the loaded dataset."

    top_n = min(10, len(counts))
    top_countries = counts.head(top_n)
    highest_count = int(counts.max())
    leaders = counts[counts == highest_count]

    ranking_lines = [
        f"{position}. {country}: {int(count)} attractions"
        for position, (country, count) in enumerate(top_countries.items(), start=1)
    ]

    leader_names = ", ".join(str(country) for country in leaders.index)

    return (
        f"Based on the currently loaded dataset ({len(df):,} total rows), "
        f"the highest country count is {highest_count:,} attractions.\n\n"
        f"Country/countries with the most attractions: {leader_names}.\n\n"
        f"Top {top_n} countries by attraction count:\n"
        + "\n".join(ranking_lines)
        + f"\n\nCountries represented: {len(counts):,}."
    )


def is_country_ranking_question(question):
    """Recognize country-level attraction ranking questions."""
    q = re.sub(r"[^a-z0-9\s]", " ", question.lower())
    q = " ".join(q.split())

    mentions_countries = any(
        term in q for term in ("country", "countries", "nation", "nations")
    )
    mentions_attractions = any(
        term in q for term in (
            "attraction", "attractions", "place", "places",
            "destination", "destinations", "tourist spot", "tourist spots",
        )
    )
    asks_for_ranking = any(
        term in q for term in (
            "most", "highest", "top", "maximum", "largest",
            "number of", "how many", "rank", "ranking", "more",
        )
    )

    return mentions_countries and mentions_attractions and asks_for_ranking


def answer(question, model_name=OLLAMA_MODEL):
    """Route analytical questions to pandas and descriptive questions to RAG."""

    # IMPORTANT: analytical questions are handled before RAG/Ollama.
    if is_country_ranking_question(question):
        return answer_analytics(question)

    import ollama

    context_records = retrieve(question)

    if not context_records:
        return (
            "I could not find matching attraction records "
            "in the available travel dataset."
        )

    context = "\n\n".join(context_records)

    # Reinforce the country restriction in the generation prompt.
    country = None
    try:
        _, records = load_index_data()
        country = detect_country(question, records)
    except Exception:
        pass

    country_instruction = ""
    if country:
        country_instruction = (
            f"The user specifically asked about {country}. "
            f"Only discuss attractions located in {country}. "
            "Do not include attractions from another country.\n"
        )

    prompt = (
        "Answer using only the supplied travel destination records. "
        + country_instruction
        + "If the records do not contain the answer, clearly say so. "
        "Do not invent facts or claim that this sample represents every "
        "attraction in the world.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}"
    )

    response = ollama.chat(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful travel destination research assistant. "
                    "Give accurate, concise and dataset-grounded answers."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )

    return response["message"]["content"]
