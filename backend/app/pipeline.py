"""Pipeline 1 - status recalculation (first match wins).

    first value done WITH evidence  -> activated (no intervention)
    customer blocker open           -> waiting_on_customer (nudge lane)
    internal blocker open           -> blocked_internal (slot ranking)
    target date passed              -> overdue (slot ranking)
    otherwise                       -> on_track (monitor)

The status column only stores the last computed value; it is recalculated
from the facts after every saved change and never written by hand.
"""

from datetime import date, datetime, timezone

from .models import Account

ACTIVATED = "activated"
WAITING_ON_CUSTOMER = "waiting_on_customer"
BLOCKED_INTERNAL = "blocked_internal"
OVERDUE = "overdue"
ON_TRACK = "on_track"


def recalculate_status(account: Account, today: date | None = None) -> str:
    """Recalculate account.status from its facts (Pipeline 1 order)."""
    today = today or date.today()
    if account.first_value_done and account.value_evidence:
        account.status = ACTIVATED
        if account.activated_at is None:
            account.activated_at = datetime.now(timezone.utc)
    elif account.customer_blocker:
        account.status = WAITING_ON_CUSTOMER
    elif account.internal_blocker:
        account.status = BLOCKED_INTERNAL
    elif account.target_date < today:
        account.status = OVERDUE
    else:
        account.status = ON_TRACK
    return account.status


def compute_flags(account: Account, today: date | None = None) -> list[str]:
    """Flags shown next to the status. A passed target never changes
    'waiting_on_customer'; it only adds the past_target flag."""
    today = today or date.today()
    flags: list[str] = []
    if not account.owner:
        flags.append("no_owner")
    if not account.next_action:
        flags.append("no_next_action")
    if account.target_date < today and account.status == WAITING_ON_CUSTOMER:
        flags.append("past_target")
    return flags
