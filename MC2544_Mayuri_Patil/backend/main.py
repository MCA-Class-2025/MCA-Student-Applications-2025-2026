from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import (
    PatientData,
    ModelEvaluationResponse,
    PredictionResponse,
    RagQuestionRequest,
    RagQuestionResponse,
    RagSource,
    RecommendationResponse,
)
from services.csv_store import (
    API_CSV_FILES,
    ApiDataStoreError,
    append_api_record,
    read_api_records,
    read_csv_preview,
)
from services.llm_service import (
    DISCLAIMER,
    LlmServiceError,
    generate_phase2_answer,
    generate_recommendation,
)
from services.model_service import (
    ModelNotReadyError,
    build_fused_record,
    get_model_evaluation,
    predict,
)
from services.external_api_service import (
    ExternalApiError,
    find_nearby_care,
    search_drug_labels,
    search_foods,
    search_packaged_foods,
)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = FastAPI(
    title="CardioCare AI API",
    version="0.1.0",
    description="Educational heart-disease risk assessment API.",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_project_root = Path(__file__).resolve().parents[1]
PHASE1_DATASET_FILES = {
    "original": _project_root
    / "dataset"
    / "heart_failure_source"
    / "heart_failure_clinical_records_dataset.csv",
    "api": _project_root / "analysis" / "phase1_output" / "data" / "phase1_api_loinc_metadata.csv",
    "fused": _project_root
    / "analysis"
    / "phase1_output"
    / "data"
    / "phase1_fused_heart_failure_loinc.csv",
}


def store_api_record(
    api_name: str,
    endpoint: str,
    request_data: dict[str, object],
    response_data: dict[str, object],
) -> None:
    try:
        append_api_record(api_name, endpoint, request_data, response_data)
    except ApiDataStoreError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/models")
def list_models() -> dict[str, object]:
    return {
        "object": "list",
        "data": [
            {
                "id": "cardiocare-ai",
                "object": "model",
                "created": 1700000000,
                "owned_by": "cardiocare",
            }
        ],
    }


@app.get("/datasets/{api_name}")
def get_saved_api_data(
    api_name: str,
    limit: int = Query(default=5, ge=1, le=10),
) -> dict[str, object]:
    if api_name not in API_CSV_FILES:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    try:
        return read_api_records(api_name, limit)
    except ApiDataStoreError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/phase1/datasets/{dataset_name}")
def get_phase1_dataset(
    dataset_name: str,
    limit: int = Query(default=5, ge=1, le=10),
) -> dict[str, object]:
    try:
        dataset_path = PHASE1_DATASET_FILES[dataset_name]
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Phase 1 dataset not found.") from error

    try:
        return read_csv_preview(dataset_path, limit)
    except ApiDataStoreError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/models/evaluation", response_model=ModelEvaluationResponse)
def get_model_comparison() -> ModelEvaluationResponse:
    try:
        return ModelEvaluationResponse(**get_model_evaluation())
    except ModelNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/predict", response_model=PredictionResponse)
def predict_heart_disease_risk(patient: PatientData) -> PredictionResponse:
    try:
        response = predict(patient)
        store_api_record(
            "fused_assessments",
            "/predict",
            patient.model_dump(),
            {
                "fused_features": build_fused_record(patient),
                "prediction": response.model_dump(),
            },
        )
        return response
    except ModelNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/recommendations", response_model=RecommendationResponse)
def generate_health_recommendations(patient: PatientData) -> RecommendationResponse:
    try:
        prediction = predict(patient)
        recommendation = generate_recommendation(patient, prediction)
        response = RecommendationResponse(
            recommendation=recommendation,
            disclaimer=DISCLAIMER,
        )
        store_api_record(
            "huggingface",
            "/recommendations",
            patient.model_dump(),
            response.model_dump(),
        )
        return response
    except ModelNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except LlmServiceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/phase2/questions", response_model=RagQuestionResponse)
def answer_phase2_question(request: RagQuestionRequest) -> RagQuestionResponse:
    try:
        answer, sources = generate_phase2_answer(request.question)
        return RagQuestionResponse(
            answer=answer,
            sources=[
                RagSource(
                    source=str(source["source"]),
                    record_id=str(source["record_id"]),
                    score=float(source["score"]),
                )
                for source in sources
            ],
            disclaimer=DISCLAIMER,
        )
    except LlmServiceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/external/foods")
def search_nutrition_data(
    query: str = Query(min_length=2, max_length=80),
    limit: int = Query(default=5, ge=1, le=10),
) -> dict[str, object]:
    try:
        response = {"results": search_foods(query, limit)}
        store_api_record("usda", "/external/foods", {"query": query, "limit": limit}, response)
        return response
    except ExternalApiError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/external/drug-labels")
def search_educational_drug_labels(
    query: str = Query(min_length=2, max_length=80),
    limit: int = Query(default=5, ge=1, le=10),
) -> dict[str, object]:
    try:
        response = {
            "disclaimer": "Drug labels are educational reference information, not prescribing guidance.",
            "results": search_drug_labels(query, limit),
        }
        store_api_record(
            "openfda",
            "/external/drug-labels",
            {"query": query, "limit": limit},
            response,
        )
        return response
    except ExternalApiError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/external/packaged-foods")
def search_packaged_food_nutrition(
    query: str = Query(min_length=2, max_length=80),
    limit: int = Query(default=1, ge=1, le=10),
) -> dict[str, object]:
    try:
        response = {"results": search_packaged_foods(query, limit)}
        store_api_record(
            "openfoodfacts",
            "/external/packaged-foods",
            {"query": query, "limit": limit},
            response,
        )
        return response
    except ExternalApiError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/external/nearby-care")
def get_nearby_care(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    radius: int = Query(default=5000, ge=500, le=10000),
) -> dict[str, object]:
    try:
        response = {"results": find_nearby_care(latitude, longitude, radius)}
        store_api_record(
            "openstreetmap",
            "/external/nearby-care",
            {"latitude": latitude, "longitude": longitude, "radius": radius},
            response,
        )
        return response
    except ExternalApiError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
