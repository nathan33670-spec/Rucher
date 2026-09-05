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
    # Récolte de pollen ajoutée aux visites (comme le miel).
    (
        "visits",
        "pollen_harvest_kg",
        "ALTER TABLE visits ADD COLUMN IF NOT EXISTS pollen_harvest_kg DOUBLE PRECISION",
    ),
    # Photo (aérienne) du rucher.
    (
        "apiaries",
        "photo_path",
        "ALTER TABLE apiaries ADD COLUMN IF NOT EXISTS photo_path VARCHAR(500)",
    ),
    # Propriété d'un article d'inventaire (NULL = l'association).
    (
        "inventory_items",
        "owner_user_id",
        "ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS owner_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL",
    ),
    # Rôle actif par défaut de l'utilisateur.
    (
        "users",
        "default_role",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS default_role VARCHAR(30)",
    ),
    # Traitement saisi directement pendant une visite.
    (
        "visits",
        "treatment_type",
        "ALTER TABLE visits ADD COLUMN IF NOT EXISTS treatment_type VARCHAR(200)",
    ),
    # Version de jeton : permet d'invalider les sessions d'un compte.
    (
        "users",
        "token_version",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0",
    ),
    (
        "visits",
        "treatment_product",
        "ALTER TABLE visits ADD COLUMN IF NOT EXISTS treatment_product VARCHAR(200)",
    ),
    # Cadres de corps comptés pendant la visite (comme les hausses).
    (
        "visits",
        "frames_count",
        "ALTER TABLE visits ADD COLUMN IF NOT EXISTS frames_count INTEGER",
    ),
    # Pertes déclarées sur une récolte (fond de cuve) et sur des pots (casse).
    (
        "honey_harvests",
        "loss_kg",
        "ALTER TABLE honey_harvests ADD COLUMN IF NOT EXISTS loss_kg DOUBLE PRECISION NOT NULL DEFAULT 0",
    ),
    (
        "honey_jars",
        "lost_quantity",
        "ALTER TABLE honey_jars ADD COLUMN IF NOT EXISTS lost_quantity INTEGER NOT NULL DEFAULT 0",
    ),
    # Boîte de réception des notifications (table créée par create_all ; la
    # migration ne concerne que les bases où la table préexisterait sans colonne).
    # Numéro propre à la ruche, distinct du NAPI (numéro d'apiculteur).
    (
        "hives",
        "number",
        "ALTER TABLE hives ADD COLUMN IF NOT EXISTS number VARCHAR(50)",
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
