"""Micro-migrations idempotentes appliquées au démarrage.

Le schéma est créé via ``Base.metadata.create_all`` qui crée les tables
manquantes mais ne modifie **pas** les tables déjà existantes. Lorsqu'une
colonne est ajoutée à un modèle, les bases déjà initialisées ne la reçoivent
pas → erreurs 500 à l'exécution.

Ce module applique des ``ALTER TABLE ... ADD COLUMN IF NOT EXISTS`` idempotents
(PostgreSQL) pour réconcilier ces bases avec les modèles courants.
"""

from sqlalchemy import text

# (table, colonne, DDL d'ajout idempotent)
COLUMN_MIGRATIONS = [
    # Colonne « events » ajoutée avec la fonctionnalité Événements : sans cette
    # migration, /api/notifications/preferences et /subscribe renvoient 500 sur
    # les bases antérieures à cette fonctionnalité.
    (
        "notification_prefs",
        "events",
        "ALTER TABLE notification_prefs ADD COLUMN IF NOT EXISTS events BOOLEAN NOT NULL DEFAULT TRUE",
    ),
]


async def ensure_schema(conn):
    """Applique les micro-migrations. Chaque instruction est isolée : une
    erreur sur l'une n'empêche pas les autres ni le démarrage."""
    for table, column, ddl in COLUMN_MIGRATIONS:
        try:
            await conn.execute(text(ddl))
        except Exception as e:  # pragma: no cover - dépend du SGBD
            print(f"⚠️  Migration {table}.{column} ignorée : {e}")
