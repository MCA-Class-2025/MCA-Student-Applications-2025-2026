
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load environment variables from project folder
load_dotenv(
    os.path.join(BASE_DIR, ".env"),
    override=True
)

# Dataset paths
ORIGINAL_DATA = os.path.join(
    BASE_DIR, "data", "original", "Food_Dataset.xlsx"
)

API_DATA_DIR = os.path.join(
    BASE_DIR, "data", "api_data"
)

FUSED_DATA_DIR = os.path.join(
    BASE_DIR, "data", "fused"
)

# API keys
USDA_API_KEY = os.getenv("USDA_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

# New AI provider
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Retained for compatibility; not used for answer generation
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

THEMEALDB_API_KEY = os.getenv("THEMEALDB_API_KEY", "1")

# Create required directories
os.makedirs(API_DATA_DIR, exist_ok=True)
os.makedirs(FUSED_DATA_DIR, exist_ok=True)
