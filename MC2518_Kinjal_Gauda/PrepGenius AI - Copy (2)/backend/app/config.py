import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "PrepGenius AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./prepgenius.db"

    # Dataset Paths
    DATA_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data"
    )
    STUDENT_DATASET_PATH: str = os.path.join(DATA_DIR, "student_career_success_dataset.csv")
    BOOKS_DATASET_PATH: str = os.path.join(DATA_DIR, "books.csv")
    YOUTUBE_DATASET_PATH: str = os.path.join(DATA_DIR, "yt data.csv")
    ARXIV_DATASET_PATH: str = os.path.join(DATA_DIR, "arXiv_scientific_dataset.csv")
    CITIES_DATASET_PATH: str = os.path.join(DATA_DIR, "cities.xlsx")

    # Security
    SECRET_KEY: str = "prepgenius_super_secret_key_change_in_production_32bytes"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Ollama & Embeddings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # Uploads
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "txt"]
    UPLOAD_DIR: str = "./uploads"

    # CORS Origins
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
