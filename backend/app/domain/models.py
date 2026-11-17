"""Domain models: enums and frozen dataclasses describing account facts.

Frozen dataclasses keep facts immutable; rules rebuild a modified copy
with ``dataclasses.replace`` instead of mutating anything. Missing data
stays ``None`` and is reported as "not calculated" downstream - it is
never estimated or invented.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date


class MilestoneKind(enum.Enum):
    """Whether a milestone is an activity step or the value milestone."""

    ACTIVITY = "activity"
    VALUE = "value"


class MilestoneStatus(enum.Enum):
    """Progress of a single milestone."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class BlockerSide(enum.Enum):
    """Who owns the unblock: our team (internal) or the customer."""

    INTERNAL = "internal"
    CUSTOMER = "customer"


class BlockerStatus(enum.Enum):
    """Lifecycle of a blocker."""

    OPEN = "open"
    RESOLVED = "resolved"


class ResolvedVia(enum.Enum):
    """How a blocker got resolved."""

    INTERNAL_FIX = "internal_fix"
    CUSTOMER_UPDATE_SIMULATED = "customer_update_simulated"


class Role(enum.Enum):
    """The single demo user: the onboarding manager does everything."""

    ONBOARDING_MANAGER = "onboarding_manager"


class Status(enum.Enum):
    """Account status, recalculated from the facts after every change."""

    ACTIVATED = "activated"
    WAITING_ON_CUSTOMER = "waiting_on_customer"
    BLOCKED_INTERNAL = "blocked_internal"
    OVERDUE = "overdue"
    ON_TRACK = "on_track"


class Flag(enum.Enum):
    """Hygiene flags computed for accounts that are not activated yet."""

    NO_OWNER = "no_owner"
    NO_NEXT_ACTION = "no_next_action"
    FOLLOW_UP_LATE = "follow_up_late"
    PAST_TARGET = "past_target"


class Lane(enum.Enum):
    """This week's intervention lane for an account."""

    INTERVENTION = "intervention"
    WAITING_FOR_CAPACITY = "waiting_for_capacity"
    TRIAGE = "triage"
    NUDGE = "nudge"
    MONITOR = "monitor"
    NO_INTERVENTION = "no_intervention"


class NudgeLevel(enum.Enum):
    """How hard the customer nudge should be this week."""

    REMIND = "remind"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class Evidence:
    """Recorded proof that first value happened through the agreed workflow."""

    approved_by: str
    invoice_ref: str
    via_agreed_workflow: bool
    approved_at: date
    recorded_by: str


@dataclass(frozen=True)
class Milestone:
    """A tracked step. Every account has exactly one milestone of kind VALUE."""

    name: str
    kind: MilestoneKind
    order: int
    status: MilestoneStatus
    completed_at: date | None
    evidence: Evidence | None


@dataclass(frozen=True)
class Blocker:
    """Something blocking progress. ``side`` says who owns the unblock.

    ``milestone`` optionally names the activity milestone (setup, import,
    training or first_value) this blocker is holding up, keeping the
    remaining dependency explicit (Instructions.md: "make the resulting
    state and remaining dependencies clear").
    """

    id: str
    description: str
    side: BlockerSide
    owner: str | None
    milestone: str | None
    status: BlockerStatus
    resolved_via: ResolvedVia | None
    opened_at: date | None
    resolved_at: date | None


@dataclass(frozen=True)
class NextAction:
    """The single next step the team committed to, with a follow-up date."""

    description: str
    owner: str
    follow_up_date: date


@dataclass(frozen=True)
class Account:
    """Account facts. Status, flags, score and lane are never stored here."""

    id: str
    name: str
    desired_outcome: str
    start_date: date | None
    target_date: date
    owner: str | None
    last_reviewed_at: date | None
    milestones: tuple[Milestone, ...]
    blockers: tuple[Blocker, ...]
    next_action: NextAction | None

    @property
    def value_milestone(self) -> Milestone | None:
        """The VALUE milestone, or None when the account has none (invalid)."""
        for milestone in self.milestones:
            if milestone.kind is MilestoneKind.VALUE:
                return milestone
        return None
