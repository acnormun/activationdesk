# Activation Desk — Frontend (Vue 3 + Vite + TypeScript)

SPA for the onboarding manager workbench. Calls the FastAPI backend on the
**same origin** (the backend serves the built frontend). In local dev, the
Vite server proxies the API paths to `http://localhost:8000` (see
`vite.config.ts`). The session lives in the HttpOnly cookie
`activationdesk_session`.

## Requirements

- Node.js 22 + npm 10.
- Backend running:
  `cd backend && python -m uvicorn app.main:app --port 8000`.

## Run

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000 — proxies /auth, /accounts, /plan, /health to :8000
```

## Test and build

```bash
npm test         # vitest, unit tests for the pure helpers
npm run build    # type-checks with vue-tsc and builds to dist/
```

The production build (`dist/`) is served by the backend via the single-service
Dockerfile at the repo root.

## Workbench

The workbench at `/` is the internal panel:

- **Week plan** — `GET /plan/week` rendered as the priority lanes, with the
  explainable score, nudge levels and slot usage.
- **Accounts** — `GET /accounts` cards with status, flags, target date,
  owner, next action, blockers and first-value evidence. Filter by status
  and free text.
- **Account detail** — `GET /accounts/{slug}` page with milestones, blockers,
  evidence, actions and history.
- **Actions** — assign owner, set next action, record progress, open/close
  blockers, and confirm first value (with evidence).

Pure helpers live in `src/utils/workbench.ts` and are covered by
`test/workbench.spec.ts`.

## Demo login

`manager / manager123` (the single onboarding-manager user).
