import qrcode
import socket
import os

# --- CONFIGURACIÓN ---
# Asegúrate de que este número coincida con el de tu script `crear_mesas.py`
NUMERO_DE_MESAS = 30
# Número de usuarios por mesa (QR codes por mesa)
USUARIOS_POR_MESA = 10
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
    Genera códigos QR para cada mesa con múltiples usuarios.
    Para cada mesa se generan 10 QR codes (uno por cada usuario posible).
    Formato: karaoke-mesa-XX-usuarioN donde XX es el número de mesa y N es 1-10.
    """
    local_ip = get_local_ip()
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Directorio '{OUTPUT_DIR}' creado.")

    total_qrs = NUMERO_DE_MESAS * USUARIOS_POR_MESA
    print(f"Generando {total_qrs} códigos QR ({NUMERO_DE_MESAS} mesas x {USUARIOS_POR_MESA} usuarios) para la IP: {local_ip}...")
    print()

    for mesa_num in range(1, NUMERO_DE_MESAS + 1):
        # Crear subdirectorio para cada mesa
        mesa_dir = os.path.join(OUTPUT_DIR, f"mesa_{mesa_num:02d}")
        if not os.path.exists(mesa_dir):
            os.makedirs(mesa_dir)
        
        print(f"📋 Mesa {mesa_num:02d}:")
        
        for usuario_num in range(1, USUARIOS_POR_MESA + 1):
            qr_code_completo = f"karaoke-mesa-{mesa_num:02d}-usuario{usuario_num}"
            url = f"http://{local_ip}:8000/?table={qr_code_completo}"
            
            qr_img = qrcode.make(url)
            file_path = os.path.join(mesa_dir, f"usuario_{usuario_num}.png")
            qr_img.save(file_path)
            
            print(f"  ✅ Usuario {usuario_num}: {qr_code_completo}")
        
        print()

    print(f"\n🎉 Proceso completado!")
    print(f"📁 Todos los QR están organizados en la carpeta '{OUTPUT_DIR}'")
    print(f"📊 Total: {NUMERO_DE_MESAS} mesas con {USUARIOS_POR_MESA} usuarios cada una")
    print(f"\n💡 Instrucciones:")
    print(f"   - Cada mesa tiene su propia carpeta con 10 QR codes")
    print(f"   - Imprime todos los QR de cada mesa y colócalos en la mesa correspondiente")
    print(f"   - Cada usuario escaneará un QR diferente para evitar conflictos")

if __name__ == "__main__":
    generate_table_qrs()