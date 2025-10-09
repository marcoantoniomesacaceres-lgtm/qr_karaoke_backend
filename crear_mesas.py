import requests
import json

# --- CONFIGURACIÓN ---
# Asegúrate de que esta URL coincida con la de tu servidor local
API_URL = "http://127.0.0.1:8000/api/v1/mesas/"
NUMERO_DE_MESAS = 30
# ---------------------

def crear_mesas():
    """
    Script para crear múltiples mesas en el sistema de karaoke.
    """
    print(f"Iniciando la creación de {NUMERO_DE_MESAS} mesas...")

    # Primero, asegúrate de que el servidor esté corriendo.
    try:
        # Usamos el endpoint de la documentación que no requiere autenticación
        requests.get("http://127.0.0.1:8000/docs", timeout=3)
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] No se pudo conectar con el servidor en http://127.0.0.1:8000.")
        print("Por favor, asegúrate de que el servidor FastAPI esté en ejecución antes de correr este script.")
        return

    for i in range(1, NUMERO_DE_MESAS + 1):
        # Generamos un nombre y un identificador único para el QR
        nombre_mesa = f"Mesa {i}"
        qr_code_mesa = f"karaoke-mesa-{i:02d}" # :02d asegura números como 01, 02, etc.

        payload = {
            "nombre": nombre_mesa,
            "qr_code": qr_code_mesa
        }

        try:
            # Para este endpoint no se necesita API Key
            response = requests.post(API_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})

            if response.status_code in [200, 201]:
                print(f"✅ Mesa '{nombre_mesa}' creada con éxito. QR Code: '{qr_code_mesa}'")
            elif response.status_code == 400 and "ya está registrado" in response.json().get("detail", ""):
                print(f"⚠️  La mesa con QR Code '{qr_code_mesa}' ya existe. Saltando...")
            else:
                print(f"❌ Error al crear la mesa {i}: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Ocurrió un error de red: {e}")
            break

    print("\nProceso finalizado.")

if __name__ == "__main__":
    crear_mesas()