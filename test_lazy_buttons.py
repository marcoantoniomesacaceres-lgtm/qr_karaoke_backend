#!/usr/bin/env python
"""
Script de prueba para verificar que los endpoints de cola lazy funcionan correctamente.
"""

import requests
import json
from typing import Dict

# Configuración
API_BASE_URL = "http://192.168.20.94:8000"
ADMIN_API_KEY = "test-api-key-default"  # Reemplazar con la clave real si es necesario

# Headers
headers = {
    "X-API-Key": ADMIN_API_KEY,
    "Content-Type": "application/json"
}

def test_endpoints():
    """Prueba los endpoints de la cola lazy"""
    
    print("=" * 70)
    print("TEST: ENDPOINTS DE COLA LAZY")
    print("=" * 70)
    
    # 1. Obtener la cola completa con lazy
    print("\n1️⃣  Obteniendo cola con lazy queue...")
    try:
        response = requests.get(f"{API_BASE_URL}/canciones/cola/extended", headers=headers)
        if response.status_code == 200:
            data = response.json()
            lazy_queue = data.get('lazy_queue', [])
            print(f"   ✓ Cola lazy obtenida: {len(lazy_queue)} canciones")
            
            if lazy_queue:
                cancion_id = lazy_queue[0]['id']
                print(f"   📌 Primera canción lazy: {lazy_queue[0]['titulo']} (ID: {cancion_id})")
                
                # 2. Probar move-up
                print(f"\n2️⃣  Intentando mover canción {cancion_id} hacia ARRIBA...")
                move_up_response = requests.post(
                    f"{API_BASE_URL}/admin/canciones/lazy/{cancion_id}/move-up",
                    headers=headers
                )
                if move_up_response.status_code == 200:
                    print(f"   ✓ Move-up: {move_up_response.json()}")
                else:
                    print(f"   ✗ Error ({move_up_response.status_code}): {move_up_response.text}")
                
                # 3. Probar move-down
                print(f"\n3️⃣  Intentando mover canción {cancion_id} hacia ABAJO...")
                move_down_response = requests.post(
                    f"{API_BASE_URL}/admin/canciones/lazy/{cancion_id}/move-down",
                    headers=headers
                )
                if move_down_response.status_code == 200:
                    print(f"   ✓ Move-down: {move_down_response.json()}")
                else:
                    print(f"   ✗ Error ({move_down_response.status_code}): {move_down_response.text}")
            else:
                print("   ⚠️  No hay canciones en cola lazy para probar")
        else:
            print(f"   ✗ Error ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"   ✗ Excepción: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETADO")
    print("=" * 70)

if __name__ == "__main__":
    test_endpoints()
