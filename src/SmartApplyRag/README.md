# SmartApply RAG

Microservice de Retrieval-Augmented Generation pour la génération de lettres de motivation.  
Tourne sur le port **8001**, séparé du backend FastAPI (port 8000).

---

## Concept

Sans RAG, Mistral génère chaque lettre depuis zéro avec une lettre de référence hardcodée.  
Avec ce microservice, avant chaque génération, le backend récupère :

- les **lettres passées** les plus similaires à l'entreprise cible (même secteur, même stack)
- les **chunks de CV** les plus pertinents pour les technologies demandées
- les **lettres de référence** manuelles les plus adaptées au type d'entreprise

Ce contexte enrichi remplace la référence statique → lettres plus précises et cohérentes au fil du temps.

```
Back (8000)                          RAG (8001)
  generate_letter(company)
    → POST /retrieve/context    →    embed(company) → query ChromaDB
                                ←    { similar_letters, cv_chunks, references }
    → build_prompt(context)
    → Ollama Mistral
    → POST /index/letter        →    embed(letter) → upsert ChromaDB
```

---

## Stack

| Composant | Rôle |
|-----------|------|
| **FastAPI** | API HTTP |
| **ChromaDB** | Vector store local, persisté sur disque |
| **nomic-embed-text** | Modèle d'embedding via Ollama (dim 768, gratuit, local) |
| **Ollama** | Sert le modèle d'embedding (le même que pour Mistral) |

---

## Structure

```
src/SmartApplyRag/
├── app/
│   ├── config.py              ← variables d'environnement
│   ├── main.py                ← FastAPI app + /health
│   ├── models/
│   │   └── schemas.py         ← Pydantic request/response
│   ├── routers/
│   │   ├── index.py           ← POST /index/* (4 routes)
│   │   └── retrieve.py        ← POST /retrieve/context
│   └── services/
│       ├── embedder.py        ← text → vecteur via Ollama
│       ├── vector_store.py    ← wrapper ChromaDB (upsert / query)
│       ├── indexer.py         ← logique d'indexation par type de document
│       └── retriever.py       ← requêtes vectorielles → contexte structuré
├── data/
│   └── chroma/                ← base vectorielle persistée (gitignored)
├── .env.example
├── Dockerfile
└── requirements.txt
```

---

## Collections ChromaDB

| Collection | Contenu | Clé document |
|------------|---------|--------------|
| `letters` | Lettres générées passées | `{user_id}_{company_slug}_{timestamp}` |
| `cv_chunks` | Morceaux du profil CV (expériences, projet, compétences, soft skills) | `{user_id}_cv_{chunk_type}` |
| `companies` | Descriptions enrichies des entreprises | `{company_slug}` |
| `references` | Lettres de référence uploadées manuellement | `ref_{source_slug}_{timestamp}` |

---

## API

### `GET /health`

Vérifie que le service est opérationnel et retourne le nombre de documents par collection.

```json
{
  "status": "ok",
  "embed_model_ready": true,
  "collections": {
    "letters": 42,
    "cv_chunks": 4,
    "companies": 18,
    "references": 3
  }
}
```

`status` vaut `"degraded"` si le modèle d'embedding n'est pas disponible.

---

### `POST /index/letter`

Indexe une lettre générée. À appeler **après** chaque génération réussie dans le backend.

**Request :**
```json
{
  "letter_text": "Objet : Candidature...\n\nMonsieur,...",
  "company": {
    "nom": "Acme Corp",
    "secteur": "SaaS",
    "ville": "Paris",
    "tech_keywords": ["React", "Node.js", "AWS"]
  },
  "mode": "letter_targeted",
  "user_id": "google_id_de_l_utilisateur"
}
```

**Valeurs `mode` :** `letter_targeted` | `letter_spontaneous` | `contact`

**Response :**
```json
{
  "success": true,
  "doc_ids": ["user123_acme_corp_1716123456"],
  "collection": "letters"
}
```

---

### `POST /index/cv`

Indexe le profil CV de l'utilisateur en 4 chunks sémantiques (expériences, projet phare, compétences, soft skills + recherche).  
À appeler lors de l'upload ou de la mise à jour du profil.

**Request :**
```json
{
  "profile": {
    "prenom_nom": "Matthieu Franques",
    "experiences": "Alternant développeur .NET chez Alb@rosa...",
    "projet_phare": "Application mobile aide autonomie malvoyants...",
    "competences": "C# .NET/Blazor, Flutter, Next.js...",
    "soft_skills": "Rigoureux, autonome...",
    "recherche": "Poste développeur .NET / fullstack"
  },
  "user_id": "google_id_de_l_utilisateur"
}
```

**Response :**
```json
{
  "success": true,
  "doc_ids": ["user123_cv_experiences", "user123_cv_project", "user123_cv_skills", "user123_cv_soft_recherche"],
  "collection": "cv_chunks"
}
```

---

### `POST /index/company`

Indexe les données enrichies d'une entreprise. Optionnel — utile pour retrouver des entreprises similaires.

**Request :**
```json
{
  "company": {
    "nom": "Acme Corp",
    "secteur": "SaaS",
    "ville": "Paris",
    "description": "Éditeur de logiciels B2B...",
    "tech_keywords": ["React", "Node.js"],
    "key_phrases": ["scale", "produit ambitieux"]
  }
}
```

---

### `POST /index/reference`

Indexe une lettre de référence manuelle. Permet d'ajouter des exemples de lettres qui ont bien fonctionné.

**Request :**
```json
{
  "letter_text": "Objet : Candidature spontanée...\n\nÀ l'attention de...",
  "source": "lettre_nrb_acceptee",
  "company_type": "grand_groupe"
}
```

**Valeurs `company_type` suggérées :** `startup` | `grand_groupe` | `esn` | `generic`

---

### `POST /retrieve/context`

**Endpoint principal.** Retourne le contexte RAG à injecter dans le prompt Mistral.

**Request :**
```json
{
  "company": {
    "nom": "Acme Corp",
    "secteur": "SaaS",
    "ville": "Paris",
    "tech_keywords": ["React", "Node.js"],
    "job_keywords": ["TypeScript", "Docker"],
    "description": "..."
  },
  "k_letters": 3,
  "k_cv": 3,
  "k_refs": 2
}
```

**Response :**
```json
{
  "similar_letters": [
    "Objet : Candidature – Développeur Frontend | TechStartup...",
    "Objet : Candidature spontanée – Développeur Fullstack | SaasCo..."
  ],
  "cv_chunks": [
    "Alternant développeur web chez Alb@rosa (Airbus/IAM, .NET/Blazor)...",
    "C# .NET/Blazor, Flutter, Next.js, Vue.js, Laravel..."
  ],
  "reference_letters": [
    "Objet : Candidature spontanée – Développeur .NET..."
  ],
  "has_context": true
}
```

`has_context: false` quand les collections sont vides (premier démarrage) — le backend doit alors utiliser son fallback hardcodé.

---

## Installation

### Prérequis

- Ollama installé et en cours d'exécution
- Modèle d'embedding téléchargé :

```bash
ollama pull nomic-embed-text
```

### Local (sans Docker)

```bash
cd src/SmartApplyRag
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Swagger disponible sur `http://localhost:8001/docs`.

### Docker Compose

Le service `rag` est déjà déclaré dans `docker-compose.yml` à la racine du projet :

```bash
# Démarrer uniquement le RAG
docker-compose up rag

# Démarrer tout le stack
docker-compose up
```

Les données ChromaDB sont persistées dans le volume Docker `rag_data`.

---

## Variables d'environnement

Copier `.env.example` en `.env` pour surcharger les valeurs par défaut.

| Variable | Défaut | Description |
|----------|--------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | URL du serveur Ollama |
| `EMBED_MODEL` | `nomic-embed-text` | Modèle d'embedding Ollama |
| `CHROMA_PATH` | `./data/chroma` | Répertoire de persistance ChromaDB |
| `TOP_K_LETTERS` | `3` | Nombre de lettres similaires à récupérer |
| `TOP_K_CV` | `3` | Nombre de chunks CV à récupérer |
| `TOP_K_REFS` | `2` | Nombre de lettres de référence à récupérer |

En Docker, `OLLAMA_HOST` doit pointer vers `http://host.docker.internal:11434` si Ollama tourne sur la machine hôte.

---

## Intégration backend

Dans `src/SmartApplyBack/app/routers/letter.py`, ajouter deux appels HTTP autour de la génération :

```python
import httpx

RAG_URL = "http://localhost:8001"  # ou http://rag:8001 en Docker

# Avant generate_letter() :
try:
    resp = httpx.post(f"{RAG_URL}/retrieve/context", json={"company": job.model_dump()}, timeout=5)
    rag_context = resp.json() if resp.is_success else {}
except Exception:
    rag_context = {}

# Après generate_letter() si succès :
try:
    httpx.post(f"{RAG_URL}/index/letter", json={
        "letter_text": letter_text,
        "company": job.model_dump(),
        "mode": mode_label,
        "user_id": current_user.google_id,
    }, timeout=5)
except Exception:
    pass  # non-bloquant
```

Le `rag_context` est ensuite passé à `build_letter_prompt()` pour enrichir le prompt Mistral.

---

## Ingestion par fichiers (inbox)

La façon la plus simple d'alimenter le RAG : **déposer les fichiers directement** dans les dossiers inbox.

```
data/inbox/
  cvs/        ← déposer CV ici (.pdf ou .txt)
  letters/    ← déposer lettres de référence ici (.txt ou .md)
```

Le service **ingère automatiquement** ces fichiers au démarrage.  
Pour re-déclencher manuellement après ajout d'un fichier :

```bash
curl -X POST http://localhost:8001/ingest/
```

### `GET /ingest/status`

Affiche les fichiers présents dans l'inbox :

```json
{
  "inbox_cvs": ["mon_cv_2025.pdf"],
  "inbox_letters": ["lettre_nrb.txt", "lettre_startup.txt"],
  "total": 3
}
```

### `POST /ingest/`

Déclenche l'ingestion de tous les fichiers de l'inbox. Idempotent — re-indexer le même fichier met à jour les vecteurs.

```json
{
  "cvs": [{"file": "mon_cv_2025.pdf", "chunks_indexed": 6}],
  "letters": [{"file": "lettre_nrb.txt", "doc_id": "ref_lettre_nrb_1716123456"}],
  "errors": []
}
```

### Découpage des CVs

Le service détecte automatiquement les sections du CV (Expériences, Compétences, Formation, Projets...) et crée un chunk par section.  
Si aucune section détectée (format atypique), découpe par paragraphes.

---

## Cycle de vie des données

```
Déposer CV dans data/inbox/cvs/           ─┐
Déposer lettres dans data/inbox/letters/   ─┤→ ingest au démarrage → cv_chunks + references
                                            │
Enrich    → POST /index/company            ─┘→ companies (optionnel)
                    ↓
          POST /retrieve/context   ← avant chaque génération Mistral
                    ↓
          Mistral génère la lettre
                    ↓
          POST /index/letter       → letters collection
                    ↓
          Chaque nouvelle lettre améliore le contexte futur
```
