from pathlib import Path
import re
from datetime import datetime, timezone, timedelta

import pandas as pd
from google import genai

from config import GEMINI_API_KEY


# ============================================================
# CHAT WITH YOUR WEATHER - GEMINI + DATA FUSION
# ============================================================
# This version is designed for a LARGE fused Excel dataset.
#
# Instead of sending the entire Excel file to Gemini for every
# question, it:
#   1. Loads the fused data.
#   2. Detects the requested city/date when possible.
#   3. Filters the relevant rows.
#   4. Sends only the useful data to Gemini.
#
# It does NOT invent missing values.
# ============================================================


if not GEMINI_API_KEY or not GEMINI_API_KEY.strip():
    raise ValueError(
        "GEMINI_API_KEY is missing from config.py"
    )

client = genai.Client(
    api_key=GEMINI_API_KEY
)

MODEL_NAME = "gemini-3.6-flash"

BASE_DIR = Path(__file__).resolve().parent

FUSION_FILE = (
    BASE_DIR / "Weather_AirQuality_Data_Fusion.xlsx"
)


# ============================================================
# LOAD FUSED DATA
# ============================================================

def load_fused_data():
    """Load the main fused dataset from Excel."""

    if not FUSION_FILE.exists():
        raise FileNotFoundError(
            "Weather_AirQuality_Data_Fusion.xlsx was not found. "
            "Run data_fusion.py first."
        )

    df = pd.read_excel(
        FUSION_FILE,
        sheet_name="Fused_Data"
    )

    if df.empty:
        raise ValueError(
            "Fused_Data sheet is empty."
        )

    # Clean column names.
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    return df


# ============================================================
# HELPERS
# ============================================================

def find_column(df, possible_names):
    """Return the first matching column name."""

    normalized = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    for name in possible_names:
        key = name.strip().lower()

        if key in normalized:
            return normalized[key]

    # Also support partial matching.
    for column in df.columns:
        column_lower = str(column).lower()

        for name in possible_names:
            if name.lower() in column_lower:
                return column

    return None


def get_city_column(df):
    return find_column(
        df,
        [
            "City",
            "city",
            "Location",
            "location"
        ]
    )


def get_timestamp_column(df):
    return find_column(
        df,
        [
            "Timestamp",
            "timestamp",
            "DateTime",
            "Datetime",
            "Date Time",
            "Date",
            "datetime"
        ]
    )


def get_unique_cities(df):
    city_column = get_city_column(df)

    if city_column is None:
        return []

    cities = (
        df[city_column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    cities = cities[
        (cities != "")
        & (cities.str.lower() != "unknown")
        & (cities.str.lower() != "nan")
    ]

    return sorted(
        cities.unique().tolist()
    )


def detect_city(question, cities):
    """
    Detect a city from the question by matching against
    the actual cities in the fused dataset.
    """

    question_lower = question.lower()

    # Longest names first prevents short-name collisions.
    for city in sorted(
        cities,
        key=len,
        reverse=True
    ):
        if city.lower() in question_lower:
            return city

    return None


def detect_date_filter(question, df):
    """
    Detect today / tomorrow / yesterday or an explicit date.

    Returns:
        (filter_type, date_value)
    """

    timestamp_column = get_timestamp_column(df)

    if timestamp_column is None:
        return None, None

    text = question.lower()

    # Use local system date for user's computer/project run.
    today = datetime.now().date()

    if "tomorrow" in text:
        return "date", today + timedelta(days=1)

    if "today" in text:
        return "date", today

    if "yesterday" in text:
        return "date", today - timedelta(days=1)

    # Match YYYY-MM-DD.
    match = re.search(
        r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b",
        question
    )

    if match:
        try:
            date_value = datetime(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3))
            ).date()

            return "date", date_value

        except ValueError:
            pass

    return None, None


def filter_relevant_data(df, question):
    """
    Filter the large fused dataset to the smallest useful
    subset without inventing values.
    """

    filtered = df.copy()

    cities = get_unique_cities(filtered)

    selected_city = detect_city(
        question,
        cities
    )

    city_column = get_city_column(filtered)

    if (
        selected_city is not None
        and city_column is not None
    ):
        filtered = filtered[
            filtered[city_column]
            .astype(str)
            .str.strip()
            .str.lower()
            == selected_city.lower()
        ]

    date_filter_type, target_date = (
        detect_date_filter(
            question,
            filtered
        )
    )

    timestamp_column = get_timestamp_column(
        filtered
    )

    if (
        date_filter_type == "date"
        and target_date is not None
        and timestamp_column is not None
    ):

        parsed_timestamp = pd.to_datetime(
            filtered[timestamp_column],
            errors="coerce"
        )

        filtered = filtered[
            parsed_timestamp.dt.date
            == target_date
        ].copy()

    # If a city/date-specific filter produced no rows,
    # return the original data only when necessary.
    # This prevents Gemini from receiving misleading data.
    if filtered.empty:

        if selected_city is not None:
            return (
                filtered,
                selected_city,
                target_date
            )

        return (
            df.head(2000).copy(),
            None,
            target_date
        )

    # Keep the context manageable.
    # For a large dataset, use the most recent rows.
    if timestamp_column is not None:

        parsed = pd.to_datetime(
            filtered[timestamp_column],
            errors="coerce"
        )

        filtered = (
            filtered.assign(
                __parsed_timestamp=parsed
            )
            .sort_values(
                "__parsed_timestamp",
                ascending=False
            )
            .drop(
                columns=["__parsed_timestamp"]
            )
        )

    # Limit rows sent to Gemini while preserving
    # real project data.
    MAX_CONTEXT_ROWS = 250

    filtered = filtered.head(
        MAX_CONTEXT_ROWS
    )

    return (
        filtered,
        selected_city,
        target_date
    )


def create_data_context(df):
    """
    Convert filtered fused data into compact text.

    Only real values from the Excel data are used.
    """

    if df.empty:
        return "NO MATCHING PROJECT DATA FOUND."

    # Keep missing values explicit rather than inventing them.
    clean_df = df.copy()

    clean_df = clean_df.fillna("Not available")

    return clean_df.to_string(
        index=False
    )


# ============================================================
# GEMINI RESPONSE
# ============================================================

def ask_weather(
    question: str,
    extra_context: str = ""
) -> str:
    """
    Answer a user's weather / air-quality question using
    real project fusion data.
    """

    fused_df = load_fused_data()

    relevant_df, selected_city, target_date = (
        filter_relevant_data(
            fused_df,
            question
        )
    )

    data_context = create_data_context(
        relevant_df
    )

    cities_available = get_unique_cities(
        fused_df
    )

    date_note = ""

    if target_date is not None:
        date_note = (
            f"\nRequested date: {target_date.isoformat()}"
        )

    city_note = ""

    if selected_city:
        city_note = (
            f"\nDetected city: {selected_city}"
        )

    prompt = f"""
You are the AI assistant for a project called
"Real-Time Weather Monitoring System".

The application provides an LLM feature called
"Chat with Your Weather".

Use ONLY the project data supplied below for factual
answers about weather, air quality, traffic, satellite
observations, predictions, and weather alerts.

PROJECT DATA:
{data_context}

PROJECT INFORMATION:
- Available fused cities: {len(cities_available)}
- Requested user question: {question}
{city_note}
{date_note}

ADDITIONAL PROJECT CONTEXT:
{extra_context}

IMPORTANT RULES:

1. Prefer the supplied project data over general knowledge.
2. Never invent a value that is not present in the project data.
3. Never convert "Not available" into a guessed value.
4. Clearly say when the requested information is not
   available in the supplied data.
5. Distinguish current PM2.5 from predicted PM2.5.
6. Distinguish ground-level PM2.5 from satellite NO2.
7. Distinguish live/current weather from forecast data.
8. Treat "No active weather alerts" as a valid result when
   that exact information is present.
9. When comparing cities, use only actual values from the
   supplied project data.
10. If the user asks about "today" or "tomorrow", answer
    only if the dataset contains records for that date.
11. Do not claim that a tomorrow forecast exists unless
    forecast data is actually present.
12. Give the answer in a simple, understandable format.
13. Mention the relevant city and date when applicable.

USER QUESTION:
{question}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response or not getattr(
        response,
        "text",
        None
    ):
        return (
            "Gemini did not return a text response."
        )

    return response.text


# ============================================================
# COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print(
        "CHAT WITH YOUR WEATHER - "
        "GEMINI + DATA FUSION"
    )
    print("=" * 80)

    try:

        fused_df = load_fused_data()

        cities = get_unique_cities(
            fused_df
        )

        print(
            "\nFused data loaded successfully."
        )

        print(
            f"Total fused rows: "
            f"{len(fused_df):,}"
        )

        print(
            f"Cities available: "
            f"{len(cities)}"
        )

        print(
            f"Columns available: "
            f"{len(fused_df.columns)}"
        )

        print(
            f"Excel file: "
            f"{FUSION_FILE.name}"
        )

        question = input(
            "\nAsk a weather or air-quality "
            "question: "
        ).strip()

        if not question:

            print(
                "Please enter a question."
            )

            raise SystemExit(1)

        print(
            "\nFiltering relevant project data..."
        )

        answer = ask_weather(
            question
        )

        print("\n" + "=" * 80)
        print("AI RESPONSE")
        print("=" * 80)

        print(
            "\n" + answer
        )

        print("\n" + "=" * 80)
        print(
            "GEMINI + DATA FUSION "
            "TEST SUCCESSFUL"
        )
        print("=" * 80)

    except Exception as exc:

        print("\n" + "=" * 80)
        print("GEMINI DATA-FUSION ERROR")
        print("=" * 80)

        print(
            "\n",
            exc
        )