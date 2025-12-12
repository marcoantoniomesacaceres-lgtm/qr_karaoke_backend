"""
Script para limpiar null bytes del archivo crud.py
"""

# Leer el archivo con manejo de errores
try:
    with open('crud.py', 'rb') as f:
        content = f.read()
    
    print(f"Tamaño original: {len(content)} bytes")
    print(f"Null bytes encontrados: {content.count(b'\\x00')}")
    
    # Eliminar null bytes
    cleaned_content = content.replace(b'\x00', b'')
    
    print(f"Tamaño limpio: {len(cleaned_content)} bytes")
    
    # Guardar el archivo limpio
    with open('crud.py', 'wb') as f:
        f.write(cleaned_content)
    
    print("Archivo limpiado exitosamente")
    
except Exception as e:
    print(f"Error: {e}")
