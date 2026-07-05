#!/usr/bin/env bash
set -euo pipefail

# Build et lancement local de la stack (identique à la prod Synology).
# Usage: ./run-local.sh [-n]
#   -n : ne pas arrêter la stack existante avant de relancer

NO_DOWN=false
while getopts "n" opt; do
  case $opt in
    n) NO_DOWN=true ;;
    *) echo "Usage: $0 [-n]"; exit 1 ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="docker-compose.yml"
cd "$ROOT_DIR"

command -v docker >/dev/null 2>&1 || { echo "ERREUR : docker introuvable."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERREUR : plugin 'docker compose' introuvable."; exit 1; }

[ -f .env ] || { echo "ℹ️  .env absent — copie depuis .env.example"; cp .env.example .env; }

if [ "$NO_DOWN" = false ]; then
  echo "Arrêt de la stack existante (non destructif)..."
  docker compose -f "$COMPOSE_FILE" down || true
fi

echo "Construction des images..."
docker compose -f "$COMPOSE_FILE" build

echo "Démarrage des services..."
docker compose -f "$COMPOSE_FILE" up -d

echo "Attente du backend (60s max)..."
for _ in $(seq 1 60); do
  if docker compose -f "$COMPOSE_FILE" ps backend | grep -q "healthy"; then
    echo "Backend opérationnel."
    break
  fi
  sleep 1
done

echo "État des services :"
docker compose -f "$COMPOSE_FILE" ps

WEB_PORT=$(grep -E '^WEB_PORT=' .env | cut -d= -f2 || true)
echo ""
echo "✅ Ouvrez http://localhost:${WEB_PORT:-7080}/"
