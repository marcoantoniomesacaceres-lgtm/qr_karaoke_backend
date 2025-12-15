import runpy
import sys
import os

# Ejecutar main.py para inicializar la app y obtener su namespace
try:
    main_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'main.py'))
    # Asegurarnos de que el directorio raíz del proyecto esté en sys.path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    print('Intentando ejecutar:', main_path)
    ns = runpy.run_path(main_path)
    app = ns.get('app') or (sys.modules.get('main').__dict__.get('app') if 'main' in sys.modules else None)
    if not app:
        print('No se encontró `app` en main.py (ejecutado).')
    else:
        print('Rutas registradas (path -> methods):')
        for r in app.routes:
            methods = getattr(r, 'methods', None)
            print(f"{r.path} -> {methods}")
except Exception as e:
    print('Error al ejecutar main.py:', e)
    import traceback
    traceback.print_exc()
