#!/usr/bin/env python
"""Aplica la migración del campo approved_at"""

from sqlalchemy import text, inspect
from database import SessionLocal

try:
    session = SessionLocal()
    
    # Verificar si la columna ya existe
    inspector = inspect(session.connection())
    columns = [col['name'] for col in inspector.get_columns('canciones')]
    
    if 'approved_at' not in columns:
        print("Agregando columna approved_at...")
        session.execute(text('ALTER TABLE canciones ADD COLUMN approved_at DATETIME NULL'))
        session.commit()
        print("✓ Migración aplicada exitosamente")
    else:
        print("✓ La columna approved_at ya existe")
    
    session.close()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
