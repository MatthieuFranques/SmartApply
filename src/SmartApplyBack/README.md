# SmartApply API

A FastAPI backend for automating job search — scraping companies, filtering prospects, and enriching data.

---

##  Getting Started

### Requirements

- Python 3.11+
- pip packages: `fastapi uvicorn requests beautifulsoup4 aiohttp aiodns python-dotenv tqdm`

### Install dependencies

```bash
pip install fastapi uvicorn requests beautifulsoup4 aiohttp aiodns python-dotenv tqdm
```

### Run the API

From the `SmartApplyBack/` directory:

```bash
python -m uvicorn app.main:app --reload
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

## Project Structure

```
SmartApplyBack/
├── app/
│   ├── main.py               # Entry point
│   ├── routers/
│   │   ├── scraping.py       # Scraping routes
│   │   ├── filter.py         # Filter routes
│   │   └── enrich.py         # Enrich routes
│   │   └── generate_letter.py# Ganerate letter routes

│   ├── models/
│   │   ├── scraping.py       # Scraping models
│   │   ├── filter.py         # Filter models
│   │   └── enrich.py         # Enrich models
│   │   └── generate_letter.py# Ganerate letter models

│   └── services/
│       ├── scraping/         # Scraping logic
│       ├── filters/          # Filter logic
│       └── enrich/           # Enrich logic
│       └── generate_letter/  # Ganerate letter logic
└── results/                  # Output JSON files
```

