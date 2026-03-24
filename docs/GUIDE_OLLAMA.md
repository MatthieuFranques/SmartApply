# 🦙 Complete Guide — Ollama + Cover Letter Generation

## What is Ollama?

Ollama is like having **ChatGPT on your own PC**, with no subscription and no internet connection required. You download an AI model once, and it runs entirely locally on your machine.

With 8GB of RAM → the **Mistral** model is the perfect fit for your setup.

---

## Step 1 — Install Ollama

### Download

Go to **[ollama.com](https://ollama.com)** and click "Download".

- **Windows** → download the `.exe` and install it normally.
- **Mac** → download the `.dmg`.
- **Linux** → paste this command into your terminal:
  ```bash
  curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh


---

## Step 2 — Download the Mistral Model

Open a terminal (PowerShell on Windows, Terminal on Mac/Linux) and type:
```bash
ollama pull mistral
```

⏳ It is about 4GB to download, so it might take a few minutes depending on your connection.

You will see something like this:
```
pulling manifest
pulling ff82381e2bea... 100% ▕████████████▏ 4.1 GB
success
```

---

## Step 3 - Run Ollama in the Background

Ollama must be **running at all times while you are using the script**.

```bash
ollama serve
```

> 💡 On Windows, after installation, Ollama often launches **automatically** in the system tray (bottom-right icon). If so, you don't need to run `ollama serve` manually.

To verify it is running, open a browser and go to:
```
http://localhost:11434
```
If you see `Ollama is running` → you're all set!

---

## Step 4 — Install Python Dependencies

In your script folder, open a terminal and run:
```bash
pip install requests beautifulsoup4 tqdm ollama
```
[← Back to SETUP](SETUP.md)

[← Back to Main README](../README.md)