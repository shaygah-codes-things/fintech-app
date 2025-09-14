# Fintech App

Full-stack fintech demo app built with **FastAPI + PostgreSQL + React**.  
Implements secure OAuth login, payout creation/listing, webhook updates, idempotency, retries, and observability.

---

## Features

- **Authentication**

  - GitHub OAuth (state + PKCE)
  - Session cookie–based auth
  - Rate-limited login endpoints

- **Payouts**

  - `POST /payouts` with **Idempotency-Key** header (safe to retry)
  - Retries to mock provider with **bounded exponential backoff + jitter**
  - `GET /payouts?page&limit` returns paginated list
  - Frontend shows statuses (`processing`, `paid`, `failed`), refresh/polling for live updates

- **Webhooks**

  - `POST /webhooks/payments` from mock provider
  - HMAC signature check (`x-sig`) over `ts.payload` with shared secret
  - Timestamp freshness (`x-sig-ts`, reject if > 5 min skew)
  - Idempotent on `event_id`

- **Resilience and Security**

  - Per-user rate limits (SlowAPI)
  - Input validation via Pydantic (currency whitelist)
  - Normalized JSON error bodies (`{error, message, details?, request_id?}`)
  - No secrets or PII in logs

- **Observability**

  - Correlation IDs: `X-Correlation-ID` generated if absent, logged, returned in responses, propagated to provider and webhooks
  - Structured logs with timing, status, request_id

- **Deliverables**
  - [openapi.yaml](./openapi.yaml) — API spec
  - [Fintech-App-API.postman_collection.json](./Fintech-App-API.postman_collection.json) — Postman collection
  - [docs/logs.md](./docs/logs.md) — correlation ID log walkthrough
  - [ai_usage.md](./ai_usage.md) — notes on AI collaboration

---

## Architecture

frontend/ -> React + Vite app
backend/ -> FastAPI + SQLAlchemy + Alembic
mock-payments/ -> Mock third-party provider (with retries + webhooks)

Services are wired with **docker-compose**: backend, frontend, Postgres, and mock-payments.

---

## Getting Started

### Prerequisites

- Docker + docker-compose
- GitHub OAuth app (Client ID/Secret)

### Environment variables

Create `.env` (see `.env.example`):

```ini
OAUTH_CLIENT_ID=your_github_app_client_id
OAUTH_CLIENT_SECRET=your_github_app_client_secret
OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
FRONTEND_URL=http://localhost:5173
SESSION_SECRET=dev-only-change-me
WEBHOOK_SHARED_SECRET=super-secret-123
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/app

### Run

docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000

### API Documentation

openapi.yaml
— OpenAPI 3 spec

Fintech-App-API.postman_collection.json
— ready to import into Postman

### Authentication in Postman

Open http://localhost:8000/auth/login
in your browser and log in with GitHub.

In browser DevTools -> Application -> Cookies -> copy the session value.

Paste into Postman collection variable session.

Ensure Postman User-Agent header matches your browser’s navigator.userAgent.

Session cookies are bound to User-Agent for safety.

## Tests

```cd backend
pytest -q
```

Covers:

- Payout idempotency
- Webhook signature and timestamp verification
- Rate limit edge cases

## Observability

see docs/logs.md

Example correlation ID log flow:

```INFO payout_created id=42 status=processing cid=cid-1747...
INFO webhook_received event=payout.updated payout_id=42 status=paid cid=cid-1747...
```

## AI Usage

See ai_usage.md
for notes on how AI tools were used, what was accepted/rejected, and validation steps.
