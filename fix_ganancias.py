#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para implementar el cálculo de ganancias reales.
"""

def update_models():
    """Agregar campo costo al modelo Producto"""
    filepath = 'models.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open(filepath + '.backup2', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Cambio: agregar campo costo después de valor
    old_line = '    valor = Column(Numeric(10, 2))'
    new_lines = '''    valor = Column(Numeric(10, 2))  # Precio de venta
    costo = Column(Numeric(10, 2), default=0)  # Precio de compra'''
    
    content = content.replace(old_line, new_lines)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("OK - models.py actualizado")

def update_schemas():
    """Actualizar schema ResumenNoche"""
    filepath = 'schemas.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open(filepath + '.backup2', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Cambio: agregar ganancias_totales
    old_schema = '''class ResumenNoche(BaseModel):
    ingresos_totales: Decimal
    canciones_cantadas: int
    usuarios_activos: int'''
    
    new_schema = '''class ResumenNoche(BaseModel):
    ingresos_totales: Decimal
    ganancias_totales: Decimal
    canciones_cantadas: int
    usuarios_activos: int'''
    
    content = content.replace(old_schema, new_schema)
    
    # Actualizar ProductoBase para incluir costo
    old_producto = '''class ProductoBase(BaseModel):
    nombre: str
    categoria: str
    valor: Decimal
    stock: int
    imagen_url: Optional[str] = None
    is_active: bool = True'''
    
    new_producto = '''class ProductoBase(BaseModel):
    nombre: str
    categoria: str
    valor: Decimal
    costo: Decimal = Decimal("0")
    stock: int
    imagen_url: Optional[str] = None
    is_active: bool = True'''
    
    content = content.replace(old_producto, new_producto)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("OK - schemas.py actualizado")

def update_dashboard_html():
    """Cambiar 'Ganancias Totales' por 'Ganancias'"""
    filepath = 'static/admin_pages/dashboard.html'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace('<h3>Ganancias Totales</h3>', '<h3>Ganancias</h3>')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("OK - dashboard.html actualizado")

def update_dashboard_js():
    """Actualizar dashboard.js para usar ganancias_totales del backend"""
    filepath = 'static/admin_pages/dashboard.js'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Cambio: usar ganancias_totales del backend en lugar de calcular
    old_code = '''        const summary = await apiFetch('/admin/summary');
        const ingresos = Number(summary.ingresos_totales) || 0;
        const costos = Number(summary.costos_totales) || 0;
        const ganancias = ingresos - costos;

        document.getElementById('summary-income').textContent = `$${ingresos.toFixed(2)}`;
        document.getElementById('summary-profits').textContent = `$${ganancias.toFixed(2)}`;'''
    
    new_code = '''        const summary = await apiFetch('/admin/summary');
        const ingresos = Number(summary.ingresos_totales) || 0;
        const ganancias = Number(summary.ganancias_totales) || 0;

        document.getElementById('summary-income').textContent = `$${ingresos.toFixed(2)}`;
        document.getElementById('summary-profits').textContent = `$${ganancias.toFixed(2)}`;'''
    
    content = content.replace(old_code, new_code)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("OK - dashboard.js actualizado")

if __name__ == '__main__':
    print("Aplicando cambios para ganancias reales...")
    print("")
    update_models()
    update_schemas()
    update_dashboard_html()
    update_dashboard_js()
    print("")
    print("Cambios aplicados exitosamente!")
    print("")
    print("Proximos pasos:")
    print("1. Crear migracion de Alembic para agregar columna 'costo' a productos")
    print("2. Agregar funcion get_ganancias_totales() en crud.py")
    print("3. Actualizar endpoint /admin/summary en admin.py")
