from pathlib import Path

import joblib
from langdetect import detect, DetectorFactory


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_FILE = (
    PROJECT_ROOT
    / "models"
    / "fake_news_model.pkl"
)

VECTORIZER_FILE = (
    PROJECT_ROOT
    / "models"
    / "tfidf_vectorizer.pkl"
)


# ============================================================
# LANGUAGE DETECTION SETTINGS
# ============================================================

# Makes language detection reproducible
DetectorFactory.seed = 42


SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi"
}


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading ML model...")

model = joblib.load(
    MODEL_FILE
)

vectorizer = joblib.load(
    VECTORIZER_FILE
)

print("ML model loaded successfully.")


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_language(text):

    try:

        detected_code = detect(text)

        language = SUPPORTED_LANGUAGES.get(
            detected_code
        )

        if language is None:

            return {
                "code": detected_code,
                "language": "Unsupported"
            }

        return {
            "code": detected_code,
            "language": language
        }

    except Exception:

        return {
            "code": None,
            "language": "Unknown"
        }


# ============================================================
# NEWS PREDICTION
# ============================================================

def predict_news(text):

    text = str(text).strip()

    if not text:

        return {
            "language": "Unknown",
            "prediction": "Unknown",
            "confidence": 0
        }


    # --------------------------------------------------------
    # DETECT LANGUAGE
    # --------------------------------------------------------

    language_result = detect_language(
        text
    )

    language = language_result["language"]


    # --------------------------------------------------------
    # CHECK SUPPORTED LANGUAGE
    # --------------------------------------------------------

    if language == "Unsupported":

        return {
            "language": "Unsupported",
            "prediction": "Unsupported",
            "confidence": 0
        }


    if language == "Unknown":

        return {
            "language": "Unknown",
            "prediction": "Unknown",
            "confidence": 0
        }


    # --------------------------------------------------------
    # TF-IDF TRANSFORMATION
    # --------------------------------------------------------

    text_vector = vectorizer.transform(
        [text]
    )


    # --------------------------------------------------------
    # ML PREDICTION
    # --------------------------------------------------------

    prediction = model.predict(
        text_vector
    )[0]


    # --------------------------------------------------------
    # PREDICTION PROBABILITY
    # --------------------------------------------------------

    probabilities = model.predict_proba(
        text_vector
    )[0]

    classes = model.classes_


    predicted_index = list(
        classes
    ).index(
        prediction
    )


    confidence = (
        probabilities[predicted_index]
        * 100
    )


    # --------------------------------------------------------
    # CONFIDENCE LEVEL
    # --------------------------------------------------------

    if confidence >= 90:

        confidence_level = "High"

    elif confidence >= 70:

        confidence_level = "Medium"

    else:

        confidence_level = "Low"


    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    return {

        "language": language,

        "prediction": prediction,

        "confidence": round(
            confidence,
            2
        ),

        "confidence_level":
            confidence_level
    }


# ============================================================
# COMMAND LINE TEST
# ============================================================

if __name__ == "__main__":

    print("\n====================================")
    print(" MULTILINGUAL NEWS PREDICTION")
    print("====================================")


    news = input(
        "\nEnter news article/claim:\n"
    )


    result = predict_news(
        news
    )


    print("\n====================================")
    print("RESULT")
    print("====================================")


    print(
        "Detected Language:",
        result["language"]
    )


    print(
        "Prediction:",
        result["prediction"]
    )


    print(
        "Confidence:",
        f'{result["confidence"]}%'
    )


    if "confidence_level" in result:

        print(
            "Confidence Level:",
            result["confidence_level"]
        )