"""Weekly priority: an explainable rule score, not a prediction.

Every point carries a short reason so the onboarding manager can audit
why an account holds an intervention slot. Gates run before scoring:
activated and on-track accounts never consume capacity, customer-blocked
accounts are nudged instead (never scored, never take a slot), and
blocked/overdue accounts without an owner go to triage because nobody
can unblock them.

``deadline_consumption`` returns None when it cannot be known (no start
date, or a planned window that is not positive): missing data is never
estimated, and the urgency component then falls back to days only and is
marked as "not calculated".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .models import (
    Account,
    BlockerSide,
    BlockerStatus,
    Lane,
    MilestoneKind,
    MilestoneStatus,
    NudgeLevel,
    Status,
)
from .status import StatusResult, derive_status


@dataclass(frozen=True)
class ScoreComponent:
    """One scored dimension: its points plus the reason for them."""

    label: str
    points: int
    reason: str
    calculated: bool = True


@dataclass(frozen=True)
class ScoreBreakdown:
    """Explainable score: total plus one component per dimension."""

    urgency: ScoreComponent
    stagnation: ScoreComponent
    closeness: ScoreComponent
    followup: ScoreComponent

    @property
    def total(self) -> int:
        return (
            self.urgency.points
            + self.stagnation.points
            + self.closeness.points
            + self.followup.points
        )

    @property
    def not_calculated(self) -> tuple[str, ...]:
        """Labels of components that could not be calculated (missing data)."""
        components = (self.urgency, self.stagnation, self.closeness, self.followup)
        return tuple(c.label for c in components if not c.calculated)


@dataclass(frozen=True)
class WeekPlanEntry:
    """One account, the lane it landed in and why. Score only for scored
    lanes; nudge level only for the NUDGE lane."""

    account: Account
    lane: Lane
    reason: str
    score: ScoreBreakdown | None = None
    nudge_level: NudgeLevel | None = None


@dataclass(frozen=True)
class WeekPlan:
    """Every account with its lane for this week, plus slot usage."""

    entries: tuple[WeekPlanEntry, ...]
    slots: int
    empty_slots: int
    message: str

    def entries_in_lane(self, lane: Lane) -> tuple[WeekPlanEntry, ...]:
        return tuple(entry for entry in self.entries if entry.lane is lane)

    @property
    def intervention(self) -> tuple[WeekPlanEntry, ...]:
        return self.entries_in_lane(Lane.INTERVENTION)

    @property
    def waiting_for_capacity(self) -> tuple[WeekPlanEntry, ...]:
        return self.entries_in_lane(Lane.WAITING_FOR_CAPACITY)

    @property
    def triage(self) -> tuple[WeekPlanEntry, ...]:
        return self.entries_in_lane(Lane.TRIAGE)

    @property
    def nudge(self) -> tuple[WeekPlanEntry, ...]:
        return self.entries_in_lane(Lane.NUDGE)

    @property
    def monitor(self) -> tuple[WeekPlanEntry, ...]:
        return self.entries_in_lane(Lane.MONITOR)

    @property
    def no_intervention(self) -> tuple[WeekPlanEntry, ...]:
        return self.entries_in_lane(Lane.NO_INTERVENTION)


def deadline_consumption(account: Account, today: date) -> float | None:
    """How much of the planned window is spent (None = unknown).

    None when the account has no start date or the planned duration is
    not positive; missing data is never estimated.
    """
    if account.start_date is None:
        return None
    planned_days = (account.target_date - account.start_date).days
    if planned_days <= 0:
        return None
    return (today - account.start_date).days / planned_days


def _urgency_component(account: Account, today: date) -> ScoreComponent:
    days_left = (account.target_date - today).days
    consumption = deadline_consumption(account, today)
    if consumption is None:
        # Days-only fallback: consumption cannot be known without a start
        # date, so this component is marked as not calculated.
        if days_left < 0:
            return ScoreComponent(
                label="urgency",
                points=50,
                reason=(
                    f"Overdue: the target was {-days_left} day(s) ago; "
                    "consumption not calculated (no start date)."
                ),
                calculated=False,
            )
        if days_left <= 1:
            return ScoreComponent(
                label="urgency",
                points=40,
                reason=(
                    f"Critical: {days_left} day(s) to the target; "
                    "consumption not calculated (no start date)."
                ),
                calculated=False,
            )
        return ScoreComponent(
            label="urgency",
            points=0,
            reason=(
                f"Comfortable: {days_left} day(s) to the target; "
                "consumption not calculated (no start date)."
            ),
            calculated=False,
        )
    if days_left < 0:
        return ScoreComponent(
            label="urgency",
            points=50,
            reason=f"Overdue: the target date passed {-days_left} day(s) ago.",
        )
    if consumption >= 0.80 or days_left <= 1:
        return ScoreComponent(
            label="urgency",
            points=40,
            reason=(
                f"Critical: {days_left} day(s) left and "
                f"{consumption:.0%} of the planned window spent."
            ),
        )
    if consumption >= 0.50:
        return ScoreComponent(
            label="urgency",
            points=20,
            reason=(
                f"Attention: {days_left} day(s) left and "
                f"{consumption:.0%} of the planned window spent."
            ),
        )
    return ScoreComponent(
        label="urgency",
        points=0,
        reason=(
            f"Comfortable: {days_left} day(s) left and "
            f"{consumption:.0%} of the planned window spent."
        ),
    )


def _stagnation_component(account: Account, today: date) -> ScoreComponent:
    open_internal = [
        blocker
        for blocker in account.blockers
        if blocker.status is BlockerStatus.OPEN
        and blocker.side is BlockerSide.INTERNAL
    ]
    if not open_internal:
        return ScoreComponent(
            label="stagnation",
            points=0,
            reason="No open internal blocker.",
        )
    known_dates = [b.opened_at for b in open_internal if b.opened_at is not None]
    if not known_dates:
        return ScoreComponent(
            label="stagnation",
            points=0,
            reason=(
                "Oldest open internal blocker has no opened date; "
                "stagnation not calculated."
            ),
            calculated=False,
        )
    oldest = min(known_dates)
    days_open = (today - oldest).days
    if days_open <= 2:
        points, band = 0, "0-2 days"
    elif days_open <= 5:
        points, band = 10, "3-5 days"
    else:
        points, band = 20, "6+ days"
    return ScoreComponent(
        label="stagnation",
        points=points,
        reason=(
            f"Oldest open internal blocker has been open for {days_open} "
            f"day(s) ({band})."
        ),
    )


def _closeness_component(account: Account) -> ScoreComponent:
    pending = sum(
        1
        for milestone in account.milestones
        if milestone.kind is MilestoneKind.ACTIVITY
        and milestone.status is not MilestoneStatus.DONE
    )
    if pending == 0:
        return ScoreComponent(
            label="closeness",
            points=20,
            reason="All activity milestones are done; only first value is missing.",
        )
    if pending == 1:
        return ScoreComponent(
            label="closeness",
            points=10,
            reason="1 activity milestone still pending before the value step.",
        )
    return ScoreComponent(
        label="closeness",
        points=0,
        reason=f"{pending} activity milestones still pending before the value step.",
    )


def _followup_component(account: Account, today: date) -> ScoreComponent:
    action = account.next_action
    if action is None:
        return ScoreComponent(
            label="followup",
            points=10,
            reason="No next action committed.",
        )
    if action.follow_up_date < today:
        return ScoreComponent(
            label="followup",
            points=10,
            reason=(
                f"Follow-up date {action.follow_up_date.isoformat()} "
                "already passed."
            ),
        )
    return ScoreComponent(
        label="followup",
        points=0,
        reason=f"Follow-up scheduled for {action.follow_up_date.isoformat()}.",
    )


def priority_score(account: Account, today: date) -> ScoreBreakdown:
    """Explainable urgency/stagnation/closeness/follow-up score."""
    return ScoreBreakdown(
        urgency=_urgency_component(account, today),
        stagnation=_stagnation_component(account, today),
        closeness=_closeness_component(account),
        followup=_followup_component(account, today),
    )


def _has_owner(account: Account) -> bool:
    return account.owner is not None and account.owner.strip() != ""


def _nudge_sort_key(entry: WeekPlanEntry, today: date) -> tuple[int, float]:
    consumption = deadline_consumption(entry.account, today)
    if consumption is None:
        return (1, 0.0)
    return (0, -consumption)


def plan_week(
    accounts: tuple[Account, ...] | list[Account], today: date, slots: int = 2
) -> WeekPlan:
    """Pick this week's lanes: gates first, then scoring for what is left."""
    no_intervention: list[WeekPlanEntry] = []
    monitor: list[WeekPlanEntry] = []
    nudges: list[WeekPlanEntry] = []
    triage: list[WeekPlanEntry] = []
    candidates: list[tuple[Account, StatusResult]] = []

    for account in accounts:
        result = derive_status(account, today)
        if result.status is Status.ACTIVATED:
            no_intervention.append(
                WeekPlanEntry(
                    account=account,
                    lane=Lane.NO_INTERVENTION,
                    reason=(
                        "Activated: first value done with valid evidence; "
                        "no intervention needed."
                    ),
                )
            )
        elif result.status is Status.ON_TRACK:
            monitor.append(
                WeekPlanEntry(
                    account=account,
                    lane=Lane.MONITOR,
                    reason="On track: keep monitoring, no intervention this week.",
                )
            )
        elif result.status is Status.WAITING_ON_CUSTOMER:
            level = (
                NudgeLevel.REMIND if today <= account.target_date else NudgeLevel.ESCALATE
            )
            nudges.append(
                WeekPlanEntry(
                    account=account,
                    lane=Lane.NUDGE,
                    reason=(
                        "Waiting on the customer: send a "
                        f"{level.value} nudge about the open customer blocker."
                    ),
                    nudge_level=level,
                )
            )
        elif not _has_owner(account):
            lane_label = result.status.value.replace("_", " ")
            triage.append(
                WeekPlanEntry(
                    account=account,
                    lane=Lane.TRIAGE,
                    reason=(
                        f"{lane_label.capitalize()} with no owner: nobody can "
                        "unblock it right now, so it needs triage first."
                    ),
                )
            )
        else:
            candidates.append((account, result))

    nudges.sort(key=lambda entry: _nudge_sort_key(entry, today))

    scored: list[tuple[Account, ScoreBreakdown]] = [
        (account, priority_score(account, today)) for account, _ in candidates
    ]
    scored.sort(
        key=lambda item: (
            -item[1].total,
            -item[1].urgency.points,
            -item[1].stagnation.points,
            item[0].name,
        )
    )

    intervention_entries: list[WeekPlanEntry] = []
    waiting_entries: list[WeekPlanEntry] = []
    for index, (account, breakdown) in enumerate(scored):
        if index < slots:
            intervention_entries.append(
                WeekPlanEntry(
                    account=account,
                    lane=Lane.INTERVENTION,
                    reason=(
                        f"Intervention slot {index + 1}: score {breakdown.total} "
                        f"(urgency {breakdown.urgency.points}, stagnation "
                        f"{breakdown.stagnation.points}, closeness "
                        f"{breakdown.closeness.points}, follow-up "
                        f"{breakdown.followup.points})."
                    ),
                    score=breakdown,
                )
            )
        else:
            waiting_entries.append(
                WeekPlanEntry(
                    account=account,
                    lane=Lane.WAITING_FOR_CAPACITY,
                    reason=(
                        f"Ranked #{index + 1} with score {breakdown.total}, "
                        f"below the {slots} intervention slot(s): capacity "
                        "went to higher-scoring accounts."
                    ),
                    score=breakdown,
                )
            )

    filled = len(intervention_entries)
    empty_slots = max(slots - filled, 0)
    message = (
        ""
        if empty_slots == 0
        else (
            f"{empty_slots} of {slots} intervention slot(s) unfilled. "
            "No other account our team can unblock right now."
        )
    )

    entries = (
        intervention_entries + waiting_entries + nudges + triage + monitor + no_intervention
    )
    return WeekPlan(
        entries=tuple(entries),
        slots=slots,
        empty_slots=empty_slots,
        message=message,
    )
