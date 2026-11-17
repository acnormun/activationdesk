"""Data model: demo workspaces, users, accounts and history.

Mock data lives in PostgreSQL: every login creates an isolated
DemoWorkspace seeded with example accounts.
"""

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role:
    """The single demo user role (the onboarding manager)."""

    ONBOARDING_MANAGER = "onboarding_manager"


class DemoWorkspace(Base):
    """Isolated workspace created for each demo login."""

    __tablename__ = "demo_workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    accounts: Mapped[list["Account"]] = relationship(back_populates="workspace")


class User(Base):
    """The single demo user: the onboarding manager sees every account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(40))
    account_ref: Mapped[str | None] = mapped_column(String(80), default=None)


class Account(Base):
    """Account facts. The status column only stores the value recalculated
    by Pipeline 1 after every change; it is never written by hand."""

    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("workspace_id", "slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("demo_workspaces.id"))
    slug: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(120))
    owner: Mapped[str | None] = mapped_column(String(120), default=None)
    start_date: Mapped[date] = mapped_column(Date)
    target_date: Mapped[date] = mapped_column(Date)
    desired_outcome: Mapped[str] = mapped_column(String(200), default="")
    last_reviewed_at: Mapped[date | None] = mapped_column(Date, default=None)
    setup_done_at: Mapped[date | None] = mapped_column(Date, default=None)
    import_done_at: Mapped[date | None] = mapped_column(Date, default=None)
    training_done_at: Mapped[date | None] = mapped_column(Date, default=None)
    evidence_approved_by: Mapped[str | None] = mapped_column(String(120), default=None)
    evidence_invoice_ref: Mapped[str | None] = mapped_column(String(80), default=None)
    evidence_workflow_confirmed: Mapped[bool] = mapped_column(default=False)
    evidence_approved_at: Mapped[date | None] = mapped_column(Date, default=None)
    evidence_recorded_by: Mapped[str | None] = mapped_column(String(120), default=None)
    next_action: Mapped[str | None] = mapped_column(String(200), default=None)
    follow_up_date: Mapped[date | None] = mapped_column(Date, default=None)
    internal_blocker: Mapped[str | None] = mapped_column(String(200), default=None)
    # Activity milestone (or first_value) this blocker is holding up.
    internal_blocker_milestone: Mapped[str | None] = mapped_column(String(40), default=None)
    internal_blocker_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    customer_blocker: Mapped[str | None] = mapped_column(String(200), default=None)
    # Activity milestone (or first_value) this blocker is holding up.
    customer_blocker_milestone: Mapped[str | None] = mapped_column(String(40), default=None)
    customer_blocker_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    status: Mapped[str] = mapped_column(String(40), default="on_track")
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    workspace: Mapped["DemoWorkspace"] = relationship(back_populates="accounts")
    history: Mapped[list["HistoryEntry"]] = relationship(back_populates="account")


class HistoryEntry(Base):
    """Append-only history. actor_role records which role did the action."""

    __tablename__ = "history_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    actor_role: Mapped[str] = mapped_column(String(40))
    action: Mapped[str] = mapped_column(String(80))
    detail: Mapped[str] = mapped_column(Text, default="")
    # True when the entry records a simulation (e.g. a customer update the
    # manager recorded on the customer's behalf). Always false otherwise.
    simulated: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    account: Mapped["Account"] = relationship(back_populates="history")
