#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Rucher Manager — déploiement Docker sur Synology (x86_64)
#
# Le HTTPS et le domaine public (ruches.corsicajack.fr) sont gérés par le
# PROXY INVERSE du Synology. Cette stack n'expose qu'un port HTTP local.
# Voir docs/DEPLOY-SYNOLOGY.md pour la configuration du proxy inverse DSM.
#
# Usage :
#   ./deploy-synology.sh                # build + démarrage
#   ./deploy-synology.sh --backup-db    # sauvegarde la base puis déploie
#   ./deploy-synology.sh --reset-db     # ⚠️ EFFACE le volume PostgreSQL puis déploie
#   ./deploy-synology.sh --down         # arrête la stack
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="$SCRIPT_DIR/backups"
KEEP_BACKUPS=7

echo "╔══════════════════════════════════════════════╗"
echo "║   🐝  Rucher Manager — Déploiement Synology   ║"
echo "╚══════════════════════════════════════════════╝"

# ─── Détection de la commande compose ──────────────────────────────
if docker compose version >/dev/null 2>&1; then
    COMPOSE=(docker compose -f "$COMPOSE_FILE")
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE=(docker-compose -f "$COMPOSE_FILE")
else
    echo "❌ Ni 'docker compose' ni 'docker-compose' ne sont disponibles."
    echo "   Installez le paquet Docker (ou Container Manager) via le Centre de paquets Synology."
    exit 1
fi

# ─── Options ───────────────────────────────────────────────────────
BACKUP_DB=false
RESET_DB=false
DOWN=false
for arg in "$@"; do
    case "$arg" in
        --backup-db) BACKUP_DB=true ;;
        --reset-db)  RESET_DB=true ;;
        --down)      DOWN=true ;;
        *) echo "⚠️  Option inconnue : $arg"; exit 1 ;;
    esac
done

# ─── Génération du .env si absent ──────────────────────────────────
if [ ! -f .env ]; then
    echo "🔑 Génération du fichier .env (secrets aléatoires) ..."
    gen() { openssl rand -hex "$1" 2>/dev/null || head -c "$(( $1 * 2 ))" /dev/urandom | od -An -tx1 | tr -d ' \n'; }
    cat > .env <<EOF
POSTGRES_PASSWORD=$(gen 16)
SECRET_KEY=$(gen 32)
FIRST_ADMIN_EMAIL=admin@rucher.local
FIRST_ADMIN_PASSWORD=admin1234
WEB_PORT=8080
EOF
    echo "   ✅ .env créé — identifiants admin : admin@rucher.local / admin1234"
    echo "   ⚠️  Changez le mot de passe admin après la 1ʳᵉ connexion."
else
    echo "✅ .env existant conservé"
fi

# ─── Backup PostgreSQL ─────────────────────────────────────────────
db_backup() {
    mkdir -p "$BACKUP_DIR"
    local container ts out
    container=$("${COMPOSE[@]}" ps -q postgres 2>/dev/null || true)
    if [ -z "$container" ]; then
        echo "ℹ️  Aucun conteneur postgres actif — backup ignoré."
        return 0
    fi
    ts=$(date +"%Y%m%d_%H%M%S")
    out="$BACKUP_DIR/rucher_backup_${ts}.sql.gz"
    echo "💾 Sauvegarde de la base → $out"
    docker exec -i "$container" pg_dump -U rucher -d rucher | gzip -c > "$out"
    # Rotation
    ls -1t "$BACKUP_DIR"/rucher_backup_*.sql.gz 2>/dev/null | tail -n +$((KEEP_BACKUPS + 1)) | xargs -r rm -f || true
    echo "   ✅ Sauvegarde terminée"
}

# ─── Arrêt simple ──────────────────────────────────────────────────
if [ "$DOWN" = true ]; then
    "${COMPOSE[@]}" down
    echo "✅ Stack arrêtée."
    exit 0
fi

[ "$BACKUP_DB" = true ] && db_backup

# ─── Réinitialisation du volume base (mot de passe changé, etc.) ───
if [ "$RESET_DB" = true ]; then
    db_backup || true
    echo "⚠️  Réinitialisation du volume PostgreSQL (les données seront recréées) ..."
    read -r -p "    Confirmer la suppression du volume pg_data ? (tapez OUI) : " confirm
    if [ "$confirm" = "OUI" ]; then
        "${COMPOSE[@]}" down
        docker volume rm "$(basename "$SCRIPT_DIR" | tr '[:upper:]' '[:lower:]')_pg_data" 2>/dev/null \
            || "${COMPOSE[@]}" down -v
        echo "   ✅ Volume supprimé."
    else
        echo "   Annulé."
        exit 0
    fi
fi

# ─── Build + démarrage ─────────────────────────────────────────────
echo ""
echo "🔨 Construction des images ..."
"${COMPOSE[@]}" build

echo ""
echo "🚀 Démarrage des services ..."
"${COMPOSE[@]}" up -d

echo ""
echo "⏳ Attente de la disponibilité du backend (60s max) ..."
for _ in $(seq 1 60); do
    if "${COMPOSE[@]}" ps backend 2>/dev/null | grep -q "healthy"; then
        echo "   ✅ Backend opérationnel."
        break
    fi
    sleep 1
done

echo ""
echo "📊 État des services :"
"${COMPOSE[@]}" ps

WEB_PORT=$(grep -E '^WEB_PORT=' .env | cut -d= -f2)
WEB_PORT=${WEB_PORT:-8080}
echo ""
echo "═══════════════════════════════════════════════"
echo "✅ Déploiement terminé !"
echo ""
echo "🌐 Accès LAN direct   : http://<IP_DU_NAS>:${WEB_PORT}"
echo "🌐 Accès via domaine  : https://ruches.corsicajack.fr"
echo "   (après configuration du proxy inverse Synology — voir docs/DEPLOY-SYNOLOGY.md)"
echo ""
echo "📋 Commandes utiles :"
echo "   ${COMPOSE[*]} logs -f          # logs en direct"
echo "   ${COMPOSE[*]} restart          # redémarrer"
echo "   ./deploy-synology.sh --down     # arrêter"
echo "   ./deploy-synology.sh --backup-db  # sauvegarder la base"
echo "═══════════════════════════════════════════════"
