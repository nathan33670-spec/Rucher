#!/usr/bin/env bash
set -euo pipefail

# Script helper to build and run the project locally with docker-compose (prod file)
# Usage: ./run-local.sh [-n]
# -n : no-down (skip docker compose down)

NO_DOWN=false
while getopts "n" opt; do
  case $opt in
    n) NO_DOWN=true ;;
    *) echo "Usage: $0 [-n]"; exit 1 ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="docker-compose.prod.yml"

echo "Working dir: $ROOT_DIR"
cd "$ROOT_DIR"

if ! command -v docker &>/dev/null; then
  echo "ERROR: docker not found. Install Docker Desktop and retry."
  exit 1
fi

if ! docker compose version &>/dev/null; then
  echo "ERROR: docker compose plugin not found. Ensure 'docker compose' works."
  exit 1
fi

if [ "$NO_DOWN" = false ]; then
  echo "Stopping existing compose stack (non destructive)..."
  docker compose -f "$COMPOSE_FILE" down || true
fi

echo "Building images (no-cache)..."
docker compose -f "$COMPOSE_FILE" build --no-cache

echo "Starting services..."
docker compose -f "$COMPOSE_FILE" up -d

echo "Waiting for services to become healthy (up to 60s)..."
for i in $(seq 1 60); do
  HEALTHY=$(docker compose -f "$COMPOSE_FILE" ps --quiet | xargs -r docker inspect --format '{{.State.Health.Status}}' 2>/dev/null | grep -c "healthy" || true)
  TOTAL=$(docker compose -f "$COMPOSE_FILE" ps --quiet | wc -l | tr -d ' ')
  if [ "$TOTAL" != "0" ] && [ "$HEALTHY" = "$TOTAL" ]; then
    echo "All services healthy"
    break
  fi
  sleep 1
done

echo "Applying database migrations (alembic upgrade head) inside backend container..."
if docker compose -f "$COMPOSE_FILE" ps -q backend >/dev/null; then
  docker compose -f "$COMPOSE_FILE" exec -T backend alembic upgrade head || {
    echo "Migration failed. Check backend logs:";
    docker compose -f "$COMPOSE_FILE" logs backend --tail=100;
    exit 1;
  }
else
  echo "Backend container not found. Skipping migration."
fi

echo "Restarting nginx to pick config/mounts"
docker compose -f "$COMPOSE_FILE" restart nginx || true

echo "Done. Services status:"
docker compose -f "$COMPOSE_FILE" ps

echo "Helpful logs (tail): backend and nginx"
docker compose -f "$COMPOSE_FILE" logs --tail=50 backend || true
docker compose -f "$COMPOSE_FILE" logs --tail=50 nginx || true

echo "If everything looks fine, open http://localhost:7080/ (or your Synology IP)"

echo "If you need to run the migration manually later:"
echo "  docker compose -f $COMPOSE_FILE exec backend alembic upgrade head"

echo "End of script."
