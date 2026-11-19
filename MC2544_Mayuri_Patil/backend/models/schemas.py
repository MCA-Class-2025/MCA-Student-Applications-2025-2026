from pydantic import BaseModel, Field


class PatientData(BaseModel):
    patient_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Pseudonymous identifier used to link records during data fusion.",
    )
    age: int = Field(ge=18, le=120)
    gender: int = Field(ge=1, le=2)
    height: int = Field(ge=120, le=220)
    weight: float = Field(ge=30, le=250)
    ap_hi: int = Field(ge=70, le=250)
    ap_lo: int = Field(ge=40, le=200)
    cholesterol: int = Field(ge=1, le=3)
    gluc: int = Field(ge=1, le=3)
    smoke: int = Field(ge=0, le=1)
    alco: int = Field(ge=0, le=1)
    active: int = Field(ge=0, le=1)


class PredictionResponse(BaseModel):
    risk_label: str
    risk_probability: float = Field(ge=0, le=1)


class RecommendationResponse(BaseModel):
    recommendation: str
    disclaimer: str


class RagQuestionRequest(BaseModel):
    question: str = Field(min_length=5, max_length=500)


class RagSource(BaseModel):
    source: str
    record_id: str
    score: float


class RagQuestionResponse(BaseModel):
    answer: str
    sources: list[RagSource]
    disclaimer: str


class ModelEvaluationResponse(BaseModel):
    selected_model_name: str
    metrics: dict[str, dict[str, float]]
