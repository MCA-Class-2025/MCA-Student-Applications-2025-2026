from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field
)


class UserRegister(BaseModel):

    full_name: str = Field(
        ...,
        min_length=3,
        max_length=100
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8
    )

    monthly_income: float = Field(
        ...,
        gt=0
    )

    preferred_currency: str = "INR"


class UserLogin(BaseModel):

    email: EmailStr

    password: str


class UserResponse(BaseModel):

    id: Optional[str] = None

    full_name: str

    email: EmailStr

    monthly_income: float

    preferred_currency: str