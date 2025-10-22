import requests
import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# --- CONFIGURACIÓN ---
# Asegúrate de que esta URL coincida con la de tu servidor local
API_URL = "http://127.0.0.1:8000/api/v1/mesas/"
NUMERO_DE_MESAS = 30
TIMEOUT_SECONDS = 5

def crear_mesas():
    """
    Script para crear múltiples mesas en el sistema de karaoke.
    """
    print(f"Iniciando la creación de {NUMERO_DE_MESAS} mesas...")

    # Obtenemos la clave de API de las variables de entorno
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
    if not ADMIN_API_KEY:
        print("\n[ERROR] La variable de entorno ADMIN_API_KEY no está configurada.")
        print("Asegúrate de tener un archivo .env con ADMIN_API_KEY='tu_clave_aqui'.")
        return

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": ADMIN_API_KEY
    }

    # Primero, asegúrate de que el servidor esté corriendo.
    try:
        # Usamos un endpoint de la API (protegido) para verificar la conexión y la clave.
        response = requests.get(API_URL, headers=headers, timeout=TIMEOUT_SECONDS)
        response.raise_for_status() # Lanza un error si el status no es 2xx
        mesas_existentes = {mesa['qr_code'] for mesa in response.json()}
        print(f"Conexión exitosa. Encontradas {len(mesas_existentes)} mesas existentes.")

    except requests.exceptions.ConnectionError:
        print("\n[ERROR] No se pudo conectar con el servidor en http://127.0.0.1:8000.")
        print("Por favor, asegúrate de que el servidor FastAPI esté en ejecución antes de correr este script.")
        return
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print("\n[ERROR] Error de autenticación (403 Forbidden). Tu ADMIN_API_KEY es incorrecta.")
        else:
            print(f"\n[ERROR] El servidor respondió con un error: {e.response.status_code} - {e.response.text}")
        return

    for i in range(1, NUMERO_DE_MESAS + 1):
        # Generamos un nombre y un identificador único para el QR
        nombre_mesa = f"Mesa {i}"
        qr_code_mesa = f"karaoke-mesa-{i:02d}" # :02d asegura números como 01, 02, etc.

        payload = {
            "nombre": nombre_mesa,
            "qr_code": qr_code_mesa
        }

        if qr_code_mesa in mesas_existentes:
            print(f"ℹ️  La mesa con QR Code '{qr_code_mesa}' ya existe. Saltando...")
            continue

        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=TIMEOUT_SECONDS)
            if response.status_code in [200, 201]:
                print(f"✅ Mesa '{nombre_mesa}' creada con éxito. QR Code: '{qr_code_mesa}'")
            else:
                print(f"❌ Error al crear la mesa {i}: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Ocurrió un error de red: {e}")
            break

    print("\nProceso finalizado.")

if __name__ == "__main__":
    crear_mesas()