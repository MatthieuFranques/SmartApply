# Nginx — SmartApply

## What is Nginx?

Nginx is a high-performance web server most often used as a **reverse proxy** and **API gateway**. A reverse proxy sits in front of one or more backend services and forwards client requests to them, then relays the responses back. The client only ever talks to Nginx — it never knows (or needs to know) which internal service actually handled the request.

Why it's useful:
- **Single entry point** — clients hit one address instead of juggling several service ports.
- **Routing** — Nginx decides which backend handles each URL path.
- **Decoupling** — backends can move, scale, or be replaced without changing the client.
- **Cross-cutting concerns** — headers, timeouts, body-size limits, TLS, and caching are configured in one place.

## How it's used in SmartApply

SmartApply is split into microservices. Nginx is the **API gateway** that routes incoming HTTP requests (on port `80`) to the correct backend service.

```
                    ┌─────────────────────────┐
   Client  ──────▶  │   Nginx  (listen :80)   │
   (Angular)        └───────────┬─────────────┘
                                │
              ┌─────────────────┴───────────────────┐
              ▼                                      ▼
   ┌──────────────────────┐            ┌──────────────────────┐
   │  pipeline-service     │            │  gmail-service        │
   │  pipeline:8002        │            │  gmail:8004           │
   └──────────────────────┘            └──────────────────────┘
```

### Routing (path → service)

| Path             | Backend            |
|------------------|--------------------|
| `/scraping`      | pipeline:8002      |
| `/filter`        | pipeline:8002      |
| `/enrich`        | pipeline:8002      |
| `/pipeline`      | pipeline:8002      |
| `/letter`        | pipeline:8002      |
| `/jobs`          | pipeline:8002      |
| `/auth`          | gmail:8004         |
| `/profile`       | gmail:8004         |
| `/gmail`         | gmail:8004         |
| `/candidatures`  | gmail:8004         |

`pipeline` and `gmail` are the service names defined in `docker-compose`; Nginx resolves them on the internal Docker network. They're declared once as `upstream` blocks so the target can be swapped in a single place.

### Key configuration choices

- **`client_max_body_size 50M`** — allows large request bodies (e.g. CV / file uploads).
- **Forwarded headers** (`Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`, `Cookie`, `Origin`) — backends see the real client info and the `session` auth cookie survives the proxy hop.
- **SSE support** — the pipeline streams results over Server-Sent Events. These settings keep the stream live instead of buffering it:
  - `proxy_buffering off` / `proxy_cache off` — send each event to the client immediately.
  - `proxy_http_version 1.1` + `Connection ''` — keep the connection open.
  - `proxy_read_timeout 300s` — don't cut long-running streams (scraping/filtering can take minutes).

## File

- `nginx.conf` — the full gateway config described above.
