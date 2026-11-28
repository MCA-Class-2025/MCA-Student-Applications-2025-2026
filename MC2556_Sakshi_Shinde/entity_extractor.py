"""
Smart entity extraction for DocuMind AI.
Detects persons, organizations, locations, financial terms, technologies, and dates
from document text and user queries to drive automatic API routing.
"""

import re
from typing import Any

# --- Known entity dictionaries for high-confidence matching ---

KNOWN_LOCATIONS = {
    "mumbai", "delhi", "bangalore", "bengaluru", "chennai", "kolkata", "hyderabad",
    "pune", "ahmedabad", "jaipur", "lucknow", "new york", "london", "paris", "tokyo",
    "beijing", "shanghai", "singapore", "dubai", "sydney", "melbourne", "toronto",
    "vancouver", "chicago", "los angeles", "san francisco", "boston", "seattle",
    "washington", "miami", "berlin", "munich", "frankfurt", "moscow", "dubai",
    "hong kong", "seoul", "mumbai", "cairo", "nairobi", "mumbai", "india", "usa",
    "united states", "united kingdom", "germany", "france", "japan", "china",
}

KNOWN_ORGANIZATIONS = {
    "microsoft", "google", "apple", "amazon", "meta", "facebook", "ibm", "oracle",
    "tesla", "netflix", "nvidia", "intel", "samsung", "sony", "walmart", "jpmorgan",
    "goldman sachs", "morgan stanley", "hsbc", "barclays", "citibank", "wells fargo",
    "world bank", "imf", "united nations", "who", "nasa", "spacex", "openai",
    "anthropic", "tcs", "infosys", "wipro", "reliance", "tata", "hdfc", "icici",
    "sbi", "reserve bank", "rbi", "sebi", "federal reserve", "ecb",
}

KNOWN_TECHNOLOGIES = {
    "artificial intelligence", "machine learning", "deep learning", "neural network",
    "blockchain", "cryptocurrency", "bitcoin", "cloud computing", "quantum computing",
    "internet of things", "iot", "big data", "data science", "natural language processing",
    "nlp", "computer vision", "robotics", "cybersecurity", "5g", "api", "rag",
    "transformer", "llm", "large language model", "generative ai", "faiss", "embeddings",
}

FINANCIAL_TERMS = {
    "loan", "credit score", "interest rate", "mortgage", "investment", "stock market",
    "bond", "equity", "debt", "inflation", "gdp", "recession", "bankruptcy",
    "portfolio", "dividend", "capital", "revenue", "profit", "loss", "audit",
    "financial risk", "creditworthiness", "collateral", "underwriting", "fintech",
    "annual income", "debt to income", "loan approval", "credit card", "savings",
}

NEWS_TOPIC_KEYWORDS = {
    "company", "companies", "finance", "economy", "economic", "technology", "tech",
    "politics", "political", "global", "market", "stock", "trade", "government",
    "policy", "regulation", "startup", "industry", "business", "corporate",
}

WEATHER_KEYWORDS = {
    "weather", "temperature", "rain", "rainfall", "climate", "forecast", "humidity",
    "storm", "cyclone", "heatwave", "snow", "wind", "sunny", "cloudy",
}

WIKIPEDIA_CONCEPT_KEYWORDS = {
    "disease", "virus", "pandemic", "history", "historical", "science", "scientific",
    "theory", "philosophy", "biology", "physics", "chemistry", "mathematics",
    "revolution", "war", "treaty", "invention", "discovery", "algorithm",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _find_keyword_matches(text: str, keywords: set[str]) -> list[str]:
    """Return keyword phrases found in normalized text."""
    normalized = _normalize(text)
    matches = []
    for kw in sorted(keywords, key=len, reverse=True):
        if kw in normalized:
            matches.append(kw.title() if len(kw) > 3 else kw.upper())
    return list(dict.fromkeys(matches))


def _extract_capitalized_phrases(text: str) -> list[str]:
    """Extract multi-word capitalized phrases (potential org/person names)."""
    pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b"
    return list(dict.fromkeys(re.findall(pattern, text)))


def _extract_dates(text: str) -> list[str]:
    """Extract common date patterns from text."""
    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b",
        r"\b\d{4}\b",
    ]
    dates = []
    for pat in patterns:
        dates.extend(re.findall(pat, text, flags=re.IGNORECASE))
    return list(dict.fromkeys(dates))[:20]


def extract_entities(document_text: str = "", user_query: str = "") -> dict[str, Any]:
    """
    Extract entities from document text and/or user query.
    Returns structured entity buckets used by the API router.
    """
    combined = f"{document_text or ''} {user_query or ''}".strip()
    if not combined:
        return {
            "persons": [],
            "organizations": [],
            "locations": [],
            "financial_terms": [],
            "technologies": [],
            "dates": [],
            "concepts": [],
            "all_entities": [],
        }

    # Location detection: known cities + "in/at/from <Capitalized>" patterns
    locations = _find_keyword_matches(combined, KNOWN_LOCATIONS)
    loc_pattern = re.findall(
        r"\b(?:in|at|from|near|to)\s+([A-Z][a-zA-Z\s]{2,25})\b",
        combined,
    )
    for loc in loc_pattern:
        cleaned = loc.strip()
        if len(cleaned) > 2 and cleaned.lower() not in {"the", "this", "that"}:
            locations.append(cleaned)

    # Organization & technology from dictionaries + capitalized phrases
    organizations = _find_keyword_matches(combined, KNOWN_ORGANIZATIONS)
    technologies = _find_keyword_matches(combined, KNOWN_TECHNOLOGIES)
    financial_terms = _find_keyword_matches(combined, FINANCIAL_TERMS)

    capitalized = _extract_capitalized_phrases(combined)
    for phrase in capitalized:
        lower = phrase.lower()
        if lower in KNOWN_ORGANIZATIONS and phrase not in organizations:
            organizations.append(phrase)
        elif lower not in {loc.lower() for loc in locations}:
            # Treat unknown capitalized phrases as potential org/person
            if any(suffix in lower for suffix in ("inc", "corp", "ltd", "llc", "bank", "group")):
                organizations.append(phrase)

    # Person names: two consecutive capitalized words not already classified
    persons = []
    person_pattern = r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b"
    for match in re.findall(person_pattern, combined):
        if match not in organizations and match not in locations:
            persons.append(match)

    dates = _extract_dates(combined)

    # Wikipedia-worthy concepts
    concepts = _find_keyword_matches(combined, WIKIPEDIA_CONCEPT_KEYWORDS)
    concepts.extend(organizations[:3])
    concepts.extend(technologies[:3])
    concepts = list(dict.fromkeys(concepts))

    all_entities = list(dict.fromkeys(
        persons + organizations + locations + financial_terms + technologies + dates + concepts
    ))

    return {
        "persons": persons[:15],
        "organizations": organizations[:15],
        "locations": locations[:15],
        "financial_terms": financial_terms[:15],
        "technologies": technologies[:15],
        "dates": dates[:15],
        "concepts": concepts[:15],
        "all_entities": all_entities[:30],
    }


def has_news_relevant_content(text: str) -> bool:
    """Check if text discusses news-worthy topics."""
    normalized = _normalize(text)
    return any(kw in normalized for kw in NEWS_TOPIC_KEYWORDS)


def has_weather_relevant_content(text: str, user_query: str = "") -> bool:
    """Check if weather API should be considered."""
    combined = _normalize(f"{text} {user_query}")
    if any(kw in combined for kw in WEATHER_KEYWORDS):
        return True
    entities = extract_entities(text, user_query)
    return len(entities["locations"]) > 0


def get_wikipedia_search_terms(entities: dict[str, Any]) -> list[str]:
    """Pick best Wikipedia search terms from extracted entities."""
    terms = []
    for key in ("organizations", "technologies", "concepts", "persons"):
        terms.extend(entities.get(key, []))
    return list(dict.fromkeys(terms))[:3]


def get_news_search_terms(entities: dict[str, Any], user_query: str) -> list[str]:
    """Pick best NewsAPI search terms."""
    terms = []
    terms.extend(entities.get("organizations", [])[:2])
    terms.extend(entities.get("technologies", [])[:1])
    terms.extend(entities.get("financial_terms", [])[:1])
    if user_query.strip():
        terms.append(user_query.strip()[:80])
    return list(dict.fromkeys(terms))[:2] or ["technology"]


def get_weather_cities(entities: dict[str, Any]) -> list[str]:
    """Return location names suitable for OpenWeather lookup."""
    cities = []
    for loc in entities.get("locations", []):
        # Use first word for multi-word known locations when appropriate
        city = loc.split(",")[0].strip()
        if city and len(city) > 2:
            cities.append(city)
    return list(dict.fromkeys(cities))[:2]
