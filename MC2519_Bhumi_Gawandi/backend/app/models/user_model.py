from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserModel(BaseModel):

    full_name: str = Field(
        ...,
        min_length=3,
        max_length=100
    )

    email: EmailStr

    password: str

    monthly_income: float = Field(
        ...,
        gt=0
    )

    preferred_currency: str = "INR"

    created_at: datetime = Field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )

    updated_at: Optional[datetime] = None