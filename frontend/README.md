# Activation Desk — Frontend (Vue 3 + Vite + TypeScript)

SPA for the onboarding manager workbench. Talks to the FastAPI backend in
`backend/` (default `http://localhost:8000`); the session lives in the
HttpOnly cookie `activationdesk_session` and CORS already allows
`http://localhost:3000` with credentials (`backend/app/main.py`), so the
dev server is pinned to port 3000.

## Requirements

- Node.js 22 + npm 10 (on this machine:
  `export PATH="$HOME/.local/node/bin:$PATH"`)
- Backend running:
  `cd backend && .venv/bin/python -m uvicorn app.main:app --port 8000`

## Run

```bash
cd frontend
npm install
npm run dev # http://localhost:3000
```

The backend origin is read at runtime from `/config.js` (`window.__API_BASE__`),
defaulting to `http://localhost:8000`. To point elsewhere in local dev, edit
`public/config.js`. In Docker, set the `API_BASE` environment variable (nginx
rewrites `config.js` at container start).

## Test and build

```bash
npm test # vitest, unit tests for the pure helpers
npm run build # type-checks with vue-tsc and builds to dist/
```

## Workbench

The workbench at `/` is the internal panel:

- **Week plan** — `GET /plan/week` rendered as the six priority lanes, with
  the explainable score per intervention entry, nudge levels and slot usage.
- **Accounts** — `GET /accounts` cards with status, flags, target date,
  owner, next action, open blockers and first-value evidence. Filter by
  status and free text, with explicit empty states.
- **Actions** — the write actions of the Roles and access table, gated in
  the UI by `GET /permissions`: assign owner, set target date, set next
  action, record progress, open/close internal blocker, close customer
  blocker (finance role) and record value evidence. Activated accounts
  accept no further changes (mirrors the backend rule).
- **History** — selecting an account loads `GET /accounts/{slug}` and shows
  the append-only history.

Pure helpers (lane metadata, labels, filters, permission checks) live in
`src/utils/workbench.ts` and are covered by `test/workbench.spec.ts`.

## Demo accounts

`manager/manager123` (full access) · `finance/finance123` (Beta scope only) ·
`cshead/cshead123` (read-only)
