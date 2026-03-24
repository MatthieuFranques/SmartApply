# SmartApply API

A FastAPI backend for automating job search — scraping companies, filtering prospects, and enriching data.

---

##  Getting Started

### Requirements

[SETUP.md](/docs/SETUP.md)

### Install dependencies

```bash
docker-compose up --build
```

### Run the API

From the `SmartApply/` directory:

```bash
docker-compose up
```

The API will be available at:

```
http://localhost:8000
```

---

## Interactive Documentation

FastAPI automatically generates interactive docs. No setup needed.

| Interface | URL | Description |
|-----------|-----|-------------|
| Swagger UI | `http://localhost:8000/docs` | Test endpoints directly in the browser |
| ReDoc | `http://localhost:8000/redoc` | Clean reference documentation |

> 💡 **Recommended**: Use Swagger UI (`/docs`) to explore and test all endpoints without any extra tool.

---
