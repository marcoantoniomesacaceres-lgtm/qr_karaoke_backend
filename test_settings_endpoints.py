"""
Script de prueba para verificar que los endpoints de configuración funcionan correctamente.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/admin"

def test_endpoints():
    print("🧪 PROBANDO ENDPOINTS DE CONFIGURACIÓN\n")
    print("=" * 60)
    
    # Test 1: GET /settings (obtener toda la configuración)
    print("\n✅ TEST 1: GET /api/v1/admin/settings")
    try:
        response = requests.get(f"{BASE_URL}/settings/", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: GET /settings/general (obtener configuración general)
    print("\n✅ TEST 2: GET /api/v1/admin/settings/general")
    try:
        response = requests.get(f"{BASE_URL}/settings/general", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: POST /settings/general (actualizar configuración general)
    print("\n✅ TEST 3: POST /api/v1/admin/settings/general")
    payload = {
        "app_name": "QR Karaoke - Prueba",
        "theme": "light",
        "enable_notifications": True
    }
    try:
        response = requests.post(f"{BASE_URL}/settings/general", json=payload, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: GET /settings/closing-time (obtener hora de cierre)
    print("\n✅ TEST 4: GET /api/v1/admin/settings/closing-time")
    try:
        response = requests.get(f"{BASE_URL}/settings/closing-time", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: POST /settings/closing-time (actualizar hora de cierre)
    print("\n✅ TEST 5: POST /api/v1/admin/settings/closing-time")
    payload = {
        "closing_hour": 4,
        "closing_minute": 30
    }
    try:
        response = requests.post(f"{BASE_URL}/settings/closing-time", json=payload, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: POST /set-closing-time (fallback endpoint)
    print("\n✅ TEST 6: POST /api/v1/admin/set-closing-time (FALLBACK)")
    payload = {
        "hora_cierre": "05:45"
    }
    try:
        response = requests.post(f"{BASE_URL}/set-closing-time", json=payload, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas. Verifica que todos muestren status 200-201")

if __name__ == "__main__":
    test_endpoints()
