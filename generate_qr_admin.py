import qrcode

# URL de acceso al panel admin (ajusta la IP)
admin_url = "http://192.168.20.94:8000/admin"

# Generar el QR
qr = qrcode.make(admin_url)
qr.save("admin_qr.png")

print("✅ QR del administrador generado: admin_qr.png")