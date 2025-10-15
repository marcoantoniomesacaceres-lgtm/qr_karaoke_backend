import sys, os, json
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import SessionLocal
import models, requests

API_BASE = 'http://127.0.0.1:8000/api/v1/mesas'

def main():
    db = SessionLocal()
    try:
        mesas = db.query(models.Mesa).all()
        if not mesas:
            print('No hay mesas en la base de datos.')
            return
        print(f'Encontradas {len(mesas)} mesas. Comprobando conexión...')
        results = []
        for i, m in enumerate(mesas, start=1):
            qr = m.qr_code
            nick = f'test_auto_{i}'
            url = f'{API_BASE}/{qr}/conectar'
            try:
                r = requests.post(url, json={'nick': nick}, timeout=5)
                results.append((qr, r.status_code, r.text))
                print(qr, r.status_code)
            except Exception as e:
                results.append((qr, 'ERROR', str(e)))
                print(qr, 'ERROR', e)
        # Summary
        ok = [r for r in results if r[1]==200]
        errors = [r for r in results if r[1]!=200]
        print('\nResumen:')
        print('OK:', len(ok))
        print('Errores:', len(errors))
        if errors:
            print('\nDetalles errores:')
            for e in errors:
                print(e)
    finally:
        db.close()

if __name__ == '__main__':
    main()
