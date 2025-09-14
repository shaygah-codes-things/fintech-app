# AI Usage

This document explains how AI tools were used during development of the Fintech App.

---

## Tools Used

- **ChatGPT**: design discussions, generating starter code, debugging
- **GitHub Copilot**: inline code suggestions while editing

---

## Initial Goals Shared with AI

- Build a small full-stack fintech app with:
  - GitHub OAuth login
  - Payout creation with idempotency and retries
  - Webhook updates with signature and timestamp verification
  - Pagination, rate limiting, and correlation IDs
- Prioritize secure defaults (no secrets in code, validate inputs)
- Provide deliverables (OpenAPI spec, Postman collection, logs, AI usage doc)

---

## Accepted Outputs

- FastAPI router scaffolding for `/auth`, `/payouts`, and `/webhooks`
- Retry logic with bounded exponential backoff and jitter
- SQLAlchemy models and Alembic migration templates
- React components for payout form and list
- Postman collection skeleton and .http file examples
- OpenAPI spec draft structure

---

## Rejected or Modified Outputs

- OAuth examples without PKCE or state -> replaced with state+PKCE implementation
- AI-suggested raw error responses -> replaced with structured error JSON (`error`, `message`, `details`, `request_id`)
- Suggestions to log full request bodies -> removed to avoid secrets/PII
- Simplistic webhook handler without idempotency -> modified to enforce `event_id` uniqueness
- Suggestions to use `print` for logs -> replaced with structured `logger.info` and correlation IDs

---

## Mistakes Made by AI

- Proposed storing secrets directly in source -> corrected by using `.env`
- Generated retry loops without jitter -> fixed to add jitter for better backoff
- Suggested nonce validation for GitHub OAuth (not supported) -> clarified and dropped
- Produced pagination that returned all rows without total count -> adjusted to proper page/limit/total

---

## Validation of AI Outputs

- Manual review of all AI code before commit
- Added tests for:
  - Payout idempotency
  - Webhook signature and timestamp verification
  - Rate limiting
- Manual end-to-end test of OAuth login, payout creation, and webhook update flows
- Observed logs to confirm correlation IDs propagate across request -> provider -> webhook

---

## Trade-offs

- GitHub OAuth supports state+PKCE but not nonce; Google OIDC could be added later for nonce
- Live updates implemented via short polling instead of SSE/WebSockets due to time constraints
- Session cookies bound to User-Agent; simplifies security but requires matching UA in Postman
