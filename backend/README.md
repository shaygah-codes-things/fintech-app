# Backend (FastAPI)

## Run (local)

```bash
# Start Postgres
docker compose up -d db

# Setup and run backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Run mock payments provider
cd mock-payments
uvicorn app.main:app --reload --port 8081
```

## Env vars

See `.env` at repo root. Important:

- `DATABASE_URL`
- `WEBHOOK_SHARED_SECRET`
- `MOCK_URL`

## Migrations

```bash
cd backend
source .venv/bin/activate
python -m alembic revision --autogenerate -m "..."
python -m alembic upgrade head
```

## Tests

```bash
cd backend
pytest -q
```

## API Docs

Visit [http://localhost:8000/docs](http://localhost:8000/docs) after starting the backend.
