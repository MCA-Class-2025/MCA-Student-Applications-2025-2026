"""
Emotion detection using your existing trained TF-IDF + sklearn
model (emotion_model/emotion_model.pkl + tfidf_vectorizer.pkl).
"""

import pickle
from functools import lru_cache

from .config import EMOTION_LABELS

EMOTION_MODEL_PATH = "emotion_model/emotion_model.pkl"
TFIDF_PATH = "emotion_model/tfidf_vectorizer.pkl"


@lru_cache(maxsize=1)
def _load_emotion_model():
    with open(EMOTION_MODEL_PATH, "rb") as file:
        emotion_model = pickle.load(file)

    with open(TFIDF_PATH, "rb") as file:
        tfidf_vectorizer = pickle.load(file)

    return emotion_model, tfidf_vectorizer


def detect_emotion(text: str) -> dict:
    """Returns {"emotion": str, "score": float}."""

    if not text or not text.strip():
        return {"emotion": "neutral", "score": 0.0}

    emotion_model, tfidf_vectorizer = _load_emotion_model()

    text_vector = tfidf_vectorizer.transform([text])
    predicted_label = emotion_model.predict(text_vector)[0]
    probabilities = emotion_model.predict_proba(text_vector)[0]
    confidence = float(max(probabilities))

    emotion = EMOTION_LABELS.get(int(predicted_label), "neutral")

    return {"emotion": emotion, "score": confidence}
