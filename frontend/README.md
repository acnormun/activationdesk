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

The backend origin comes from `VITE_API_BASE`; override without editing
code: `VITE_API_BASE=http://127.0.0.1:9000 npm run dev`.

## Test and build

```bash
npm test # vitest, unit tests for the pure helpers
npm run build # type-checks with vue-tsc and builds to dist/
```

## Demo accounts

`manager/manager123` (full access) · `finance/finance123` (Beta scope only) ·
`cshead/cshead123` (read-only)
