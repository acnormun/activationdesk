# Activation Desk API

Pipeline 0 - access and request flow. FastAPI + PostgreSQL with mock data.

## Stack

- FastAPI (Python 3.10+), SQLAlchemy 2, PyJWT (session token in an HttpOnly cookie), bcrypt
- PostgreSQL for the mock data (SQLite fallback for quick local runs without Docker)

## Run

```bash
# 1. PostgreSQL (from the repository root)
docker compose -f docker-compose.dev.yml up -d

# 2. API
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # points to the compose PostgreSQL
uvicorn app.main:app --reload

# 3. Tests
python -m unittest discover -s tests -v
```

### Run without Docker (mock SQLite database)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload   # no .env: runs on sqlite:///./activationdesk.dev.db
```

- Without a `.env` file the API runs on a local mock SQLite database, created
  and seeded automatically at startup (git-ignored).
- Every login creates an isolated demo workspace with 5 mock accounts covering
  every Pipeline 1 lane.
- To switch to PostgreSQL later, uncomment the PostgreSQL URL in `.env` and
  start the compose stack.

## Request checks (every request, in this order)

1. Valid session -> otherwise **401**
2. Role with permission -> otherwise **403**, saying which role is allowed
3. Account inside the user scope -> otherwise **404**
4. Business rules -> otherwise **422**, with the reason

## Roles and access (10 actions x 3 roles)

| Action | Onboarding manager | Client finance | CS head |
|---|---|---|---|
| view_dashboard | yes | yes (own account) | yes |
| view_account | yes | yes (own account) | yes |
| assign_owner | yes | no | no |
| set_target_date | yes | no | no |
| set_next_action | yes | no | no |
| record_progress | yes | no | no |
| open_internal_blocker | yes | no | no |
| close_internal_blocker | yes | no | no |
| close_customer_blocker | no | yes (own account) | no |
| record_value_evidence | yes | no | no |

The UI colors for this table live in the Nuxt app; the API serves the matrix at `GET /permissions`.

## Demo-only access

| Username | Password | Role | Scope |
|---|---|---|---|
| manager | manager123 | onboarding_manager | all accounts in the workspace |
| finance | finance123 | client_finance | Beta account only |
| cshead | cshead123 | cs_head | read-only |

- Every login creates an isolated demo workspace seeded with mock accounts.
- Not included (demo-only): sign-up, password recovery, user management and configurable permissions.

## Writes

Every change runs in a single PostgreSQL transaction: fact change + history
entry (with `actor_role`) + Pipeline 1 status recalculation.
