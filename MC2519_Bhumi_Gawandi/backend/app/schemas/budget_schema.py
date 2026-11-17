from pydantic import BaseModel, Field


# ============================================================
# CREATE BUDGET
# ============================================================

class BudgetCreate(BaseModel):

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


# ============================================================
# UPDATE BUDGET
# ============================================================

class BudgetUpdate(BaseModel):

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


# ============================================================
# BUDGET UPGRADE REQUEST
# ============================================================

class BudgetUpgradeRequest(BaseModel):

    new_amount: float = Field(
        gt=0
    )


# ============================================================
# BUDGET UPGRADE OTP VERIFICATION
# ============================================================

class BudgetUpgradeVerify(BaseModel):

    otp: str = Field(
        min_length=6,
        max_length=6
    )