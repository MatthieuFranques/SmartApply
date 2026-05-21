# Guide — Ollama + SmartApply

Ollama runs **natively on your host machine**. Docker containers connect to it via `host.docker.internal:11434`.

SmartApply uses Ollama for two things:
- **Pipeline** — deep AI filtering of scraped companies
- **RAG** — cover letter and contact form generation
- **Gmail** — parsing ambiguous application emails

---

## Step 1 — Install Ollama

Download from **[ollama.com](https://ollama.com)**:
- **Windows** → `.exe` installer
- **Mac** → `.dmg`
- **Linux** → `curl -fsSL https://ollama.com/install.sh | sh`

---

## Step 2 — Download Required Models

```bash
# Generation model (used by pipeline + gmail + rag)
ollama pull mistral

# Embedding model (used by RAG for vector search)
ollama pull nomic-embed-text
```

`mistral` is ~4 GB. `nomic-embed-text` is ~274 MB.

You can use a different generation model by setting `OLLAMA_MODEL` in your `.env` files. Alternatives that work well:
- `mistral` (default, 4B — fast on 8 GB RAM)
- `llama3` (8B — better quality, needs 16 GB RAM)
- `qwen2.5:7b` (good balance)

---

## Step 3 — Keep Ollama Running

Ollama must be **running while Docker Compose is up**.

```bash
ollama serve
```

On Windows, after installation, Ollama typically auto-starts in the system tray. Verify it is running:
```
http://localhost:11434
```
You should see: `Ollama is running`

---

## Step 4 — Configure in Docker Compose

The root `.env` sets the Ollama connection for all services:

```env
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=mistral
EMBED_MODEL=nomic-embed-text
```

`host.docker.internal` resolves to your host machine from inside Docker containers.

On Linux, `host.docker.internal` may not exist by default. Add this to `docker-compose.yml` for affected services:
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

---

## Model Selection Guide

| Model | RAM needed | Speed | Quality | Use case |
|---|---|---|---|---|
| `mistral` | 8 GB | Fast | Good | Default — recommended for most setups |
| `llama3` | 16 GB | Medium | Better | Better letter quality |
| `qwen2.5:7b` | 8 GB | Fast | Good | Alternative to mistral |
| `mistral-nemo` | 16 GB | Medium | Best | Best quality letters |

To switch model: change `OLLAMA_MODEL` in each service `.env` and restart.

---

## RAG + Ollama Flow

The RAG service uses Ollama in two distinct steps:

```
1. Embeddings (nomic-embed-text)
   CV chunks + letters + company data → vector representations → ChromaDB

2. Generation (mistral or other)
   Retrieved context + company data + user profile
   → 2-pass generation:
     Pass 1: company analysis  (temperature 0.3)
     Pass 2: cover letter      (temperature 0.7)
```

The 2-pass approach produces more coherent, targeted letters.

---

## Troubleshooting

**RAG health shows `embed_model_ready: false`:**
Run `ollama pull nomic-embed-text` and ensure Ollama is running.

**Letter generation times out:**
Ollama is slow on first call (model loading). Subsequent calls are faster. Increase `proxy_read_timeout` in nginx if needed.

**`connection refused` on `host.docker.internal`:**
- Windows/Mac: works by default in Docker Desktop
- Linux: add `extra_hosts: - "host.docker.internal:host-gateway"` to the service in `docker-compose.yml`

---

[← Back to SETUP](SETUP.md)

[← Back to Main README](../README.md)
