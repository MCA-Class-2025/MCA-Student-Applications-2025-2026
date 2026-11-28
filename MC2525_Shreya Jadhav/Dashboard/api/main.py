
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from Dashboard.utils.clinical_engine import analyze
from Dashboard.analytics.dashboard import load_data, get_metrics


# ==========================================================
# FemCare API
# ==========================================================

app = FastAPI(
    title="FemCare AI API",
    description="REST API for the FemCare AI Menstrual Health Assistant",
    version="1.0.0"
)


# ==========================================================
# Request Models
# ==========================================================

class SymptomRequest(BaseModel):

    pain: Optional[int] = None
    stress: Optional[int] = None
    sleep: Optional[int] = None
    flow: Optional[str] = None
    pcos: Optional[bool] = None


class HealthQuery(BaseModel):

    question: str


# ==========================================================
# Home / API Information
# ==========================================================

@app.get("/")
def home():

    return {
        "application": "FemCare AI",
        "message": "FemCare AI API is running",
        "version": "1.0.0",
        "endpoints": [
            "/api/health",
            "/api/analyze",
            "/api/metrics"
        ]
    }


# ==========================================================
# Health Check
# ==========================================================

@app.get("/api/health")
def health_check():

    return {
        "status": "healthy",
        "application": "FemCare AI"
    }


# ==========================================================
# Clinical Assessment API
# ==========================================================

@app.post("/api/analyze")
def analyze_symptoms(data: SymptomRequest):

    # Convert API input into the format
    # expected by the existing clinical engine.

    parts = []

    if data.pain is not None:
        parts.append(f"Pain: {data.pain}/10")

    if data.stress is not None:
        parts.append(f"Stress: {data.stress}/10")

    if data.sleep is not None:
        parts.append(f"Sleep: {data.sleep} hours")

    if data.flow is not None:
        parts.append(f"Flow: {data.flow}")

    if data.pcos is not None:
        parts.append(
            f"PCOS: {'Yes' if data.pcos else 'No'}"
        )

    if not parts:

        raise HTTPException(
            status_code=400,
            detail="Please provide at least one symptom."
        )

    symptom_text = ", ".join(parts)

    result = analyze(symptom_text)

    return {
        "application": "FemCare AI",
        "input": {
            "pain": data.pain,
            "stress": data.stress,
            "sleep": data.sleep,
            "flow": data.flow,
            "pcos": data.pcos
        },
        "assessment": result
    }


# ==========================================================
# Dataset Analytics API
# ==========================================================

@app.get("/api/metrics")
def dataset_metrics():

    try:

        df = load_data()

        metrics = get_metrics(df)

        return {
            "application": "FemCare AI",
            "dataset_metrics": metrics
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to load dataset metrics: {str(e)}"
        )