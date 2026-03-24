# Contribution Guide - SmartApply

Welcome to the **SmartApply** project! To maintain high-quality code and a clear history (especially important for Docker deployments), please adhere to the following conventions.

---

## Branching Strategy (Git Flow)

We use a simplified structure to ensure the stability of all services.

* **`main`**: The production branch. It must always be stable and ready for deployment.
* **`develop`**: The integration branch. All features are merged here before being promoted to `main`.
* **`feature/feature-name`**: Used for every new task or improvement (e.g., `feature/auth-service`, `feature/cv-parser`).

**Workflow:**
1. Always start from the `develop` branch.
2. Create your branch: `git checkout -b feature/my-awesome-feature`.
3. Work on your code and commit your changes.
4. Open a **Pull Request (PR)** targeting the `develop` branch.

---

## Commit Message Format (Conventional Commits)

Messages must be clear to allow for quick history scanning.
**Format:** `<type>: <short description>`

### Allowed Types:
* **`feat`**: A new feature (e.g., `feat: add AI analysis via Ollama`).
* **`fix`**: A bug fix (e.g., `fix: resolve Docker timeout`).
* **`docs`**: Documentation changes only.
* **`style`**: Formatting, missing semi-colons, etc. (no code change).
* **`refactor`**: Code changes that neither fix a bug nor add a feature (cleanup).
* **`chore`**: Updating build tasks, package manager configs, etc.

---

##  Development Standards

### Naming Conventions
* **Backend (FastAPI/Python)**: Use `snake_case` for functions and variables, and `PascalCase` for classes.
* **Frontend (Angular)**: Use `camelCase` for variables/properties and `PascalCase` for components/services.
* **Language**: All code (function names, variables) and comments must be written in **English**.


### Security & Environment
* **Never commit `.env` files** or API keys.
* Always use the `.gitignore` file provided at the root.
* Any new environment variable must be added to the `.env.example` template file.

---

##  Pull Requests (PR) & Merging

To maintain high code quality:
1. **PR Title**: Must be explicit (e.g., "Integrate PDF CV Parser").
2. **Description**: Briefly explain what you implemented and how you tested it within the Docker environment.
3. **Cleanup**: Delete your local and remote branches after the merge is complete.

---

Thank you for contributing to making **SmartApply** the ultimate tool for job seekers! 

[← Back to Main README](../README.md)