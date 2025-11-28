"""
Script para aplicar el cambio en la función check_if_song_in_user_list en crud.py
Este script modifica la verificación de canciones duplicadas para que funcione a nivel de mesa.
"""

import re

def aplicar_cambio():
    # Leer el archivo crud.py
    with open('crud.py', 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Patrón para encontrar la función actual
    patron_viejo = r'def check_if_song_in_user_list\(db: Session, usuario_id: int, youtube_id: str\):\s*"""[^"]*"""\s*return db\.query\(models\.Cancion\)\.filter\([^)]+\)\.first\(\)'
    
    # Nueva función
    nueva_funcion = '''def check_if_song_in_user_list(db: Session, usuario_id: int, youtube_id: str):
    """
    Verifica si ALGÚN USUARIO DE LA MISMA MESA ya tiene esta canción en la cola.
    CAMBIO: Ahora verifica a nivel de mesa para evitar duplicados entre usuarios de la misma mesa.
    """
    # Obtener el usuario y su mesa
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario or not usuario.mesa_id:
        return None
    
    # Buscar si algún usuario de la misma mesa ya tiene esta canción en cola
    return db.query(models.Cancion).join(
        models.Usuario, models.Cancion.usuario_id == models.Usuario.id
    ).filter(
        models.Usuario.mesa_id == usuario.mesa_id,
        models.Cancion.youtube_id == youtube_id,
        models.Cancion.estado.in_(['pendiente', 'aprobado', 'reproduciendo'])
    ).first()'''
    
    # Buscar la función en el contenido
    if 'def check_if_song_in_user_list' in contenido:
        # Encontrar el inicio de la función
        inicio = contenido.find('def check_if_song_in_user_list')
        if inicio == -1:
            print("❌ No se encontró la función check_if_song_in_user_list")
            return False
        
        # Encontrar el final de la función (siguiente def o final del archivo)
        fin = contenido.find('\ndef ', inicio + 1)
        if fin == -1:
            fin = len(contenido)
        
        # Extraer la función actual
        funcion_actual = contenido[inicio:fin]
        
        # Mostrar la función actual
        print("📄 Función actual encontrada:")
        print("=" * 80)
        print(funcion_actual[:200] + "...")
        print("=" * 80)
        
        # Reemplazar la función
        contenido_nuevo = contenido[:inicio] + nueva_funcion + contenido[fin:]
        
        # Crear backup
        with open('crud.py.backup_antes_cambio', 'w', encoding='utf-8') as f:
            f.write(contenido)
        print("\n✅ Backup creado: crud.py.backup_antes_cambio")
        
        # Escribir el nuevo contenido
        with open('crud.py', 'w', encoding='utf-8') as f:
            f.write(contenido_nuevo)
        
        print("✅ Cambio aplicado exitosamente en crud.py")
        print("\n📋 Nueva función:")
        print("=" * 80)
        print(nueva_funcion)
        print("=" * 80)
        
        return True
    else:
        print("❌ No se encontró la función check_if_song_in_user_list en crud.py")
        return False

if __name__ == "__main__":
    print("🔧 Aplicando cambio en crud.py...")
    print()
    
    try:
        if aplicar_cambio():
            print("\n✅ ¡Cambio aplicado con éxito!")
            print("\n📝 Próximos pasos:")
            print("   1. Revisa el cambio en crud.py")
            print("   2. Ejecuta: python generate_qr_mesas.py")
            print("   3. Reinicia el servidor")
        else:
            print("\n❌ No se pudo aplicar el cambio")
            print("   Por favor, aplica el cambio manualmente siguiendo las instrucciones en:")
            print("   SISTEMA_MULTIPLES_USUARIOS_POR_MESA.md")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Por favor, aplica el cambio manualmente")
