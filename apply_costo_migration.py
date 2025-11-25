#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar la migración directamente a la base de datos
"""
import sqlite3

def apply_migration():
    # Conectar a la base de datos
    conn = sqlite3.connect('karaoke.db')
    cursor = conn.cursor()
    
    try:
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(productos)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'costo' in columns:
            print("La columna 'costo' ya existe en la tabla productos")
            return
        
        # Agregar la columna costo
        cursor.execute("""
            ALTER TABLE productos 
            ADD COLUMN costo NUMERIC(10, 2) DEFAULT 0
        """)
        
        conn.commit()
        print("OK - Columna 'costo' agregada exitosamente a la tabla productos")
        print("Todos los productos existentes tienen costo = 0 por defecto")
        
    except Exception as e:
        print(f"ERROR - {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("Aplicando migracion: agregar campo costo a productos...")
    print("")
    apply_migration()
