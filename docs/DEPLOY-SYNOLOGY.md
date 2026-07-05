# 🐝 Déploiement de Rucher Manager sur Synology (Docker)

Ce guide décrit le déploiement complet sur un NAS Synology **x86_64** (ex.
DS920+, DS220+… ; CPU Intel/AMD) accessible depuis le réseau **wifi/LAN** et
depuis **Internet** via l'URL `https://ruches.corsicajack.fr`.

L'architecture retenue est la plus simple et la plus robuste :

```
Navigateur ──HTTPS──►  Proxy inverse Synology (ruches.corsicajack.fr, TLS)
                              │  http://localhost:8080
                              ▼
                       Conteneur « web » (nginx)
                        ├── sert la SPA Vue/Vuetify (build statique)
                        └── /api, /ws, /uploads ──► backend FastAPI
                                                     ├── postgres
                                                     └── redis
```

> 👉 Le **TLS et le certificat Let's Encrypt sont gérés par le Synology**
> (proxy inverse + gestionnaire de certificats DSM). La stack Docker n'expose
> qu'**un seul port HTTP local** (`8080`). Aucun certbot dans Docker.

---

## 1. Prérequis

| Élément | Détail |
|---------|--------|
| Paquet Docker | « Container Manager » (DSM 7.2+) ou « Docker » — Centre de paquets |
| Accès SSH | Panneau de configuration › Terminal & SNMP › Activer le service SSH |
| DNS public | `ruches.corsicajack.fr` doit pointer (enregistrement A / CNAME) vers votre IP publique |
| Box Internet | Redirection de ports **443 → IP_du_NAS:443** (et 80 → 443 pour le renouvellement du certificat) |
| Architecture | x86_64 (vérifiée dans `diag.log` : Intel Celeron J4125) |

---

## 2. Transfert des fichiers sur le NAS

**Option A — via git** (si le paquet Git est installé) :

```bash
ssh admin@IP_DU_NAS
sudo mkdir -p /volume1/docker/rucher && cd /volume1/docker/rucher
git clone <URL_DU_DEPOT> .
```

**Option B — via archive** (depuis votre poste) :

```bash
./package-synology.sh                 # crée rucher-synology-*.tar.gz
# Copiez l'archive dans /volume1/docker/rucher via File Station ou scp, puis :
ssh admin@IP_DU_NAS
cd /volume1/docker/rucher && tar xzf rucher-synology-*.tar.gz
```

---

## 3. Déploiement de la stack

```bash
cd /volume1/docker/rucher
sudo ./deploy-synology.sh
```

Le script :
1. génère un fichier `.env` avec des **secrets aléatoires** (au premier lancement) ;
2. construit les images Docker (backend Python + web nginx) ;
3. démarre `postgres`, `redis`, `backend`, `web` ;
4. attend que le backend soit *healthy*.

À la fin, l'application est accessible **en LAN** sur :

```
http://IP_DU_NAS:8080
```

Identifiants par défaut : **admin@rucher.local / admin1234**
(⚠️ à changer immédiatement après la première connexion).

> Pour changer le port local, éditez `WEB_PORT` dans `.env` puis relancez le script.

---

## 4. Configuration du proxy inverse Synology (l'URL)

C'est cette étape qui route `https://ruches.corsicajack.fr` vers le conteneur.

### 4.1 Certificat Let's Encrypt (DSM)

1. **Panneau de configuration › Sécurité › Certificat › Ajouter**
2. « Ajouter un nouveau certificat » › « Obtenir un certificat de Let's Encrypt »
3. Nom de domaine : `ruches.corsicajack.fr` — E-mail : le vôtre
4. Valider (le port 80 doit être joignable depuis Internet le temps de la validation)

> DSM renouvelle ce certificat automatiquement.

### 4.2 Règle de proxy inverse

**Panneau de configuration › Portail de connexion › Avancé › Proxy inversé › Créer**

| Champ | Source (Frontend) | Destination (Backend) |
|-------|-------------------|-----------------------|
| Protocole | **HTTPS** | **HTTP** |
| Nom d'hôte | `ruches.corsicajack.fr` | `localhost` |
| Port | `443` | `8080` |

Onglet **En-têtes personnalisés** › cliquer sur « Créer › WebSocket » (ajoute
automatiquement `Upgrade` et `Connection`) — nécessaire pour le temps réel `/ws`.

Ajoutez aussi ces en-têtes (bouton « Créer ») pour que le backend connaisse le
schéma d'origine :

| Nom de l'en-tête | Valeur |
|------------------|--------|
| `X-Forwarded-Proto` | `https` |
| `X-Forwarded-Host` | `$host` |

Dans l'onglet **Personnalisé**, laissez « HSTS » activé si souhaité et associez le
certificat Let's Encrypt créé en 4.1 (Panneau de config › Sécurité › Certificat ›
Paramètres › associer `ruches.corsicajack.fr` à ce service de proxy inversé).

### 4.3 Redirection de ports sur la box

Sur votre box/routeur Internet, redirigez vers l'IP du NAS :

| Port public | → | NAS |
|-------------|---|-----|
| 443 (HTTPS) | → | 443 |
| 80 (HTTP)   | → | 80  (uniquement pour le renouvellement du certificat) |

Après cela : **https://ruches.corsicajack.fr** fonctionne depuis Internet **et**
depuis le wifi local.

> 💡 Accès local par le nom de domaine : si votre box ne gère pas le
> « hairpin NAT », ajoutez une entrée DNS locale (Synology DNS Server, ou le
> fichier hosts des postes) faisant pointer `ruches.corsicajack.fr` vers l'IP
> LAN du NAS.

---

## 5. Exploitation

```bash
cd /volume1/docker/rucher

docker compose logs -f              # logs en direct
docker compose restart              # redémarrer
./deploy-synology.sh --down         # arrêter la stack
./deploy-synology.sh                # reconstruire + redémarrer
./deploy-synology.sh --backup-db    # sauvegarde PostgreSQL (dans ./backups)
./diag-synology.sh                  # diagnostic complet (état, logs, CPU, disque)
```

### Sauvegardes

`--backup-db` crée un dump `./backups/rucher_backup_AAAAMMJJ_HHMMSS.sql.gz`
(7 dernières conservées). Vous pouvez planifier une tâche Synology
(Planificateur de tâches) exécutant `./deploy-synology.sh --backup-db`.

---

## 6. Dépannage

| Symptôme | Cause / solution |
|----------|------------------|
| Backend en boucle « Restarting », logs `password authentication failed for user "rucher"` | Le volume `pg_data` a été créé avec un autre mot de passe que celui du `.env`. PostgreSQL ne fixe le mot de passe qu'à la 1ʳᵉ init du volume. **Solution :** `./deploy-synology.sh --reset-db` (⚠️ efface la base — une sauvegarde est faite avant). |
| `exec format error` au démarrage d'un conteneur | Images d'une mauvaise architecture. Cette stack utilise des images multi-arch standards (x86_64 OK). Reconstruisez : `./deploy-synology.sh`. |
| La page charge mais l'API renvoie 502 | Le backend n'est pas encore *healthy*. `docker compose logs backend`. |
| Le domaine ne répond pas depuis Internet | Vérifier DNS (`nslookup ruches.corsicajack.fr`), la redirection de port 443 sur la box, et la règle de proxy inversé DSM. |
| Avertissement certificat | Associer le certificat Let's Encrypt DSM au service de proxy inversé (§4.2). |
| Le temps réel (`/ws`) ne fonctionne pas | Ajouter l'en-tête WebSocket dans la règle de proxy inversé (§4.2). |

---

## 7. Sécurité — à faire après le déploiement

- [ ] Changer le mot de passe de `admin@rucher.local`.
- [ ] Vérifier que `.env` contient bien un `SECRET_KEY` et un `POSTGRES_PASSWORD` aléatoires (générés par le script).
- [ ] Ne jamais exposer directement le port `8080` sur Internet — seul le proxy inverse Synology (443/TLS) doit être public.
- [ ] Activer le pare-feu Synology et n'autoriser que les ports nécessaires.
