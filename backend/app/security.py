"""Password hashing (bcrypt) and the session token (JWT in an HttpOnly cookie)."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def issue_token(user_id: int, workspace_id: int) -> str:
    """Session token: user + demo workspace, expiring after the configured TTL."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "workspace_id": workspace_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.token_ttl_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def read_token(token: str) -> dict | None:
    """Return the payload, or None when the token is invalid or expired."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.PyJWTError:
        return None
