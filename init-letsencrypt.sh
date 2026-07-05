#!/usr/bin/env bash
# =============================================================================
# Rucher Manager — Déploiement avec certificat HTTPS auto-renouvelé (Let's Encrypt)
#
# Le script s'adapte automatiquement à l'environnement :
#
#  • Serveur public (domaine + port 80 ouvert + accès Docker Hub) :
#       -> obtient un VRAI certificat Let's Encrypt, renouvelé automatiquement
#          par le service `certbot` (toutes les 12h) ; nginx se recharge seul.
#
#  • Poste local / réseau restreint (Docker Hub bloqué, port 80 non exposé) :
#       -> déploie quand même en HTTPS:7080 avec un certificat AUTO-SIGNÉ
#          (avertissement navigateur), pour pouvoir tester l'interface.
#
# Pré-requis pour un VRAI certificat :
#   - le domaine $DOMAIN doit pointer (DNS) vers l'IP publique du serveur
#   - le port 80 doit être redirigé depuis Internet vers ce serveur
#
# Usage :
#   ./init-letsencrypt.sh            # déploiement complet
#   STAGING=1 ./init-letsencrypt.sh  # certificat de test Let's Encrypt (sans quota)
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

PROJECT="rucher"
COMPOSE_FILE="docker-compose.prod.yml"
RSA_KEY_SIZE=4096

# --- Variables d'environnement ---------------------------------------------
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi
DOMAIN="${DOMAIN:-ruches.corsicajack.fr}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"
STAGING="${STAGING:-0}"
HTTPS_PORT="${HTTPS_PORT:-7080}"
HELPER_IMAGE="${HELPER_IMAGE:-postgres:16}"   # image présente servant à générer le cert auto-signé

# --- Docker dans le PATH (Docker Desktop sur macOS) ------------------------
command -v docker >/dev/null 2>&1 || export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
command -v docker >/dev/null 2>&1 || { echo "ERREUR : docker introuvable." >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERREUR : plugin 'docker compose' introuvable." >&2; exit 1; }

compose() { docker compose -p "$PROJECT" -f "$COMPOSE_FILE" "$@"; }

CONF_VOLUME="${PROJECT}_certbot_conf"
LIVE_PATH="/etc/letsencrypt/live/$DOMAIN"

echo "==> Domaine      : $DOMAIN"
echo "==> Port HTTPS    : $HTTPS_PORT"
echo "==> Email certbot : ${CERTBOT_EMAIL:-(aucun)}"
echo "==> Mode staging  : $STAGING"
echo

# --- Détection de la disponibilité de certbot (image Docker Hub) -----------
CERTBOT_OK=1
if ! docker image inspect certbot/certbot >/dev/null 2>&1; then
  echo "==> Image certbot/certbot absente — tentative de téléchargement..."
  if docker pull certbot/certbot >/dev/null 2>&1; then
    CERTBOT_OK=1
  else
    CERTBOT_OK=0
    echo "    ⚠️  Téléchargement impossible (Docker Hub bloqué ?)."
    echo "    -> Bascule en mode certificat AUTO-SIGNÉ (Let's Encrypt désactivé)."
  fi
fi
echo

# --- 1. Construction des images (uniquement si absentes) -------------------
echo "==> [1/6] Vérification des images applicatives..."
NEED_BUILD=0
docker image inspect "${PROJECT}-backend"  >/dev/null 2>&1 || NEED_BUILD=1
docker image inspect "${PROJECT}-frontend" >/dev/null 2>&1 || NEED_BUILD=1
if [ "$NEED_BUILD" = "1" ]; then
  echo "    Construction des images (build)..."
  compose build
else
  echo "    Images déjà présentes — build ignoré (le code est monté en live)."
fi

# --- 2. Création des volumes (gérés par compose) ---------------------------
echo "==> [2/6] Préparation des volumes..."
compose create postgres redis backend frontend nginx >/dev/null

# --- 3. Génération du certificat initial -----------------------------------
if [ "$CERTBOT_OK" = "1" ]; then
  echo "==> [3/6] Certificat temporaire (remplacé par Let's Encrypt)..."
  compose run --rm --entrypoint "\
    sh -c 'mkdir -p $LIVE_PATH && \
    openssl req -x509 -nodes -newkey rsa:$RSA_KEY_SIZE -days 1 \
      -keyout $LIVE_PATH/privkey.pem -out $LIVE_PATH/fullchain.pem \
      -subj /CN=localhost'" certbot
else
  echo "==> [3/6] Génération d'un certificat auto-signé pour $DOMAIN..."
  docker run --rm -v "${CONF_VOLUME}:/etc/letsencrypt" "$HELPER_IMAGE" \
    sh -c "mkdir -p $LIVE_PATH && \
    openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
      -keyout $LIVE_PATH/privkey.pem -out $LIVE_PATH/fullchain.pem \
      -subj /CN=$DOMAIN \
      -addext subjectAltName=DNS:$DOMAIN,DNS:localhost"
fi

# --- 4. Démarrage de la stack ----------------------------------------------
echo "==> [4/6] Démarrage de la stack..."
if [ "$CERTBOT_OK" = "1" ]; then
  compose up -d
else
  compose up -d postgres redis backend frontend nginx
fi

echo "    Attente des services (jusqu'à 90s)..."
for _ in $(seq 1 90); do
  ids=$(compose ps --quiet 2>/dev/null || true)
  [ -z "$ids" ] && { sleep 1; continue; }
  healthy=$(echo "$ids" | xargs -r docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}n/a{{end}}' 2>/dev/null | grep -c "healthy" || true)
  [ "${healthy:-0}" -ge 3 ] && { echo "    Services principaux opérationnels."; break; }
  sleep 1
done

# --- 5. Migrations de base de données --------------------------------------
echo "==> [5/6] Migrations (alembic upgrade head)..."
compose exec -T backend alembic upgrade head || {
  echo "    ⚠️  Échec des migrations. Logs backend :"
  compose logs backend --tail=60 || true
}

# --- 6. Certificat Let's Encrypt (si disponible) ---------------------------
CERT_RESULT=0
if [ "$CERTBOT_OK" = "1" ]; then
  echo "==> [6/6] Demande du certificat Let's Encrypt pour $DOMAIN..."
  compose run --rm --entrypoint "\
    sh -c 'rm -rf /etc/letsencrypt/live/$DOMAIN /etc/letsencrypt/archive/$DOMAIN /etc/letsencrypt/renewal/$DOMAIN.conf'" certbot

  email_arg="--register-unsafely-without-email"
  [ -n "$CERTBOT_EMAIL" ] && email_arg="--email $CERTBOT_EMAIL"
  staging_arg=""; [ "$STAGING" != "0" ] && staging_arg="--staging"

  set +e
  compose run --rm --entrypoint "\
    certbot certonly --webroot -w /var/www/certbot \
      $staging_arg $email_arg -d $DOMAIN \
      --rsa-key-size $RSA_KEY_SIZE \
      --agree-tos --no-eff-email --non-interactive --keep-until-expiring" certbot
  CERT_RESULT=$?
  set -e
  compose exec nginx nginx -s reload >/dev/null 2>&1 || compose restart nginx || true
else
  echo "==> [6/6] Mode auto-signé : étape Let's Encrypt ignorée."
fi

# --- Bilan -----------------------------------------------------------------
echo
if [ "$CERTBOT_OK" = "1" ] && [ "$CERT_RESULT" -eq 0 ]; then
  echo "✅ Certificat Let's Encrypt actif pour $DOMAIN (renouvellement automatique)."
elif [ "$CERTBOT_OK" = "1" ]; then
  echo "⚠️  Let's Encrypt a échoué (code $CERT_RESULT) — certificat temporaire en place."
  echo "    Vérifiez le DNS de $DOMAIN et l'ouverture du port 80 depuis Internet, puis relancez."
else
  echo "⚠️  Certificat AUTO-SIGNÉ en place (avertissement navigateur attendu)."
  echo "    Pour un vrai certificat Let's Encrypt, déployez sur un serveur :"
  echo "      - dont le DNS $DOMAIN pointe vers l'IP publique"
  echo "      - avec le port 80 ouvert depuis Internet"
  echo "      - ayant accès à Docker Hub (image certbot/certbot)"
fi
echo "   Interface : https://$DOMAIN:$HTTPS_PORT/  (ou https://localhost:$HTTPS_PORT/)"
echo
echo "État des services :"
compose ps
