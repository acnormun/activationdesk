"""Activation Desk API - Pipeline 0 (access and request flow)."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .auth import router as auth_router
from .config import parse_origins, settings
from .database import Base, SessionLocal, engine, get_db
from .routers import accounts, plan
from .seed import ensure_demo_users

# Where the built frontend lives (single-service deployment). The root
# Dockerfile copies the Vite build here; local dev runs `npm run dev` instead
# and proxies the API paths to the backend.
FRONTEND_DIST = Path(os.environ.get("FRONTEND_DIST", "frontend/dist"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create the tables and ensure the demo users exist."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_demo_users(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Activation Desk API", version="0.1.0", lifespan=lifespan)

# CORS is only relevant when the frontend runs on a different origin (local
# Vite dev at :3000). Same-origin deployments never trigger it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_origins(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(accounts.router)
app.include_router(plan.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# Serve the built frontend (index.html + hashed assets + SPA fallback) when it
# is present. API routes above always take precedence.
if FRONTEND_DIST.is_dir():
    assets = FRONTEND_DIST / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
