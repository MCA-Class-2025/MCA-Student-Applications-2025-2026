from pydantic import BaseModel, Field


# ============================================================
# AI CHAT
# ============================================================

class AIChatRequest(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=3000
    )

    conversation_id: str | None = None


# ============================================================
# NEWS
# ============================================================

class NewsRequest(BaseModel):

    query: str = Field(
        default="personal finance India",
        min_length=1,
        max_length=200
    )


# ============================================================
# CURRENCY
# ============================================================

class CurrencyRequest(BaseModel):

    base: str = Field(
        min_length=3,
        max_length=3
    )

    target: str = Field(
        min_length=3,
        max_length=3
    )

    amount: float = Field(
        gt=0
    )


# ============================================================
# WEATHER
# ============================================================

class WeatherRequest(BaseModel):

    latitude: float

    longitude: float


# ============================================================
# CHAT HISTORY
# ============================================================

class ConversationCreate(BaseModel):

    title: str = Field(
        min_length=1,
        max_length=150
    )


class ConversationRename(BaseModel):

    title: str = Field(
        min_length=1,
        max_length=150
    )