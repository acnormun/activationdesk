"""Input validation: every function returns a list of human-readable errors.

An empty list means the input is valid. Messages say what is wrong and
what to do about it, written for the onboarding manager rather than for
logs.
"""

from __future__ import annotations

from datetime import date

from .models import (
    Blocker,
    BlockerSide,
    BlockerStatus,
    Evidence,
    Milestone,
    MilestoneKind,
    NextAction,
    ResolvedVia,
    Role,
)


def _is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def validate_evidence(evidence: Evidence | None, milestone: Milestone | None, today: date) -> list[str]:
    """Evidence is valid only on the VALUE milestone, complete, recorded as
    going through the agreed workflow, and not dated in the future."""
    errors: list[str] = []
    if milestone is None:
        return [
            "No milestone given: evidence must be recorded on the account's "
            "VALUE milestone (first value)."
        ]
    if milestone.kind is not MilestoneKind.VALUE:
        errors.append(
            "Evidence can only be recorded on the VALUE milestone (first "
            f"value), not on the activity milestone '{milestone.name}'."
        )
    if evidence is None:
        errors.append(
            "Evidence is missing: record who approved the invoice, the "
            "invoice reference, whether it followed the agreed workflow, "
            "when it was approved and who recorded it."
        )
        return errors
    if _is_blank(evidence.approved_by):
        errors.append(
            "Evidence is missing the approver: record the name of the "
            "customer finance owner who approved the invoice."
        )
    if _is_blank(evidence.invoice_ref):
        errors.append(
            "Evidence is missing the invoice reference: record the invoice "
            "number that was approved."
        )
    if evidence.via_agreed_workflow is not True:
        errors.append(
            "Approval did not go through the agreed workflow: first value "
            "requires the invoice approval to follow the agreed workflow, "
            "so redo the approval there before recording it."
        )
    if evidence.approved_at is None:
        errors.append(
            "Evidence is missing the approval date: record when the invoice "
            "was approved."
        )
    elif evidence.approved_at > today:
        errors.append(
            f"Evidence approval date {evidence.approved_at.isoformat()} is "
            f"in the future (today is {today.isoformat()}): fix the date "
            "before recording first value."
        )
    return errors


def validate_next_action(action: NextAction | None, today: date) -> list[str]:
    """A next action needs a description, an owner and a follow-up date
    that is not in the past (today itself is fine)."""
    if action is None:
        return [
            "Next action is missing: set what happens next, who owns it and "
            "the follow-up date."
        ]
    errors: list[str] = []
    if _is_blank(action.description):
        errors.append(
            "Next action has no description: write what specifically "
            "happens next."
        )
    if _is_blank(action.owner):
        errors.append(
            "Next action has no owner: name the person responsible for it."
        )
    if action.follow_up_date is None:
        errors.append(
            "Next action has no follow-up date: set when the team checks "
            "on it."
        )
    elif action.follow_up_date < today:
        errors.append(
            f"Next action follow-up date {action.follow_up_date.isoformat()} "
            f"is in the past (today is {today.isoformat()}): move the "
            "follow-up to today or later."
        )
    return errors


def validate_blocker_resolution(
    blocker: Blocker, via: ResolvedVia | None, actor_role: Role | None
) -> list[str]:
    """Only the blocker's owner side can resolve it, and only through the
    matching route: customer blockers need a customer update confirmed by
    the customer finance lead; internal blockers need an internal fix by
    the onboarding manager."""
    if blocker.status is not BlockerStatus.OPEN:
        return [
            f"Blocker '{blocker.description}' is not open: only an open "
            "blocker can be resolved."
        ]
    errors: list[str] = []
    if blocker.side is BlockerSide.CUSTOMER:
        if via is not ResolvedVia.CUSTOMER_UPDATE_SIMULATED:
            errors.append(
                "Only a customer update can resolve a customer-owned "
                "blocker: ask the customer finance lead to confirm the "
                "update instead of fixing it internally."
            )
        if actor_role is not Role.CUSTOMER_FINANCE_LEAD:
            errors.append(
                "Only the customer finance lead can resolve a "
                "customer-owned blocker: route the resolution to them."
            )
    else:  # BlockerSide.INTERNAL
        if via is not ResolvedVia.INTERNAL_FIX:
            errors.append(
                "An internal blocker is resolved by an internal fix, not "
                "by a customer update."
            )
        if actor_role is not Role.ONBOARDING_MANAGER:
            errors.append(
                "Only the onboarding manager can resolve an internal "
                "blocker: route the resolution to them."
            )
    return errors


def validate_dates(start_date: date | None, target_date: date | None) -> list[str]:
    """The target date must fall after the start date (when both exist)."""
    if (
        start_date is not None
        and target_date is not None
        and target_date <= start_date
    ):
        return [
            f"Target date {target_date.isoformat()} must be after the "
            f"start date {start_date.isoformat()}: move the target later."
        ]
    return []


def validate_milestones(milestones: tuple[Milestone, ...]) -> list[str]:
    """Every account must have exactly one VALUE milestone."""
    value_count = sum(
        1 for milestone in milestones if milestone.kind is MilestoneKind.VALUE
    )
    if value_count != 1:
        return [
            "An account must have exactly one VALUE milestone (first "
            f"value), found {value_count}: keep one VALUE milestone per "
            "account."
        ]
    return []
