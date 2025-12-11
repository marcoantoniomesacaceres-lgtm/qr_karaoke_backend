#!/usr/bin/env python
"""Script de prueba para validar el sistema de aprobación de canciones"""

from database import SessionLocal
import models, crud, schemas
from timezone_utils import now_bogota
from datetime import timedelta

def test_approval_system():
    """Prueba el sistema de aprobación automática después de 10 minutos"""
    
    db = SessionLocal()
    try:
        print("=" * 60)
        print("PRUEBA: Sistema de Aprobación de Canciones")
        print("=" * 60)
        
        # 1. Crear un usuario de prueba
        print("\n1. Creando usuario de prueba...")
        existing_user = crud.get_usuario_by_nick(db, "TEST_USER")
        if existing_user:
            usuario_id = existing_user.id
            print(f"   ✓ Usuario existente: {existing_user.nick} (ID: {usuario_id})")
        else:
            # Crear una mesa primero
            mesa = models.Mesa(nombre="MESA_TEST", qr_code="test_qr_001")
            db.add(mesa)
            db.commit()
            
            usuario = models.Usuario(nick="TEST_USER", mesa_id=mesa.id)
            db.add(usuario)
            db.commit()
            usuario_id = usuario.id
            print(f"   ✓ Usuario creado: TEST_USER (ID: {usuario_id})")
        
        # 2. Crear canciones pendientes (con tiempos variados)
        print("\n2. Creando canciones pendientes...")
        
        # Canción antigua (más de 10 minutos)
        old_song = models.Cancion(
            titulo="Canción Antigua (>10 min)",
            youtube_id="oldtest001",
            duracion_seconds=180,
            estado="pendiente",
            usuario_id=usuario_id,
            created_at=now_bogota() - timedelta(minutes=11)
        )
        db.add(old_song)
        
        # Canción reciente (menos de 10 minutos)
        new_song = models.Cancion(
            titulo="Canción Reciente (<10 min)",
            youtube_id="newtest001",
            duracion_seconds=200,
            estado="pendiente",
            usuario_id=usuario_id,
            created_at=now_bogota()
        )
        db.add(new_song)
        
        db.commit()
        print(f"   ✓ Creada canción antigua (ID: {old_song.id})")
        print(f"   ✓ Creada canción reciente (ID: {new_song.id})")
        
        # 3. Probar aprobación automática
        print("\n3. Probando aprobación automática...")
        approved = crud.auto_approve_songs_after_10_minutes(db)
        print(f"   ✓ Canciones aprobadas automáticamente: {len(approved)}")
        for song in approved:
            print(f"     - {song.titulo} (ID: {song.id}, approved_at: {song.approved_at})")
        
        # 4. Verificar que la canción reciente sigue pendiente
        print("\n4. Verificando estados...")
        db.refresh(new_song)
        db.refresh(old_song)
        print(f"   ✓ Canción antigua: {old_song.estado} (esperado: aprobado)")
        print(f"   ✓ Canción reciente: {new_song.estado} (esperado: pendiente)")
        
        # 5. Obtener cola completa
        print("\n5. Obteniendo cola completa...")
        cola = crud.get_cola_completa(db)
        print(f"   ✓ Now Playing: {cola['now_playing']}")
        print(f"   ✓ Approved Songs: {len(cola['upcoming'])}")
        print(f"   ✓ Pending Songs: {len(cola['pending'])}")
        
        # 6. Probar aprobación manual
        print("\n6. Probando aprobación manual...")
        approved_manual = crud.approve_song_by_admin(db, new_song.id)
        if approved_manual:
            print(f"   ✓ Canción aprobada manualmente: {approved_manual.titulo}")
            print(f"   ✓ Nuevo estado: {approved_manual.estado}")
        
        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_approval_system()
