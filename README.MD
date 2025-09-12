# Fintech Payouts — Take-Home

## Stack

- Backend: FastAPI, SQLAlchemy, Alembic
- DB: Postgres (dev/prod), SQLite (unit tests)
- Mock provider: FastAPI (simulated webhooks)
- Frontend: React (Vite)

## Run locally

1. Start Postgres:

   ```bash
   docker compose up -d db
   ```

2. Backend:
   ```cd backend
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python -m alembic upgrade head
    uvicorn app.main:app --reload --port 8000
   ```
3. Mock-payments:
   ```cd mock-payments
    python -m venv .venv && source .venv/bin/activate
    pip install fastapi uvicorn httpx
    export WEBHOOK_SHARED_SECRET=changeme
    export WEBHOOK_TARGET=http://localhost:8000/webhooks/payments
    uvicorn app.main:app --reload --port 8081
   ```
4. Frontend:
   ```cd frontend
   npm install
   echo "VITE_API_BASE=http://localhost:8000" > .env
   npm run dev
   ```
