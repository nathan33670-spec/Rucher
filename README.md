# 🐝 Rucher Manager

Application web complète (PWA) de gestion d'une association apicole — ruches, visites, inventaire, trésorerie, suivi sanitaire.

## 🚀 Démarrage rapide

### Prérequis
- Docker & Docker Compose ([installer](https://docs.docker.com/get-docker/))

### Lancement (local ou serveur)

```bash
cp .env.example .env      # puis adaptez les secrets (ou laissez deploy-synology.sh les générer)
docker compose up -d --build
```

L'application est accessible sur **http://localhost:7080**

### Déploiement sur Synology

Guide complet (proxy inverse DSM, certificat Let's Encrypt, routage de l'URL
`ruches.corsicajack.fr`) : **[docs/DEPLOY-SYNOLOGY.md](docs/DEPLOY-SYNOLOGY.md)**.

```bash
./deploy-synology.sh      # build + démarrage de la stack sur le port HTTP local 7080
```

Le Synology (proxy inverse) gère ensuite le HTTPS et le domaine public.

### Connexion

La connexion se fait par **nom d'utilisateur** (identifiant simple, sans e-mail).
Chacun peut **changer son mot de passe** en cliquant sur son nom (en haut à
droite) → « Changer mon mot de passe ». Un administrateur peut réinitialiser le
mot de passe de n'importe quel utilisateur depuis l'onglet **Utilisateurs**.

**Compte administrateur initial**
- **Identifiant** : `admin@rucher.local` · **Mot de passe** : `admin1234`

**Comptes de l'association créés automatiquement** (au premier démarrage, une
seule fois — mot de passe initial commun `rucher2026`, à changer) :

| Identifiant | Rôle |
|-------------|------|
| `paulin`, `luc`, `marion`, `isabelle`, `thomas-admin` | Administrateur |
| `thomas` | Usager (propriétaire d'une ruche de démonstration) |

> ⚠️ Changez les mots de passe par défaut immédiatement en production.
> Les comptes ne sont amorcés qu'**une seule fois** par base : si vous en
> supprimez un, il ne réapparaîtra pas au redémarrage.

---

## 📱 Fonctionnalités

| Onglet | Description |
|--------|-------------|
| **Tableau de bord** | Alertes actives, stats, dernières visites, stocks bas |
| **Ruchers** | CRUD ruchers, plan visuel drag & drop des ruches, géolocalisation |
| **Visites** | Formulaire complet + **Mode Live terrain** (gros boutons, sliders, utilisable avec gants) |
| **Visite rapide** | Bouton sur le tableau de bord et le menu mobile : lance le Mode Live en ne faisant défiler **que les ruches dont l'utilisateur est propriétaire** (tous ruchers confondus) |
| **Inventaire** | Entrées/sorties de matériel, seuils d'alerte, lien trésorerie |
| **Trésorerie** | Recettes/dépenses catégorisées, upload factures, bilan annuel |
| **Sanitaire** | Suivi traitements (varroa…), comptages, calendrier |
| **Météo** | Météo de Bois-d'Arcy (température, hygrométrie, pluie, vent) + **créneau optimal de visite** sur 7 jours + planification |
| **Événements** | Les admins créent des événements (sortie, réunion, récolte), publics ou privés, avec notification optionnelle de tous les adhérents. Chaque adhérent indique s'il vient (oui / peut-être / absent), peut changer sa réponse et **ajouter l'événement à son calendrier** (Apple/Android `.ics` ou Google Agenda). Les admins voient la liste des participants. |
| **Notifications** | Notifications push web (opt-in) : chacun choisit ses catégories (événement de l'association, nouvelle visite, mouvement de matériel, alerte, sanitaire, trésorerie). L'activation est **proposée au premier lancement de l'app installée**, et réglable à tout moment. Fonctionne sur **Android** (navigateur ou app installée) et **iOS** (app installée sur l'écran d'accueil). |
| **Utilisateurs** | 5 rôles, import CSV, création/suppression, reset mot de passe |
| **Journal** | Historique complet des actions (audit) |
| **Documentation** | Centre d'aide **public** : mémo rapide, guide illustré, formation (cycle de l'abeille, varroa, réglementation & registres). Les admins créent leurs propres pages (Markdown). |

> **Page d'accueil publique** : `/` affiche une page grand public de sensibilisation
> à la protection des abeilles (photo du canal de la Croix Bonnet), avec un lien
> « Accéder à l'application » vers la connexion. L'application est sous `/app`.
>
> 🖼️ La photo d'accueil est un visuel d'illustration : remplacez
> `frontend/public/accueil-canal.jpg` par une vraie photo (même nom) pour la
> personnaliser.
>
> 📲 **PWA** installable (Android/iOS) et utilisable **hors-ligne** (saisie des
> visites sans réseau, synchronisées au retour).

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
├── docker-compose.yml          # stack : postgres + redis + backend + web
├── .env.example                # modèle de configuration (copier en .env)
├── deploy-synology.sh          # déploiement Synology (build + up)
├── docs/DEPLOY-SYNOLOGY.md     # guide déploiement + proxy inverse
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
    ├── Dockerfile              # build statique multi-étapes → nginx
    ├── nginx.conf              # sert la SPA + proxy /api, /ws, /uploads
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

> Le conteneur **web** contient le build statique du frontend servi par nginx,
> qui fait aussi office de reverse-proxy interne vers le **backend** FastAPI.
> En production Synology, le TLS et le domaine sont gérés par le proxy inverse DSM.

## 🔧 Administration

### Variables d'environnement (.env)

| Variable | Défaut | Description |
|----------|--------|-------------|
| `POSTGRES_PASSWORD` | `rucher_secret_2026` | Mot de passe PostgreSQL (⚠️ fixé à la 1ʳᵉ init du volume — voir dépannage) |
| `SECRET_KEY` | `change-me-in-production` | Clé secrète JWT (`openssl rand -hex 32`) |
| `FIRST_ADMIN_EMAIL` | `admin@rucher.local` | Email du premier admin |
| `FIRST_ADMIN_PASSWORD` | `admin1234` | Mot de passe du premier admin |
| `WEB_PORT` | `7080` | Port HTTP local exposé (cible du proxy inverse Synology + accès LAN) |

> ⚠️ Si vous changez `POSTGRES_PASSWORD` après le premier démarrage, vous
> obtiendrez `password authentication failed`. Réinitialisez alors le volume :
> `./deploy-synology.sh --reset-db` (une sauvegarde est effectuée avant).

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
