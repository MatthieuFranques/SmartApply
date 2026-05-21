# Installation Guide — SmartApply

SmartApply runs as **microservices orchestrated by Docker Compose**. One command starts everything: MongoDB, 5 FastAPI services, nginx gateway, and ChromaDB.

Ollama runs natively on your host machine for GPU acceleration.

---

## Prerequisites

- **Docker Desktop** (WSL2 enabled on Windows)
- **Ollama** installed on your host machine
- **Node.js 20+** (only if running the frontend outside Docker)
- **Minimum RAM:** 8 GB recommended (16 GB comfortable)

---

## Step 1 — Install and Start Ollama

See [GUIDE_OLLAMA.md](GUIDE_OLLAMA.md) for the full guide.

Quick version:
```bash
# Download and install from https://ollama.com
ollama pull mistral          # required — used by pipeline + gmail
ollama pull nomic-embed-text # required — used by RAG for embeddings
```

Ollama must be running (check `http://localhost:11434`).

---

## Step 2 — Configure Environment Variables

Each microservice has its own `.env` file. Copy the examples and fill in your credentials:

```bash
cp src/SmartApplyAuth/.env.example     src/SmartApplyAuth/.env
cp src/SmartApplyPipeline/.env.example src/SmartApplyPipeline/.env
cp src/SmartApplyJobs/.env.example     src/SmartApplyJobs/.env
cp src/SmartApplyGmail/.env.example    src/SmartApplyGmail/.env
```

Create a root `.env` for Docker Compose infrastructure:
```bash
# .env (root)
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=your_password
MONGODB_DB=smartapply
OLLAMA_MODEL=mistral
EMBED_MODEL=nomic-embed-text
OLLAMA_HOST=http://host.docker.internal:11434
```

### Required credentials per service

**All services** need in their `.env`:
```env
MONGODB_URI=mongodb://admin:your_password@mongodb:27017/smartapply?authSource=admin
MONGODB_DB=smartapply
JWT_SECRET_KEY=your_random_secret_here
```

**Auth service** additionally needs:
```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost/auth/callback
FRONTEND_URL=http://localhost:4200
```

**Jobs service** additionally needs (optional — for Adzuna):
```env
ADZUNA_APP_ID=...
ADZUNA_APP_KEY=...
```

> Get Google credentials at [console.cloud.google.com](https://console.cloud.google.com). Enable the Gmail API and OAuth2 for your project.

---

## Step 3 — Start the Stack

```bash
# First time (builds all images)
docker-compose up --build

# Subsequent starts
docker-compose up

# Stop
docker-compose down

# Stop and wipe database
docker-compose down -v
```

**Startup order** (enforced by healthchecks):
1. MongoDB starts and becomes healthy
2. Auth, RAG start
3. Pipeline starts (depends on RAG)
4. Jobs starts (depends on Pipeline)
5. Gmail starts
6. Gateway (nginx) starts last

---

## Step 4 — Access the Application

| URL | Description |
|---|---|
| `http://localhost` | Gateway → Angular frontend (or direct API) |
| `http://localhost:4200` | Angular dev server (if running locally) |
| `http://localhost/auth/login` | Start Google OAuth2 |
| `http://localhost:8001/docs` | RAG service Swagger (internal) |

> All API routes go through `http://localhost` (port 80). Direct service ports (8000, 8002–8004) are not exposed by default.

---

## Step 5 — Run the Frontend (Dev Mode)

The frontend is not containerized in development. Run it separately:

```bash
cd src/SmartApplyFront
npm install
ng serve    # http://localhost:4200
```

The Angular app proxies API calls to `http://localhost` (the nginx gateway).

---

## Adding Documents to the RAG

Drop your CV and reference letters into the RAG inbox volumes before starting, or after by using the API:

**Via Docker volumes** (recommended):
```bash
# Copy your CV
docker cp your_cv.pdf smartapply-rag:/app/data/inbox/cvs/

# Copy a reference letter
docker cp reference.pdf smartapply-rag:/app/data/inbox/letters/

# Trigger ingestion
curl -X POST http://localhost:8001/ingest/
```

Supported formats: PDF, DOCX, TXT.

---

## Common Issues

**Gateway fails to start:**
Wait for all health checks to pass. Run `docker-compose ps` to see which service is not healthy yet.

**Ollama connection refused:**
Ensure Ollama is running on your host. On Windows, check the system tray icon. The container connects via `host.docker.internal:11434`.

**Auth callback fails:**
In Google Cloud Console, add `http://localhost/auth/callback` to the list of authorized redirect URIs.

**MongoDB connection refused:**
`MONGODB_URI` in each service `.env` must use the Docker service name `mongodb`, not `localhost`.

---

