"""Pipeline 1 status: first match wins, recomputed from the facts.

The status is never stored: ``derive_status`` reads the account facts and
returns the status plus the hygiene flags for the given day.

Order (first match wins):
1. ACTIVATED: value milestone DONE with evidence that passes validation.
2. WAITING_ON_CUSTOMER: any OPEN blocker owned by the customer.
3. BLOCKED_INTERNAL: any OPEN blocker owned by our team.
4. OVERDUE: today is past the target date.
5. ON_TRACK: otherwise.

Flags are computed only for accounts that are NOT activated. A passed
target never changes WAITING_ON_CUSTOMER; it only adds PAST_TARGET.
Resolving a blocker never activates an account: only valid evidence does.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .models import (
    Account,
    Blocker,
    BlockerSide,
    BlockerStatus,
    Flag,
    MilestoneStatus,
    Status,
)
from .validation import validate_evidence


@dataclass(frozen=True)
class StatusResult:
    """Computed status and hygiene flags for one account on one day."""

    status: Status
    flags: tuple[Flag, ...]

    def has_flag(self, flag: Flag) -> bool:
        return flag in self.flags


def _open_blockers(account: Account) -> list[Blocker]:
    return [
        blocker
        for blocker in account.blockers
        if blocker.status is BlockerStatus.OPEN
    ]


def _has_valid_value_evidence(account: Account, today: date) -> bool:
    milestone = account.value_milestone
    if milestone is None:
        return False
    if milestone.status is not MilestoneStatus.DONE:
        return False
    if milestone.evidence is None:
        return False
    return validate_evidence(milestone.evidence, milestone, today) == []


def _flags_for(account: Account, today: date) -> tuple[Flag, ...]:
    flags: list[Flag] = []
    if account.owner is None or account.owner.strip() == "":
        flags.append(Flag.NO_OWNER)
    if account.next_action is None:
        flags.append(Flag.NO_NEXT_ACTION)
    elif account.next_action.follow_up_date < today:
        flags.append(Flag.FOLLOW_UP_LATE)
    if today > account.target_date:
        flags.append(Flag.PAST_TARGET)
    return tuple(flags)


def derive_status(account: Account, today: date) -> StatusResult:
    """First match wins: activated, waiting on customer, blocked internal,
    overdue, otherwise on track."""
    if _has_valid_value_evidence(account, today):
        return StatusResult(status=Status.ACTIVATED, flags=())

    open_blockers = _open_blockers(account)
    if any(blocker.side is BlockerSide.CUSTOMER for blocker in open_blockers):
        status = Status.WAITING_ON_CUSTOMER
    elif any(blocker.side is BlockerSide.INTERNAL for blocker in open_blockers):
        status = Status.BLOCKED_INTERNAL
    elif today > account.target_date:
        status = Status.OVERDUE
    else:
        status = Status.ON_TRACK

    return StatusResult(status=status, flags=_flags_for(account, today))
