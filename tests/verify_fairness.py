
import sys
import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import crud and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models
import crud
from database import Base

# Setup In-Memory DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def test_fair_queue():
    db = TestingSessionLocal()
    
    # 1. Create Mesas & Users
    # Consumo: Bronze <= 50k, Silver > 50k, Gold > 150k
    
    # Mesa A (Gold) - Consumo 200k
    mesa_a = models.Mesa(nombre="Mesa A", qr_code="A", is_active=True)
    db.add(mesa_a)
    db.commit()
    user_a = models.Usuario(nick="UserA", mesa_id=mesa_a.id)
    db.add(user_a)
    db.commit()
    # Consumo
    db.add(models.Consumo(cantidad=1, valor_total=200000, mesa_id=mesa_a.id, usuario_id=user_a.id))
    
    # Mesa B (Silver) - Consumo 100k
    mesa_b = models.Mesa(nombre="Mesa B", qr_code="B", is_active=True)
    db.add(mesa_b)
    db.commit()
    user_b = models.Usuario(nick="UserB", mesa_id=mesa_b.id)
    db.add(user_b)
    db.commit()
    # Consumo
    db.add(models.Consumo(cantidad=1, valor_total=100000, mesa_id=mesa_b.id, usuario_id=user_b.id))
    
    # Mesa C (Bronze) - Consumo 10k
    mesa_c = models.Mesa(nombre="Mesa C", qr_code="C", is_active=True)
    db.add(mesa_c)
    db.commit()
    user_c = models.Usuario(nick="UserC", mesa_id=mesa_c.id)
    db.add(user_c)
    db.commit()
    # Consumo
    db.add(models.Consumo(cantidad=1, valor_total=10000, mesa_id=mesa_c.id, usuario_id=user_c.id))
    
    db.commit()
    
    # 2. Add Songs (Approved)
    # Order of arrival: A1, B1, C1, A2, B2, C2, A3, B3, C3, A4
    now = datetime.datetime.now()
    
    songs_data = [
        ("A1", user_a.id),
        ("B1", user_b.id),
        ("C1", user_c.id), # End of Round 1 expectation
        ("A2", user_a.id),
        ("B2", user_b.id),
        ("C2", user_c.id),
        ("A3", user_a.id),
        ("B3", user_b.id),
        ("C3", user_c.id),
        ("A4", user_a.id)
    ]
    
    for i, (title, uid) in enumerate(songs_data):
        song = models.Cancion(
            titulo=title,
            youtube_id=f"yt_{title}",
            usuario_id=uid,
            estado="aprobado",
            duracion_seconds=100,
            created_at=now + datetime.timedelta(seconds=i) # Incremental timestamp implies ID order
        )
        db.add(song)
    
    db.commit()
    
    # 3. Call get_cola_priorizada
    queue = crud.get_cola_priorizada(db)
    
    # 4. Verify Order
    # Expected Logic:
    # Arrival Order of First Song: A (A1), B (B1), C (C1) -> So Turn Order is A, B, C
    # Quotas: A(Gold)=3, B(Silver)=2, C(Bronze)=1
    
    # Round 1:
    # A takes 3: A1, A2, A3
    # B takes 2: B1, B2
    # C takes 1: C1
    
    # Round 2:
    # A takes remaining: A4
    # B takes remaining: B3
    # C takes remaining: C2
    
    # Round 3:
    # A empty
    # B empty
    # C takes remaining: C3
    
    # Expected List: A1, A2, A3, B1, B2, C1, A4, B3, C2, C3
    expected_titles = ["A1", "A2", "A3", "B1", "B2", "C1", "A4", "B3", "C2", "C3"]
    actual_titles = [s.titulo for s in queue]
    
    print(f"Expected: {expected_titles}")
    print(f"Actual:   {actual_titles}")
    
    if expected_titles == actual_titles:
        print("✅ TEST PASSED: Fair Queue logic is correct.")
    else:
        print("❌ TEST FAILED: Order mismatch.")
        
    db.close()

if __name__ == "__main__":
    test_fair_queue()
