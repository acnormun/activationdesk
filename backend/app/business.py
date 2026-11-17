"""Check 4 - business rules.

validate_action returns the rejection reason (HTTP 422) or None when the
change is allowed.
"""

from .models import Account

# Action names shared by the routers and the business rules. The demo has a
# single user (the onboarding manager): there is no role matrix anymore.
VIEW_DASHBOARD = "view_dashboard"
VIEW_ACCOUNT = "view_account"
ASSIGN_OWNER = "assign_owner"
SET_TARGET_DATE = "set_target_date"
SET_NEXT_ACTION = "set_next_action"
RECORD_PROGRESS = "record_progress"
OPEN_INTERNAL_BLOCKER = "open_internal_blocker"
OPEN_CUSTOMER_BLOCKER = "open_customer_blocker"
CLOSE_INTERNAL_BLOCKER = "close_internal_blocker"
CLOSE_CUSTOMER_BLOCKER = "close_customer_blocker"
RECORD_VALUE_EVIDENCE = "record_value_evidence"
UPDATE_MILESTONE = "update_milestone"

# Activity milestones: persisted column for each public milestone name.
ACTIVITY_MILESTONES = {
    "setup": "setup_done_at",
    "import": "import_done_at",
    "training": "training_done_at",
}

# Milestones a blocker may reference: the three activity milestones plus
# the first value milestone.
BLOCKER_MILESTONES = {"setup", "import", "training", "first_value"}
from .domain.models import Status
from .facts import has_evidence

MUTATING_ACTIONS = {
    ASSIGN_OWNER,
    SET_TARGET_DATE,
    SET_NEXT_ACTION,
    RECORD_PROGRESS,
    OPEN_INTERNAL_BLOCKER,
    OPEN_CUSTOMER_BLOCKER,
    CLOSE_INTERNAL_BLOCKER,
    CLOSE_CUSTOMER_BLOCKER,
    RECORD_VALUE_EVIDENCE,
    UPDATE_MILESTONE,
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
    if action in (OPEN_INTERNAL_BLOCKER, OPEN_CUSTOMER_BLOCKER):
        if not (payload.get("description") or "").strip():
            return "Blocker description is required."
        if action == OPEN_INTERNAL_BLOCKER and account.internal_blocker:
            return "An internal blocker is already open."
        if action == OPEN_CUSTOMER_BLOCKER and account.customer_blocker:
            return "A customer blocker is already open."
        milestone = (payload.get("milestone") or "").strip()
        if not milestone:
            return "Blocker milestone is required: choose setup, import, training or first_value."
        if milestone not in BLOCKER_MILESTONES:
            return "Unknown milestone: use setup, import, training or first_value."
    if action == CLOSE_INTERNAL_BLOCKER and not account.internal_blocker:
        return "No internal blocker is open."
    if action == CLOSE_CUSTOMER_BLOCKER:
        if not account.customer_blocker:
            return "No customer blocker is open."
        if not (payload.get("customer_update") or "").strip():
            return "Closing a customer blocker requires a (simulated) customer update."
    if action == RECORD_VALUE_EVIDENCE and has_evidence(account):
        return "First value is already registered with evidence."
    if action == UPDATE_MILESTONE:
        column = ACTIVITY_MILESTONES.get(payload.get("milestone") or "")
        if column is None:
            return "Unknown activity milestone."
        if getattr(account, column) is not None:
            return "That milestone is already done."
    return None
