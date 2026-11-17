"""Week plan route: the pure domain priority engine over workspace accounts.

GET /plan/week derives the lanes, the explainable score per scored entry
and the slot usage. Nothing here decides priority: the domain layer does;
this router only maps rows, calls plan_week and serializes the result.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import Actor, get_actor
from ..domain.models import Lane
from ..domain.priority import ScoreComponent, WeekPlanEntry, plan_week
from ..facts import to_domain
from ..models import Account
from ..permissions import VIEW_DASHBOARD, require_permission

router = APIRouter(prefix="/plan", tags=["plan"])


def _component_out(component: ScoreComponent) -> dict:
    return {
        "label": component.label,
        "points": component.points,
        "reason": component.reason,
        "calculated": component.calculated,
    }


def _entry_out(entry: WeekPlanEntry) -> dict:
    data = {
        "account_slug": entry.account.id,
        "account_name": entry.account.name,
        "lane": entry.lane.value,
        "reason": entry.reason,
    }
    if entry.nudge_level is not None:
        data["nudge_level"] = entry.nudge_level.value
    if entry.score is not None:
        data["score_total"] = entry.score.total
        data["score"] = {
            "urgency": _component_out(entry.score.urgency),
            "stagnation": _component_out(entry.score.stagnation),
            "closeness": _component_out(entry.score.closeness),
            "followup": _component_out(entry.score.followup),
        }
    return data


@router.get("/week")
def week_plan(
    slots: int = Query(default=2, ge=1, le=8),
    actor: Actor = Depends(get_actor),
    _: None = Depends(require_permission(VIEW_DASHBOARD)),
    db: Session = Depends(get_db),
) -> dict:
    """This week's lanes for the workspace, computed by the domain layer."""
    today = date.today()
    rows = db.query(Account).filter(Account.workspace_id == actor.workspace_id)
    if actor.user.account_ref:
        # Pipeline 0 scope rule: client finance only sees their own account.
        rows = rows.filter(Account.slug == actor.user.account_ref)
    domain_accounts = tuple(to_domain(row) for row in rows.order_by(Account.slug))
    week = plan_week(domain_accounts, today, slots=slots)

    lanes: dict[str, list[dict]] = {lane.value: [] for lane in Lane}
    for entry in week.entries:
        lanes[entry.lane.value].append(_entry_out(entry))

    return {
        "today": today.isoformat(),
        "slots": week.slots,
        "empty_slots": week.empty_slots,
        "message": week.message,
        "lanes": lanes,
    }
