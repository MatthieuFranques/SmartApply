# SmartApply — Microservices Documentation

## Architecture Overview

```
                        ┌─────────────────────────────────────────┐
                        │          Gateway (nginx :80)            │
                        │  /auth, /profile  → auth:8000           │
                        │  /scraping, /filter, /enrich,           │
                        │  /pipeline, /letter → pipeline:8002     │
                        │  /jobs            → jobs:8003           │
                        │  /gmail, /candidatures → gmail:8004     │
                        └───────────┬──────────┬──────────────────┘
                                    │          │
          ┌─────────────────────────┼──────────┼──────────────────────┐
          │                         │          │                      │
     auth:8000               pipeline:8002  jobs:8003           gmail:8004
          │                         │                                 │
          └────────────┬────────────┘─────────────────────────────────┘
                       │
                  MongoDB :27017         rag:8001 (internal)
```

**All services** share a MongoDB instance. The RAG service is **internal-only** (no nginx route) — only `pipeline` and `gmail` call it.

---

## Services

### 1. Auth — `src/SmartApplyAuth` · port `8000`

Handles Google OAuth2 login and user profile management.

**Env vars required:**
| Variable | Description |
|---|---|
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DB` | Database name |
| `GOOGLE_CLIENT_ID` | Google OAuth2 client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth2 client secret |
| `GOOGLE_REDIRECT_URI` | OAuth2 callback URL |
| `JWT_SECRET_KEY` | Secret for signing JWTs |
| `FRONTEND_URL` | Redirect target after login (default: `http://localhost:4200`) |
| `ENV` | `production` enables `secure` cookie flag |

**Endpoints:**

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/auth/login` | — | Redirects to Google OAuth2 consent screen |
| `GET` | `/auth/callback?code=` | — | Exchanges code, upserts user, sets `session` HttpOnly cookie (7 days), redirects to frontend |
| `GET` | `/auth/status` | ✓ | Returns `{ authenticated, email, name }` |
| `POST` | `/auth/logout` | — | Clears `session` cookie |
| `GET` | `/profile` | ✓ | Returns user profile (excludes `cv_text`) |
| `PUT` | `/profile` | ✓ | Upserts user profile fields |
| `GET` | `/profile/defaults` | — | Returns default profile template |
| `GET` | `/health` | — | Pings MongoDB, returns `{ status: "ok", service: "auth" }` |

**Auth flow:**
1. Frontend calls `/auth/login` → browser redirected to Google
2. Google redirects to `/auth/callback?code=...`
3. Service exchanges code for tokens, upserts user in MongoDB
4. Sets `session` cookie (JWT signed with `JWT_SECRET_KEY`, subject = `google_id`)
5. Redirects to `FRONTEND_URL`

All protected routes use `Depends(get_current_user)` which decodes the JWT and loads the User from MongoDB.

**User profile fields:** `prenom_nom`, `titre`, `email`, `telephone`, `ville`, `portfolio`, `github`, `diplome`, `ecole`, `annee`, `experiences`, `projet_phare`, `competences`, `soft_skills`, `recherche`, `reference_letter`

---

### 2. Pipeline — `src/SmartApplyPipeline` · port `8002`

Core pipeline: scrapes companies → filters → enriches → generates cover letters.

**Env vars required:**
| Variable | Description |
|---|---|
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DB` | Database name |
| `JWT_SECRET_KEY` | Same secret as auth service |
| `RAG_URL` | RAG service URL (set by docker-compose: `http://rag:8001`) |
| `OLLAMA_HOST` | Ollama host for AI filtering (default: `http://localhost:11434`) |
| `OLLAMA_MODEL` | Model name (default: `mistral`) |

**Job stages in MongoDB `jobs` collection:**
```
scraping → filtered → deep → enriched
```
Each job is uniquely keyed on `(user_id, domaine)`. Each stage has status `active` or `eliminated`.

**All stream endpoints** return `StreamingResponse(media_type="text/event-stream")`. Events are newline-delimited JSON. Stream terminates with `{"type": "done"}`.

**Endpoints:**

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/scraping/stream` | ✓ | Scrapes Google Maps for companies, streams results to DB |
| `GET` | `/scraping/config` | — | Returns default sectors and supported cities |
| `GET` | `/filter/stream` | ✓ | Filters scraped jobs (pre-score + deep AI score), streams updates |
| `GET` | `/filter/results` | ✓ | Returns jobs at `deep` stage |
| `GET` | `/enrich/stream` | ✓ | Scrapes company websites for tech keywords and recruiting signals |
| `GET` | `/enrich/results` | ✓ | Returns jobs at `enriched` stage |
| `GET` | `/pipeline/config` | — | Returns all configurable pipeline parameters with defaults/ranges |
| `POST` | `/letter/` | — | Generate letter from local JSON file (batch/offline use) |
| `GET` | `/letter/{name}` | ✓ | Generate letter for company by name (calls RAG service) |
| `GET` | `/health` | — | Pings MongoDB, returns `{ status: "ok", service: "pipeline" }` |

**Scraping query params:**
- `cities` (default: `"Toulouse"`) — comma-separated list
- `sectors` (default: all) — comma-separated sectors
- `max_results` (default: 100, range: 10–500)
- `keyword_match` (`any` | `all`)

**Filter query params:**
- `min_prescore` — DNS/HTTP/keyword pre-filter threshold
- `min_deep_score` — AI deep-filter threshold
- `concurrency` — parallel AI calls
- `skip_deep` — skip AI step (fast mode)

**Filter stages:**
1. `prefilter.py` — DNS check + HTTP reachability + keyword scoring (fast, free)
2. `deep_filter.py` — Ollama AI scoring for ambiguous results

**Letter generation modes:**
- `letter_targeted` — company has `job_offers`
- `letter_spontaneous` — no open offers found
- `contact` — company only has a contact form

---

### 3. Jobs — `src/SmartApplyJobs` · port `8003`

Aggregates job offers from external sources + pipeline enriched companies.

**Env vars required:**
| Variable | Description |
|---|---|
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DB` | Database name |
| `JWT_SECRET_KEY` | Same secret as auth service |
| `PIPELINE_URL` | Pipeline service URL (set by docker-compose: `http://pipeline:8002`) |
| `ADZUNA_APP_ID` | Adzuna API credentials (optional) |
| `ADZUNA_APP_KEY` | Adzuna API credentials (optional) |

**Endpoints:**

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/jobs/offers` | ✓ | Get job offers (see sources below) |
| `GET` | `/jobs/stored/grouped` | ✓ | Stored external offers grouped by search query |
| `GET` | `/jobs/stored/count` | ✓ | Count of stored offers for user |
| `GET` | `/health` | — | Pings MongoDB, returns `{ status: "ok", service: "jobs" }` |

**`/jobs/offers` query params:**
- `source` (`all` | `pipeline` | `indeed`) — default: `all`
- `keywords` — search terms for external APIs
- `location` — default: `"France"`
- `days` — lookback window (1–90), default: 30
- `limit` — max results (1–300), default: 100

**Source behavior:**
- `pipeline` — returns enriched companies from pipeline DB
- `indeed` + `keywords` — calls Indeed RSS + Adzuna, caches 12h, persists 90 days
- `indeed` + no keywords — returns previously stored offers from DB
- `all` — combines both, deduplicates by `id`

---

### 4. Gmail — `src/SmartApplyGmail` · port `8004`

Gmail integration: read emails, create drafts, sync application status.

**Env vars required:**
| Variable | Description |
|---|---|
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DB` | Database name |
| `JWT_SECRET_KEY` | Same secret as auth service |
| `RAG_URL` | RAG service URL (set by docker-compose: `http://rag:8001`) |
| `GMAIL_LABEL` | Gmail label to sync (default: `"Candidatures"`) |

**Endpoints:**

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/gmail/messages` | ✓ | Fetch emails by label (default: `Candidatures`) |
| `POST` | `/gmail/draft` | ✓ | Generate cover letter via RAG and create Gmail draft |
| `GET` | `/candidatures` | ✓ | List synced applications (optional `?statut=` filter) |
| `GET` | `/candidatures/status` | ✓ | Last sync timestamp + total cached count |
| `POST` | `/candidatures/sync` | ✓ | Sync Gmail `Candidatures` label to DB |
| `DELETE` | `/candidatures/reset` | ✓ | Delete all application history for user |
| `GET` | `/health` | — | Pings MongoDB, returns `{ status: "ok", service: "gmail" }` |

**`/candidatures/sync` params:**
- `force_full` (bool) — re-parse all emails, not just new ones

**Application status priority** (statuses only upgrade, never downgrade):
```
Offre reçue > Entretien > Refusé > Décision requise > En attente
```

**Parser strategy (`gmail_ollama_parser.py`):**
1. Regex for obvious spam/alerts and clear statuses (fast, no LLM)
2. Ollama for ambiguous cases (email too long without clear signal)
3. Fallback to regex extraction if Ollama fails

**Draft creation flow:**
1. Load company from MongoDB by `domaine`
2. Determine mode: `contact` | `letter_targeted` | `letter_spontaneous`
3. Call RAG service to generate letter
4. Create Gmail draft via Gmail API

---

### 5. RAG — `src/SmartApplyRag` · port `8001` (internal)

Vector store for CV, cover letters, and reference letters. Powers cover letter generation via Ollama.

> **Not exposed through nginx** — only callable by `pipeline` and `gmail` services via `http://rag:8001`.

**Env vars:**
| Variable | Description |
|---|---|
| `OLLAMA_HOST` | Ollama host (default: `http://host.docker.internal:11434`) |
| `OLLAMA_MODEL` | Generation model (default: `mistral`) |
| `EMBED_MODEL` | Embedding model (default: `nomic-embed-text`) |
| `CHROMA_PATH` | ChromaDB persistence path (default: `/app/data/chroma`) |
| `INBOX_PATH` | Inbox folder for file ingestion (default: `/app/data/inbox`) |

**Collections (ChromaDB):**
- `cv_chunks` — CV profile chunks
- `letters` — generated cover letters
- `companies` — indexed company data
- `references` — reference letter examples

**On startup:** auto-ingests all files from `data/inbox/cvs/` and `data/inbox/letters/`.

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| `POST` | `/generate/letter` | Generate cover letter via Ollama + RAG context |
| `POST` | `/generate/contact` | Generate contact form message |
| `POST` | `/retrieve/context` | Retrieve relevant chunks (CV + letters + refs) for a company |
| `POST` | `/index/letter` | Index a generated letter |
| `POST` | `/index/cv` | Index CV profile chunks |
| `POST` | `/index/company` | Index company data |
| `POST` | `/index/reference` | Index a reference letter |
| `POST` | `/ingest/` | Trigger inbox ingestion |
| `GET` | `/ingest/status` | List pending files in inbox |
| `GET` | `/health` | Returns embed model status + collection counts |

**Generation flow:**
1. `retrieve/context` — fetch relevant CV chunks, past letters, references from ChromaDB
2. Build prompt with retrieved context + company data + user profile
3. Call Ollama with 2 passes:
   - Analysis prompt at temperature 0.3
   - Letter generation at temperature 0.7

**Adding documents to RAG:**
Drop files into the Docker volume:
- CVs: `data/inbox/cvs/` (PDF, DOCX, TXT)
- Reference letters: `data/inbox/letters/` (PDF, DOCX, TXT)

Then call `POST /ingest/` or restart the service.

---

### 6. Gateway — `nginx:1.27-alpine` · port `80`

Reverse proxy routing all public traffic to the appropriate service.

**Route table:**

| Path prefix | Upstream |
|---|---|
| `/auth`, `/profile` | `auth:8000` |
| `/scraping`, `/filter`, `/enrich`, `/pipeline`, `/letter` | `pipeline:8002` |
| `/jobs` | `jobs:8003` |
| `/gmail`, `/candidatures` | `gmail:8004` |

**Config:** `nginx/nginx.conf`

Key settings:
- `proxy_buffering off` — required for SSE streams
- `proxy_read_timeout 300s` — allows long-running pipeline streams
- `client_max_body_size 50M` — for CV/file uploads

---

### 7. MongoDB — `mongo:7` · port `27017`

Shared database for all services. Each service creates its own indexes at startup via `create_indexes()`.

**Collections:**
| Collection | Owner service(s) | Description |
|---|---|---|
| `users` | auth, pipeline, gmail, jobs | User accounts + Google OAuth tokens |
| `user_profiles` | auth, pipeline, gmail | User profile for letter generation |
| `jobs` | pipeline, gmail, jobs | Scraped/filtered/enriched companies |
| `job_offers` | jobs | External job offers (Indeed, Adzuna) |
| `applications` | gmail | Synced application history from Gmail |

**Memory limits (docker-compose):** MongoDB: 512M.

---

## Dependency Graph

```
gateway (nginx)
  ├── auth       (depends on: mongodb)
  ├── pipeline   (depends on: mongodb, rag)
  ├── jobs       (depends on: mongodb, pipeline)
  └── gmail      (depends on: mongodb)

rag              (depends on: ollama [external])
mongodb          (standalone)
ollama           (external — runs on host or separate container)
```

## Running Locally

```bash
# Full stack
docker-compose up --build   # first time
docker-compose up           # subsequent

# Each service exposes its own Swagger UI at /docs
# All routed through gateway at http://localhost:80
```

Each service has its own `.env` file:
- `src/SmartApplyAuth/.env`
- `src/SmartApplyPipeline/.env`
- `src/SmartApplyJobs/.env`
- `src/SmartApplyGmail/.env`

Root `.env` for docker-compose infrastructure vars: `MONGO_ROOT_USER`, `MONGO_ROOT_PASSWORD`, `MONGODB_DB`, `OLLAMA_HOST`, `OLLAMA_MODEL`, `EMBED_MODEL`.
