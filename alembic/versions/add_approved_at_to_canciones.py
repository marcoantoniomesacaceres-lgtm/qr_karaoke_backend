"""Agregar campo approved_at a canciones para sistema de aprobación diferida

Revision ID: add_approved_at_to_canciones
Revises: 
Create Date: 2025-12-11

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_approved_at_to_canciones'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Agregar columna approved_at a la tabla canciones
    op.add_column('canciones', sa.Column('approved_at', sa.DateTime, nullable=True))


def downgrade():
    # Eliminar columna approved_at de la tabla canciones
    op.drop_column('canciones', 'approved_at')
