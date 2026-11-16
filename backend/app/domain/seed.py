"""Sample day and the six seeded demo accounts.

Everything here is synthetic data for demos and tests; no real customer.
Assumptions baked into the numbers (documented so they are auditable):

- The company sells invoice-approval software, so first value is the same
  desired outcome for every account: the customer's finance owner approves
  a representative invoice through the agreed workflow, with recorded
  evidence.
- All dates are relative to ``SAMPLE_DAY`` (D): "D-4" means four days
  before it, "D+3" three days after it.
- ``start_date`` is D-14 and ``owner`` is "Ana" for every account unless
  stated otherwise for that account.
- Activity milestones follow the default template Setup / Data import /
  Training. Milestones marked done as an assumption (the brief does not
  say when they finished) get ``completed_at = D - 7``; that date never
  affects any rule (only blocker ``opened_at`` and evidence ``approved_at``
  feed the calculations).
- ``last_reviewed_at`` stays None everywhere the brief does not mention a
  review: missing data is kept, not invented.
"""

from __future__ import annotations

from datetime import date, timedelta

from .models import (
    Account,
    Blocker,
    BlockerSide,
    BlockerStatus,
    Evidence,
    Milestone,
    MilestoneKind,
    MilestoneStatus,
    NextAction,
)

SAMPLE_DAY = date(2026, 11, 16)

DESIRED_OUTCOME = (
    "The customer's finance owner approves a representative invoice "
    "through the agreed workflow, with recorded evidence (first value)."
)

ACTIVITY_TEMPLATE = ("Setup", "Data import", "Training")

ASSUMED_COMPLETED_AT = SAMPLE_DAY - timedelta(days=7)


def _activities(states: dict[str, MilestoneStatus]) -> tuple[Milestone, ...]:
    """The default activity template with a status per step."""
    return tuple(
        Milestone(
            name=name,
            kind=MilestoneKind.ACTIVITY,
            order=order,
            status=states.get(name, MilestoneStatus.NOT_STARTED),
            completed_at=(
                ASSUMED_COMPLETED_AT
                if states.get(name) is MilestoneStatus.DONE
                else None
            ),
            evidence=None,
        )
        for order, name in enumerate(ACTIVITY_TEMPLATE, start=1)
    )


def _value_milestone(
    status: MilestoneStatus = MilestoneStatus.NOT_STARTED,
    evidence: Evidence | None = None,
    completed_at: date | None = None,
) -> Milestone:
    return Milestone(
        name="First value",
        kind=MilestoneKind.VALUE,
        order=4,
        status=status,
        completed_at=completed_at,
        evidence=evidence,
    )


def _blocker(
    id: str,
    description: str,
    side: BlockerSide,
    owner: str | None,
    opened_at: date,
) -> Blocker:
    return Blocker(
        id=id,
        description=description,
        side=side,
        owner=owner,
        status=BlockerStatus.OPEN,
        resolved_via=None,
        opened_at=opened_at,
        resolved_at=None,
    )


def _build_accounts() -> tuple[Account, ...]:
    gamma_evidence = Evidence(
        approved_by="Carla Mendes (finance owner)",
        invoice_ref="INV-1042",
        via_agreed_workflow=True,
        approved_at=SAMPLE_DAY - timedelta(days=1),
        recorded_by="Ana",
    )

    alpha = Account(
        id="alpha",
        name="Alpha Corp",
        desired_outcome=DESIRED_OUTCOME,
        start_date=SAMPLE_DAY - timedelta(days=14),
        target_date=SAMPLE_DAY + timedelta(days=3),
        owner="Ana",
        last_reviewed_at=None,
        milestones=_activities(
            {
                "Setup": MilestoneStatus.DONE,
                "Data import": MilestoneStatus.DONE,  # assumed
                "Training": MilestoneStatus.DONE,
            }
        )
        + (_value_milestone(),),
        blockers=(
            _blocker(
                "alpha-1",
                "Sample-data mapping issue",
                BlockerSide.INTERNAL,
                "Data specialist",
                SAMPLE_DAY - timedelta(days=4),
            ),
        ),
        next_action=None,
    )

    beta = Account(
        id="beta",
        name="Beta Ltd",
        desired_outcome=DESIRED_OUTCOME,
        start_date=SAMPLE_DAY - timedelta(days=14),
        target_date=SAMPLE_DAY + timedelta(days=2),
        owner="Ana",
        last_reviewed_at=None,
        milestones=_activities(
            {
                "Setup": MilestoneStatus.DONE,
                "Data import": MilestoneStatus.DONE,
                # Training NOT_STARTED is itself an assumption of the sample.
                "Training": MilestoneStatus.NOT_STARTED,
            }
        )
        + (_value_milestone(),),
        blockers=(
            _blocker(
                "beta-1",
                "Approval policy not provided",
                BlockerSide.CUSTOMER,
                "Customer finance lead",
                SAMPLE_DAY - timedelta(days=4),
            ),
        ),
        next_action=None,
    )

    gamma = Account(
        id="gamma",
        name="Gamma SA",
        desired_outcome=DESIRED_OUTCOME,
        start_date=SAMPLE_DAY - timedelta(days=14),
        target_date=SAMPLE_DAY,
        owner="Ana",
        last_reviewed_at=None,
        milestones=_activities(
            {
                "Setup": MilestoneStatus.DONE,
                "Data import": MilestoneStatus.DONE,
                "Training": MilestoneStatus.DONE,
            }
        )
        + (
            _value_milestone(
                status=MilestoneStatus.DONE,
                evidence=gamma_evidence,
                completed_at=SAMPLE_DAY - timedelta(days=1),
            ),
        ),
        blockers=(),
        next_action=None,
    )

    delta = Account(
        id="delta",
        name="Delta LLC",
        desired_outcome=DESIRED_OUTCOME,
        start_date=SAMPLE_DAY - timedelta(days=14),
        target_date=SAMPLE_DAY + timedelta(days=7),
        owner="Pedro (implementation)",
        last_reviewed_at=None,
        milestones=_activities({"Setup": MilestoneStatus.IN_PROGRESS})
        + (_value_milestone(),),
        blockers=(),
        next_action=NextAction(
            description="Finish approval workflow setup",
            owner="Pedro",
            follow_up_date=SAMPLE_DAY + timedelta(days=1),
        ),
    )

    epsilon = Account(
        id="epsilon",
        name="Epsilon GmbH",
        desired_outcome=DESIRED_OUTCOME,
        start_date=SAMPLE_DAY - timedelta(days=30),
        target_date=SAMPLE_DAY - timedelta(days=5),
        owner=None,
        last_reviewed_at=None,
        milestones=_activities({}) + (_value_milestone(),),
        blockers=(),
        next_action=None,
    )

    zeta = Account(
        id="zeta",
        name="Zeta Inc",
        desired_outcome=DESIRED_OUTCOME,
        start_date=SAMPLE_DAY - timedelta(days=14),
        target_date=SAMPLE_DAY + timedelta(days=1),
        owner="Ana",
        last_reviewed_at=None,
        milestones=_activities(
            {
                "Setup": MilestoneStatus.DONE,
                "Data import": MilestoneStatus.DONE,  # assumed
                "Training": MilestoneStatus.DONE,
            }
        )
        + (_value_milestone(),),
        blockers=(
            _blocker(
                "zeta-1",
                (
                    "Customer disputes that the sample workflow matches "
                    "their real approval process"
                ),
                BlockerSide.INTERNAL,
                "Ana",
                SAMPLE_DAY - timedelta(days=2),
            ),
        ),
        next_action=None,
    )

    return (alpha, beta, gamma, delta, epsilon, zeta)


SAMPLE_ACCOUNTS: tuple[Account, ...] = _build_accounts()


def account_by_id(account_id: str) -> Account:
    """Return the seeded account with the given id (KeyError if absent)."""
    for account in SAMPLE_ACCOUNTS:
        if account.id == account_id:
            return account
    raise KeyError(f"No seeded account with id '{account_id}'.")
