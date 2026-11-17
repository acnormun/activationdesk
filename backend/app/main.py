"""Activation Desk API - Pipeline 0 (access and request flow)."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import router as auth_router
from .config import parse_origins, settings
from .database import Base, SessionLocal, engine, get_db
from .deps import Actor, get_actor
from .permissions import ALL_ACTIONS, ROLE_ACTIONS
from .routers import accounts, plan
from .seed import ensure_demo_users


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

# The Vue frontend (Vite dev server or the nginx container, port 3000) calls
# this API with cookies. Override with ALLOWED_ORIGINS (comma-separated).
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


@app.get("/permissions")
def permissions_matrix(actor: Actor = Depends(get_actor)) -> dict:
    """Roles and access: the 10 actions x 3 roles matrix."""
    return {
        "actions": [
            {
                "action": action,
                **{role: action in ROLE_ACTIONS[role] for role in ROLE_ACTIONS},
            }
            for action in ALL_ACTIONS
        ]
    }
