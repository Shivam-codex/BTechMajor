"""
Main FastAPI Application Entrypoint.
Smart City Complaint Management System.
Architecture: Non-ML Deterministic Natural Language Processing & Classical IR.
"""

import sys
import time
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure both project root and backend folder are in sys.path
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.parent
_backend_root = _current_file.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.core.logging import logger
from backend.app.services.retrieval.ranking import initialize_retriever_if_needed
from backend.app.api import complaints, dashboard, assistant, knowledge_base, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes database tables and verifies the TF-IDF knowledge base index.
    """
    logger.info(f"Initializing {settings.PROJECT_NAME} v{settings.VERSION}...")
    init_db()
    logger.info("Database schema synchronized.")

    initialize_retriever_if_needed()
    logger.info("Knowledge Base Retrieval Index initialized and ready.")

    yield

    logger.info("Shutting down application cleanly.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Local Smart City Grievance Redressal and Municipal Information Assistant. "
        "Built strictly with Non-ML Deterministic NLP, Rule-Based Classification, "
        "and Classical TF-IDF/BM25 Information Retrieval."
    ),
    lifespan=lifespan,
)

# CORS Configuration - permit localhost and 127.0.0.1 across all development ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Adds X-Process-Time-Ms execution header to API responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact the administrator."},
    )


# Health Check
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "architecture": "Deterministic Non-ML NLP & Retrieval",
    }


# Include Modular Routers under /api
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(complaints.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(assistant.router, prefix=settings.API_V1_STR)
app.include_router(knowledge_base.router, prefix=settings.API_V1_STR)
