# 🦙 Guide complet — Ollama + Génération de lettres de motivation

## C'est quoi Ollama ?

Ollama, c'est comme avoir **ChatGPT sur ton propre PC**, sans abonnement et sans connexion internet. Tu télécharges un modèle d'IA une seule fois, et il tourne entièrement en local.

Avec 8 Go de RAM → le modèle **Mistral** est parfait pour toi.

---

## Étape 1 — Installer Ollama

### Téléchargement

Va sur **[ollama.com](https://ollama.com)** et clique sur "Download".

- **Windows** → télécharge le `.exe` et installe-le normalement
- **Mac** → télécharge le `.dmg`
- **Linux** → colle cette commande dans le terminal :
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```

---

## Étape 2 — Télécharger le modèle Mistral

Ouvre un terminal (PowerShell sur Windows, Terminal sur Mac/Linux) et tape :

```bash
ollama pull mistral
```

⏳ C'est ~4 Go à télécharger, ça prend quelques minutes selon ta connexion.

Tu verras quelque chose comme ça :
```
pulling manifest
pulling ff82381e2bea... 100% ▕████████████▏ 4.1 GB
success
```

---

## Étape 3 — Lancer Ollama en arrière-plan

Ollama doit tourner **en permanence pendant que tu utilises le script**.

```bash
ollama serve
```

> 💡 Sur Windows, après l'installation, Ollama se lance souvent **automatiquement** dans la barre des tâches (icône en bas à droite). Dans ce cas, pas besoin de `ollama serve`.

Pour vérifier qu'il tourne, ouvre un navigateur et va sur :
```
http://localhost:11434
```
Si tu vois `Ollama is running` → c'est bon ✅

---

## Étape 4 — Installer les dépendances Python

Dans le dossier de tes scripts, ouvre un terminal et tape :

```bash
pip install requests beautifulsoup4 tqdm ollama
```

---

## Étape 5 — Remplir ton profil dans `generate_letter.py`

Ouvre `generate_letter.py` et remplis le bloc `PROFILE` en haut du fichier.  
Il est déjà pré-rempli avec tes infos, **seul le portfolio est à compléter** :

```python
PROFILE = {
    "prenom_nom":   "Matthieu Franques",
    "diplome":      "Architecte de Systèmes d'Information (RNCP niveau 7)",
    ...
    "portfolio":    "https://TON-VRAI-LIEN.dev",  # ← à changer
    ...
}
```

---

## Étape 6 — Lancer les scripts

### 6a. Enrichir les entreprises (scraping)

```bash
python enrich.py --input results/be/prospects.csv --output results/be/enriched.json
```

Ce que ça fait :
- Lit chaque ligne de ton CSV
- Va scraper le site web de l'entreprise
- Extrait la description, les technologies utilisées, les phrases clés
- Sauvegarde tout dans `enriched.json`

Pour tester sur 5 entreprises d'abord :
```bash
python enrich.py --input results/be/prospects.csv --output results/be/enriched.json --limit 5
```

### 6b. Générer les lettres de motivation

```bash
python generate_letter.py --input results/be/enriched.json --output results/be/letters/
```

Ce que ça fait :
- Lit chaque entreprise dans le JSON enrichi
- Envoie le contexte + ton profil à Mistral
- Génère une lettre personnalisée
- Sauvegarde chaque lettre dans un fichier `.txt` séparé

Pour générer la lettre d'**une seule entreprise** (pour tester) :
```bash
python generate_letter.py --input results/be/enriched.json --output results/be/letters/ --company "Nom de l'entreprise"
```

Pour ignorer les entreprises dont le scraping a échoué :
```bash
python generate_letter.py --input results/be/enriched.json --output results/be/letters/ --only-ok
```

---

## Résultat attendu

Après exécution, tu auras un dossier `results/be/letters/` avec un fichier par entreprise :

```
results/be/letters/
├── lettre_acme_corp.txt
├── lettre_agx_informatique.txt
├── lettre_pinkin.txt
└── ...
```

Chaque lettre est personnalisée avec :
- Le secteur et l'activité réelle de l'entreprise
- Les technologies détectées sur leur site
- Ton parcours Epitech + expériences Alb@rosa / Pinkin
- Tes liens GitHub et portfolio

---

## Schéma du flux complet

```
prospects.csv
      │
      ▼
 enrich.py          ← scrape les sites web
      │
      ▼
enriched.json       ← contexte de chaque entreprise
      │
      ▼
generate_letter.py  ← Mistral génère les lettres
      │
      ▼
letters/*.txt       ← une lettre par entreprise
```

---

## Problèmes fréquents

### ❌ `ollama: command not found`
Ollama n'est pas dans le PATH. Sur Windows, redémarre ton terminal après l'installation.

### ❌ `Connection refused` sur localhost:11434
Ollama ne tourne pas. Lance `ollama serve` dans un terminal séparé.

### ❌ `Error: model 'mistral' not found`
Tu n'as pas encore téléchargé le modèle. Lance `ollama pull mistral`.

### ❌ Le scraping échoue sur beaucoup d'entreprises
Certains sites bloquent les bots. C'est normal, le script passe à la suivante automatiquement. Les lettres seront quand même générées avec les données du CSV.

### ⚠️ Les lettres sont trop génériques
Le scraping n'a pas réussi à extraire assez de contexte. Tu peux relancer avec `--only-ok` pour ne garder que les entreprises bien enrichies.

---

## Commandes résumées (copier-coller)

```bash
# 1. Télécharger le modèle (une seule fois)
ollama pull mistral

# 2. Lancer Ollama (si pas automatique)
ollama serve

# 3. Installer les dépendances Python (une seule fois)
pip install requests beautifulsoup4 tqdm ollama

# 4. Enrichir les entreprises
python enrich.py --input results/be/prospects.csv --output results/be/enriched.json

# 5. Générer les lettres
python generate_letter.py --input results/be/enriched.json --output results/be/letters/
```
