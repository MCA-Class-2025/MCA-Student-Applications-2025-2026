"""
api_server.py — SnapKnow's own REST API.

This exposes the same image-identification logic used by the Streamlit app
(app.py) as a standalone HTTP API, built with FastAPI. It reuses core.py so
there is exactly one implementation of the prompting/parsing logic behind
both the web UI and this API — they can never drift out of sync.

Run it with:
    uvicorn api_server:app --reload

Then open http://127.0.0.1:8000/docs for interactive Swagger documentation
(FastAPI generates this automatically — a good thing to show in a demo).
"""

from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core import (
    analyze_image,
    guess_media_type_from_bytes,
    parse_response,
    resize_image_bytes,
    translate_result_text,
)

app = FastAPI(
    title="SnapKnow API",
    description=(
        "Upload a photo and get it identified — category, name, description, "
        "details, and a fun fact — powered by Google Gemini or Anthropic Claude."
    ),
    version="1.0.0",
)

# Allow browser-based clients (e.g. a separate frontend) to call this API directly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeResponse(BaseModel):
    caption: Optional[str] = None
    category: Optional[str] = None
    name: Optional[str] = None
    confidence: Optional[str] = None
    description: Optional[str] = None
    details: Optional[str] = None
    fun_fact: Optional[str] = None
    answer: Optional[str] = None


class TranslateRequest(BaseModel):
    result: dict
    target_language: str
    api_key: str
    model_name: str
    provider: str  # "gemini" or "claude"


def _to_response(parsed: dict) -> AnalyzeResponse:
    return AnalyzeResponse(
        caption=parsed.get("CAPTION"),
        category=parsed.get("CATEGORY"),
        name=parsed.get("NAME"),
        confidence=parsed.get("CONFIDENCE"),
        description=parsed.get("DESCRIPTION"),
        details=parsed.get("DETAILS"),
        fun_fact=parsed.get("FUN_FACT"),
        answer=parsed.get("ANSWER"),
    )


def _resolve_provider(provider: str) -> str:
    """Accept a few friendly spellings and map them to what core.analyze_image expects."""
    p = provider.strip().lower()
    if p in ("gemini", "google", "google gemini"):
        return "Google Gemini"
    if p in ("claude", "anthropic", "anthropic claude"):
        return "Anthropic Claude"
    if p in ("ollama", "local"):
        return "Ollama"
    raise HTTPException(status_code=400, detail="provider must be 'gemini', 'claude', or 'ollama'")


@app.get("/")
def root():
    return {
        "name": "SnapKnow API",
        "docs": "/docs",
        "endpoints": ["/analyze", "/translate", "/health"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile = File(..., description="Image file (jpg/png/webp/gif) to identify"),
    provider: str = Form(..., description="'gemini', 'claude', or 'ollama'"),
    model_name: str = Form(..., description="e.g. gemini-3.6-flash or claude-sonnet-4-6"),
    api_key: str = Form(
        ..., description="API key for gemini/claude, or the Ollama base URL (e.g. http://localhost:11434) for ollama"
    ),
    language: str = Form("English", description="Output language, e.g. English, Hindi, Marathi"),
    question: Optional[str] = Form(None, description="Optional follow-up question about the image"),
):
    """Identify the subject of an uploaded photo and return a structured result."""
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    image_bytes = resize_image_bytes(raw_bytes)
    media_type = guess_media_type_from_bytes(image_bytes)
    provider_name = _resolve_provider(provider)

    try:
        raw_text = analyze_image(
            image_bytes,
            media_type,
            api_key,
            model_name,
            provider_name,
            language=language,
            extra_question=question,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream AI provider error: {e}")

    parsed = parse_response(raw_text)
    if not parsed:
        raise HTTPException(status_code=502, detail="Could not parse a structured response from the model")

    return _to_response(parsed)


@app.post("/translate", response_model=AnalyzeResponse)
def translate(req: TranslateRequest):
    """Translate an already-analyzed result into another language (text-only, no image needed)."""
    provider_name = _resolve_provider(req.provider)
    try:
        translated = translate_result_text(
            req.result,
            req.target_language,
            req.api_key,
            req.model_name,
            provider_name,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream AI provider error: {e}")
    return _to_response(translated)
