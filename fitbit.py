"""OneiricAi API — dreams reconstructed and verified against your own biology.

Run locally:  uvicorn app.main:app --reload   (from the backend/ folder)
Docs:         http://localhost:8000/docs
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import biometrics, dreams, feed, generate
from .services.video import MEDIA_DIR

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="OneiricAi API",
    version="0.1.0",
    description="Dream reconstruction with a Biological Authenticity (Anti-Fake) engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

for r in (biometrics.router, dreams.router, generate.router, feed.router):
    app.include_router(r, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "video_provider": settings.video_provider,
        "claude": bool(settings.anthropic_api_key),
        "antifake_threshold": settings.antifake_threshold,
    }
