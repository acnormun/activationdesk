"""Bridge between persisted account rows and the pure domain layer.

The database stores account facts; the domain derives status, flags and
priority from them. This module is the only place that maps between the
two, so the API never duplicates a domain rule.

Mapping notes (demo scope):
- Three activity milestones (Setup, Import, Training) come from the
  *_done_at columns; "First value" remains the only VALUE milestone.
- Only OPEN blockers are mapped: closing a blocker clears the column, so
  resolved history is not persisted yet.
- A next action is mapped only when it has a follow-up date (the write
  action already requires one).
"""

from datetime import date

from .domain.models import (
    Account as DomainAccount,
    Blocker,
    BlockerSide,
    BlockerStatus,
    Evidence,
    Milestone,
    MilestoneKind,
    MilestoneStatus,
    NextAction,
    Status,
)
from .domain.status import StatusResult, derive_status
from .models import Account, utcnow


def has_evidence(account: Account) -> bool:
    """True when first-value evidence is recorded."""
    return account.evidence_approved_at is not None


def to_domain(account: Account) -> DomainAccount:
    """Map a persisted account row to the frozen domain dataclass."""
    evidence: Evidence | None = None
    milestone_status = MilestoneStatus.NOT_STARTED
    completed_at: date | None = None
    if has_evidence(account):
        evidence = Evidence(
            approved_by=account.evidence_approved_by or "",
            invoice_ref=account.evidence_invoice_ref or "",
            via_agreed_workflow=account.evidence_workflow_confirmed,
            approved_at=account.evidence_approved_at,
            recorded_by=account.evidence_recorded_by or "",
        )
        milestone_status = MilestoneStatus.DONE
        completed_at = account.evidence_approved_at

    activity_specs = (
        ("Setup", account.setup_done_at),
        ("Import", account.import_done_at),
        ("Training", account.training_done_at),
    )
    milestones = tuple(
        Milestone(
            name=name,
            kind=MilestoneKind.ACTIVITY,
            order=order,
            status=(
                MilestoneStatus.DONE
                if done_at is not None
                else MilestoneStatus.NOT_STARTED
            ),
            completed_at=done_at,
            evidence=None,
        )
        for order, (name, done_at) in enumerate(activity_specs, start=1)
    ) + (
        Milestone(
            name="First value",
            kind=MilestoneKind.VALUE,
            order=len(activity_specs) + 1,
            status=milestone_status,
            completed_at=completed_at,
            evidence=evidence,
        ),
    )

    blockers: list[Blocker] = []
    if account.internal_blocker:
        blockers.append(
            Blocker(
                id=f"internal-{account.slug}",
                description=account.internal_blocker,
                side=BlockerSide.INTERNAL,
                owner=None,
                status=BlockerStatus.OPEN,
                resolved_via=None,
                opened_at=(
                    account.internal_blocker_opened_at.date()
                    if account.internal_blocker_opened_at
                    else None
                ),
                resolved_at=None,
            )
        )
    if account.customer_blocker:
        blockers.append(
            Blocker(
                id=f"customer-{account.slug}",
                description=account.customer_blocker,
                side=BlockerSide.CUSTOMER,
                owner=None,
                status=BlockerStatus.OPEN,
                resolved_via=None,
                opened_at=(
                    account.customer_blocker_opened_at.date()
                    if account.customer_blocker_opened_at
                    else None
                ),
                resolved_at=None,
            )
        )

    next_action: NextAction | None = None
    if account.next_action and account.follow_up_date:
        next_action = NextAction(
            description=account.next_action,
            owner=account.owner or "",
            follow_up_date=account.follow_up_date,
        )

    return DomainAccount(
        id=account.slug,
        name=account.name,
        desired_outcome=account.desired_outcome,
        start_date=account.start_date,
        target_date=account.target_date,
        owner=account.owner,
        last_reviewed_at=account.last_reviewed_at,
        milestones=milestones,
        blockers=tuple(blockers),
        next_action=next_action,
    )


def recalculate(account: Account, today: date | None = None) -> StatusResult:
    """Derive the status from the facts and refresh the cached column.

    The source of truth is always the facts plus ``derive_status``; the
    status column stays as a SQL-friendly cache written after every
    change, and activation timestamps the moment evidence became valid.
    """
    result = derive_status(to_domain(account), today or date.today())
    account.status = result.status.value
    if result.status is Status.ACTIVATED and account.activated_at is None:
        account.activated_at = utcnow()
    return result
