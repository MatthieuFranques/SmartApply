# Security Policy

## Project Intent

Personal project designed for individual local use. Not intended as a public multi-tenant SaaS.

## Local-First Security

- **Self-hosted**: entire stack runs locally via Docker Compose
- **No external data storage**: CV, profile, job data stays in your local MongoDB
- **Local AI inference**: Ollama runs on your host — no data sent to OpenAI, Anthropic, or any external AI provider

## Authentication

- Google OAuth2 — user authenticates via Google, no passwords stored
- JWT token signed with `JWT_SECRET_KEY` (HS256), encoded as `google_id`
- `session` cookie: `HttpOnly`, `SameSite=lax`, `Secure` in production, 7-day expiry
- All protected API routes use `Depends(get_current_user)` — decodes JWT, verifies user exists in MongoDB

## Secret Management

| Secret | Location | How to protect |
|---|---|---|
| `.env` files | Per-service (`src/SmartApply*/. env`) | Listed in `.gitignore` — never commit |
| `JWT_SECRET_KEY` | All service `.env` files | Must be identical across services; use a random 32+ char string |
| `GOOGLE_CLIENT_ID/SECRET` | `src/SmartApplyAuth/.env` | Google Cloud Console credentials |
| `ADZUNA_APP_ID/KEY` | `src/SmartApplyJobs/.env` | Optional — only if using Adzuna |
| `cv.pdf`, `token.json` | Local filesystem | Listed in `.gitignore` — never commit |

## Never Commit

```
.env
token.json
cv.pdf
*.pem
```

## Service Isolation

Services communicate only through the Docker Compose internal network:
- RAG (`rag:8001`) is **not exposed** through nginx — only `pipeline` and `gmail` can call it
- MongoDB (`mongodb:27017`) is not exposed outside Docker by default
- Each service only accesses collections it owns

## Exposing to the Internet

Not recommended without:
- SSL/TLS termination at the nginx layer (Let's Encrypt)
- Rate limiting on auth endpoints
- `ENV=production` set (enables `Secure` cookie flag)
- Strong `JWT_SECRET_KEY` (32+ random characters)
- MongoDB not exposed on port 27017

## Disclaimer

This project has not undergone a professional security audit. Use at your own risk in production environments.

---

*Last updated: 2026-05-20*

