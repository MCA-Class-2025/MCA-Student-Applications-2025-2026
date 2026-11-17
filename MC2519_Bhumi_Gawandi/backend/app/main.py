from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.database.mongodb import client

from app.routers.auth.auth_router import router as auth_router
from app.routers.expense_router import router as expense_router
from app.routers.budget_router import router as budget_router
from app.routers.email_test_router import router as email_test_router
from app.routers.category_router import router as category_router
from app.routers.report_router import router as report_router
from app.routers.ai_router import router as ai_router
from app.routers.receipt_router import router as receipt_router
from app.routers.voice_router import router as voice_router
from app.routers.ml_router import router as ml_router
from app.routers.analytics_router import router as analytics_router
from app.routers.chat_history_router import (
    router as chat_history_router
)
from app.routers.price_api_router import (
    router as price_api_router
)

# ============================================================
# LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("MongoDB Connected Successfully")

    yield

    client.close()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Smart Expense Tracker API",
    description="Backend API for AI Smart Expense Tracker",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    auth_router
)

app.include_router(
    expense_router
)

app.include_router(
    budget_router
)

app.include_router(
    email_test_router
)

app.include_router(
    category_router
)

app.include_router(
    report_router
)

app.include_router(
    ai_router
)

app.include_router(
    receipt_router
)

app.include_router(
    voice_router
)

app.include_router(
    ml_router
)

app.include_router(
    analytics_router
)

app.include_router(
    chat_history_router
)

app.include_router(
    price_api_router
)

# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "message":
            "AI Smart Expense Tracker Backend Running 🚀"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {
        "status":
            "healthy",

        "database":
            settings.DATABASE_NAME
    }