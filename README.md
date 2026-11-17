# Activation Desk — an onboarding workbench

A small decision tool for an invoice-approval SaaS onboarding team. It replaces a shared task checklist with a queue that distinguishes **verified first value** from **activity completed**, and makes the owner of every remaining dependency explicit.

Demo login: **manager / manager123**.

---

## Buyer, user and business outcome

- **Buyer:** the head of customer success at a fictional invoice-approval software company.
- **Primary user:** an onboarding manager with six new accounts and capacity to actively unblock **two** this week.
- **Business outcome:** more customers reach a verified, useful outcome — a representative invoice approved through the agreed workflow — with less time spent on accounts that only look healthy because tasks are ticked.
- **Workflow replaced:** a shared checklist that shows task completion, not whether the customer has approved a representative invoice. The workbench adds outcome evidence, dependency ownership, a decision about where to spend the two intervention slots, and a next action with an owner and follow-up.

## First value: the definition used

> The customer's finance owner has approved a representative invoice through the agreed workflow, and an approval record with the approver, invoice reference, approval date and workflow is attached as evidence.

This is deliberately stronger than "setup complete". These do **not** establish first value:

- importing data, configuring the workflow, or finishing training;
- an internal task marked done;
- a verbal claim with no approval record;
- an approval against a workflow the customer disputes.

## The six seeded cases

Dates are relative to the login day.

| Account | Target | What is happening | Expected status | This week |
|---|---|---|---|---|
| **Alpha** | in 3 days | Setup and training done; import blocked by a sample-data mapping issue | Blocked — internal | Intervene (#1) |
| **Beta** | in 2 days | Data imported; the customer has not sent the approval policy | Waiting on customer | Nudge |
| **Gamma** | today | Finance owner approved a representative invoice yesterday; evidence recorded | Activated | None |
| **Delta** | in 7 days | Setup incomplete; internal owner has work scheduled tomorrow | On track | Monitor |
| **Epsilon** | 5 days ago | No first value; owner and next action unknown | Overdue + no owner | Triage |
| **Zeta** | tomorrow | Training done; customer disputes whether the sample workflow matches their process | Blocked — internal | Intervene (#2) |

Gamma is shown as **activated**, not as unfinished onboarding.

## How the two interventions are chosen

Status, flags and priority are **recalculated from the facts after every change** — never stored. First match wins:

1. **Activated** (first value + valid evidence) → out of the queue.
2. **Waiting on customer** (open customer blocker) → Nudge lane, never a slot.
3. **Blocked — internal** (open internal blocker) → candidate for a slot.
4. **Overdue** (target passed) → candidate, unless it has no owner (Triage).
5. **On track** → Monitor.

Eligible accounts are ordered by a **rule-based score (0–100), not a prediction**:

| Factor | Points |
|---|---|
| Urgency (deadline consumption) | Overdue 50 · Critical 40 · Attention 20 · Comfortable 0 |
| Stagnation (oldest internal blocker) | 0–2d 0 · 3–5d 10 · 6+d 20 |
| Closeness (pending activities) | 0 → 20 · 1 → 10 · 2+ → 0 |
| Follow-up (missing or late) | 10 |

Tie-break: urgency, then stagnation, then name. Unknown data scores 0 and shows "not calculated". Customer-blocked accounts are nudged (Remind before the target, Escalate after), never scored. Clearing a blocker is progress, not activation — only valid evidence activates.

**The trade-off:** the prioritisation is a short, explainable rule rather than a predictive model, so it is auditable but does not forecast whether the customer will activate.

## The proposed success metric

**Time to verified first value (TVFV)**

- **Start:** the account start date (kickoff).
- **End:** the recorded approval date on the evidence — not the date someone typed it in.

The dashboard shows the median and `n`. Completed task count is insufficient because a checklist can be 100% complete with zero verified value: Alpha has every activity done except the blocked import, Beta has prep done with an open customer blocker, and Zeta has training done with a disputed workflow.

This is a demo observation (`n=1`), not a claim of revenue, savings or retention impact.

## What is deliberately not done

- No real customer invoice engine, CRM/calendar integration, messaging or notifications.
- No multi-user permissions or production auth (one demo user).
- No implementation of the customer-owned dependency — we record the ask, not the artifact.
- No AI model or paid API.
- Activity milestones are seeded from a fixed template (Setup, Import, Training), though the model treats milestones as generic (any number, any name).

## Engineering choices

- **FastAPI + SQLAlchemy**, PostgreSQL (production) with a SQLite fallback (local dev).
- **Vue 3 + Vite + TypeScript + Pinia**, hand-written CSS, no UI framework.
- **Derived state**: a pure domain layer recomputes status, flags, score and lanes from the facts; nothing is stored as a stale label.
- **Isolated demo workspaces**: each login clones the seed, so reviewers never overwrite each other.
- **Append-only history** with a `simulated` flag that labels recorded customer updates.
- **Single service**: the FastAPI backend serves the built frontend on the same origin, so there is no CORS or cross-origin cookie configuration.

## Local setup

```bash
# Single service (PostgreSQL + API serving the built frontend) on :8000
docker compose -f docker-compose.dev.yml up -d --build

# Or run the API manually (SQLite fallback) and the frontend with hot-reload:
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000

cd frontend
npm install
npm run dev                             # http://localhost:3000 (proxies the API to :8000)
```

Environment variables live in a single reference at the repo root: `.env.example`.

## Tests

```bash
cd backend && python -m unittest discover -s tests -t .   # 98 tests
cd frontend && npm test                                    # 24 tests
cd frontend && npm run build                               # type-check + build
```

Backend tests cover the six derived statuses, the priority score and its boundaries, and the validation rules: activation without evidence, next action without owner/follow-up, customer blocker closed without a customer update, and blocker opened without a milestone.

## Reviewer walkthrough

1. **Dashboard** — six accounts, the cohort metric, and the two focus slots (Alpha and Zeta).
2. **Alpha vs Beta** — open each: Alpha is ours to fix (internal mapping); Beta is customer-owned (approval policy) and cannot be closed by an internal task.
3. **Close Beta's blocker** — it is refused without a recorded (simulated) customer update.
4. **Confirm first value on Zeta** — the workflow is disputed, so activation is blocked until it is agreed.
5. **Gamma** — reads as verified first value, not unfinished onboarding.
6. **Activate Alpha** — resolve the internal blocker (with a resolution note), then confirm first value with evidence. The status recomputes and the slot compacts.
7. **Empty state** — filter to a status with no matches; reload to confirm persistence.

## Known limitations and next steps

**Limitations:** single demo user; the seed uses a fixed activity template; no real customer data; the metric is `n=1`; no file uploads; dates are day-granularity.

**Next steps:** replace recorded approvals with a product audit event; add a server database with auth; add CRM/calendar sources; add evidence attachments and a verifier role; track the metric over cohorts.
