#!/usr/bin/env python3
"""
Script de prueba para el endpoint: POST /api/v1/admin/mesas/{mesa_id}/add-song
Este script verifica que el endpoint funciona correctamente y devuelve una respuesta 200.
"""
import requests
import json

# Configuración
BASE_URL = "http://192.168.20.94:8000"
API_KEY = "test_admin_key"  # Esta debe ser una clave de API válida del admin

def test_add_song_to_mesa():
    """Prueba agregar una canción a una mesa específica."""
    
    # Primero necesitamos obtener una clave de API válida del admin
    # Para esto, necesitarías tener acceso a los logs o tener una clave preconfigurada
    
    mesa_id = 1
    
    # Datos de la canción
    song_data = {
        "titulo": "Bohemian Rhapsody",
        "youtube_id": "fJ9rUzIMt7o",
        "duracion_seconds": 355
    }
    
    # Realizar la petición POST
    url = f"{BASE_URL}/api/v1/admin/mesas/{mesa_id}/add-song"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"Enviando petición POST a: {url}")
    print(f"Headers: {headers}")
    print(f"Datos: {json.dumps(song_data, indent=2)}")
    
    try:
        response = requests.post(url, json=song_data, headers=headers, timeout=5)
        print(f"\n✓ Respuesta recibida:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n✅ ¡Éxito! El endpoint funciona correctamente.")
            return True
        else:
            print(f"\n❌ Error: El endpoint devolvió status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error de conexión: {e}")
        return False

if __name__ == "__main__":
    test_add_song_to_mesa()
