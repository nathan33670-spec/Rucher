#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Rucher Manager — durcissement d'une installation de production
#
# Remplace tous les secrets par défaut :
#   • mot de passe PostgreSQL       (ALTER USER + .env, dans le bon ordre)
#   • clé de signature JWT           (déconnecte toutes les sessions)
#   • mots de passe des comptes encore sur le mot de passe d'amorçage
#   • permissions du fichier .env
#
# Usage :  cd /volume1/docker/rucher && sudo ./harden-synology.sh
# ═══════════════════════════════════════════════════════════════════════════

set -uo pipefail

ENV_FILE=".env"
COMPOSE="docker compose"
CHANGED=()
SKIPPED=()

# ─── Présentation ────────────────────────────────────────────────────────
c_red()  { printf '\033[31m%s\033[0m\n' "$*"; }
c_grn()  { printf '\033[32m%s\033[0m\n' "$*"; }
c_yel()  { printf '\033[33m%s\033[0m\n' "$*"; }
c_bold() { printf '\033[1m%s\033[0m\n' "$*"; }
title()  { echo; c_bold "── $* ──────────────────────────────"; }
die()    { echo; c_red "✖ $*"; exit 1; }

# ─── Vérifications préalables ────────────────────────────────────────────
title "Vérifications"

[ -t 0 ] || die "Ce script est interactif : lancez-le depuis un terminal SSH."
command -v docker >/dev/null 2>&1 || die "docker est introuvable."
$COMPOSE version >/dev/null 2>&1 || COMPOSE="docker-compose"
$COMPOSE version >/dev/null 2>&1 || die "docker compose est introuvable."
[ -f docker-compose.yml ] || die "docker-compose.yml absent. Placez-vous dans /volume1/docker/rucher."
[ -f "$ENV_FILE" ] || die "$ENV_FILE absent. Lancez d'abord ./deploy-synology.sh."

if ! $COMPOSE ps --status running </dev/null 2>/dev/null | grep -q postgres; then
  die "La base de données n'est pas démarrée. Lancez : $COMPOSE up -d"
fi
c_grn "✓ Stack démarrée, fichier .env présent"

# Sauvegarde du .env avant toute modification
BACKUP_ENV=".env.avant-durcissement.$(date +%Y%m%d_%H%M%S)"
cp "$ENV_FILE" "$BACKUP_ENV"
chmod 600 "$BACKUP_ENV"
c_grn "✓ Sauvegarde de la configuration : $BACKUP_ENV"

# ─── Outils ──────────────────────────────────────────────────────────────
get_env() { grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2-; }

set_env() {
  local key="$1" val="$2" tmp
  tmp=$(mktemp)
  if grep -qE "^${key}=" "$ENV_FILE"; then
    # Réécriture sans interprétation (le mot de passe peut contenir & \ /)
    awk -v k="$key" -v v="$val" \
      'BEGIN{FS=OFS="="} $1==k {print k "=" v; done=1; next} {print} END{if(!done) print k "=" v}' \
      "$ENV_FILE" > "$tmp"
  else
    cp "$ENV_FILE" "$tmp"; printf '%s=%s\n' "$key" "$val" >> "$tmp"
  fi
  mv "$tmp" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
}

# Demande deux fois un mot de passe et valide sa robustesse.
ask_password() {
  local label="$1" p1 p2
  while true; do
    printf '   %s : ' "$label" >&2; read -rs p1; echo >&2
    if [ ${#p1} -lt 12 ]; then
      c_yel "   ⚠ 12 caractères minimum (${#p1} saisis). Recommencez." >&2; continue
    fi
    case "$p1" in
      *[!a-zA-Z0-9]*) : ;;
      *) c_yel "   ⚠ Ajoutez au moins un caractère non alphanumérique. Recommencez." >&2; continue ;;
    esac
    if ! printf '%s' "$p1" | grep -q '[0-9]'; then
      c_yel "   ⚠ Ajoutez au moins un chiffre. Recommencez." >&2; continue
    fi
    printf '   Confirmez              : ' >&2; read -rs p2; echo >&2
    [ "$p1" = "$p2" ] || { c_yel "   ⚠ Les deux saisies diffèrent. Recommencez." >&2; continue; }
    printf '%s' "$p1"; return 0
  done
}

confirm() {
  local answer
  printf '   %s [o/N] ' "$1"; read -r answer
  case "$answer" in [oOyY]*) return 0 ;; *) return 1 ;; esac
}

# ═════════════════════════════════════════════════════════════════════════
# 1. Mot de passe PostgreSQL
# ═════════════════════════════════════════════════════════════════════════
title "1/4 — Mot de passe de la base de données"

CURRENT_PG=$(get_env POSTGRES_PASSWORD)
if [ "$CURRENT_PG" = "rucher_secret_2026" ] || [ "$CURRENT_PG" = "change-me-strong-password" ]; then
  c_red "   ⚠ Mot de passe par défaut détecté — changement fortement recommandé."
else
  echo "   Un mot de passe personnalisé est déjà en place."
fi

if confirm "Changer le mot de passe PostgreSQL ?"; then
  NEW_PG=$(ask_password "Nouveau mot de passe base")

  # L'ordre compte : PostgreSQL ne relit POSTGRES_PASSWORD qu'à la création du
  # volume. On modifie donc le compte DANS la base d'abord, puis le .env.
  echo "   → Modification du compte dans PostgreSQL…"
  if $COMPOSE exec -T postgres psql -U rucher -d rucher -v ON_ERROR_STOP=1 \
       -c "ALTER USER rucher WITH PASSWORD '$(printf '%s' "$NEW_PG" | sed "s/'/''/g")';" \
       </dev/null >/dev/null 2>&1; then
    set_env POSTGRES_PASSWORD "$NEW_PG"
    echo "   → Redémarrage des services applicatifs…"
    $COMPOSE up -d </dev/null >/dev/null 2>&1
    CHANGED+=("Mot de passe PostgreSQL")
    c_grn "   ✓ Mot de passe de la base modifié"
  else
    c_red "   ✖ ALTER USER a échoué — le .env n'a PAS été modifié (rien n'est cassé)."
    SKIPPED+=("Mot de passe PostgreSQL (échec ALTER USER)")
  fi
else
  SKIPPED+=("Mot de passe PostgreSQL (refusé)")
fi

# ═════════════════════════════════════════════════════════════════════════
# 2. Clé de signature JWT
# ═════════════════════════════════════════════════════════════════════════
title "2/4 — Clé de signature des sessions (JWT)"

CURRENT_KEY=$(get_env SECRET_KEY)
if [ "$CURRENT_KEY" = "change-me-in-production" ] || [ ${#CURRENT_KEY} -lt 32 ]; then
  c_red "   ⚠ Clé faible ou par défaut détectée."
else
  echo "   Une clé personnalisée est déjà en place."
fi
c_yel "   Note : changer cette clé déconnecte TOUS les appareils."
c_yel "   Chacun devra se reconnecter (y compris les téléphones)."

if confirm "Régénérer la clé de signature ?"; then
  if command -v openssl >/dev/null 2>&1; then
    NEW_KEY=$(openssl rand -hex 32)
  else
    NEW_KEY=$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')
  fi
  if [ ${#NEW_KEY} -lt 32 ]; then
    c_red "   ✖ Génération aléatoire impossible — clé inchangée."
    SKIPPED+=("Clé JWT (génération impossible)")
  else
    set_env SECRET_KEY "$NEW_KEY"
    $COMPOSE up -d </dev/null >/dev/null 2>&1
    CHANGED+=("Clé de signature JWT (toutes les sessions invalidées)")
    c_grn "   ✓ Nouvelle clé générée et appliquée"
  fi
else
  SKIPPED+=("Clé JWT (refusée)")
fi

# ═════════════════════════════════════════════════════════════════════════
# 3. Comptes utilisateurs encore sur un mot de passe par défaut
# ═════════════════════════════════════════════════════════════════════════
title "3/4 — Comptes sur mot de passe par défaut"

echo "   → Analyse des comptes…"
WEAK=$($COMPOSE exec -T backend python - <<'PY' 2>/dev/null
import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models.user import User
from app.utils.auth import verify_password

DEFAULTS = ["rucher2026", "admin1234", "changeme", "rucher", "admin"]

async def main():
    async with async_session() as s:
        users = (await s.execute(select(User).order_by(User.email))).scalars().all()
        for u in users:
            for d in DEFAULTS:
                try:
                    if verify_password(d, u.hashed_password):
                        print(u.email); break
                except Exception:
                    pass

asyncio.run(main())
PY
)
WEAK=$(printf '%s' "$WEAK" | tr -d '\r' | grep -v '^$' || true)

if [ -z "$WEAK" ]; then
  c_grn "   ✓ Aucun compte sur un mot de passe par défaut"
else
  c_red "   ⚠ Comptes concernés :"
  printf '      • %s\n' $WEAK
  echo
  for acct in $WEAK; do
    if confirm "Changer le mot de passe de « $acct » ?"; then
      NEW_UP=$(ask_password "Nouveau mot de passe pour $acct")
      if $COMPOSE exec -T -e RUCHER_ACCT="$acct" -e RUCHER_PW="$NEW_UP" backend python - <<'PY' >/dev/null 2>&1
import asyncio, os
from sqlalchemy import select, func
from app.database import async_session
from app.models.user import User
from app.utils.auth import hash_password

async def main():
    ident = os.environ["RUCHER_ACCT"]; pw = os.environ["RUCHER_PW"]
    async with async_session() as s:
        u = (await s.execute(select(User).where(func.lower(User.email) == ident.lower()))).scalar_one_or_none()
        if not u:
            raise SystemExit(1)
        u.hashed_password = hash_password(pw)
        await s.commit()

asyncio.run(main())
PY
      then
        CHANGED+=("Mot de passe du compte « $acct »")
        c_grn "   ✓ Mot de passe de « $acct » modifié"
      else
        c_red "   ✖ Échec pour « $acct »"
        SKIPPED+=("Compte « $acct » (échec)")
      fi
    else
      SKIPPED+=("Compte « $acct » (refusé)")
    fi
  done
fi

# FIRST_ADMIN_PASSWORD ne sert qu'au tout premier démarrage : on le neutralise
# pour qu'il ne traîne pas en clair dans le .env.
if [ "$(get_env FIRST_ADMIN_PASSWORD)" = "admin1234" ]; then
  if confirm "Neutraliser FIRST_ADMIN_PASSWORD dans .env (valeur d'amorçage) ?"; then
    if command -v openssl >/dev/null 2>&1; then
      set_env FIRST_ADMIN_PASSWORD "$(openssl rand -hex 16)"
    else
      set_env FIRST_ADMIN_PASSWORD "$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')"
    fi
    CHANGED+=("FIRST_ADMIN_PASSWORD neutralisé")
    c_grn "   ✓ Valeur d'amorçage remplacée par une valeur aléatoire"
  fi
fi

# ═════════════════════════════════════════════════════════════════════════
# 4. Hygiène du système de fichiers et exposition réseau
# ═════════════════════════════════════════════════════════════════════════
title "4/4 — Fichiers et exposition réseau"

chmod 600 "$ENV_FILE" && c_grn "   ✓ .env restreint au propriétaire (600)"
if [ -d backups ]; then
  chmod 700 backups && c_grn "   ✓ Dossier backups/ restreint (700)"
fi

WEB_PORT=$(get_env WEB_PORT); WEB_PORT=${WEB_PORT:-7080}
echo
echo "   Le port $WEB_PORT ne doit PAS être ouvert sur Internet."
echo "   Seul le proxy inverse Synology doit l'atteindre, en localhost."
echo "   → Vérifiez dans votre box qu'aucune redirection ne vise le port $WEB_PORT."

# ─── Contrôle final ──────────────────────────────────────────────────────
title "Contrôle de bon fonctionnement"
echo "   → Attente du démarrage de l'application…"
OK=0
for _ in $(seq 1 30); do
  if curl -fsS "http://localhost:${WEB_PORT}/api/health" </dev/null >/dev/null 2>&1; then OK=1; break; fi
  sleep 2
done

if [ "$OK" = "1" ]; then
  c_grn "   ✓ L'application répond correctement"
else
  c_red "   ✖ L'application ne répond pas sur le port $WEB_PORT"
  echo "     Diagnostic :  $COMPOSE logs --tail=50 backend"
  echo "     Restauration :  cp $BACKUP_ENV .env && $COMPOSE up -d"
fi

# ─── Résumé ──────────────────────────────────────────────────────────────
title "Résumé"
if [ ${#CHANGED[@]} -gt 0 ]; then
  c_grn "Modifié :"; printf '   ✓ %s\n' "${CHANGED[@]}"
else
  c_yel "Aucune modification effectuée."
fi
if [ ${#SKIPPED[@]} -gt 0 ]; then
  echo; c_yel "Non traité :"; printf '   • %s\n' "${SKIPPED[@]}"
fi

echo
c_bold "À faire maintenant :"
echo "   1. Reconnectez-vous à l'application (les sessions ont été invalidées)."
echo "   2. Prévenez les adhérents : ils devront se reconnecter sur leur téléphone."
echo "   3. Conservez les nouveaux mots de passe dans un gestionnaire de mots de passe."
echo "   4. Supprimez la sauvegarde une fois tout vérifié :  rm $BACKUP_ENV"
echo
