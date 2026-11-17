from pydantic import BaseModel, Field


# ============================================================
# CREATE CATEGORY
# ============================================================

class CategoryCreate(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=50
    )

    description: str = Field(
        default="",
        max_length=200
    )


# ============================================================
# UPDATE CATEGORY
# ============================================================

class CategoryUpdate(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=50
    )

    description: str = Field(
        default="",
        max_length=200
    )