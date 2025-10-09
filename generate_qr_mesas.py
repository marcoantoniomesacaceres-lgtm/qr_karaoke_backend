import qrcode
import socket
import os

# --- CONFIGURACIÓN ---
# Asegúrate de que este número coincida con el de tu script `crear_mesas.py`
NUMERO_DE_MESAS = 30
# Directorio donde se guardarán los códigos QR
OUTPUT_DIR = "qrcodes_mesas"
# ---------------------

def get_local_ip():
    """Obtiene la dirección IP local de la máquina."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No necesita estar conectado, solo es para obtener la IP
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        print("⚠️ No se pudo determinar la IP local. Usando '127.0.0.1'.")
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def generate_table_qrs():
    """
    Genera un código QR para cada mesa y lo guarda en un directorio.
    """
    local_ip = get_local_ip()
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Directorio '{OUTPUT_DIR}' creado.")

    print(f"Generando {NUMERO_DE_MESAS} códigos QR para la IP: {local_ip}...")

    for i in range(1, NUMERO_DE_MESAS + 1):
        qr_code_mesa = f"karaoke-mesa-{i:02d}"
        url = f"http://{local_ip}:8000/?table={qr_code_mesa}"
        qr_img = qrcode.make(url)
        file_path = os.path.join(OUTPUT_DIR, f"mesa_{i:02d}.png")
        qr_img.save(file_path)
        print(f"✅ QR para '{qr_code_mesa}' guardado en '{file_path}'")

    print(f"\nProceso completado. Todos los QR están en la carpeta '{OUTPUT_DIR}'.")

if __name__ == "__main__":
    generate_table_qrs()