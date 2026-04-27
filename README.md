# 🎓 Pynote — Client Pronote local

Client de bureau léger pour consulter votre **emploi du temps** et vos **devoirs** Pronote, développé avec Python et CustomTkinter.

---

## Aperçu

| Vue | Description |
|---|---|
| Connexion | Saisie URL / identifiant / mot de passe Pronote |
| Emploi du temps | Navigation par semaine, affichage des cours avec horaires |
| Devoirs | Liste des devoirs à rendre triés par date |

---

## 🚀 Téléchargement (utilisateurs)

> **Aucune installation de Python requise.**

1. Rendez-vous sur la page [**Releases**](https://github.com/marchandbelmontcamille-wq/Pynote/releases/latest)
2. Téléchargez **Pynote-windows.zip**
3. Extrayez le dossier où vous voulez
4. Double-cliquez sur **Pynote.exe**
5. Entrez l'URL Pronote de votre établissement, votre identifiant et mot de passe

---

## Prérequis (développeurs)

- Python **3.11+**
- pip

### Mode Développement (`dev`)

```bash
# Cloner et basculer sur la branche dev
git clone https://github.com/marchandbelmontcamille-wq/Pynote.git
cd Pynote
git checkout dev

# Environnement virtuel
python -m venv .venv
.venv\Scripts\activate

# Installer les dépendances dev (inclut prod + outils)
pip install -r requirements-dev.txt

# Copier et remplir les variables d'environnement
copy .env.example .env
# Éditer .env avec vos credentials Pronote

# Lancer en mode dev (credentials chargés automatiquement)
$env:APP_ENV="dev"  # PowerShell
# export APP_ENV=dev  # Bash
python main.py
```

---

## Variables d'environnement (`.env`)

| Variable | Description | Exemple |
|---|---|---|
| `APP_ENV` | Mode de l'application | `dev` ou `prod` |
| `PRONOTE_URL` | URL de la page élève | `https://xxx/pronote/eleve.html` |
| `PRONOTE_USER` | Identifiant Pronote | `prenom.nom` |
| `PRONOTE_PASS` | Mot de passe Pronote | `motdepasse` |

> ⚠️ Le fichier `.env` est **exclu de Git** (voir `.gitignore`). Ne jamais le commiter.

---

## Structure du projet

```
Pynote/
├── main.py                  # Point d'entrée
├── config.py                # Configuration DEV / PROD
├── requirements.txt         # Dépendances production
├── requirements-dev.txt     # Dépendances développement
├── .env.example             # Template de configuration
├── .gitignore
├── README.md
└── app/
    ├── app.py               # Fenêtre principale
    ├── pronote_service.py   # Service Pronote (pronotepy)
    └── views/
        ├── login_view.py    # Écran de connexion
        ├── edt_view.py      # Emploi du temps
        └── devoirs_view.py  # Devoirs
```

---

## Branches Git

| Branche | Rôle |
|---|---|
| `main` | Version **stable** (production) |
| `dev` | Développement actif |

---

## Développement

```bash
# Linter
ruff check .

# Formater
ruff format .

# Tests
pytest
```

---

## Licence

MIT
