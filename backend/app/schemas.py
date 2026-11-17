"""Request and response models."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    account_ref: str | None = None


class WorkspaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LoginResponse(BaseModel):
    user: UserOut
    workspace: WorkspaceOut


class AssignOwnerRequest(BaseModel):
    owner: str | None = None


class SetTargetDateRequest(BaseModel):
    target_date: date | None = None


class SetNextActionRequest(BaseModel):
    next_action: str | None = None
    follow_up_date: date | None = None


class NoteRequest(BaseModel):
    note: str | None = None


class BlockerRequest(BaseModel):
    description: str | None = None


class CustomerUpdateRequest(BaseModel):
    customer_update: str | None = None


class EvidenceRequest(BaseModel):
    approved_by: str
    invoice_ref: str
    via_agreed_workflow: bool
    approved_at: date
    recorded_by: str


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_role: str
    action: str
    detail: str
    created_at: datetime


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    desired_outcome: str = ""
    owner: str | None = None
    last_reviewed_at: date | None = None
    start_date: date
    target_date: date
    status: str
    flags: list[str] = []
    next_action: str | None = None
    follow_up_date: date | None = None
    internal_blocker: str | None = None
    customer_blocker: str | None = None
