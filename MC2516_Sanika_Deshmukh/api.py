"""
api.py — PlatePal REST API
────────────────────────────────────────────────────────────────
A FastAPI layer on top of the same utils/ functions the Streamlit
app (app.py) already uses. This does NOT duplicate logic — it
imports and calls the exact same functions, so the API and the
Streamlit UI always behave identically.

Run it:
    pip install fastapi "uvicorn[standard]" python-multipart
    uvicorn api:app --reload --port 8000

Then open http://127.0.0.1:8000/docs for interactive Swagger UI
(FastAPI generates this automatically from the type hints below —
useful to screenshot for your assignment).

NOTE ON MISSING FILES:
Two endpoints (/history and /rag/similar) depend on utils/rag_utils.py
and utils/history_utils.py, which weren't available when this was
written. Their imports and endpoints are included below but guarded —
if those modules aren't present yet, the app still starts and every
other endpoint works; only those two return HTTP 501 until you add
the real modules.
"""

import io
import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from PIL import Image
from pydantic import BaseModel

from utils.gemini_utils import (
    configure_gemini, set_model, get_model, MODEL_OPTIONS,
    analyze_food_image, chat_with_gemini, transcribe_audio,
)
from utils.speech_utils import text_to_speech_bytes
from utils.csv_utils import build_export_csv
from utils.xlsx_utils import build_export_xlsx, build_fusion_csv
from utils.food_apis import (
    get_recipes, get_weather_food_advice, get_cultural_info,
    get_exchange_rates, get_workout_suggestions, lookup_product,
)

# Optional module — degrades gracefully if not present yet
try:
    from utils.rag_utils import (
        add_to_vector_store, retrieve_similar, build_rag_context, get_store_stats,
    )
    _RAG_AVAILABLE = True
except ImportError:
    _RAG_AVAILABLE = False

try:
    from utils.history_utils import load_history
    _HISTORY_AVAILABLE = True
except ImportError:
    _HISTORY_AVAILABLE = False


load_dotenv()

app = FastAPI(
    title="PlatePal API",
    description="AI food & nutrition assistant — vision analysis, chat, "
                 "speech-to-text, and enrichment from 6 external APIs.",
    version="1.0.0",
)

# Configure Gemini once at startup from .env, same as app.py does
_startup_key = os.getenv("GEMINI_API_KEY", "")
if _startup_key:
    configure_gemini(_startup_key)


def _require_key(api_key: Optional[str]) -> str:
    """Every AI endpoint accepts an optional api_key override per-request
    (for multi-user API use); otherwise falls back to the server's .env key."""
    key = api_key or _startup_key
    if not key:
        raise HTTPException(
            status_code=400,
            detail="No Gemini API key available. Pass api_key= or set GEMINI_API_KEY in .env.",
        )
    configure_gemini(key)
    return key


# ────────────────────────────────────────────────────────────────
# Root / health
# ────────────────────────────────────────────────────────────────
@app.get("/", tags=["Meta"])
def root():
    return {
        "name": "PlatePal API",
        "status": "ok",
        "current_model": get_model(),
        "available_models": MODEL_OPTIONS,
        "docs": "/docs",
    }


# ────────────────────────────────────────────────────────────────
# 1. Vision analysis
# ────────────────────────────────────────────────────────────────
@app.post("/analyze", tags=["Core AI"])
async def analyze(
    file: UploadFile = File(..., description="Food photo (jpg/png)"),
    language: str = Form("English"),
    model: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
):
    """Upload a food photo → dish, cuisine, ingredients, calories, macros."""
    _require_key(api_key)
    if model:
        if model not in MODEL_OPTIONS:
            raise HTTPException(400, f"Unknown model '{model}'. Options: {MODEL_OPTIONS}")
        set_model(model)

    try:
        img_bytes = await file.read()
        pil_image = Image.open(io.BytesIO(img_bytes))
    except Exception:
        raise HTTPException(400, "Could not read image file.")

    try:
        result = analyze_food_image(pil_image, language=language)
    except RuntimeError as e:
        raise HTTPException(502, str(e))

    return {
        "filename": file.filename,
        "size_kb": round(len(img_bytes) / 1024, 1),
        "dimensions": f"{pil_image.width}x{pil_image.height}",
        "language": language,
        "model": get_model(),
        "analysis": result["raw_text"],
    }


# ────────────────────────────────────────────────────────────────
# 2. Chat
# ────────────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    food_context: str = ""
    language: str = "English"
    model: Optional[str] = None
    api_key: Optional[str] = None


@app.post("/chat", tags=["Core AI"])
def chat(req: ChatRequest):
    """Follow-up question → Gemini reply, with optional rolling history + food context."""
    _require_key(req.api_key)
    if req.model:
        if req.model not in MODEL_OPTIONS:
            raise HTTPException(400, f"Unknown model '{req.model}'. Options: {MODEL_OPTIONS}")
        set_model(req.model)

    try:
        reply = chat_with_gemini(
            user_message=req.message,
            history=[m.dict() for m in req.history],
            food_context=req.food_context,
            language=req.language,
        )
    except RuntimeError as e:
        raise HTTPException(502, str(e))

    return {"reply": reply, "model": get_model()}


# ────────────────────────────────────────────────────────────────
# 3. Speech-to-text
# ────────────────────────────────────────────────────────────────
@app.post("/transcribe", tags=["Core AI"])
async def transcribe(
    file: UploadFile = File(..., description="Audio clip (wav/mp3/m4a)"),
    api_key: Optional[str] = Form(None),
):
    """Voice message → text transcript, via Gemini's audio understanding."""
    _require_key(api_key)
    audio_bytes = await file.read()
    mime = file.content_type or "audio/wav"
    try:
        text = transcribe_audio(audio_bytes, mime_type=mime)
    except RuntimeError as e:
        raise HTTPException(502, str(e))
    return {"transcript": text}


# ────────────────────────────────────────────────────────────────
# 4. Text-to-speech
# ────────────────────────────────────────────────────────────────
@app.get("/speak", tags=["Core AI"])
def speak(text: str = Query(..., min_length=1), lang: str = "en"):
    """Text → MP3 audio stream (gTTS)."""
    try:
        audio_bytes = text_to_speech_bytes(text, lang=lang)
    except Exception as e:
        raise HTTPException(502, f"TTS failed: {e}")
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")


# ────────────────────────────────────────────────────────────────
# 5. Enrichment APIs (recipes / weather / culture / price / workout / products)
# ────────────────────────────────────────────────────────────────
@app.get("/recipes", tags=["Enrichment"])
def recipes(dish: str = Query(..., description="Dish name, e.g. 'Chicken Tikka Masala'")):
    """Matching recipes from TheMealDB."""
    return get_recipes(dish)


@app.get("/weather", tags=["Enrichment"])
def weather(dish: str, city: str = "Mumbai"):
    """Current weather for `city` + a verdict on whether `dish` suits it."""
    return get_weather_food_advice(dish, city=city)


@app.get("/culture", tags=["Enrichment"])
def culture(dish: str):
    """Cultural/historical origin of the dish (Wikipedia + curated data)."""
    return get_cultural_info(dish)


@app.get("/price", tags=["Enrichment"])
def price(dish: str, cost_inr: Optional[float] = None):
    """Estimated dish cost (INR) converted into 8 world currencies."""
    return get_exchange_rates(dish, cost_inr=cost_inr)


@app.get("/workout", tags=["Enrichment"])
def workout(dish: str, calories: int = 300, weight_kg: float = 65):
    """How long common exercises take to burn off the dish's calories."""
    return get_workout_suggestions(dish, calories=calories, weight_kg=weight_kg)


@app.get("/products", tags=["Enrichment"])
def products(name: str, max_results: int = 3):
    """Related packaged products from Open Food Facts."""
    return lookup_product(name, max_results=max_results)


# ────────────────────────────────────────────────────────────────
# 6. RAG — similar past analyses (utils/rag_utils.py)
# ────────────────────────────────────────────────────────────────
class RagAddRequest(BaseModel):
    dish_name: str
    analysis_text: str
    api_key: Optional[str] = None
    metadata: dict = {}


@app.get("/rag/similar", tags=["RAG"])
def rag_similar(
    query: str = Query(..., description="Text to search for similar past analyses — usually the dish name or a user question"),
    top_k: int = 3,
    min_score: float = 0.45,
    api_key: Optional[str] = None,
):
    """
    Real vector-similarity retrieval: embeds `query` with Gemini
    text-embedding-004 and returns the top_k most similar past analyses
    by cosine similarity (only entries that have a stored embedding —
    entries where the embedding call failed at store-time are skipped).
    """
    if not _RAG_AVAILABLE:
        raise HTTPException(501, "utils/rag_utils.py not found on this server.")
    key = _require_key(api_key)
    results = retrieve_similar(query, key, top_k=top_k, min_score=min_score)
    return {"query": query, "count": len(results), "results": results}


@app.post("/rag/add", tags=["RAG"])
def rag_add(req: RagAddRequest):
    """Embed and store a new analysis in the RAG vector store."""
    if not _RAG_AVAILABLE:
        raise HTTPException(501, "utils/rag_utils.py not found on this server.")
    key = _require_key(req.api_key)
    ok = add_to_vector_store(req.dish_name, req.analysis_text, key, extra_metadata=req.metadata)
    return {"stored": ok}


@app.get("/rag/stats", tags=["RAG"])
def rag_stats():
    """Quick health check — how many entries are in the vector store, which dishes, most recent."""
    if not _RAG_AVAILABLE:
        raise HTTPException(501, "utils/rag_utils.py not found on this server.")
    return get_store_stats()


# ────────────────────────────────────────────────────────────────
# 7. History  (needs utils/history_utils.py)
# ────────────────────────────────────────────────────────────────
@app.get("/history", tags=["History"])
def history():
    if not _HISTORY_AVAILABLE:
        raise HTTPException(
            501,
            "utils/history_utils.py not found on this server — add it to enable this endpoint.",
        )
    return {"sessions": load_history()}


# ────────────────────────────────────────────────────────────────
# 8. Export
# ────────────────────────────────────────────────────────────────
class ExportRequest(BaseModel):
    analysis_text: str = ""
    messages: list[ChatMessage] = []
    language: str = "English"
    model: str = ""
    image_info: dict = {}
    api_results: dict = {}
    rag_results: list = []


@app.post("/export/xlsx", tags=["Export"])
def export_xlsx(req: ExportRequest):
    """Full formatted Excel workbook — Fusion Data sheet + one sheet per source.
    Text/JSON only, no photo — use /export/xlsx-with-photo to embed the image."""
    xlsx_bytes = build_export_xlsx(
        analysis_text=req.analysis_text,
        messages=[m.dict() for m in req.messages],
        language=req.language,
        model=req.model,
        image_info=req.image_info,
        api_results=req.api_results,
        rag_results=req.rag_results,
        pil_image=None,
    )
    filename = f"platepal_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/export/xlsx-with-photo", tags=["Export"])
async def export_xlsx_with_photo(
    file: UploadFile = File(..., description="The food photo to embed in the Overview sheet"),
    analysis_text: str = Form(""),
    messages_json: str = Form("[]", description='JSON array, e.g. [{"role":"user","content":"..."}]'),
    language: str = Form("English"),
    model: str = Form(""),
    api_results_json: str = Form("{}", description="JSON object of weather/recipes/culture/etc. results"),
    rag_results_json: str = Form("[]", description="JSON array of RAG hits"),
):
    """
    Same export as /export/xlsx, but takes the actual photo as a real file
    upload and embeds it in the Overview sheet — this is the endpoint that
    matches what the Streamlit app produces (photo + full session data
    in one workbook).
    """
    import json as _json

    try:
        messages = _json.loads(messages_json)
        api_results = _json.loads(api_results_json)
        rag_results = _json.loads(rag_results_json)
    except _json.JSONDecodeError as e:
        raise HTTPException(400, f"One of the *_json fields isn't valid JSON: {e}")

    try:
        img_bytes = await file.read()
        pil_image = Image.open(io.BytesIO(img_bytes))
    except Exception:
        raise HTTPException(400, "Could not read image file.")

    image_info = {
        "filename": file.filename,
        "size_kb": round(len(img_bytes) / 1024, 1),
        "width": pil_image.width,
        "height": pil_image.height,
    }

    xlsx_bytes = build_export_xlsx(
        analysis_text=analysis_text,
        messages=messages,
        language=language,
        model=model,
        image_info=image_info,
        api_results=api_results,
        rag_results=rag_results,
        pil_image=pil_image,
    )
    filename = f"platepal_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/export/csv", tags=["Export"])
def export_csv(req: ExportRequest, clean: bool = Query(True, description="True = fusion CSV (clean), False = raw CSV with Base64 image")):
    if clean:
        csv_bytes = build_fusion_csv(
            analysis_text=req.analysis_text,
            messages=[m.dict() for m in req.messages],
            language=req.language,
            model=req.model,
            image_info=req.image_info,
            api_results=req.api_results,
            rag_results=req.rag_results,
        )
        suffix = "fusion"
    else:
        csv_bytes = build_export_csv(
            analysis_text=req.analysis_text,
            messages=[m.dict() for m in req.messages],
            language=req.language,
            model=req.model,
            image_info=req.image_info,
            api_results=req.api_results,
            rag_results=req.rag_results,
            pil_image=None,
        )
        suffix = "raw"
    filename = f"platepal_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{suffix}.csv"
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )