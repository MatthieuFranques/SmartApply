# Product Roadmap — SmartApply

## Phase 1 — Foundation ✅

- [x] Basic CRUD for job applications
- [x] Local AI integration with Ollama (Mistral)
- [x] Dockerization of the full stack
- [x] Google OAuth2 + JWT session authentication
- [x] Gmail integration — read emails, sync application status
- [x] SSE streaming pipeline (scraping → filter → enrich)
- [x] Cover letter generation (RAG + Ollama)
- [x] Documentation and professional repo setup

## Phase 2 — Microservices Migration ✅

- [x] Split into 3 independent FastAPI services
  - `gmail` (port 8004) — auth + Gmail sync + application tracker
  - `pipeline` (port 8002) — scraping + filter + enrich + jobs aggregation
  - `rag` (port 8001) — ChromaDB vector store + Ollama generation
- [x] nginx gateway routing all services
- [x] RAG service with ChromaDB for CV + letter retrieval
- [x] External job offers: Indeed + Adzuna with 12h cache
- [x] Gmail draft creation from generated letters
- [x] SonarQube code quality integration

## Phase 3 — Quality & Tests 🔄

- [ ] Unit tests for all microservices (Pytest, per-service)
  - Gmail: auth flow, draft creation, candidature sync
  - Pipeline: scraping, filter scoring, enrich, jobs aggregation
  - RAG: generation, indexing, retrieval
- [ ] GitHub Actions CI — lint + test on every PR
- [ ] Code coverage ≥ 80% per service

## Phase 4 — Design & UX

- [ ] Full UI redesign (Angular)
  - New design system (colors, typography, spacing)
  - Improved pipeline dashboard with progress indicators
  - Better application tracker layout (kanban or timeline view)
  - Responsive design for tablet
- [ ] Improved onboarding flow (first-time user experience)

## Phase 5 — Deployment

- [ ] Production deployment setup
  - VPS or cloud provider (Hetzner / DigitalOcean / Railway)
  - HTTPS via Let's Encrypt (Certbot + nginx)
  - Environment secrets management (`.env` → vault or provider secrets)
  - MongoDB backup strategy (daily dump, off-site storage)
- [ ] Docker Compose production profile (resource limits, restart policies)
- [ ] Health check monitoring + alerting (Uptime Robot or similar)
- [ ] CI/CD pipeline — auto-deploy on merge to `main`
- [ ] Kubernetes (learning / scalable deploy) — alternative to Compose
  - Local cluster: k3d / minikube / kind
  - Manifests: Deployment + Service per microservice
  - Ingress (replaces nginx gateway)
  - StatefulSet + PVC for MongoDB + ChromaDB
  - Secrets / ConfigMap for env vars

---

*Roadmap updated 2026-05-29*
