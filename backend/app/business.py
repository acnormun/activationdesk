"""Check 4 - business rules.

validate_action returns the rejection reason (HTTP 422) or None when the
change is allowed.
"""

from .models import Account
from .permissions import (
    ASSIGN_OWNER,
    CLOSE_CUSTOMER_BLOCKER,
    CLOSE_INTERNAL_BLOCKER,
    OPEN_INTERNAL_BLOCKER,
    RECORD_PROGRESS,
    RECORD_VALUE_EVIDENCE,
    SET_NEXT_ACTION,
    SET_TARGET_DATE,
)
from .domain.models import Status
from .facts import has_evidence

MUTATING_ACTIONS = {
    ASSIGN_OWNER,
    SET_TARGET_DATE,
    SET_NEXT_ACTION,
    RECORD_PROGRESS,
    OPEN_INTERNAL_BLOCKER,
    CLOSE_INTERNAL_BLOCKER,
    CLOSE_CUSTOMER_BLOCKER,
    RECORD_VALUE_EVIDENCE,
}


def validate_action(action: str, account: Account, payload: dict) -> str | None:
    """Return the reason to reject (HTTP 422), or None when allowed."""
    if action in MUTATING_ACTIONS and account.status == Status.ACTIVATED.value:
        return "Account is activated: no further intervention is allowed."

    if action == ASSIGN_OWNER and not (payload.get("owner") or "").strip():
        return "Owner name is required."
    if action == SET_TARGET_DATE:
        if payload.get("target_date") is None:
            return "Target date is required."
        if payload["target_date"] < account.start_date:
            return "Target date cannot be before the start date."
    if action == SET_NEXT_ACTION:
        if not (payload.get("next_action") or "").strip():
            return "Next action description is required."
        if not account.owner:
            return "Next action requires an owner on the account."
        if payload.get("follow_up_date") is None:
            return "Next action requires a follow-up date."
    if action == RECORD_PROGRESS and not (payload.get("note") or "").strip():
        return "Progress note is required."
    if action == OPEN_INTERNAL_BLOCKER:
        if not (payload.get("description") or "").strip():
            return "Blocker description is required."
        if account.internal_blocker:
            return "An internal blocker is already open."
    if action == CLOSE_INTERNAL_BLOCKER and not account.internal_blocker:
        return "No internal blocker is open."
    if action == CLOSE_CUSTOMER_BLOCKER:
        if not account.customer_blocker:
            return "No customer blocker is open."
        if not (payload.get("customer_update") or "").strip():
            return "Closing a customer blocker requires a (simulated) customer update."
    if action == RECORD_VALUE_EVIDENCE and has_evidence(account):
        return "First value is already registered with evidence."
    return None
