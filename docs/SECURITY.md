# 🛡️ Security Policy

## Project Intent
This is a **personal project** designed for individual use. It is currently not intended to be published as a public-facing web service or hosted on a shared production server.

## Local-First Security Strategy
To ensure maximum data privacy and security, the application follows a **Local-First** approach:

* **Self-Hosted:** The entire stack (Frontend, Backend, and Database) runs locally on your own machine using Docker.
* **No External Data Storage:** Your data (CVs, job applications, notes) stays within your local environment.
* **Local AI Inference:** By using **Ollama**, all AI processing for cover letters and analysis is done on your local hardware. No sensitive data is sent to external AI providers (like OpenAI or Anthropic).

## 🔑 Secret Management
* **Personal API Keys:** If the application requires external services (e.g., specific job board APIs), you must provide your own API keys.
* **Environment Variables:** All secrets and configurations are managed via a `.env` file. 
* **Protection:** The `.env` file is strictly listed in `.gitignore` to prevent any sensitive credentials from being committed to the repository.

## ⚠️ Disclaimer
Since this project is for personal use in a local environment, it has not undergone a professional security audit. 
* It is **not recommended** to expose the Docker containers to the open internet without additional security layers (Reverse Proxy, SSL/TLS, Authentication middleware).
* Users are responsible for securing their own local machine and API credentials.

---
*Last updated: March 2026*

[← Back to Main README](../README.md)