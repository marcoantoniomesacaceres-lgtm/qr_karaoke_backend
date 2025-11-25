#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para agregar la función get_ganancias_totales a crud.py
"""

def add_ganancias_function():
    filepath = 'crud.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar donde está get_total_ingresos y agregar después
    function_to_add = '''
def get_ganancias_totales(db: Session):
    """
    Calcula las ganancias reales: (precio_venta - costo) * cantidad
    Solo de productos que ya fueron pagados (mesas con pagos registrados).
    """
    from decimal import Decimal
    
    # Obtener todas las mesas que tienen al menos un pago
    mesas_con_pagos = db.query(models.Pago.mesa_id).distinct().all()
    mesas_ids = [mesa_id for (mesa_id,) in mesas_con_pagos]
    
    if not mesas_ids:
        return Decimal("0")
    
    # Obtener todos los consumos de esas mesas
    consumos = (
        db.query(models.Consumo)
        .join(models.Usuario)
        .filter(models.Usuario.mesa_id.in_(mesas_ids))
        .all()
    )
    
    ganancias_total = Decimal("0")
    for consumo in consumos:
        producto = consumo.producto
        # Ganancia = (precio_venta - costo) * cantidad
        ganancia_item = (producto.valor - producto.costo) * consumo.cantidad
        ganancias_total += ganancia_item
    
    return ganancias_total

'''
    
    # Encontrar la posición después de get_total_ingresos
    marker = '''def get_total_ingresos(db: Session):
    """Calcula la suma total de todos los pagos recibidos durante la noche."""
    total = db.query(func.sum(models.Pago.monto)).scalar()
    return total or 0
'''
    
    if marker in content:
        content = content.replace(marker, marker + function_to_add)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("OK - Funcion get_ganancias_totales agregada a crud.py")
        return True
    else:
        print("ERROR - No se encontro la funcion get_total_ingresos en crud.py")
        return False

def update_admin_summary():
    filepath = 'admin.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar el endpoint /summary y actualizarlo
    old_endpoint = '''    summary_data = crud.get_resumen_noche(db)
    # Aseguramos que los tipos sean primitivos JSON-serializables (float/int)
    ingresos = summary_data.get('ingresos_totales', 0)
    try:
        ingresos_val = float(ingresos)
    except Exception:
        ingresos_val = 0.0

    canciones = summary_data.get('canciones_cantadas', 0)
    try:
        canciones_val = int(canciones)
    except Exception:
        canciones_val = 0

    usuarios = summary_data.get('usuarios_activos', 0)
    try:
        usuarios_val = int(usuarios)
    except Exception:
        usuarios_val = 0

    return {
        'ingresos_totales': ingresos_val,
        'canciones_cantadas': canciones_val,
        'usuarios_activos': usuarios_val,
    }'''
    
    new_endpoint = '''    summary_data = crud.get_resumen_noche(db)
    ganancias = crud.get_ganancias_totales(db)
    
    # Aseguramos que los tipos sean primitivos JSON-serializables (float/int)
    ingresos = summary_data.get('ingresos_totales', 0)
    try:
        ingresos_val = float(ingresos)
    except Exception:
        ingresos_val = 0.0

    try:
        ganancias_val = float(ganancias)
    except Exception:
        ganancias_val = 0.0

    canciones = summary_data.get('canciones_cantadas', 0)
    try:
        canciones_val = int(canciones)
    except Exception:
        canciones_val = 0

    usuarios = summary_data.get('usuarios_activos', 0)
    try:
        usuarios_val = int(usuarios)
    except Exception:
        usuarios_val = 0

    return {
        'ingresos_totales': ingresos_val,
        'ganancias_totales': ganancias_val,
        'canciones_cantadas': canciones_val,
        'usuarios_activos': usuarios_val,
    }'''
    
    if old_endpoint in content:
        content = content.replace(old_endpoint, new_endpoint)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("OK - Endpoint /admin/summary actualizado en admin.py")
        return True
    else:
        print("ERROR - No se encontro el endpoint /summary en admin.py")
        return False

if __name__ == '__main__':
    print("Agregando funciones de ganancias...")
    print("")
    success1 = add_ganancias_function()
    success2 = update_admin_summary()
    print("")
    if success1 and success2:
        print("Cambios aplicados exitosamente!")
        print("")
        print("Proximo paso:")
        print("Ejecutar: python apply_migration.py add_costo_to_productos")
    else:
        print("Hubo errores. Revisa los archivos manualmente.")
