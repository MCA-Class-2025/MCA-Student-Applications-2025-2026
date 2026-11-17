from datetime import datetime, timezone

from pydantic import BaseModel, Field


class BudgetModel(BaseModel):
    """
    MongoDB budget document model.

    Stores a category-wise monthly budget
    for the logged-in user.
    """

    user_id: str

    category: str = Field(
        min_length=1,
        max_length=50
    )

    amount: float = Field(
        gt=0
    )

    month: int = Field(
        ge=1,
        le=12
    )

    year: int = Field(
        ge=2020,
        le=2100
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )