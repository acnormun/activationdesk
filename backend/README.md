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
- Every login creates an isolated demo workspace with the six starting cases
  from the instructions (Alpha-Zeta), covering every Pipeline 1 lane.
- To switch to PostgreSQL later, uncomment the PostgreSQL URL in `.env` and
  start the compose stack.

## Request checks (every request, in this order)

1. Valid session -> otherwise **401**
2. Account exists in the workspace -> otherwise **404**
3. Business rules -> otherwise **422**, with the reason

## Single demo user

| Username | Password | Role |
|---|---|---|
| manager | manager123 | onboarding_manager |

The onboarding manager is the only user of the app: sees every account,
can perform every write action and closes customer blockers by recording
the (simulated) customer update.

- Every login creates an isolated demo workspace seeded with mock accounts.
- Not included (demo-only): sign-up, password recovery, user management and configurable permissions.

## Writes

Every change runs in a single PostgreSQL transaction: fact change + history
entry (with `actor_role`) + Pipeline 1 status recalculation.
