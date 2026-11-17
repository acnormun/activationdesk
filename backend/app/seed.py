"""Demo seed: one example user (created once) and mock accounts per workspace.

Demo-only access: no sign-up, no password recovery, no user management and
no configurable permissions.
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .models import Account, DemoWorkspace, Role, User
from .facts import recalculate
from .security import hash_password

DEMO_USERS = [
    {"username": "manager", "password": "manager123", "role": Role.ONBOARDING_MANAGER, "account_ref": None},
]


def ensure_demo_users(db: Session) -> None:
    """Create the example users once (idempotent)."""
    for spec in DEMO_USERS:
        exists = db.query(User).filter(User.username == spec["username"]).first()
        if exists is not None:
            continue
        db.add(
            User(
                username=spec["username"],
                password_hash=hash_password(spec["password"]),
                role=spec["role"],
                account_ref=spec["account_ref"],
            )
        )
    db.commit()


def seed_workspace_accounts(db: Session, workspace: DemoWorkspace) -> None:
    """The instructions' six starting cases (Alpha-Zeta), with dates relative
    to the demo login day; facts mirror app/domain/seed.py (the demo database
    does not track activity milestones, only the VALUE milestone evidence)."""
    today = date.today()
    now = datetime.now(timezone.utc)
    desired_outcome = (
        "The customer's finance owner approves a representative invoice "
        "through the agreed workflow, with recorded evidence (first value)."
    )
    accounts = [
        Account(
            workspace_id=workspace.id,
            slug="alpha",
            name="Alpha Corp",
            desired_outcome=desired_outcome,
            owner="Ana",
            start_date=today - timedelta(days=14),
            target_date=today + timedelta(days=3),
            internal_blocker="Sample-data mapping issue",
            internal_blocker_opened_at=now - timedelta(days=4),
        ),
        Account(
            workspace_id=workspace.id,
            slug="beta",
            name="Beta LLC",
            desired_outcome=desired_outcome,
            owner="Ana",
            start_date=today - timedelta(days=14),
            target_date=today + timedelta(days=2),
            customer_blocker="Approval policy not provided",
            customer_blocker_opened_at=now - timedelta(days=4),
        ),
        Account(
            workspace_id=workspace.id,
            slug="gamma",
            name="Gamma SA",
            desired_outcome=desired_outcome,
            owner="Ana",
            start_date=today - timedelta(days=14),
            target_date=today,
            evidence_approved_by="Morgan Lee",
            evidence_invoice_ref="INV-2041",
            evidence_workflow_confirmed=True,
            evidence_approved_at=today - timedelta(days=1),
            evidence_recorded_by="Dana Reed",
        ),
        Account(
            workspace_id=workspace.id,
            slug="delta",
            name="Delta LLC",
            desired_outcome=desired_outcome,
            owner="Ana",
            start_date=today - timedelta(days=14),
            target_date=today + timedelta(days=7),
            next_action="Schedule the customer training session",
            follow_up_date=today + timedelta(days=1),
        ),
        Account(
            workspace_id=workspace.id,
            slug="epsilon",
            name="Epsilon GmbH",
            desired_outcome=desired_outcome,
            owner=None,
            start_date=today - timedelta(days=14),
            target_date=today - timedelta(days=5),
        ),
        Account(
            workspace_id=workspace.id,
            slug="zeta",
            name="Zeta Inc",
            desired_outcome=desired_outcome,
            owner="Ana",
            start_date=today - timedelta(days=14),
            target_date=today + timedelta(days=1),
            internal_blocker="Disputed invoice does not match the workflow",
            internal_blocker_opened_at=now - timedelta(days=2),
        ),
    ]
    for account in accounts:
        recalculate(account)
    db.add_all(accounts)
    db.commit()
