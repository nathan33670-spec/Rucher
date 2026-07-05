"""add photo_path to hives

Revision ID: 20260520_add_hive_photo_path
Revises: 
Create Date: 2026-05-20 11:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260520_add_hive_photo_path'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('hives', sa.Column('photo_path', sa.String(length=500), nullable=True))


def downgrade():
    op.drop_column('hives', 'photo_path')

