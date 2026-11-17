import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database.session import engine
from app.database.base import Base
from app.routers import health, auth, documents, chat, study, students, fusion
from app.utils.exceptions import PrepGeniusException, prepgenius_exception_handler, global_exception_handler
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info(f"Starting {settings.APP_NAME} Backend Engine...")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Initialize database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified & initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")

    yield

    # Shutdown actions
    logger.info(f"Shutting down {settings.APP_NAME} Backend Engine...")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Production-grade AI Study Assistant & RAG Engine",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(PrepGeniusException, prepgenius_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Include Routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(students.router, prefix=settings.API_V1_STR)
app.include_router(fusion.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(study.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "docs": "/docs",
        "api_v1": f"{settings.API_V1_STR}/health"
    }
