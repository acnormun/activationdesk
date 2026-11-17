"""Pipeline 0 - demo login.

Login checks the password, issues the session token in an HttpOnly cookie
and creates an isolated demo workspace for the session (mock accounts seeded).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .deps import Actor, get_actor
from .models import DemoWorkspace, User
from .schemas import LoginRequest, LoginResponse, UserOut, WorkspaceOut
from .security import issue_token, verify_password
from .seed import seed_workspace_accounts

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Check the password, create the demo workspace and set the session cookie."""
    user = db.query(User).filter(User.username == body.username).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    workspace = DemoWorkspace(name=f"Demo workspace - {body.username} - {stamp}")
    db.add(workspace)
    db.commit()

    seed_workspace_accounts(db, workspace)

    token = issue_token(user_id=user.id, workspace_id=workspace.id)
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
        max_age=settings.token_ttl_minutes * 60,
    )
    return LoginResponse(
        user=UserOut.model_validate(user),
        workspace=WorkspaceOut.model_validate(workspace),
    )


@router.post("/logout")
def logout(response: Response) -> dict:
    """Clear the session cookie."""
    response.delete_cookie(settings.cookie_name)
    return {"message": "Logged out."}


@router.get("/me")
def me(
    actor: Actor = Depends(get_actor),
    db: Session = Depends(get_db),
) -> dict:
    """Who is logged in and which demo workspace the session uses."""
    workspace = db.get(DemoWorkspace, actor.workspace_id)
    return {
        "user": UserOut.model_validate(actor.user).model_dump(),
        "workspace": WorkspaceOut.model_validate(workspace).model_dump(),
    }
