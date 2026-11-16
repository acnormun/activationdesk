"""Builders for small synthetic accounts used in the domain tests."""

from __future__ import annotations

from datetime import date, timedelta

from app.domain.models import (
    Account,
    Blocker,
    BlockerSide,
    BlockerStatus,
    Milestone,
    MilestoneKind,
    MilestoneStatus,
    NextAction,
)


def activity(
    status: MilestoneStatus = MilestoneStatus.NOT_STARTED,
    name: str = "Setup",
    order: int = 1,
) -> Milestone:
    return Milestone(
        name=name,
        kind=MilestoneKind.ACTIVITY,
        order=order,
        status=status,
        completed_at=None,
        evidence=None,
    )


def value(
    status: MilestoneStatus = MilestoneStatus.NOT_STARTED,
    evidence=None,
) -> Milestone:
    return Milestone(
        name="First value",
        kind=MilestoneKind.VALUE,
        order=4,
        status=status,
        completed_at=None,
        evidence=evidence,
    )


def blocker(
    side: BlockerSide = BlockerSide.INTERNAL,
    status: BlockerStatus = BlockerStatus.OPEN,
    opened_at: date | None = None,
    owner: str | None = None,
    id: str = "b1",
) -> Blocker:
    return Blocker(
        id=id,
        description="Sample blocker",
        side=side,
        owner=owner,
        status=status,
        resolved_via=None,
        opened_at=opened_at,
        resolved_at=None,
    )


def make_account(
    *,
    id: str = "acc",
    name: str = "Acc",
    target: date,
    start: date | None = None,
    owner: str | None = "Ana",
    milestones: tuple[Milestone, ...] = (),
    blockers: tuple[Blocker, ...] = (),
    next_action: NextAction | None = None,
) -> Account:
    return Account(
        id=id,
        name=name,
        desired_outcome=(
            "The customer's finance owner approves a representative invoice "
            "through the agreed workflow."
        ),
        start_date=start,
        target_date=target,
        owner=owner,
        last_reviewed_at=None,
        milestones=milestones,
        blockers=blockers,
        next_action=next_action,
    )


def window_account(
    today: date,
    *,
    elapsed: int,
    total: int,
    name: str = "Acc",
    owner: str | None = "Ana",
    milestones: tuple[Milestone, ...] | None = None,
    blockers: tuple[Blocker, ...] = (),
) -> Account:
    """Account inside a planned window: start = today - elapsed days,
    target = start + total days."""
    start = today - timedelta(days=elapsed)
    return make_account(
        id=name.lower(),
        name=name,
        start=start,
        target=start + timedelta(days=total),
        owner=owner,
        milestones=milestones if milestones is not None else (value(),),
        blockers=blockers,
    )
