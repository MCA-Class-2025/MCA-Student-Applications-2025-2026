from pydantic import BaseModel, Field


# ============================================================
# REPORT FILTER
# ============================================================

class ReportFilter(BaseModel):

    month: int = Field(
        ge=1,
        le=12
    )

    year: int = Field(
        ge=2020,
        le=2100
    )

    category: str | None = None