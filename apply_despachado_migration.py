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
        cursor.execute("PRAGMA table_info(consumos)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_dispatched' in columns:
            print("La columna 'is_dispatched' ya existe en la tabla consumos")
            return
        
        # Agregar la columna is_dispatched
        cursor.execute("""
            ALTER TABLE consumos 
            ADD COLUMN is_dispatched BOOLEAN DEFAULT 0
        """)
        
        conn.commit()
        print("OK - Columna 'is_dispatched' agregada exitosamente a la tabla consumos")
        
    except Exception as e:
        print(f"ERROR - {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("Aplicando migracion: agregar campo is_dispatched a consumos...")
    print("")
    apply_migration()
