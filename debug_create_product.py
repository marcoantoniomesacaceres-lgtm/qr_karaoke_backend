import traceback
from decimal import Decimal
from database import SessionLocal
import crud, schemas

print('Opening DB session...')
db = SessionLocal()
try:
    prod = schemas.ProductoCreate(nombre='TEST_DRINK', categoria='bebida', valor=Decimal('10.0'), stock=5)
    print('Calling crud.create_producto...')
    new_p = crud.create_producto(db, producto=prod)
    print('Created product with id:', getattr(new_p, 'id', None))
except Exception as e:
    print('EXCEPTION RAISED:')
    traceback.print_exc()
finally:
    db.close()
print('Done')
