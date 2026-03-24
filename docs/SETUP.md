# Installation Guide - SmartApply

This project is a Full Stack application designed to automate and manage your job applications. It uses **Angular** (Frontend) and **FastAPI** (Backend).

Orchestration is managed by **Docker**, with the exception of the AI engine (Ollama), which runs natively for better performance.

---

## Prerequisites

* **Docker Desktop** (with WSL2 enabled on Windows).
* **Ollama** installed on your host machine (Windows/Mac/Linux).
* **Minimum RAM:** 8 GB recommended.

---

## Step 1: Ollama Configuration (AI Engine)

To benefit from GPU acceleration and avoid overloading Docker containers, **Ollama must be running in the background on your host machine.**

1. **Launch Ollama**: Ensure the Ollama icon is visible in your system tray (taskbar).
2. **Download the model**: Open a terminal and run:
   ```bash
   ollama pull llama3

[GUIDE_OLLAMA.md](GUIDE_OLLAMA.md)

## Step 2: Launch the Docker Image
To start the application and all its services: 

    ```bash
    docker-compose up

### Stop the Services 

    ```bash
    docker-compose down

## Running Services :
* **Frontend** (Angular) : http://localhost:4200
* **Backend** (FastAPI) : http://localhost:8000


[← Back to Main README](../README.md)