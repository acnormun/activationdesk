"""Roles and access: 10 actions x 3 roles.

The onboarding manager does everything EXCEPT closing the customer-side
blocker: only the (simulated) client finance closes it, and only on their
own account (Beta). The CS head is read-only.
"""

from fastapi import Depends, HTTPException, status

from .deps import Actor, get_actor
from .models import Role

VIEW_DASHBOARD = "view_dashboard"
VIEW_ACCOUNT = "view_account"
ASSIGN_OWNER = "assign_owner"
SET_TARGET_DATE = "set_target_date"
SET_NEXT_ACTION = "set_next_action"
RECORD_PROGRESS = "record_progress"
OPEN_INTERNAL_BLOCKER = "open_internal_blocker"
CLOSE_INTERNAL_BLOCKER = "close_internal_blocker"
CLOSE_CUSTOMER_BLOCKER = "close_customer_blocker"
RECORD_VALUE_EVIDENCE = "record_value_evidence"

ALL_ACTIONS = [
    VIEW_DASHBOARD,
    VIEW_ACCOUNT,
    ASSIGN_OWNER,
    SET_TARGET_DATE,
    SET_NEXT_ACTION,
    RECORD_PROGRESS,
    OPEN_INTERNAL_BLOCKER,
    CLOSE_INTERNAL_BLOCKER,
    CLOSE_CUSTOMER_BLOCKER,
    RECORD_VALUE_EVIDENCE,
]

ROLE_ACTIONS: dict[str, set[str]] = {
    Role.ONBOARDING_MANAGER: set(ALL_ACTIONS) - {CLOSE_CUSTOMER_BLOCKER},
    Role.CLIENT_FINANCE: {VIEW_DASHBOARD, VIEW_ACCOUNT, CLOSE_CUSTOMER_BLOCKER},
    Role.CS_HEAD: {VIEW_DASHBOARD, VIEW_ACCOUNT},
}


def roles_allowed(action: str) -> list[str]:
    """Roles that may perform the action (used in 403 responses)."""
    return [role for role, actions in ROLE_ACTIONS.items() if action in actions]


def require_permission(action: str):
    """Check 2 - the role must have permission, else 403 saying which role can."""

    def dependency(actor: Actor = Depends(get_actor)) -> None:
        if action not in ROLE_ACTIONS[actor.role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": f"Role '{actor.role}' is not allowed to perform '{action}'.",
                    "allowed_roles": roles_allowed(action),
                },
            )

    return dependency
