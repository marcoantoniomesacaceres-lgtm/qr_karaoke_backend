#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que los usuarios de la misma mesa
no puedan agregar canciones duplicadas.
"""

import requests
import json

# Configuración
BASE_URL = "http://localhost:8000/api/v1"

def test_duplicate_song_same_table():
    """
    Prueba que dos usuarios de la misma mesa no puedan agregar la misma canción.
    """
    print("=" * 60)
    print("PRUEBA: Validación de canciones duplicadas a nivel de mesa")
    print("=" * 60)
    
    # Datos de la canción de prueba
    song_data = {
        "titulo": "Bohemian Rhapsody - Test",
        "youtube_id": "fJ9rUzIMcio",
        "duracion_seconds": 355
    }
    
    # Supongamos que tenemos dos usuarios de la Mesa 1
    # Usuario 1 de la Mesa 1 (ID podría ser diferente en tu BD)
    usuario1_id = 1  # Mesa 1 - Usuario 1
    usuario2_id = 2  # Mesa 1 - Usuario 2
    
    print(f"\n1. Usuario {usuario1_id} intenta agregar '{song_data['titulo']}'...")
    
    # Primer intento: Usuario 1 agrega la canción
    try:
        response1 = requests.post(
            f"{BASE_URL}/canciones/{usuario1_id}",
            json=song_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response1.status_code == 200:
            print(f"   ✅ Éxito! La canción fue agregada por el Usuario {usuario1_id}")
            print(f"   Respuesta: {response1.json()['titulo']}")
        else:
            print(f"   ⚠️  Error: {response1.status_code}")
            print(f"   Detalle: {response1.json().get('detail', 'Sin detalle')}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return
    
    print(f"\n2. Usuario {usuario2_id} (misma mesa) intenta agregar la MISMA canción...")
    
    # Segundo intento: Usuario 2 intenta agregar la misma canción
    try:
        response2 = requests.post(
            f"{BASE_URL}/canciones/{usuario2_id}",
            json=song_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response2.status_code == 409:
            print(f"   ✅ ¡Correcto! La canción fue rechazada (código 409)")
            print(f"   Mensaje: {response2.json().get('detail', 'Sin detalle')}")
            print("\n" + "=" * 60)
            print("✅ PRUEBA EXITOSA: La validación funciona correctamente")
            print("=" * 60)
        elif response2.status_code == 200:
            print(f"   ❌ ERROR: La canción fue agregada cuando NO debería")
            print(f"   Esto indica que la validación NO está funcionando")
            print("\n" + "=" * 60)
            print("❌ PRUEBA FALLIDA: La validación NO funciona")
            print("=" * 60)
        else:
            print(f"   ⚠️  Código inesperado: {response2.status_code}")
            print(f"   Detalle: {response2.json().get('detail', 'Sin detalle')}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")

if __name__ == "__main__":
    print("\n🎤 Iniciando prueba de validación de canciones duplicadas...\n")
    test_duplicate_song_same_table()
    print("\n✨ Prueba completada\n")
