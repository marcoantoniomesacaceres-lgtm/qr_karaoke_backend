"""Agregar campo costo a productos

Revision ID: add_costo_to_productos
Revises: 
Create Date: 2025-11-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_costo_to_productos'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Agregar columna costo a la tabla productos
    op.add_column('productos', sa.Column('costo', sa.Numeric(10, 2), server_default='0', nullable=True))


def downgrade():
    # Eliminar columna costo de la tabla productos
    op.drop_column('productos', 'costo')
