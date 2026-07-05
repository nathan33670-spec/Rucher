#!/usr/bin/env bash
# Archive le projet pour déploiement Synology
# - Copie les sources essentielles (backend/frontend/nginx, compose, scripts)
# - Exclut les données et les dossiers lourds (pg_data, upload_data, node_modules, .git...)
# Usage: ./package-synology.sh [output-archive-path]

set -eu

OUT=${1:-"rucher-synology-$(date +%Y%m%d_%H%M%S).tar.gz"}

TMPDIR=$(mktemp -d)
echo "Création d'une copie propre du projet dans $TMPDIR ..."

# Fichiers / dossiers à inclure
INCLUDES=(
  backend
  frontend
  nginx
  docker-compose.prod.yml
  deploy-synology.sh
  init-letsencrypt.sh
  diag-synology.sh
  package-synology.sh
  run-local.sh
  .env.example
  README.md
  docs
)

# Exclure les éléments lourds / temporaires
EXCLUDES=(
  --exclude='.git'
  --exclude='.git/*'
  --exclude='**/node_modules'
  --exclude='**/.venv'
  --exclude='logs'
  --exclude='*.log'
  --exclude='__pycache__'
  --exclude='*.pyc'
  --exclude='rucher-synology-*.tar.gz'
  --exclude='pg_data'
  --exclude='upload_data'
  --exclude='frontend/dist'
)

pushd "$TMPDIR" >/dev/null

echo "Copying selected files..."
for p in "${INCLUDES[@]}"; do
  if [ -e "$OLDPWD/$p" ]; then
    cp -R "$OLDPWD/$p" .
  else
    echo "  (ignoré, absent : $p)"
  fi
done

popd >/dev/null

# S'assurer que les scripts sont exécutables dans l'archive
chmod +x "$TMPDIR"/*.sh 2>/dev/null || true

echo "Création de l'archive $OUT (exclusions appliquées)..."
# Place exclude options before the file list so tar treats them as options (BSD tar on macOS
# can interpret them as file names if they come after the file list)
tar czf "$OUT" "${EXCLUDES[@]}" -C "$TMPDIR" .

echo "Calcul du checksum..."
if command -v shasum >/dev/null 2>&1; then
  shasum -a 256 "$OUT" > "$OUT.sha256"
else
  sha256sum "$OUT" > "$OUT.sha256" || true
fi

echo "Nettoyage temporaire..."
rm -rf "$TMPDIR"

echo ""
echo "✅ Archive créée : $OUT"
echo "✅ Checksum : ${OUT}.sha256"
echo ""
echo "📦 Contenu de l'archive :"
tar tzf "$OUT" | sed 's#^\./##' | awk -F/ 'NF && $1 != "" {print $1}' | sort -u | sed 's/^/   - /'
echo ""
echo "🚀 Déploiement sur Synology :"
echo "   1. Transférez $OUT sur le NAS"
echo "   2. Extrayez : tar xzf $(basename "$OUT")"
echo "   3. Lancez :   ./deploy-synology.sh"
echo "   Le script construit les images, prépare le certificat HTTPS,"
echo "   applique les migrations et démarre la stack sur le port HTTPS 7080."

