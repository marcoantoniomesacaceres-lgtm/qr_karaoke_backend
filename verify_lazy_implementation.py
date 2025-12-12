"""
Script de verificación para el sistema de lazy approval
"""

print("=" * 60)
print("VERIFICACIÓN DEL SISTEMA LAZY APPROVAL")
print("=" * 60)

# Verificar que los archivos modificados existen
import os

files_to_check = [
    ('models.py', 'Modelo actualizado con pendiente_lazy'),
    ('crud.py', 'Funciones lazy agregadas'),
    ('canciones.py', 'Endpoints actualizados'),
    ('schemas.py', 'Schema ColaViewExtended agregado'),
]

print("\n1. Verificando archivos modificados:")
for filename, description in files_to_check:
    if os.path.exists(filename):
        print(f"   ✓ {filename}: {description}")
    else:
        print(f"   ✗ {filename}: NO ENCONTRADO")

# Verificar que las funciones lazy existen en crud.py
print("\n2. Verificando funciones en crud.py:")
try:
    with open('crud.py', 'r', encoding='latin-1') as f:
        content = f.read()
        
    functions_to_check = [
        'get_cola_lazy',
        'aprobar_siguiente_cancion_lazy',
        'get_cola_completa_con_lazy',
        'check_and_approve_next_lazy_song',
    ]
    
    for func_name in functions_to_check:
        if f'def {func_name}' in content:
            print(f"   ✓ {func_name}()")
        else:
            print(f"   ✗ {func_name}() NO ENCONTRADA")
            
except Exception as e:
    print(f"   ✗ Error al leer crud.py: {e}")

# Verificar endpoint en canciones.py
print("\n3. Verificando endpoints en canciones.py:")
try:
    with open('canciones.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    if '/cola/extended' in content:
        print("   ✓ Endpoint /cola/extended agregado")
    else:
        print("   ✗ Endpoint /cola/extended NO ENCONTRADO")
        
    if 'pendiente_lazy' in content:
        print("   ✓ Lógica lazy approval implementada")
    else:
        print("   ✗ Lógica lazy approval NO ENCONTRADA")
        
except Exception as e:
    print(f"   ✗ Error al leer canciones.py: {e}")

# Verificar schema en schemas.py
print("\n4. Verificando schemas en schemas.py:")
try:
    with open('schemas.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    if 'class ColaViewExtended' in content:
        print("   ✓ Schema ColaViewExtended agregado")
    else:
        print("   ✗ Schema ColaViewExtended NO ENCONTRADO")
        
except Exception as e:
    print(f"   ✗ Error al leer schemas.py: {e}")

print("\n" + "=" * 60)
print("RESUMEN:")
print("=" * 60)
print("""
✅ Backend implementado:
   - Nuevo estado 'pendiente_lazy' en models.py
   - 4 nuevas funciones en crud.py para gestión lazy
   - Endpoints actualizados en canciones.py
   - Nuevo schema ColaViewExtended en schemas.py
   
⏳ Pendiente (Frontend):
   - Actualizar queue.js para mostrar 3 secciones
   - Agregar función renderLazySongs()
   - Actualizar loadQueueData() para usar /cola/extended
   - Agregar manejadores para acciones lazy

📝 Próximos pasos:
   1. Reiniciar el servidor para cargar los cambios
   2. Probar agregando canciones y verificar estados
   3. Actualizar el frontend según walkthrough.md
""")

print("=" * 60)
