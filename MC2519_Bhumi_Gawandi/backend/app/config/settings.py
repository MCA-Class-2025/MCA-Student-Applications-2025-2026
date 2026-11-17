from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # ============================================================
    # DATABASE
    # ============================================================

    MONGODB_URL: str

    DATABASE_NAME: str


    # ============================================================
    # JWT
    # ============================================================

    JWT_SECRET_KEY: str

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


    # ============================================================
    # GROQ AI
    # ============================================================

    GROQ_API_KEY: str

    GROQ_MODEL: str = "llama-3.3-70b-versatile"


    # ============================================================
    # OTHER APIs
    # ============================================================

    OCR_API_KEY: str = ""

    NEWS_API_KEY: str = ""

    EXCHANGE_RATE_API_KEY: str = ""

    CURRENCY_API_KEY: str = ""


    # ============================================================
    # EMAIL
    # ============================================================

    MAIL_USERNAME: str

    MAIL_PASSWORD: str

    MAIL_FROM: str

    MAIL_PORT: int = 587

    MAIL_SERVER: str = "smtp.gmail.com"

    MAIL_STARTTLS: bool = True

    MAIL_SSL_TLS: bool = False


    # ============================================================
    # PYDANTIC SETTINGS
    # ============================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()