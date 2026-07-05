#!/bin/bash
#═══════════════════════════════════════════════════════════════
# Script de déploiement — Rucher Manager sur Synology (Docker)
# Usage : ./deploy-synology.sh
#═══════════════════════════════════════════════════════════════
set -e

# ─── Configuration ─────────────────────────────────────
INSTALL_DIR="/volume1/docker/rucher"
COMPOSE_FILE="docker-compose.prod.yml"
PORT=7080

echo "╔══════════════════════════════════════════════╗"
echo "║   🐝  Rucher Manager — Déploiement Synology  ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ─── Vérifier Docker ───────────────────────────────────
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Installez le paquet Docker via le Centre de paquets Synology."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "⚠️  docker compose plugin non trouvé, tentative avec docker-compose..."
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Ni 'docker compose' ni 'docker-compose' ne sont disponibles."
        exit 1
    fi
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# ─── Créer le répertoire d'installation ────────────────
echo "📁 Répertoire d'installation : $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# ─── Si on est dans l'archive extraite, copier les fichiers
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ "$SCRIPT_DIR" != "$INSTALL_DIR" ]; then
    echo "📦 Copie des fichiers vers $INSTALL_DIR ..."
    cp -r "$SCRIPT_DIR"/backend "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR"/frontend "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR"/nginx "$INSTALL_DIR/"
    cp "$SCRIPT_DIR"/$COMPOSE_FILE "$INSTALL_DIR/"
    [ -f "$SCRIPT_DIR/init-letsencrypt.sh" ] && cp "$SCRIPT_DIR/init-letsencrypt.sh" "$INSTALL_DIR/"
    [ -f "$SCRIPT_DIR/diag-synology.sh" ] && cp "$SCRIPT_DIR/diag-synology.sh" "$INSTALL_DIR/"
    [ -f "$SCRIPT_DIR/.env" ] && cp "$SCRIPT_DIR/.env" "$INSTALL_DIR/"
    [ -f "$SCRIPT_DIR/.env.example" ] && cp "$SCRIPT_DIR/.env.example" "$INSTALL_DIR/"
fi

cd "$INSTALL_DIR"

# ─── Générer le .env si absent ─────────────────────────
if [ ! -f .env ]; then
    echo "🔑 Génération du fichier .env ..."
    SECRET=$(openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | od -An -tx1 | tr -d ' \n')
    PG_PASS=$(openssl rand -hex 16 2>/dev/null || head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')
    cat > .env << EOF
POSTGRES_PASSWORD=${PG_PASS}
SECRET_KEY=${SECRET}
FIRST_ADMIN_EMAIL=admin@rucher.local
FIRST_ADMIN_PASSWORD=admin1234

# --- Réseau / HTTPS ---
# Port HTTP côté hôte : port HAUT pour éviter le conflit avec le port 80 déjà
# utilisé par d'autres applis. Le port 80 PUBLIC doit être redirigé vers ce port
# pour le renouvellement automatique Let's Encrypt.
HTTP_PORT=7081
HTTPS_PORT=${PORT}

# --- Certificat Let's Encrypt ---
DOMAIN=ruches.corsicajack.fr
CERTBOT_EMAIL=admin@corsicajack.fr
STAGING=0
EOF
    echo "   ✅ .env créé"
    echo ""
    echo "   ╔═══════════════════════════════════════╗"
    echo "   ║ Identifiants admin par défaut :        ║"
    echo "   ║   Email : admin@rucher.local           ║"
    echo "   ║   Mot de passe : admin1234             ║"
    echo "   ║                                        ║"
    echo "   ║ ⚠️  Changez-les après la 1ère connexion ║"
    echo "   ╚═══════════════════════════════════════╝"
    echo ""
else
    echo "✅ .env existant conservé"
fi

# ─── Options de nettoyage des anciens déploiements ─────
# Usage: ./deploy-synology.sh [--clean] [--full-clean] [--remove-volumes] [--remove-images] [-y|--yes]
#   --clean            : stoppe et supprime le stack (containers) mais conserve images/volumes
#   --remove-volumes   : supprime aussi les volumes déclarés par le compose (-v)
#   --remove-images    : supprime les images créées par le compose (--rmi all)
#   --full-clean       : équivalent à --clean + --remove-volumes + --remove-images
#   -y, --yes          : n'affiche pas la confirmation

CLEAN=false
REMOVE_VOLUMES=false
REMOVE_IMAGES=false
YES=false
## Par défaut, ne PAS activer le nettoyage complet (préférer option explicite)
FULL_CLEAN=false
BACKUP_DB=false
RESTORE_DB=""
KEEP_BACKUPS=7
## Par défaut, activer l'auto-backup : effectue un backup automatique avant toute opération destructive
AUTO_BACKUP=true

# Options backup/restore:
#   --backup-db            : effectue un pg_dump de la base vers INSTALL_DIR/backups
#   --restore-db <file>    : restaure la base depuis un fichier SQL (peut être gzip .gz)
#   --keep-backups <N>     : conserve N backups (par défaut 7)

while [ "$#" -gt 0 ]; do
    case "$1" in
        --clean)
            CLEAN=true
            shift
            ;;
        --remove-volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        --remove-images)
            REMOVE_IMAGES=true
            shift
            ;;
            --backup-db)
                BACKUP_DB=true
                shift
                ;;
            --restore-db)
                RESTORE_DB="$2"
                shift 2
                ;;
            --keep-backups)
                KEEP_BACKUPS="$2"
                shift 2
                ;;
            --auto-backup)
                AUTO_BACKUP=true
                shift
                ;;
        --full-clean)
            FULL_CLEAN=true
            shift
            ;;
        -y|--yes)
            YES=true
            shift
            ;;
        *)
            echo "⚠️  Option inconnue: $1"
            exit 1
            ;;
    esac
done

if [ "$FULL_CLEAN" = true ]; then
    CLEAN=true
    REMOVE_VOLUMES=true
    REMOVE_IMAGES=true
fi

# ─── Fonctions backup / restore ───────────────────────
BACKUP_DIR="$INSTALL_DIR/backups"
mkdir -p "$BACKUP_DIR"

db_backup() {
    echo "💾 Démarrage du backup PostgreSQL..."
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    OUT_FILE="$BACKUP_DIR/rucher_backup_${TIMESTAMP}.sql.gz"

    # Récupérer le nom du conteneur postgres (si en cours d'exécution)
    POSTGRES_CONTAINER=$(docker ps --filter "name=postgres" --format '{{.Names}}' | head -n1)
    if [ -z "$POSTGRES_CONTAINER" ]; then
        echo "⚠️  Aucun conteneur Postgres en cours. Tentative d'exécution temporaire du service..."
        # Lancer le service postgres seul
        $COMPOSE_CMD -f $COMPOSE_FILE up -d postgres
        POSTGRES_CONTAINER=$(docker ps --filter "name=postgres" --format '{{.Names}}' | head -n1)
        sleep 2
    fi

    if [ -z "$POSTGRES_CONTAINER" ]; then
        echo "❌ Impossible de trouver le conteneur postgres. Backup annulé."
        return 1
    fi

    echo "🔁 Exécution du pg_dump dans le conteneur $POSTGRES_CONTAINER -> $OUT_FILE"
    docker exec -i "$POSTGRES_CONTAINER" /bin/sh -c "pg_dump -U rucher -d rucher" | gzip -c > "$OUT_FILE"
    if [ $? -ne 0 ]; then
        echo "❌ Backup échoué"
        return 1
    fi

    echo "✅ Backup enregistré : $OUT_FILE"

    # Rotation des backups
    echo "🧾 Rotation des backups (conserver $KEEP_BACKUPS dernières)"
    ls -1t "$BACKUP_DIR"/rucher_backup_*.sql.gz 2>/dev/null | tail -n +$((KEEP_BACKUPS+1)) | xargs -r rm -f || true
    return 0
}

db_restore() {
    local FILE="$1"
    if [ ! -f "$FILE" ]; then
        echo "❌ Fichier de restauration introuvable: $FILE"
        return 1
    fi

    echo "♻️  Restauration depuis $FILE"
    POSTGRES_CONTAINER=$(docker ps --filter "name=postgres" --format '{{.Names}}' | head -n1)
    if [ -z "$POSTGRES_CONTAINER" ]; then
        echo "⚠️  Aucun conteneur Postgres en cours. Démarrage du service postgres..."
        $COMPOSE_CMD -f $COMPOSE_FILE up -d postgres
        POSTGRES_CONTAINER=$(docker ps --filter "name=postgres" --format '{{.Names}}' | head -n1)
        sleep 2
    fi

    if [ -z "$POSTGRES_CONTAINER" ]; then
        echo "❌ Impossible de trouver le conteneur postgres. Restore annulé."
        return 1
    fi

    # On arrête les services dépendants pendant la restauration
    echo "⏸️  Arrêt des services dépendants (backend) pour restauration..."
    $COMPOSE_CMD -f $COMPOSE_FILE stop backend || true

    if [[ "$FILE" == *.gz ]]; then
        gunzip -c "$FILE" | docker exec -i "$POSTGRES_CONTAINER" psql -U rucher -d rucher
    else
        cat "$FILE" | docker exec -i "$POSTGRES_CONTAINER" psql -U rucher -d rucher
    fi

    if [ $? -ne 0 ]; then
        echo "❌ Restauration échouée"
        return 1
    fi

    echo "✅ Restauration terminée"
    # Redémarrer le backend
    $COMPOSE_CMD -f $COMPOSE_FILE start backend || true
    return 0
}


if [ "$CLEAN" = true ] || [ "$REMOVE_VOLUMES" = true ] || [ "$REMOVE_IMAGES" = true ]; then
    echo ""
    echo "🧹 Nettoyage demandé avant déploiement :"
    [ "$CLEAN" = true ] && echo "  - Suppression du stack (containers)"
    [ "$REMOVE_VOLUMES" = true ] && echo "  - Suppression des volumes déclarés (-v)"
    [ "$REMOVE_IMAGES" = true ] && echo "  - Suppression des images créées par le compose (--rmi all)"

    if [ "$YES" != true ]; then
        read -p "Confirmer le nettoyage ? (y/N) : " confirm
        case "$confirm" in
            [yY]|[yY][eE][sS]) ;;
            *) echo "Annulation du nettoyage"; CLEAN=false; REMOVE_VOLUMES=false; REMOVE_IMAGES=false; ;;
        esac
    else
        echo "  - Confirmation automatique (--yes)"
    fi

    if [ "$CLEAN" = true ] || [ "$REMOVE_VOLUMES" = true ] || [ "$REMOVE_IMAGES" = true ]; then
        # Si backup demandé explicitement ou auto-backup activé, le faire avant toute opération destructive
        if [ "$BACKUP_DB" = true ] || [ "$AUTO_BACKUP" = true ]; then
            db_backup || { echo "❌ Backup échoué, arrêt."; exit 1; }
        fi

        # Si une restauration est demandée, l'exécuter et sortir
        if [ -n "$RESTORE_DB" ]; then
            db_restore "$RESTORE_DB" || { echo "❌ Restore échoué, arrêt."; exit 1; }
            echo "✅ Restore effectué, sortie du script (les services restent en l'état)."
            exit 0
        fi

        DOWN_FLAGS=("--remove-orphans")
        if [ "$REMOVE_IMAGES" = true ]; then
            DOWN_FLAGS+=("--rmi" "all")
        fi
        if [ "$REMOVE_VOLUMES" = true ]; then
            DOWN_FLAGS+=("-v")
        fi

        echo "⚙️  Exécution : $COMPOSE_CMD -f $COMPOSE_FILE down ${DOWN_FLAGS[*]}"
        # shellcheck disable=SC2086
        $COMPOSE_CMD -f $COMPOSE_FILE down "${DOWN_FLAGS[@]}" || true

        # Certaines anciennes versions de docker-compose peuvent ne pas supporter --rmi;
        # dans ce cas, on tente un fallback (safe) pour supprimer les images locales construites par compose.
        if [ "$REMOVE_IMAGES" = true ]; then
            echo "🗑️  Suppression supplémentaire des images locales créées par le projet (fallback)..."
            PROJECT_NAME=$(basename "$INSTALL_DIR" | tr '[:upper:]' '[:lower:]')
            # Supprimer les images construites localement par docker compose (--rmi local peut être insuffisant)
            docker images --format '{{.Repository}} {{.ID}}' | grep -E "${PROJECT_NAME}_|${PROJECT_NAME}-" | awk '{print $2}' | xargs -r docker rmi -f || true
        fi

        echo "✅ Nettoyage terminé"
    fi
fi

# ─── Build et démarrage ───────────────────────────────
echo ""
echo "🔨 Construction des images Docker ..."
$COMPOSE_CMD -f $COMPOSE_FILE build --no-cache

# ─── Configuration HTTPS / Let's Encrypt ──────────────
# Charger les variables du .env (DOMAIN, HTTPS_PORT, CERTBOT_EMAIL, STAGING)
set -a; . "$INSTALL_DIR/.env"; set +a
DOMAIN="${DOMAIN:-ruches.corsicajack.fr}"
HTTPS_PORT="${HTTPS_PORT:-${PORT}}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"
STAGING="${STAGING:-0}"
RSA_KEY_SIZE=4096
PROJECT_NAME=$(basename "$INSTALL_DIR" | tr '[:upper:]' '[:lower:]')
CONF_VOLUME="${PROJECT_NAME}_certbot_conf"
LIVE_PATH="/etc/letsencrypt/live/${DOMAIN}"

# S'assurer qu'un certificat existe AVANT de démarrer nginx (sinon nginx échoue
# car sa configuration référence les fichiers .pem). On crée un certificat
# auto-signé temporaire qui sera remplacé par le vrai certificat Let's Encrypt.
ensure_certificate() {
    docker volume create "$CONF_VOLUME" >/dev/null 2>&1 || true
    # Certificat déjà présent ? (vérif via une image légère déjà construite)
    if docker run --rm -v "${CONF_VOLUME}:/etc/letsencrypt" "${PROJECT_NAME}-backend" \
         test -f "${LIVE_PATH}/fullchain.pem" >/dev/null 2>&1; then
        echo "🔐 Certificat déjà présent dans le volume."
        return 0
    fi
    echo "🔐 Génération d'un certificat auto-signé temporaire pour ${DOMAIN} ..."
    # certbot/certbot embarque openssl ; l'image est récupérable sur Synology (accès Internet)
    if $COMPOSE_CMD -f $COMPOSE_FILE run --rm --entrypoint \
         "sh -c 'mkdir -p ${LIVE_PATH} && openssl req -x509 -nodes -newkey rsa:2048 -days 365 -keyout ${LIVE_PATH}/privkey.pem -out ${LIVE_PATH}/fullchain.pem -subj /CN=${DOMAIN} -addext subjectAltName=DNS:${DOMAIN},DNS:localhost'" \
         certbot >/dev/null 2>&1; then
        echo "   ✅ Certificat temporaire créé"
    else
        echo "   ⚠️  Échec via certbot, tentative avec l'image postgres ..."
        $COMPOSE_CMD -f $COMPOSE_FILE pull postgres >/dev/null 2>&1 || true
        docker run --rm -v "${CONF_VOLUME}:/etc/letsencrypt" postgres:16 \
          sh -c "mkdir -p ${LIVE_PATH} && openssl req -x509 -nodes -newkey rsa:2048 -days 365 -keyout ${LIVE_PATH}/privkey.pem -out ${LIVE_PATH}/fullchain.pem -subj /CN=${DOMAIN} -addext subjectAltName=DNS:${DOMAIN},DNS:localhost" \
          && echo "   ✅ Certificat temporaire créé (postgres)" \
          || echo "   ❌ Impossible de générer un certificat temporaire"
    fi
}

echo ""
echo "🔐 Préparation du certificat HTTPS ..."
ensure_certificate

echo ""
echo "🚀 Démarrage des services ..."
$COMPOSE_CMD -f $COMPOSE_FILE up -d

echo ""
echo "⏳ Attente du démarrage (30s max) ..."
for i in $(seq 1 30); do
    if $COMPOSE_CMD -f $COMPOSE_FILE ps 2>/dev/null | grep -q "healthy"; then
        break
    fi
    sleep 1
    printf "."
done
echo ""

# ─── Migrations de base de données ────────────────────
echo ""
echo "🗃️  Application des migrations (alembic upgrade head) ..."
if $COMPOSE_CMD -f $COMPOSE_FILE exec -T backend alembic upgrade head; then
    echo "   ✅ Migrations appliquées"
else
    echo "   ⚠️  Migrations non appliquées (voir les logs backend)"
fi

# ─── Obtention du vrai certificat Let's Encrypt ───────
# Nécessite que le DNS de $DOMAIN pointe vers ce Synology et que le port 80
# soit accessible depuis Internet. En cas d'échec, le certificat auto-signé
# temporaire reste en place (avertissement navigateur).
echo ""
echo "🔏 Demande du certificat Let's Encrypt pour ${DOMAIN} ..."
email_arg="--register-unsafely-without-email"
[ -n "$CERTBOT_EMAIL" ] && email_arg="--email $CERTBOT_EMAIL"
staging_arg=""
[ "$STAGING" != "0" ] && staging_arg="--staging"

if $COMPOSE_CMD -f $COMPOSE_FILE run --rm --entrypoint \
     "certbot certonly --webroot -w /var/www/certbot $staging_arg $email_arg -d ${DOMAIN} --rsa-key-size ${RSA_KEY_SIZE} --agree-tos --no-eff-email --non-interactive --keep-until-expiring" \
     certbot; then
    echo "   ✅ Certificat Let's Encrypt obtenu"
    $COMPOSE_CMD -f $COMPOSE_FILE exec -T nginx nginx -s reload >/dev/null 2>&1 \
        || $COMPOSE_CMD -f $COMPOSE_FILE restart nginx || true
    CERT_OK=true
else
    echo "   ⚠️  Let's Encrypt indisponible — certificat temporaire conservé."
    echo "      (Vérifiez le DNS de ${DOMAIN} et l'ouverture du port 80 depuis Internet,"
    echo "       puis relancez : cd $INSTALL_DIR && ./init-letsencrypt.sh)"
    CERT_OK=false
fi

# ─── Vérification ─────────────────────────────────────
echo ""
echo "📊 État des services :"
$COMPOSE_CMD -f $COMPOSE_FILE ps

echo ""
# Lister les volumes Docker nommés liés au projet (aide au nettoyage manuel)
echo "🔍 Volumes Docker nommés (vérifiez si vous souhaitez les conserver) :"
docker volume ls --format '{{.Name}}' | grep -E "$(basename "$INSTALL_DIR")|pg_data|rucher" || true

echo "Si vous devez supprimer un volume manuellement : docker volume rm <VOLUME>"

echo ""
echo "═══════════════════════════════════════════════"
echo "✅ Déploiement terminé !"
echo ""
echo "🌐 Accès HTTPS : https://${DOMAIN}:${HTTPS_PORT}"
echo "   (ou https://<IP_SYNOLOGY>:${HTTPS_PORT})"
if [ "$CERT_OK" != true ]; then
    echo "   ⚠️  Certificat temporaire auto-signé : avertissement navigateur à accepter."
fi
echo ""
echo "📋 Commandes utiles :"
echo "   cd $INSTALL_DIR"
echo "   $COMPOSE_CMD -f $COMPOSE_FILE logs -f          # Voir les logs"
echo "   $COMPOSE_CMD -f $COMPOSE_FILE restart           # Redémarrer"
echo "   $COMPOSE_CMD -f $COMPOSE_FILE down              # Arrêter"
echo "   $COMPOSE_CMD -f $COMPOSE_FILE up -d             # Démarrer"
echo "   ./init-letsencrypt.sh                            # (Re)obtenir le certificat HTTPS"
echo "═══════════════════════════════════════════════"
