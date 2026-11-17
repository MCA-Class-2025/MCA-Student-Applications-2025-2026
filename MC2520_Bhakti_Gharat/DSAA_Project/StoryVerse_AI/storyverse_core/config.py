"""
Shared configuration for the StoryVerse core logic. This module has
NO Streamlit dependency, so it can be imported by both the FastAPI
app and (if you want to keep it) the original Streamlit app.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MUSICAPI_KEY = os.getenv("MUSICAPI_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# API key required to call THIS api (protects your free-tier quota
# on Gemini/Groq/Pollinations from being burned by strangers).
STORYVERSE_API_KEY = os.getenv("STORYVERSE_API_KEY")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

DATA_FOLDER = Path("storyverse_data")
AUDIO_FOLDER = DATA_FOLDER / "audio"
JOBS_FOLDER = DATA_FOLDER / "jobs"
BACKGROUND_MUSIC_FOLDER = Path("background_music")

DATA_FOLDER.mkdir(exist_ok=True)
AUDIO_FOLDER.mkdir(exist_ok=True)
JOBS_FOLDER.mkdir(exist_ok=True)

for _emotion_name in (
    "joy", "sadness", "love", "anger", "fear", "surprise", "neutral"
):
    (BACKGROUND_MUSIC_FOLDER / _emotion_name).mkdir(
        parents=True, exist_ok=True
    )

VOICE_MAP = {
    "English": "en-US-AriaNeural",
    "Hindi (हिंदी)": "hi-IN-SwaraNeural",
    "Marathi (मराठी)": "mr-IN-AarohiNeural",
}

EMOTION_LABELS = {
    0: "sadness",
    1: "joy",
    2: "love",
    3: "anger",
    4: "fear",
    5: "surprise",
}
