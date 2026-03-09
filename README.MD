# SmartApply

![Angular](https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![OpenAI](https://img.shields.io/badge/LLM-412991?style=for-the-badge&logo=openai&logoColor=white)

> **SmartApply** is a job search optimization tool that automates company scraping, prospect filtering, data enrichment, and cover letter generation using AI.

---

## 🗂 Project Structure

```
SmartApply/
├── src/
│   ├── SmartApplyBack/     ← FastAPI REST API (Python)
│   └── SmartApplyFront/    ← Angular Frontend
```

---

## ⚙️ Backend — SmartApplyBack

Built with **FastAPI** (Python 3.11), the backend exposes a REST API that orchestrates the full job search pipeline.

### Stack
- **FastAPI** — REST API
- **BeautifulSoup / aiohttp** — Web scraping
- **Hunter.io** — Company & email discovery
- **LLM (OpenAI / Claude)** — Cover letter generation

### Structure

```
SmartApplyBack/
├── app/
│   ├── main.py               # Entry point
│   ├── routers/
│   │   ├── scraping.py       # Scraping endpoints
│   │   ├── filter.py         # Filter endpoints
│   │   └── enrich.py         # Enrich endpoints
│   ├── models/
│   │   ├── scraping.py
│   │   ├── filter.py
│   │   └── enrich.py
│   └── services/
│       ├── scraping/         # Hunter.io scraping logic
│       ├── filters/          # Pre-filter + deep filter pipeline
│       └── enrich/           # Company enrichment logic
└── results/                  # JSON output files
```

### API Documentation

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | Swagger UI — interactive docs |
| `http://localhost:8000/redoc` | ReDoc — reference docs |


---

##  Frontend — SmartApplyFront

Built with **Angular 17+**, the frontend provides a dashboard to control the pipeline and visualize results.

### Stack
- **Angular 17+** — Frontend framework
- **TypeScript** — Language
- **SCSS** — Styling

### Structure

```
SmartApplyFront/
└── src/
    └── app/
        ├── core/services/        # API service calls
        ├── models/               # TypeScript interfaces
        ├── pages/dashboard/      # Main dashboard page
        └── shared/components/    # Reusable components
```
---

##  Cover Letter Generation

SmartApply uses a **LLM** (Large Language Model) to automatically generate personalized cover letters based on enriched company data — tech stack, job offers, company size, and recruiting status.

---

##  License

MIT