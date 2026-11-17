"""Account routes: reads plus the 8 write actions of the Roles and access table.

Every write runs change + history + Pipeline 1 recalculation in a single
transaction (apply_change). Dependencies keep the check order:
session (401) -> permission (403) -> scope (404) -> business rule (422).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..business import validate_action
from ..database import get_db
from ..deps import Actor, get_actor, get_scoped_account
from ..models import Account, HistoryEntry, utcnow
from ..permissions import (
    ASSIGN_OWNER,
    CLOSE_CUSTOMER_BLOCKER,
    CLOSE_INTERNAL_BLOCKER,
    OPEN_INTERNAL_BLOCKER,
    RECORD_PROGRESS,
    RECORD_VALUE_EVIDENCE,
    SET_NEXT_ACTION,
    SET_TARGET_DATE,
    VIEW_ACCOUNT,
    VIEW_DASHBOARD,
    require_permission,
)
from datetime import date

from ..domain.models import Evidence, Milestone, MilestoneKind, MilestoneStatus
from ..domain.status import derive_status
from ..facts import recalculate, to_domain
from ..domain.validation import validate_evidence
from ..schemas import (
    AccountOut,
    AssignOwnerRequest,
    BlockerRequest,
    CustomerUpdateRequest,
    EvidenceRequest,
    HistoryOut,
    NoteRequest,
    SetNextActionRequest,
    SetTargetDateRequest,
)

router = APIRouter(prefix="/accounts", tags=["accounts"])


def account_out(account: Account) -> AccountOut:
    """Serialize an account; status and flags come from the domain layer."""
    data = AccountOut.model_validate(account)
    result = derive_status(to_domain(account), date.today())
    return data.model_copy(
        update={
            "status": result.status.value,
            "flags": [flag.value for flag in result.flags],
        }
    )


def apply_change(
    db: Session,
    account: Account,
    actor_role: str,
    action: str,
    mutate,
    detail: str,
) -> None:
    """One transaction: fact change + history entry + domain recalculation."""
    mutate()
    recalculate(account)
    db.add(
        HistoryEntry(
            account_id=account.id,
            actor_role=actor_role,
            action=action,
            detail=detail,
        )
    )
    db.commit()


@router.get("", response_model=list[AccountOut])
def list_accounts(
    actor: Actor = Depends(get_actor),
    _: None = Depends(require_permission(VIEW_DASHBOARD)),
    db: Session = Depends(get_db),
) -> list[AccountOut]:
    """Dashboard: accounts in the session workspace (scoped users see only theirs)."""
    query = db.query(Account).filter(Account.workspace_id == actor.workspace_id)
    if actor.user.account_ref:
        query = query.filter(Account.slug == actor.user.account_ref)
    return [account_out(a) for a in query.all()]


@router.get("/{slug}")
def account_detail(
    slug: str,
    actor: Actor = Depends(get_actor),
    _: None = Depends(require_permission(VIEW_ACCOUNT)),
    account: Account = Depends(get_scoped_account),
    db: Session = Depends(get_db),
) -> dict:
    """Account detail with its history (newest first)."""
    history = (
        db.query(HistoryEntry)
        .filter(HistoryEntry.account_id == account.id)
        .order_by(HistoryEntry.created_at.desc())
        .all()
    )
    return {
        "account": account_out(account),
        "history": [HistoryOut.model_validate(h).model_dump(mode="json") for h in history],
    }


@router.post("/{slug}/owner", response_model=AccountOut)
def assign_owner(
    slug: str,
    body: AssignOwnerRequest,
    actor: Actor = Depends(get_actor),
    _: None = Depends(require_permission(ASSIGN_OWNER)),
    account: Account = Depends(get_scoped_account),
    db: Session = Depends(get_db),
) -> AccountOut:
    """Assign the account owner."""
    reason = validate_action(ASSIGN_OWNER, account, body.model_dump())
    if reason:
        raise HTTPException(status_code=422, detail=reason)
    owner = body.owner.strip()

    def mutate() -> None:
        account.owner = owner

    apply_change(db, account, actor.role, ASSIGN_OWNER, mutate, f"Owner set to '{owner}'.")
    return account_out(account)


@router.post("/{slug}/target-date", response_model=AccountOut)
def set_target_date(
    slug: str,
    body: SetTargetDateRequest,
    actor: Actor = Depends(get_actor),
    _: None = Depends(require_permission(SET_TARGET_DATE)),
    account: Account = Depends(get_scoped_account),
    db: Session = Depends(get_db),
) -> AccountOut:
    """Set a new target date."""
    reason = validate_action(SET_TARGET_DATE, account, body.model_dump())
    if reason:
        raise HTTPException(status_code=422, detail=reason)
    target = body.target_date

    def mutate() -> None:
        account.target_date = target

    apply_change(
        db, account, actor.role, SET_TARGET_DATE, mutate,
        f"Target date set to {target.isoformat()}.",
    )
    return account_out(account)


@router.post("/{slug}/next-action", response_model=AccountOut)
def set_next_action(
    slug: str,
    body: SetNextActionRequest,
    actor: Actor = Depends(get_actor),
    _: None = Depends(require_permission(SET_NEXT_ACTION)),
    account: Account = Depends(get_scoped_account),
    db: Session = Depends(get_db),
) -> AccountOut:
    """Set the next action and its follow-up date."""
    reason = validate_action(SET_NEXT_ACTION, account, body.model_dump())
    if reason:
        raise HTTPException(status_code=422, detail=reason)
    next_action = body.next_action.strip()
    follow_up = body.follow_up_date

    def mutate() -> None:
        account.next_action = next_action
        account.follow_up_date = follow_up

    apply_change(
        db, account, actor.role, SET_NEXT_ACTION, mutate,
        f"Next action '{next_action}' (follow-up {follow_up.isoformat()}).",
    )
    return account_out(account)


@router.post("/{slug}/progress", response_model=AccountOut)
def record_progress(
    slug: str,
    body: NoteRequest,
    actor: Actor = Depends(get_actor),
    _: None = Depends(require_permission(RECORD_PROGRESS)),
    account: Account = Depends(get_scoped_account),
    db: Session = Depends(get_db),
) -> AccountOut:
    """Record a progress note (history only; no fact changes)."""
    reason = validate_action(RECORD_PROGRESS, account, body.model_dump())
    if reason:
        raise HTTPException(status_code=422, detail=reason)
    note = body.note.strip()

    def mutate() -> None:
        pass  # progress is recorded in the history only

    apply_change(db, account, actor.role, RECORD_PROGRESS, mutate, f"Progress note: {note}")
    return account_out(account)


@router.post("/{slug}/internal-blocker", response_model=AccountOut)
def open_internal_blocker(
    slug: str,
    body: BlockerRequest,
    actor: Actor = Depends(get_actor),
    _: None = Depends(require_permission(OPEN_INTERNAL_BLOCKER)),
    account: Account = Depends(get_scoped_account),
    db: Session = Depends(get_db),
) -> AccountOut:
    """Open an internal blocker."""
    reason = validate_action(OPEN_INTERNAL_BLOCKER, account, body.model_dump())
    if reason:
        raise HTTPException(status_code=422, detail=reason)
    description = body.description.strip()

    def mutate() -> None:
        account.internal_blocker = description
        account.internal_blocker_opened_at = utcnow()

    apply_change(
        db, account, actor.role, OPEN_INTERNAL_BLOCKER, mutate,
        f"Internal blocker: {description}",
    )
    return account_out(account)


@router.post("/{slug}/internal-blocker/close", response_model=AccountOut)
def close_internal_blocker(
    slug: str,
    actor: Actor = Depends(get_actor),
    _: None = Depends(require_permission(CLOSE_INTERNAL_BLOCKER)),
    account: Account = Depends(get_scoped_account),
    db: Session = Depends(get_db),
) -> AccountOut:
    """Close the internal blocker."""
    reason = validate_action(CLOSE_INTERNAL_BLOCKER, account, {})
    if reason:
        raise HTTPException(status_code=422, detail=reason)

    def mutate() -> None:
        account.internal_blocker = None
        account.internal_blocker_opened_at = None

    apply_change(db, account, actor.role, CLOSE_INTERNAL_BLOCKER, mutate, "Internal blocker closed.")
    return account_out(account)


@router.post("/{slug}/customer-blocker/close", response_model=AccountOut)
def close_customer_blocker(
    slug: str,
    body: CustomerUpdateRequest,
    actor: Actor = Depends(get_actor),
    _: None = Depends(require_permission(CLOSE_CUSTOMER_BLOCKER)),
    account: Account = Depends(get_scoped_account),
    db: Session = Depends(get_db),
) -> AccountOut:
    """Close the customer blocker with a (simulated) customer update."""
    reason = validate_action(CLOSE_CUSTOMER_BLOCKER, account, body.model_dump())
    if reason:
        raise HTTPException(status_code=422, detail=reason)
    update_text = body.customer_update.strip()

    def mutate() -> None:
        account.customer_blocker = None
        account.customer_blocker_opened_at = None

    apply_change(
        db, account, actor.role, CLOSE_CUSTOMER_BLOCKER, mutate,
        f"Customer blocker closed. Update: {update_text}",
    )
    return account_out(account)


@router.post("/{slug}/value-evidence", response_model=AccountOut)
def record_value_evidence(
    slug: str,
    body: EvidenceRequest,
    actor: Actor = Depends(get_actor),
    _: None = Depends(require_permission(RECORD_VALUE_EVIDENCE)),
    account: Account = Depends(get_scoped_account),
    db: Session = Depends(get_db),
) -> AccountOut:
    """Record first-value evidence; the domain layer validates it before
    saving (activation still comes only from valid evidence)."""
    today = date.today()
    evidence = Evidence(
        approved_by=body.approved_by,
        invoice_ref=body.invoice_ref,
        via_agreed_workflow=body.via_agreed_workflow,
        approved_at=body.approved_at,
        recorded_by=body.recorded_by,
    )
    milestone = Milestone(
        name="First value",
        kind=MilestoneKind.VALUE,
        order=1,
        status=MilestoneStatus.DONE,
        completed_at=evidence.approved_at,
        evidence=evidence,
    )
    reason = validate_action(RECORD_VALUE_EVIDENCE, account, {})
    if reason:
        raise HTTPException(status_code=422, detail=reason)
    errors = validate_evidence(evidence, milestone, today)
    if errors:
        raise HTTPException(status_code=422, detail=" ".join(errors))

    def mutate() -> None:
        account.evidence_approved_by = evidence.approved_by
        account.evidence_invoice_ref = evidence.invoice_ref
        account.evidence_workflow_confirmed = evidence.via_agreed_workflow
        account.evidence_approved_at = evidence.approved_at
        account.evidence_recorded_by = evidence.recorded_by

    apply_change(
        db, account, actor.role, RECORD_VALUE_EVIDENCE, mutate,
        f"Value evidence: invoice {evidence.invoice_ref} approved by "
        f"{evidence.approved_by}.",
    )
    return account_out(account)
