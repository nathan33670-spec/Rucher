#!/bin/bash
#═══════════════════════════════════════════════════════════
# Diagnostic Rucher — à exécuter sur le Synology
#═══════════════════════════════════════════════════════════
set -e
INSTALL_DIR="/volume1/docker/rucher"
COMPOSE_FILE="docker-compose.yml"

# Détection compose
if docker compose version &>/dev/null; then
    DC="docker compose"
elif command -v docker-compose &>/dev/null; then
    DC="docker-compose"
else
    echo "❌ docker compose introuvable"
    exit 1
fi

cd "$INSTALL_DIR" 2>/dev/null || { echo "❌ Répertoire $INSTALL_DIR introuvable"; exit 1; }

echo "═══ 1. Version Docker ═══"
docker --version
$DC version 2>/dev/null || echo "(version non dispo)"

echo ""
echo "═══ 2. Fichiers présents ═══"
ls -la $COMPOSE_FILE .env backend/Dockerfile backend/requirements.txt 2>&1

echo ""
echo "═══ 3. Contenu .env ═══"
cat .env 2>/dev/null || echo "❌ .env absent"

echo ""
echo "═══ 4. État des containers ═══"
$DC -f $COMPOSE_FILE ps -a 2>&1

echo ""
echo "═══ 5. Logs backend (50 dernières lignes) ═══"
$DC -f $COMPOSE_FILE logs backend --tail=50 2>&1

echo ""
echo "═══ 6. Logs postgres (20 dernières lignes) ═══"
$DC -f $COMPOSE_FILE logs postgres --tail=20 2>&1

echo ""
echo "═══ 7. Logs web (nginx + frontend, 20 dernières lignes) ═══"
$DC -f $COMPOSE_FILE logs web --tail=20 2>&1

echo ""
echo "═══ 9. Architecture CPU ═══"
uname -m
cat /proc/cpuinfo 2>/dev/null | grep "model name" | head -1 || echo "(info CPU non dispo)"

echo ""
echo "═══ 10. Espace disque ═══"
df -h /volume1 2>/dev/null || df -h .

echo ""
echo "═══ FIN DIAGNOSTIC ═══"
