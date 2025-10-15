import sys
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import SessionLocal
import crud, models

def main():
    db = SessionLocal()
    try:
        qr = 'karaoke-mesa-01'
        existing = crud.get_mesa_by_qr(db, qr_code=qr)
        if existing:
            print('Mesa ya existe:', existing.id, existing.nombre, existing.qr_code)
            return
        # Create with a readable name
        mesa = models.Mesa(nombre='Mesa 01', qr_code=qr)
        db.add(mesa)
        db.commit()
        db.refresh(mesa)
        print('Mesa creada:', mesa.id, mesa.nombre, mesa.qr_code)
    except Exception as e:
        print('ERROR creando mesa:', e, file=sys.stderr)
    finally:
        db.close()

if __name__ == '__main__':
    main()
