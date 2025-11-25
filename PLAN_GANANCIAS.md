# PLAN PARA IMPLEMENTAR GANANCIAS REALES

## Problema Actual
El dashboard muestra "Ganancias" calculadas como `ingresos - costos`, pero:
1. El campo `costos_totales` NO existe en el backend
2. El modelo `Producto` NO tiene un campo para el costo de compra
3. No se están calculando las ganancias reales (precio venta - precio compra)

## Solución Propuesta

### 1. Agregar campo `costo` al modelo Producto
```python
# En models.py, clase Producto:
costo = Column(Numeric(10, 2), default=0)  # Precio de compra del producto
```

### 2. Crear migración de Alembic
Agregar la columna `costo` a la tabla `productos`

### 3. Crear función para calcular ganancias reales
```python
# En crud.py:
def get_ganancias_totales(db: Session):
    """
    Calcula las ganancias reales: (precio_venta - costo) * cantidad
    Solo de productos que ya fueron pagados.
    """
    # Obtener todos los pagos
    pagos = db.query(models.Pago).all()
    
    ganancias_total = 0
    for pago in pagos:
        # Para cada pago, obtener los consumos de esa mesa
        consumos = db.query(models.Consumo).join(models.Usuario).filter(
            models.Usuario.mesa_id == pago.mesa_id
        ).all()
        
        for consumo in consumos:
            producto = consumo.producto
            # Ganancia = (precio_venta - costo) * cantidad
            ganancia_item = (producto.valor - producto.costo) * consumo.cantidad
            ganancias_total += ganancia_item
    
    return ganancias_total
```

### 4. Actualizar schema ResumenNoche
```python
# En schemas.py:
class ResumenNoche(BaseModel):
    ingresos_totales: Decimal
    ganancias_totales: Decimal  # NUEVO
    canciones_cantadas: int
    usuarios_activos: int
```

### 5. Actualizar endpoint /admin/summary
```python
# En admin.py:
@router.get("/summary", response_model=schemas.ResumenNoche)
def get_night_summary(db: Session = Depends(get_db)):
    summary_data = crud.get_resumen_noche(db)
    ganancias = crud.get_ganancias_totales(db)  # NUEVO
    
    return {
        'ingresos_totales': summary_data['ingresos_totales'],
        'ganancias_totales': ganancias,  # NUEVO
        'canciones_cantadas': summary_data['canciones_cantadas'],
        'usuarios_activos': summary_data['usuarios_activos'],
    }
```

### 6. Actualizar dashboard.html
Cambiar "Ganancias Totales" por "Ganancias"

### 7. Actualizar dashboard.js
```javascript
const ganancias = Number(summary.ganancias_totales) || 0;
document.getElementById('summary-profits').textContent = `$${ganancias.toFixed(2)}`;
```

## Notas Importantes
- Los productos existentes tendrán `costo = 0` por defecto
- Deberás actualizar el costo de cada producto manualmente
- Las ganancias solo se calcularán de mesas que hayan pagado
