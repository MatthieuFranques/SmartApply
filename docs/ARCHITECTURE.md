# System Architecture

This document describes the high-level architecture of **SmartApply**.

## Component Overview
- **Frontend**: Angular 18 Single Page Application (SPA).
- **Backend**: FastAPI (Python 3.11) asynchronous REST API.
<!-- - **Database**: MongoDB (NoSQL) for flexible job offer schemas. -->
- **AI Engine**: Ollama (Running locally on Host OS).


```mermaid
graph TD
    %% Define Nodes and Styles
    subgraph Host_Machine ["Host Machine (Your PC)"]
        style Host_Machine fill:#f9f9f9,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5

        %% Local AI Engine (Native)
        Ollama[("🦙 Ollama (Mistral/Llama3)
        Running Natively")]
        style Ollama fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    end

    subgraph Docker_Compose_Environment ["Docker Compose Network"]
        style Docker_Compose_Environment fill:#e3f2fd,stroke:#1565c0,stroke-width:2px

        %% Frontend Container
        Nginx[("🌐 smartapply-ui
        (Angular SPA)")]
        style Nginx fill:#fff9c4,stroke:#fbc02d,stroke-width:2px

        %% Backend Container
        FastAPI[("⚡ smartapply-api
        (FastAPI Backend)")]
        style FastAPI fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px

        %% Database Container
        MongoDB[("🍃 smartapply-db
        (MongoDB)")]
        style MongoDB fill:#fbe9e7,stroke:#d84315,stroke-width:2px
    end

    %% External APIs
    GoogleAPI[("🔍 Google Search API
    (Job Discovery)")]
    style GoogleAPI fill:#fce4ec,stroke:#c2185b,stroke-width:1px
    
    HunterAPI[("📧 Hunter.io API
    (Email Verification)")]
    style HunterAPI fill:#fce4ec,stroke:#c2185b,stroke-width:1px

    %% Define Connections & Data Flow
    User((User)) -.->|Accesses| Nginx
    Nginx ==>|REST API Calls| FastAPI
    FastAPI ==>|Reads/Writes| MongoDB

    %% Component Detail Connections
    Nginx -.- DashboardViews
    subgraph DashboardViews ["Dashboard Views"]
        style DashboardViews fill:none,stroke:none
        DV1[Dashboard 1: Scraped & Filtered Job Info]
        DV2[Dashboard 2: Applied Jobs & Drafted Emails]
    end

    %% Backend Interactions
    FastAPI ===>|Job Discovery (Phase 2)| GoogleAPI
    FastAPI ===>|Email Data (Hunter)| HunterAPI
    
    %% AI Connection (Docker to Host)
    FastAPI <-.->|AI Inference (host.docker.internal)| Ollama

    %% Connection styling
    linkStyle 0,1,2 stroke:#333,stroke-width:1px,stroke-dasharray: 3 3;
    linkStyle 3,4,5,6,7 stroke:#01579b,stroke-width:2px;
```

## Data Flow
1. User uploads a CV or Job Description via the **Angular UI**.
2. **FastAPI** processes the request and calls **Ollama** via the internal Docker bridge (`host.docker.internal`).
3. The AI-generated content is stored in **MongoDB** and sent back to the user.

## Why this Stack?
- **FastAPI**: For high performance and automatic Swagger documentation.
- **Docker**: To ensure environment consistency between development and deployment.

[← Back to Main README](../README.md)