"""Request dependencies for the Pipeline 0 checks.

Check order on every request:
1. valid session -> else 401 (get_actor)
2. account exists in the workspace -> else 404 (get_scoped_account)
3. business rules -> else 422 (business.validate_action, in the endpoints)
"""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import Account, User
from .security import read_token


@dataclass
class Actor:
    """The authenticated user and the demo workspace bound to the session."""

    user: User
    user_id: int
    workspace_id: int

    @property
    def role(self) -> str:
        return self.user.role


def get_actor(request: Request, db: Session = Depends(get_db)) -> Actor:
    """Check 1 - the session cookie must carry a valid token and user."""
    token = request.cookies.get(settings.cookie_name)
    payload = read_token(token) if token else None
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid session. Log in again.",
        )
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid session. Log in again.",
        )
    return Actor(user=user, user_id=user.id, workspace_id=int(payload["workspace_id"]))


def get_scoped_account(
    slug: str,
    actor: Actor = Depends(get_actor),
    db: Session = Depends(get_db),
) -> Account:
    """Check 2 - the account must exist inside the session workspace;
    unknown slugs answer 404 so the account list is never leaked."""
    account = (
        db.query(Account)
        .filter(
            Account.slug == slug,
            Account.workspace_id == actor.workspace_id,
        )
        .first()
    )
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found.",
        )
    return account
