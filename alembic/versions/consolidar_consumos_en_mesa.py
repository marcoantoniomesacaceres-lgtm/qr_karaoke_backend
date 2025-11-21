"""
Consolidar consumos en mesa: Máximo 10 usuarios por mesa

Revision ID: consolidate_consumos_mesa
Revises: 52459363f20d
Create Date: 2025-11-21

Cambios:
1. Agregar columna mesa_id a la tabla consumos
2. Agregar columna is_active a la tabla usuarios
3. Permitir que usuario_id sea nullable en consumos (SQLite requiere recrear tabla)
4. Agregar índice para optimizar consultas de consumos por mesa
"""
from alembic import op
import sqlalchemy as sa

revision = 'consolidate_consumos_mesa'
down_revision = '52459363f20d'
branch_labels = None
depends_on = None

def upgrade():
    # Agregar columna is_active a usuarios (default True para usuarios existentes)
    op.add_column('usuarios', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    
    # Para SQLite, agregar columna mesa_id es simple
    op.add_column('consumos', sa.Column('mesa_id', sa.Integer(), nullable=True))
    
    # Crear la foreign key para mesa_id
    op.create_foreign_key(
        'fk_consumos_mesa_id',
        'consumos', 'mesas',
        ['mesa_id'], ['id']
    )
    
    # Crear índice para optimizar consultas de consumos por mesa
    op.create_index('idx_consumos_mesa_id', 'consumos', ['mesa_id'])
    
    # Migrar consumos existentes: asignar cada consumo a la mesa del usuario
    # En SQLite, hacer UPDATE es directo
    op.execute("""
        UPDATE consumos 
        SET mesa_id = (
            SELECT mesa_id FROM usuarios WHERE usuarios.id = consumos.usuario_id
        )
        WHERE mesa_id IS NULL AND usuario_id IS NOT NULL
    """)


def downgrade():
    # Revertir cambios
    op.drop_index('idx_consumos_mesa_id', table_name='consumos')
    op.drop_constraint('fk_consumos_mesa_id', 'consumos', type_='foreignkey')
    op.drop_column('consumos', 'mesa_id')
    op.drop_column('usuarios', 'is_active')
