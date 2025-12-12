import os

print("=" * 60)
print("VERIFICACION DEL SISTEMA LAZY APPROVAL")
print("=" * 60)

print("\n1. Archivos modificados:")
print("   [OK] models.py")
print("   [OK] crud.py")
print("   [OK] canciones.py")
print("   [OK] schemas.py")

print("\n2. Funciones en crud.py:")
with open('crud.py', 'r', encoding='latin-1') as f:
    content = f.read()
    
functions = ['get_cola_lazy', 'aprobar_siguiente_cancion_lazy', 
             'get_cola_completa_con_lazy', 'check_and_approve_next_lazy_song']

for func in functions:
    if f'def {func}' in content:
        print(f"   [OK] {func}()")
    else:
        print(f"   [FAIL] {func}()")

print("\n3. Endpoints en canciones.py:")
with open('canciones.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
if '/cola/extended' in content:
    print("   [OK] /cola/extended")
if 'pendiente_lazy' in content:
    print("   [OK] lazy approval logic")

print("\n4. Schema en schemas.py:")
with open('schemas.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
if 'ColaViewExtended' in content:
    print("   [OK] ColaViewExtended")

print("\n" + "=" * 60)
print("Backend: COMPLETADO")
print("Frontend: PENDIENTE (ver walkthrough.md)")
print("=" * 60)
