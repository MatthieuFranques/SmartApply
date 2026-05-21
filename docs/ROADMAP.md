# Product Roadmap — SmartApply

## Phase 1 — Foundation (Completed)

- [x] Basic CRUD for job applications
- [x] Local AI integration with Ollama (Mistral)
- [x] Dockerization of the full stack
- [x] Google OAuth2 + JWT session authentication
- [x] Gmail integration — read emails, sync application status
- [x] SSE streaming pipeline (scraping → filter → enrich)
- [x] Cover letter generation (RAG + Ollama)
- [x] Hunter.io domain discovery
- [x] Documentation and professional repo setup

## Phase 2 — Microservices Migration (Completed)

- [x] Split monolith into 5 independent FastAPI services
  - `auth` (port 8000) — OAuth2 + JWT + user profile
  - `pipeline` (port 8002) — scraping + filter + enrich + letter
  - `jobs` (port 8003) — external job offers aggregation
  - `gmail` (port 8004) — Gmail sync + application tracker
  - `rag` (port 8001) — ChromaDB vector store + Ollama generation
- [x] nginx gateway (port 80) routing all services
- [x] Independent memory budgets per service
- [x] RAG service with ChromaDB for CV + letter retrieval
- [x] External job offers: Indeed RSS + Adzuna aggregation with 12h cache
- [x] User profile management (separate from auth)
- [x] Gmail draft creation from generated letters

## Phase 3 — Reliability & DevOps (In Progress)

- [ ] Automated tests for all microservices (Pytest, per-service)
- [ ] GitHub Actions CI — lint + test on PR
- [ ] Per-service `.env.example` templates fully documented
- [ ] Flutter mobile app (BLoC pattern, mirrors Angular features)
- [ ] Advanced analytics — response rate charts, interview funnel

## Phase 4 — Future

- [ ] LinkedIn job scraping integration
- [ ] Multi-user support with tenant isolation
- [ ] Email open tracking
- [ ] Application follow-up reminders
- [ ] SonarQube integration for code quality monitoring

---

*Roadmap updated 2026-05-20 — reflects microservices architecture.*

[← Back to Main README](../README.md)
