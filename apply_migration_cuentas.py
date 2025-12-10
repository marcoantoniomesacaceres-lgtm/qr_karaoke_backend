import sqlite3
import os
from datetime import datetime

DB_FILE = "karaoke.db"

def run_migration():
    if not os.path.exists(DB_FILE):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # 1. Create 'cuentas' table if it doesn't exist
        print("Creating 'cuentas' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cuentas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mesa_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP,
                closed_at TIMESTAMP,
                FOREIGN KEY(mesa_id) REFERENCES mesas(id)
            )
        """)
        
        # 2. Add 'cuenta_id' to 'consumos' if not exists
        print("Checking 'consumos' table...")
        cursor.execute("PRAGMA table_info(consumos)")
        columns = [info[1] for info in cursor.fetchall()]
        if "cuenta_id" not in columns:
            print("Adding 'cuenta_id' column to 'consumos'...")
            cursor.execute("ALTER TABLE consumos ADD COLUMN cuenta_id INTEGER REFERENCES cuentas(id)")

        # 3. Add 'cuenta_id' to 'pagos' if not exists
        print("Checking 'pagos' table...")
        cursor.execute("PRAGMA table_info(pagos)")
        columns = [info[1] for info in cursor.fetchall()]
        if "cuenta_id" not in columns:
            print("Adding 'cuenta_id' column to 'pagos'...")
            cursor.execute("ALTER TABLE pagos ADD COLUMN cuenta_id INTEGER REFERENCES cuentas(id)")

        # 4. Migrate Data: Create active account for each mesa and link items
        print("Migrating data...")
        
        # Get all mesas
        cursor.execute("SELECT id FROM mesas")
        mesas = cursor.fetchall()
        
        for (mesa_id,) in mesas:
            # Check if there is already an active cuenta for this mesa
            cursor.execute("SELECT id FROM cuentas WHERE mesa_id = ? AND is_active = 1", (mesa_id,))
            active_cuenta = cursor.fetchone()
            
            if not active_cuenta:
                # Create active cuenta
                now = datetime.now()
                cursor.execute("INSERT INTO cuentas (mesa_id, is_active, created_at) VALUES (?, 1, ?)", (mesa_id, now))
                cuenta_id = cursor.lastrowid
                print(f"Created active cuenta {cuenta_id} for mesa {mesa_id}")
            else:
                cuenta_id = active_cuenta[0]
                # print(f"Mesa {mesa_id} already has active cuenta {cuenta_id}")

            # Link unlinked consumos to this compte
            cursor.execute("UPDATE consumos SET cuenta_id = ? WHERE mesa_id = ? AND cuenta_id IS NULL", (cuenta_id, mesa_id))
            
            # Link unlinked pagos to this compte
            cursor.execute("UPDATE pagos SET cuenta_id = ? WHERE mesa_id = ? AND cuenta_id IS NULL", (cuenta_id, mesa_id))

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        print(f"Error migrating: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
