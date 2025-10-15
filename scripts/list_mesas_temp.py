import sys
import os
# Ensure project root is on sys.path so imports like `database` and `models` work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import SessionLocal
import models

def main():
    try:
        db = SessionLocal()
        rows = db.query(models.Mesa).all()
        if not rows:
            print("No mesas encontradas en la base de datos.")
            return
        print("Mesas en DB:")
        for m in rows:
            print(m.id, repr(m.nombre), m.qr_code)
    except Exception as e:
        print("ERROR al listar mesas:", e, file=sys.stderr)
    finally:
        try:
            db.close()
        except Exception:
            pass

if __name__ == '__main__':
    main()
