"""FastAPI application entrypoint.

Startup sequence (idempotent):
1. create tables
2. generate/load cleaned synthetic data
3. seed the database
4. train all six application models (or load cached artifacts)
5. generate fraud/AML alerts from model scores
"""
from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager

# Make `backend/` importable when running `uvicorn app.main:app` from backend/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from .api.routes import router  # noqa: E402
from .config import settings  # noqa: E402
from .db import SessionLocal, init_db  # noqa: E402
from .data.loader import run_pipeline, seed_db  # noqa: E402
from .ml.models import store  # noqa: E402
from .services.risk import generate_alerts  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    frames = run_pipeline()
    db = SessionLocal()
    try:
        seed_db(db, frames)
    finally:
        db.close()
    store.train_all(frames)
    created = generate_alerts()
    print(f"[startup] model training complete · alerts created: {created}")
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Open-source AI platform for corporate banking: credit risk, fraud, AML, "
                "liquidity forecasting, RM decision support and client segmentation.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": settings.version,
        "docs": "/docs",
        "api": settings.api_prefix,
        "synthetic_data": True,
        "llm": settings.ollama_model,
        "llm_provider": "ollama (open source, self-hosted)",
    }
