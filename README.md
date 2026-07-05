# 🐝 Rucher Manager

Application web complète (PWA) de gestion d'une association apicole — ruches, visites, inventaire, trésorerie, suivi sanitaire.

## 🚀 Démarrage rapide

### Prérequis
- Docker & Docker Compose ([installer](https://docs.docker.com/get-docker/))

### Lancement

```bash
cd /Users/U51YP03/Documents/rucher
docker compose up -d --build
```

L'application est accessible sur **http://localhost:8080**

### Compte administrateur par défaut
- **Email** : `admin@rucher.local`
- **Mot de passe** : `admin1234`

> ⚠️ Changez le mot de passe admin immédiatement en production.

---

## 📱 Fonctionnalités

| Onglet | Description |
|--------|-------------|
| **Tableau de bord** | Alertes actives, stats, dernières visites, stocks bas |
| **Ruchers** | CRUD ruchers, plan visuel drag & drop des ruches, géolocalisation |
| **Visites** | Formulaire complet + **Mode Live terrain** (gros boutons, sliders, utilisable avec gants) |
| **Inventaire** | Entrées/sorties de matériel, seuils d'alerte, lien trésorerie |
| **Trésorerie** | Recettes/dépenses catégorisées, upload factures, bilan annuel |
| **Sanitaire** | Suivi traitements (varroa…), comptages, calendrier |
| **Utilisateurs** | 5 rôles, import CSV, reset mot de passe |
| **Journal** | Historique complet des actions (audit) |

### Mode Live (terrain)
- Interface simplifiée sans texte superflu
- Boutons XXL pour gants d'apiculteur
- Sliders couvain (0-9) et réserves (0-9)
- Toggle reine oui/non
- Enchaînement automatique des ruches
- Dictée vocale pour commentaires
- **Mode hors-ligne** : synchronisation automatique au retour du réseau

---

## 🔒 Rôles et Permissions

| Action | Admin | Resp. Rucher | Trésorier | Usager | Lecture seule |
|--------|-------|-------------|-----------|--------|--------------|
| Gérer utilisateurs | ✅ | ❌ | ❌ | ❌ | ❌ |
| Modifier toutes ruches | ✅ | ✅ | ❌ | ❌ | ❌ |
| Modifier ses ruches | ✅ | ✅ | ❌ | ✅ | ❌ |
| Saisir visites | ✅ | ✅ | ❌ | ✅ | ❌ |
| Supprimer visites | ✅ | ❌ | ❌ | ❌ | ❌ |
| Gérer trésorerie | ✅ | ❌ | ✅ | ❌ | ❌ |
| Gérer inventaire | ✅ | ✅ | ✅ | ❌ | ❌ |
| Consulter | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 🏗️ Architecture

```
rucher/
├── docker-compose.yml
├── .env
├── nginx/nginx.conf
├── backend/                    # FastAPI (Python 3.12)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/                # Migrations BDD
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models/             # SQLAlchemy ORM
│       ├── schemas/            # Pydantic
│       ├── routers/            # Routes API REST
│       └── utils/              # Auth JWT, audit
└── frontend/                   # Vue.js 3 + Vuetify (PWA)
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    ├── public/                 # PWA manifest, service worker
    └── src/
        ├── views/              # Pages
        ├── layouts/            # MainLayout
        ├── stores/             # Pinia (auth, notifications)
        ├── services/           # API client, offline storage
        └── plugins/            # Vuetify config
```

## 🔧 Administration

### Variables d'environnement (.env)

| Variable | Défaut | Description |
|----------|--------|-------------|
| `POSTGRES_PASSWORD` | `rucher_secret_2026` | Mot de passe PostgreSQL |
| `SECRET_KEY` | `change-me-in-production` | Clé secrète JWT |
| `FIRST_ADMIN_EMAIL` | `admin@rucher.local` | Email du premier admin |
| `FIRST_ADMIN_PASSWORD` | `admin1234` | Mot de passe du premier admin |

### Commandes utiles

```bash
# Logs
docker compose logs -f

# Redémarrer un service
docker compose restart backend

# Accès BDD
docker compose exec postgres psql -U rucher -d rucher

# Sauvegarde BDD
docker compose exec postgres pg_dump -U rucher rucher > backup.sql

# Restauration
cat backup.sql | docker compose exec -T postgres psql -U rucher -d rucher
```

### Import CSV utilisateurs

Format attendu (colonnes) :
```
email,first_name,last_name,phone,roles
jean@example.com,Jean,Dupont,0601020304,user
marie@example.com,Marie,Martin,,yard_manager|user
```

- Les rôles multiples sont séparés par `|`
- Le mot de passe par défaut est `changeme`
- Les valeurs possibles pour roles : `admin`, `treasurer`, `yard_manager`, `user`, `readonly`

## 📄 Licence

MIT
