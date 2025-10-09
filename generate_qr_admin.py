import qrcode
import socket

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

local_ip = get_local_ip()
admin_url = f"http://{local_ip}:8000/admin"

# Generar el QR
qr = qrcode.make(admin_url)
qr.save("admin_qr.png")

print(f"✅ QR del administrador generado para la URL: {admin_url}")
print("Archivo guardado como: admin_qr.png")