"""Demo seed: 3 example users (created once) and mock accounts per workspace.

Demo-only access: no sign-up, no password recovery, no user management and
no configurable permissions.
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .models import Account, DemoWorkspace, Role, User
from .pipeline import recalculate_status
from .security import hash_password

DEMO_USERS = [
    {"username": "manager", "password": "manager123", "role": Role.ONBOARDING_MANAGER, "account_ref": None},
    {"username": "finance", "password": "finance123", "role": Role.CLIENT_FINANCE, "account_ref": "beta"},
    {"username": "cshead", "password": "cshead123", "role": Role.CS_HEAD, "account_ref": None},
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
    """Mock accounts for a fresh workspace, covering every Pipeline 1 lane."""
    today = date.today()
    now = datetime.now(timezone.utc)
    accounts = [
        Account(
            workspace_id=workspace.id,
            slug="alpha",
            name="Alpha Corp",
            owner="Dana Reed",
            start_date=today - timedelta(days=15),
            target_date=today + timedelta(days=15),
            next_action="Schedule the kickoff call",
            follow_up_date=today + timedelta(days=2),
        ),
        Account(
            workspace_id=workspace.id,
            slug="beta",
            name="Beta LLC",
            owner="Dana Reed",
            start_date=today - timedelta(days=10),
            target_date=today + timedelta(days=5),
            customer_blocker="Waiting for the client data feed",
            customer_blocker_opened_at=now - timedelta(days=3),
        ),
        Account(
            workspace_id=workspace.id,
            slug="gamma",
            name="Gamma Partners",
            start_date=today - timedelta(days=30),
            target_date=today - timedelta(days=2),
        ),
        Account(
            workspace_id=workspace.id,
            slug="delta",
            name="Delta Systems",
            owner="Evan Ortiz",
            start_date=today - timedelta(days=12),
            target_date=today + timedelta(days=18),
            internal_blocker="Blocked by the data migration",
            internal_blocker_opened_at=now - timedelta(days=7),
        ),
        Account(
            workspace_id=workspace.id,
            slug="epsilon",
            name="Epsilon Group",
            owner="Dana Reed",
            start_date=today - timedelta(days=25),
            target_date=today + timedelta(days=5),
            first_value_done=True,
            value_evidence="First value delivered: reporting dashboard is live.",
        ),
    ]
    for account in accounts:
        recalculate_status(account)
    db.add_all(accounts)
    db.commit()
