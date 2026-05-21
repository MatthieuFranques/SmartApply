# SmartApply — Microservices

## Architecture

```
                    nginx :80
                    /auth /profile /gmail /candidatures  → gmail:8004
                    /scraping /filter /enrich /pipeline
                    /letter /jobs                        → pipeline:8002
                    rag:8001 (internal only)
```

3 services + gateway:

| Service | Port | Source |
|---|---|---|
| Gmail | 8004 | `src/SmartApplyGmail` |
| Pipeline | 8002 | `src/SmartApplyPipeline` |
| RAG | 8001 (internal) | `src/SmartApplyRag` |

Inter-service HTTP calls (no shared code):
- `pipeline` → `gmail:8004/auth/me` — session validation
- `gmail` → `pipeline:8002/enrich/company` — company data for draft generation

---

## 1. Gmail — port `8004`

Auth + Gmail integration + application tracking.

**Env vars:**
| Var | Description |
|---|---|
| `MONGODB_URI` / `MONGODB_DB` | Database |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth2 credentials |
| `GOOGLE_REDIRECT_URI` | OAuth2 callback URL |
| `JWT_SECRET_KEY` | JWT signing secret (shared with Pipeline) |
| `FRONTEND_URL` | Redirect after login (default: `http://localhost:4200`) |
| `RAG_URL` | RAG service (default: `http://rag:8001`) |
| `PIPELINE_URL` | Pipeline service for company data (e.g. `http://pipeline:8002`) |
| `GMAIL_LABEL` | Label to sync (default: `Candidatures`) |
| `ENV` | `production` enables secure cookie |

**Endpoints:**

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/auth/login` | — | Redirect to Google OAuth2 |
| `GET` | `/auth/callback` | — | Exchange code, set `session` cookie (7 days) |
| `GET` | `/auth/status` | ✓ | `{ authenticated, email, name }` |
| `GET` | `/auth/me` | ✓ | `{ google_id, email, name, picture }` — called by Pipeline |
| `POST` | `/auth/logout` | — | Clear session cookie |
| `GET` | `/gmail/messages` | ✓ | Fetch emails by label |
| `POST` | `/gmail/draft` | ✓ | Generate cover letter (via RAG) and create Gmail draft |
| `GET` | `/candidatures` | ✓ | List synced applications |
| `GET` | `/candidatures/status` | ✓ | Last sync timestamp + count |
| `POST` | `/candidatures/sync` | ✓ | Sync Gmail label to DB |
| `DELETE` | `/candidatures/reset` | ✓ | Delete all application history |
| `GET` | `/health` | — | `{ status: "ok", service: "gmail" }` |

**Draft flow:**
1. Call `pipeline:8002/enrich/company?domaine=x` (forwards session cookie)
2. Determine mode: `letter` or `contact`
3. Call RAG to generate text
4. Create Gmail draft via Gmail API

**Application status priority** (upgrade only):
```
Offre reçue > Entretien > Refusé > Décision requise > En attente
```

---

## 2. Pipeline — port `8002`

Scraping → filter → enrich → jobs aggregation.

**Auth:** `get_current_user` calls `gmail:8004/auth/me` (no direct DB access for users).

**Env vars:**
| Var | Description |
|---|---|
| `MONGODB_URI` / `MONGODB_DB` | Database |
| `GMAIL_URL` | Gmail service for auth (e.g. `http://gmail:8004`) |
| `RAG_URL` | RAG service (default: `http://rag:8001`) |
| `OLLAMA_HOST` / `OLLAMA_MODEL` | AI filter (default: `localhost:11434` / `mistral`) |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | Adzuna API (optional) |

**Job stages** (MongoDB `jobs` collection, keyed on `(user_id, domaine)`):
```
scraping → filtered → deep → enriched
```

All stream endpoints return `text/event-stream`. Terminate with `{"type": "done"}`.

**Endpoints:**

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/scraping/stream` | ✓ | Scrape Google Maps, stream to DB |
| `GET` | `/scraping/config` | — | Default sectors + supported cities |
| `GET` | `/filter/stream` | ✓ | Pre-score + AI deep filter |
| `GET` | `/filter/results` | ✓ | Jobs at `deep` stage |
| `GET` | `/enrich/stream` | ✓ | Scrape company websites |
| `GET` | `/enrich/results` | ✓ | Jobs at `enriched` stage |
| `GET` | `/enrich/company?domaine=` | ✓ | Single enriched company — called by Gmail |
| `GET` | `/pipeline/config` | — | Pipeline parameters + defaults |
| `GET` | `/jobs/offers` | ✓ | Job offers (pipeline + Indeed + Adzuna) |
| `GET` | `/jobs/stored/grouped` | ✓ | Stored external offers grouped by search |
| `GET` | `/jobs/stored/count` | ✓ | Count of stored offers |
| `GET` | `/health` | — | `{ status: "ok", service: "pipeline" }` |

---

## 3. RAG — port `8001` (internal)

Vector store + Ollama letter generation. Not exposed through nginx.

**Env vars:**
| Var | Default |
|---|---|
| `OLLAMA_HOST` | `http://host.docker.internal:11434` |
| `OLLAMA_MODEL` | `mistral` |
| `EMBED_MODEL` | `nomic-embed-text` |
| `CHROMA_PATH` | `/app/data/chroma` |
| `INBOX_PATH` | `/app/data/inbox` |

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| `POST` | `/generate/letter` | Generate cover letter |
| `POST` | `/generate/contact` | Generate contact form message |
| `POST` | `/retrieve/context` | Fetch relevant chunks (CV + letters + refs) |
| `POST` | `/index/letter` | Index a generated letter |
| `POST` | `/index/cv` | Index CV chunks |
| `POST` | `/ingest/` | Trigger inbox ingestion |
| `GET` | `/ingest/status` | Pending files in inbox |
| `GET` | `/health` | Embed model status + collection counts |

**Add documents:** drop into Docker volume — CVs: `data/inbox/cvs/`, letters: `data/inbox/letters/`, then call `POST /ingest/`.

---

## MongoDB Collections

| Collection | Owner | Description |
|---|---|---|
| `users` | gmail | User accounts + Google OAuth tokens |
| `jobs` | pipeline | Scraped/enriched companies |
| `job_offers` | pipeline | External job offers (Indeed, Adzuna) |
| `applications` | gmail | Synced application history |

---

## Running

```bash
docker-compose up --build   # first time
docker-compose up           # subsequent
```

Swagger UI at `http://localhost:80/docs` (per service via nginx).

Env files: `src/SmartApplyGmail/.env`, `src/SmartApplyPipeline/.env`
Root `.env`: `MONGO_ROOT_USER`, `MONGO_ROOT_PASSWORD`, `MONGODB_DB`, `OLLAMA_HOST`, `OLLAMA_MODEL`
