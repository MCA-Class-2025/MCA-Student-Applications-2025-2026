from datetime import datetime, timezone

from pydantic import BaseModel, Field


class CategoryModel(BaseModel):
    """
    Category document for the logged-in user.
    """

    user_id: str

    name: str = Field(
        min_length=1,
        max_length=50
    )

    description: str = Field(
        default="",
        max_length=200
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )