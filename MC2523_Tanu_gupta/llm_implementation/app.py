import os
import csv
import json
import re
import requests
import warnings

from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.exceptions import InconsistentVersionWarning

from google import genai

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


# =========================================================
# CONFIGURATION
# =========================================================

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

GEMINI_MODEL = "gemini-3.6-flash"

# Spring Boot Weather Application
SPRING_BOOT_URL = "http://localhost:8090"

LLM_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = LLM_DIR.parent
VECTORSTORE_PATH = str(LLM_DIR / "vectorstore")
FUSED_DATA_CSV = str(
    PROJECT_ROOT / "dataset" / "processed" / "fused_weather_data.csv"
)
MODELS_DIR = PROJECT_ROOT / "ml_algorithm" / "results" / "models"
MODEL_METADATA_PATH = (
    PROJECT_ROOT / "ml_algorithm" / "results" / "metrics" / "model_metadata.json"
)

CLASSIFICATION_FEATURES = [
    "current_temperature_celsius",
    "historical_average_celsius",
    "historical_min_celsius",
    "historical_max_celsius",
    "current_humidity_percent",
    "current_wind_speed_kmh",
    "historical_records_used"
]

REGRESSION_FEATURES = [
    "historical_average_celsius",
    "historical_min_celsius",
    "historical_max_celsius",
    "current_humidity_percent",
    "current_wind_speed_kmh",
    "historical_records_used"
]

CLASSIFICATION_MODELS = {
    "Naive Bayes": "naive_bayes.joblib",
    "SVM": "svm.joblib",
    "Decision Tree": "decision_tree.joblib",
    "Random Forest": "random_forest.joblib",
    "Logistic Regression": "logistic_regression.joblib"
}

REGRESSION_MODELS = {
    "Regression Analysis (Simple Linear Regression)": (
        "regression_analysis_(simple_linear_regression).joblib",
        ["historical_average_celsius"]
    ),
    "Multiple Linear Regression": (
        "multiple_linear_regression.joblib",
        REGRESSION_FEATURES
    ),
    "Polynomial Regression": (
        "polynomial_regression.joblib",
        ["historical_average_celsius"]
    )
}

SUPPORTED_CITIES = [
    "New Delhi", "Bangalore", "Bengaluru", "Ahmedabad",
    "Chandigarh", "Hyderabad", "Kolkata", "Lucknow",
    "Mumbai", "Chennai", "Jaipur", "Nagpur", "Bhopal",
    "Indore", "Surat", "Patna", "Pune", "Delhi",
    "Thane", "Andheri", "Malad"
]

COUNTRY_NAMES = {
    "india": "India",
    "bharat": "India"
}

HISTORICAL_CITY_ALIASES = {
    "bengaluru": "Bangalore",
    "new delhi": "Delhi"
}


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found"
    )


# =========================================================
# CREATE GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=api_key
)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="AI Weather RAG API",
    description="Weather Question Answering API using RAG, Data Fusion and CSV Storage",
    version="3.0"
)


# =========================================================
# CORS CONFIGURATION
# =========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"],
)


# =========================================================
# LOAD EMBEDDING MODEL
# =========================================================

print("Loading embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)

print("Embedding model loaded.")


# =========================================================
# LOAD FAISS VECTOR DATABASE
# =========================================================

print("Loading FAISS vector database...")

vectorstore = FAISS.load_local(
    VECTORSTORE_PATH,
    embeddings,
    allow_dangerous_deserialization=True
)

print("FAISS loaded successfully.")


# =========================================================
# CREATE RETRIEVER
# =========================================================

retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 5
    }
)


# =========================================================
# REQUEST DTO
# =========================================================

class WeatherQuestion(BaseModel):

    question: str
    previous_context: str | None = None


class WeatherCapture(BaseModel):

    city: str


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
def home():

    return {
        "message":
            "AI Weather RAG API with Data Fusion and CSV Storage is running"
    }


# =========================================================
# EXTRACT CITY FROM QUESTION
# =========================================================

def extract_city(question):

    """
    Attempts to identify the city from the user's question.
    """
    matched_cities = extract_cities(question)
    if matched_cities:
        return matched_cities[0]
    if extract_country(question):
        return None

    location_match = re.search(
        r"\b(?:in|for|at)\s+([A-Za-z][A-Za-z .'-]*?)"
        r"(?=\s+(?:compared|against|relative|today|tonight|now|"
        r"currently|historical|history|weather|temperature)\b|[?.!,]|$)",
        question,
        re.IGNORECASE
    )

    if location_match:
        candidate = location_match.group(1).strip()
        if candidate.casefold() not in COUNTRY_NAMES:
            return candidate.title()

    return None


def extract_country(question):
    for country_name, display_name in COUNTRY_NAMES.items():
        if re.search(
            rf"\b{re.escape(country_name)}\b",
            question,
            re.IGNORECASE
        ):
            return display_name
    return None


def extract_cities(question):
    city_lookup = {city.casefold(): city for city in SUPPORTED_CITIES}
    city_pattern = re.compile(
        r"\b("
        + "|".join(
            re.escape(city)
            for city in sorted(SUPPORTED_CITIES, key=len, reverse=True)
        )
        + r")\b",
        re.IGNORECASE
    )
    return list(dict.fromkeys(
        city_lookup[match.group(1).casefold()]
        for match in city_pattern.finditer(question)
    ))


def get_model_insights(current_weather, historical_statistics):
    if "temperature_celsius" not in current_weather:
        return {
            "available": False,
            "reason": "Live weather is required to prepare model inputs.",
            "classification": None,
            "regression": None
        }

    if not historical_statistics.get("historical_temperature_available"):
        return {
            "available": False,
            "reason": "Historical statistics are required to prepare model inputs.",
            "classification": None,
            "regression": None
        }

    row = {
        "current_temperature_celsius":
            current_weather["temperature_celsius"],
        "historical_average_celsius":
            historical_statistics["average_temperature_celsius"],
        "historical_min_celsius":
            historical_statistics["minimum_temperature_celsius"],
        "historical_max_celsius":
            historical_statistics["maximum_temperature_celsius"],
        "current_humidity_percent":
            current_weather["humidity_percent"],
        "current_wind_speed_kmh":
            current_weather["wind_speed_kmh"],
        "historical_records_used":
            historical_statistics["number_of_values"]
    }

    training_records = None
    if MODEL_METADATA_PATH.exists():
        with MODEL_METADATA_PATH.open(encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
        training_records = metadata.get("dataset_rows")

    sample_warning = None
    if training_records is None:
        sample_warning = (
            "Training size is unknown. Retrain the models to record model "
            "metadata before relying on predictions."
        )
    elif training_records < 50:
        sample_warning = (
            f"Exploratory only: trained on {training_records} fused records; "
            "more varied observations are needed for reliable predictions."
        )

    model_frame = pd.DataFrame([row])
    classification_votes = []
    regression_predictions = []
    model_errors = []

    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always", InconsistentVersionWarning)
        for name, filename in CLASSIFICATION_MODELS.items():
            model_path = MODELS_DIR / filename
            if not model_path.exists():
                continue
            try:
                model = joblib.load(model_path)
                if list(getattr(model, "feature_names_in_", [])) != CLASSIFICATION_FEATURES:
                    model_errors.append(f"{name}: model features do not match fused data.")
                    continue
                prediction = str(model.predict(model_frame[CLASSIFICATION_FEATURES])[0])
                classification_votes.append({
                    "algorithm": name,
                    "prediction": prediction
                })
            except (AttributeError, ImportError, OSError, ValueError) as error:
                model_errors.append(f"{name}: {error}")

        for name, (filename, model_features) in REGRESSION_MODELS.items():
            model_path = MODELS_DIR / filename
            if not model_path.exists():
                continue
            try:
                model = joblib.load(model_path)
                if list(getattr(model, "feature_names_in_", [])) != model_features:
                    model_errors.append(f"{name}: model features do not match fused data.")
                    continue
                value = float(model.predict(model_frame[model_features])[0])
                regression_predictions.append({
                    "algorithm": name,
                    "temperature_celsius": round(value, 2)
                })
            except (AttributeError, ImportError, OSError, ValueError) as error:
                model_errors.append(f"{name}: {error}")

    if caught_warnings:
        model_errors.append(
            "One or more model files were created with a different scikit-learn "
            "version; retrain them in the AI service environment."
        )

    classification = None
    if classification_votes:
        vote_counts = pd.Series(
            [item["prediction"] for item in classification_votes]
        ).value_counts()
        winning_condition = str(vote_counts.index[0])
        agreement = int(vote_counts.iloc[0])
        classification = {
            "predicted_condition": winning_condition,
            "model_agreement_percent": round(
                agreement / len(classification_votes) * 100,
                1
            ),
            "models_used": classification_votes
        }

    regression = None
    if regression_predictions:
        selected = next(
            (
                item for item in regression_predictions
                if item["algorithm"] == "Multiple Linear Regression"
            ),
            regression_predictions[0]
        )
        regression = {
            "predicted_temperature_celsius":
                selected["temperature_celsius"],
            "selected_model": selected["algorithm"],
            "models_used": regression_predictions
        }

    return {
        "available": classification is not None or regression is not None,
        "training_records": training_records,
        "reliability": "low" if sample_warning or model_errors else "unassessed",
        "warning": sample_warning,
        "model_errors": model_errors,
        "classification": classification,
        "regression": regression
    }


def get_city_trend(city):
    if not city or not os.path.isfile(FUSED_DATA_CSV):
        return {"city": city, "records": [], "reason": "No city history is available."}

    with open(FUSED_DATA_CSV, newline="", encoding="utf-8") as csv_file:
        rows = [
            row for row in csv.DictReader(csv_file)
            if row.get("city", "").strip().casefold() == city.casefold()
            and row.get("timestamp")
            and row.get("current_temperature_celsius")
        ]

    rows = rows[-20:]
    return {
        "city": city,
        "records": [
            {
                "timestamp": row["timestamp"],
                "current_temperature_celsius":
                    float(row["current_temperature_celsius"]),
                "historical_average_celsius":
                    float(row["historical_average_celsius"])
                    if row.get("historical_average_celsius") else None
            }
            for row in rows
        ],
        "reason": None if rows else "No saved observations for this city yet."
    }


# =========================================================
# GET CURRENT WEATHER
# =========================================================

def get_current_weather(city):

    """
    Calls the existing Spring Boot weather API.

    GET http://localhost:8090/weather/{city}
    """

    try:

        url = (
            SPRING_BOOT_URL
            + "/weather/"
            + city
        )

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code != 200:

            print(
                "Spring Boot returned:",
                response.status_code
            )

            return None

        return response.json()

    except Exception as e:

        print(
            "Current weather API error:",
            e
        )

        return None


# =========================================================
# NORMALIZE CURRENT WEATHER
# =========================================================

def normalize_current_weather(data):

    """
    Converts the Spring Boot/OpenWeather
    response into a simpler structure.
    """

    if not data:

        return {
            "status":
                "Current weather data unavailable"
        }

    try:

        wind_speed_mps = data["wind"]["speed"]

        wind_speed_kmh = (
            wind_speed_mps * 3.6
        )

        return {

            "city":
                data.get(
                    "name",
                    "Unknown"
                ),

            "temperature_celsius":
                round(
                    float(data["main"]["temp"]),
                    2
                ),

            "humidity_percent":
                round(
                    float(data["main"]["humidity"]),
                    2
                ),

            "wind_speed_mps":
                round(
                    float(wind_speed_mps),
                    2
                ),

            "wind_speed_kmh":
                round(
                    float(wind_speed_kmh),
                    2
                ),

            "weather_condition":
                data["weather"][0]["main"],

            "weather_description":
                data["weather"][0]["description"]

        }

    except Exception as e:

        print(
            "Error normalizing weather:",
            e
        )

        return {
            "status":
                "Unable to process current weather data"
        }


# =========================================================
# RETRIEVE HISTORICAL WEATHER
# =========================================================

def get_historical_weather(question, city=None):

    """
    Retrieves relevant historical weather
    documents from FAISS.
    """

    try:

        if city:
            historical_city = HISTORICAL_CITY_ALIASES.get(
                city.casefold(),
                city
            )
            documents = vectorstore.similarity_search(
                question,
                k=5,
                filter={"city": historical_city}
            )
        else:
            documents = retriever.invoke(question)

        return documents

    except Exception as e:

        print(
            "Historical retrieval error:",
            e
        )

        return []


# =========================================================
# CREATE HISTORICAL CONTEXT
# =========================================================

def create_historical_context(documents):

    if not documents:

        return "No historical weather data found."

    context = "\n\n".join(

        document.page_content

        for document in documents

    )

    return context


# =========================================================
# EXTRACT TEMPERATURES FROM HISTORICAL DATA
# =========================================================

def extract_historical_temperatures(
        documents
):

    """
    Extracts maximum and minimum temperatures
    from retrieved historical weather documents.
    """

    max_temperatures = []

    min_temperatures = []

    for document in documents:

        text = document.page_content

        max_matches = re.findall(

            r"Maximum temperature:\s*([-+]?\d*\.?\d+)",

            text,

            re.IGNORECASE

        )

        min_matches = re.findall(

            r"Minimum temperature:\s*([-+]?\d*\.?\d+)",

            text,

            re.IGNORECASE

        )


        for value in max_matches:

            try:

                max_temperatures.append(
                    float(value)
                )

            except ValueError:

                pass


        for value in min_matches:

            try:

                min_temperatures.append(
                    float(value)
                )

            except ValueError:

                pass


    return (
        max_temperatures,
        min_temperatures
    )


# =========================================================
# CALCULATE HISTORICAL STATISTICS
# =========================================================

def calculate_historical_statistics(
        documents
):

    """
    Calculates historical temperature statistics
    from retrieved documents.
    """

    max_temperatures, min_temperatures = (
        extract_historical_temperatures(
            documents
        )
    )


    all_temperatures = (
        max_temperatures
        +
        min_temperatures
    )


    if not all_temperatures:

        return {

            "historical_temperature_available":
                False,

            "average_temperature_celsius":
                None,

            "minimum_temperature_celsius":
                None,

            "maximum_temperature_celsius":
                None,

            "number_of_values":
                0

        }


    average_temperature = (
        sum(all_temperatures)
        /
        len(all_temperatures)
    )


    return {

        "historical_temperature_available":
            True,

        "average_temperature_celsius":
            round(
                average_temperature,
                2
            ),

        "minimum_temperature_celsius":
            round(
                min(all_temperatures),
                2
            ),

        "maximum_temperature_celsius":
            round(
                max(all_temperatures),
                2
            ),

        "number_of_values":
            len(all_temperatures)

    }


# =========================================================
# PERFORM TEMPERATURE COMPARISON
# =========================================================

def calculate_temperature_comparison(
        current_weather,
        historical_statistics
):

    """
    Compares current temperature
    with historical average temperature.
    """

    if (
        not current_weather
        or "temperature_celsius" not in current_weather
    ):

        return {

            "comparison_generated":
                False,

            "reason":
                "Current weather unavailable"

        }


    if (
        not historical_statistics
        or
        not historical_statistics[
            "historical_temperature_available"
        ]
    ):

        return {

            "comparison_generated":
                False,

            "reason":
                "Historical temperature unavailable"

        }


    current_temperature = (
        current_weather[
            "temperature_celsius"
        ]
    )


    historical_average = (
        historical_statistics[
            "average_temperature_celsius"
        ]
    )


    difference = (
        current_temperature
        -
        historical_average
    )


    if difference > 0:

        status = (
            "above historical average"
        )

    elif difference < 0:

        status = (
            "below historical average"
        )

    else:

        status = (
            "equal to historical average"
        )


    return {

        "comparison_generated":
            True,

        "current_temperature_celsius":
            round(
                current_temperature,
                2
            ),

        "historical_average_celsius":
            round(
                historical_average,
                2
            ),

        "difference_celsius":
            round(
                difference,
                2
            ),

        "status":
            status

    }


# =========================================================
# DATA FUSION
# =========================================================

def perform_data_fusion(
        historical_context,
        historical_statistics,
        current_weather,
        temperature_comparison
):

    """
    Combines:

    1. Historical weather data
    2. Historical statistics
    3. Current weather data
    4. Temperature comparison
    """

    return {

        "historical_data": {

            "raw_context":
                historical_context,

            "statistics":
                historical_statistics

        },

        "current_weather":
            current_weather,

        "temperature_comparison":
            temperature_comparison

    }


# =========================================================
# SAVE FUSED DATA TO CSV
# =========================================================

def save_fused_data_to_csv(
        city,
        historical_statistics,
        current_weather,
        temperature_comparison
):

    """
    Stores the processed fused weather data
    into fused_weather_data.csv.

    A new row is appended for every
    successful data fusion operation.
    """

    file_exists = os.path.isfile(
        FUSED_DATA_CSV
    )


    fieldnames = [

        "timestamp",

        "city",

        "current_temperature_celsius",

        "historical_average_celsius",

        "historical_min_celsius",

        "historical_max_celsius",

        "temperature_difference_celsius",

        "comparison_status",

        "current_humidity_percent",

        "current_wind_speed_mps",

        "current_wind_speed_kmh",

        "current_condition",

        "current_description",

        "historical_records_used"

    ]


    try:

        with open(
            FUSED_DATA_CSV,
            mode="a",
            newline="",
            encoding="utf-8"
        ) as csv_file:


            writer = csv.DictWriter(

                csv_file,

                fieldnames=fieldnames

            )


            # Write header only once
            if not file_exists:

                writer.writeheader()


            writer.writerow({

                "timestamp":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "city":
                    city or "-",

                "current_temperature_celsius":
                    (
                        current_weather.get(
                            "temperature_celsius"
                        )
                        if current_weather
                        else None
                    ),

                "historical_average_celsius":
                    historical_statistics.get(
                        "average_temperature_celsius"
                    ),

                "historical_min_celsius":
                    historical_statistics.get(
                        "minimum_temperature_celsius"
                    ),

                "historical_max_celsius":
                    historical_statistics.get(
                        "maximum_temperature_celsius"
                    ),

                "temperature_difference_celsius":
                    temperature_comparison.get(
                        "difference_celsius"
                    ),

                "comparison_status":
                    temperature_comparison.get(
                        "status"
                    ),

                "current_humidity_percent":
                    (
                        current_weather.get(
                            "humidity_percent"
                        )
                        if current_weather
                        else None
                    ),

                "current_wind_speed_mps":
                    (
                        current_weather.get(
                            "wind_speed_mps"
                        )
                        if current_weather
                        else None
                    ),

                "current_wind_speed_kmh":
                    (
                        current_weather.get(
                            "wind_speed_kmh"
                        )
                        if current_weather
                        else None
                    ),

                "current_condition":
                    (
                        current_weather.get(
                            "weather_condition"
                        )
                        if current_weather
                        else None
                    ),

                "current_description":
                    (
                        current_weather.get(
                            "weather_description"
                        )
                        if current_weather
                        else None
                    ),

                "historical_records_used":
                    historical_statistics.get(
                        "number_of_values"
                    )

            })


        print(
            "Fused data saved to:",
            FUSED_DATA_CSV
        )


        return True


    except Exception as e:

        print(
            "CSV storage error:",
            e
        )

        return False


# =========================================================
# CAPTURE LIVE WEATHER LOOKUPS
# =========================================================

@app.post("/capture")
def capture_weather(request: WeatherCapture):

    city = request.city.strip()
    if not city:
        raise HTTPException(
            status_code=400,
            detail="City cannot be empty."
        )

    current_weather_raw = get_current_weather(city)
    current_weather = normalize_current_weather(current_weather_raw)
    if "temperature_celsius" not in current_weather:
        raise HTTPException(
            status_code=502,
            detail=f"Could not retrieve live weather for {city}."
        )

    documents = get_historical_weather(f"weather in {city}", city=city)
    historical_statistics = calculate_historical_statistics(documents)
    temperature_comparison = calculate_temperature_comparison(
        current_weather,
        historical_statistics
    )

    if not save_fused_data_to_csv(
        city,
        historical_statistics,
        current_weather,
        temperature_comparison
    ):
        raise HTTPException(
            status_code=500,
            detail="Live weather was retrieved, but the fused record could not be saved."
        )

    return {
        "recorded": True,
        "city": current_weather.get("city", city)
    }


# =========================================================
# ASK WEATHER QUESTION
# =========================================================

@app.post("/ask")
def ask_weather(
        request: WeatherQuestion
):

    question = request.question.strip()


    # =====================================================
    # VALIDATE QUESTION
    # =====================================================

    if not question:

        return {

            "answer":
                "Please provide a question."

        }


    print(
        "\n========================================"
    )

    print(
        "USER QUESTION:",
        question
    )


    # =====================================================
    # STEP 1 - EXTRACT CITY
    # =====================================================

    requested_cities = extract_cities(question)[:2]
    country = extract_country(question)
    if not requested_cities and country:
        return {
            "question": question,
            "city": None,
            "answer": (
                f"{country} is a country, so I need a city to look up "
                "local weather. Which city would you like?"
            ),
            "ai_status": "clarification",
            "data_fusion": {
                "historical_data_used": False,
                "current_weather_used": False,
                "comparison_generated": False,
                "csv_saved": False
            },
            "fused_data": {},
            "sources": [],
            "city_comparison": [],
            "model_insights": {
                "available": False,
                "reason": "A city is required for weather estimates."
            },
            "trend_data": {
                "city": None,
                "records": [],
                "reason": "A city is required for weather history."
            },
            "sources_and_confidence": {}
        }

    city = requested_cities[0] if requested_cities else extract_city(question)
    if not city and request.previous_context:
        city = extract_city(request.previous_context)


    print(
        "DETECTED CITY:",
        city
    )


    # =====================================================
    # STEP 2 - RETRIEVE HISTORICAL DATA
    # =====================================================

    print(
        "Retrieving historical weather data..."
    )


    city_comparison = []
    if len(requested_cities) == 2:
        documents = []
        comparison_documents = []
        for comparison_city in requested_cities:
            city_documents = get_historical_weather(
                f"Historical weather in {comparison_city}",
                city=comparison_city
            )
            comparison_documents.append(city_documents)
            city_statistics = calculate_historical_statistics(city_documents)
            raw_weather = get_current_weather(comparison_city)
            normalized_weather = normalize_current_weather(raw_weather)
            city_comparison.append({
                "city": comparison_city,
                "current_weather": normalized_weather,
                "historical_statistics": city_statistics,
                "temperature_comparison": calculate_temperature_comparison(
                    normalized_weather,
                    city_statistics
                )
            })
            documents.extend(city_documents)

        historical_context = "\n\n".join(
            f"Historical records for {item['city']}:\n"
            f"{create_historical_context(city_documents)}"
            for item, city_documents in zip(
                city_comparison,
                comparison_documents
            )
        )
        historical_statistics = city_comparison[0]["historical_statistics"]
        current_weather = city_comparison[0]["current_weather"]
    else:
        retrieval_query = (
            f"{question} weather in {city}"
            if city else question
        )
        documents = get_historical_weather(retrieval_query, city=city)
        historical_context = create_historical_context(documents)
        historical_statistics = calculate_historical_statistics(documents)

        if city:
            raw_weather = get_current_weather(city)
            current_weather = normalize_current_weather(raw_weather)
        else:
            current_weather = {
                "status": "City could not be identified from the question."
            }


    print(
        "Current weather available:",
        "temperature_celsius" in current_weather
    )


    # =====================================================
    # STEP 5 - TEMPERATURE COMPARISON
    # =====================================================

    print(
        "Calculating temperature comparison..."
    )


    temperature_comparison = (
        calculate_temperature_comparison(

            current_weather,

            historical_statistics

        )
    )


    print(
        "Temperature comparison:",
        temperature_comparison
    )


    # =====================================================
    # STEP 6 - DATA FUSION
    # =====================================================

    print(
        "Performing data fusion..."
    )


    fused_data = perform_data_fusion(

        historical_context,

        historical_statistics,

        current_weather,

        temperature_comparison

    )
    if city_comparison:
        fused_data["city_comparison"] = city_comparison


    print(
        "Data fusion completed."
    )


    # =====================================================
    # STEP 7 - SAVE FUSED DATA TO CSV
    # =====================================================

    print(
        "Saving fused data to CSV..."
    )


    csv_saved = False
    if "temperature_celsius" in current_weather:
        csv_saved = save_fused_data_to_csv(
            city,
            historical_statistics,
            current_weather,
            temperature_comparison
        )

    model_insights = get_model_insights(
        current_weather,
        historical_statistics
    )
    trend_data = get_city_trend(city)
    fused_data["model_predictions"] = model_insights
    fused_data["city_trend"] = trend_data

    with open(FUSED_DATA_CSV, newline="", encoding="utf-8") as csv_file:
        fused_observation_count = sum(1 for _ in csv.DictReader(csv_file))

    sources_and_confidence = {
        "current_weather_source": "Spring Boot / OpenWeather API",
        "historical_source": "FAISS historical weather records",
        "historical_documents_retrieved": len(documents),
        "historical_temperature_values_used":
            historical_statistics.get("number_of_values", 0),
        "model_training_records": model_insights.get("training_records"),
        "model_reliability": model_insights.get("reliability", "unavailable"),
        "model_warning": model_insights.get("warning"),
        "fused_observations_saved": fused_observation_count
    }

    # =====================================================
    # STEP 8 - CREATE GEMINI PROMPT
    # =====================================================

    prompt = f"""

You are an AI Weather Assistant.

You are part of an intelligent weather
application that uses:

1. Historical Weather Data
2. RAG
3. FAISS Vector Database
4. Live Weather API
5. Data Fusion
6. Gemini LLM

The system has fused historical weather
information with current weather information.

IMPORTANT RULES:

- Use ONLY the information provided
  in the fused weather data.

- Do NOT invent information.

- Clearly distinguish historical data
  from current weather data.

- If current weather information is
  unavailable, say so.

- If historical information is
  unavailable, say so.

- Use Celsius for temperature.

- Use mm for rainfall.

- Use km/h for wind speed.

- Current wind speed may be provided
  in m/s and km/h.

- When comparing temperatures,
  use the calculated temperature
  comparison when available.

- Clearly mention whether the current
  temperature is above, below, or equal
  to the historical average.

- Mention the difference in Celsius.

- Give a simple and understandable answer.
- Treat model predictions as estimates, never as confirmed observations.
- Explain low model reliability whenever the provided model warning is present.
- For two-city comparisons, compare only the supplied values for both cities.
- For follow-up questions, use the previous conversation context when relevant.

================ FUSED WEATHER DATA ================

{fused_data}

================ PREVIOUS CONVERSATION ================

{request.previous_context or "No previous conversation."}


================ USER QUESTION ================

{question}


================ FINAL ANSWER ================

"""


    # =====================================================
    # STEP 9 - CALL GEMINI
    # =====================================================

    print(
        "Calling Gemini..."
    )


    ai_status = "generated"
    try:

        response = client.models.generate_content(

            model=GEMINI_MODEL,

            contents=prompt

        )

        answer = response.text


    except Exception as e:

        print(
            "Gemini API error:",
            repr(e).encode("ascii", "backslashreplace").decode("ascii")
        )

        ai_status = "fallback"
        if city_comparison:
            comparison_lines = [
                (
                    f"{item['city']}: current temperature "
                    f"{item['current_weather'].get('temperature_celsius', 'unavailable')} °C; "
                    f"historical average "
                    f"{item['historical_statistics'].get('average_temperature_celsius', 'unavailable')} °C."
                )
                for item in city_comparison
            ]
            answer = (
                "Gemini is temporarily unavailable. Here is the comparison "
                "from the weather and historical data retrieved:\n\n"
                + "\n".join(comparison_lines)
            )
        elif "temperature_celsius" in current_weather:
            answer = (
                f"Gemini is temporarily unavailable. For {city}, the live "
                f"temperature is {current_weather['temperature_celsius']} °C "
                f"with {current_weather['weather_description']}. "
            )
            if temperature_comparison.get("comparison_generated"):
                answer += (
                    f"This is {temperature_comparison['difference_celsius']} °C "
                    f"{temperature_comparison['status']} "
                    f"(historical average "
                    f"{temperature_comparison['historical_average_celsius']} °C). "
                )
            if model_insights.get("available"):
                prediction = model_insights.get("classification") or {}
                estimate = model_insights.get("regression") or {}
                answer += (
                    f"Model estimates (not observations): condition "
                    f"{prediction.get('predicted_condition', 'unavailable')}, "
                    f"temperature "
                    f"{estimate.get('predicted_temperature_celsius', 'unavailable')} °C. "
                )
            answer += model_insights.get("warning") or ""
        else:
            answer = (
                "Gemini is temporarily unavailable, and live weather could "
                "not be retrieved for this location. Historical information "
                "and any available model insights are shown below."
            )


    # =====================================================
    # STEP 10 - RETURN RESPONSE
    # =====================================================

    print(
        "AI response generated."
    )


    return {

        "question":
            question,

        "city":
            city,

        "answer":
            answer,

        "ai_status":
            ai_status,

        "data_fusion": {

            "historical_data_used":
                bool(documents),

            "current_weather_used":
                current_weather is not None
                and
                "temperature_celsius"
                in current_weather,

            "comparison_generated":
                temperature_comparison.get(
                    "comparison_generated",
                    False
                ),

            "csv_saved":
                csv_saved

        },

        "fused_data":
            fused_data,

        "sources": [

            document.metadata

            for document in documents

        ],

        "city_comparison": city_comparison,

        "model_insights": model_insights,

        "trend_data": trend_data,

        "sources_and_confidence": sources_and_confidence

    }