# CAMBIOS NECESARIOS PARA CALCULAR INGRESOS CORRECTAMENTE

## Problema Identificado

Actualmente, los "ingresos totales" se calculan sumando TODOS los consumos (pedidos).
Esto es incorrecto porque:
- Un consumo puede nunca pagarse
- Los ingresos reales son solo el dinero que YA INGRESÓ (pagos recibidos)

## Solución

Los ingresos deben calcularse sumando los PAGOS, no los CONSUMOS.

---

## CAMBIOS EN crud.py

### 1. Función `get_total_ingresos` (líneas 477-480)

**ANTES:**
```python
def get_total_ingresos(db: Session):
    """Calcula la suma total de todos los consumos de la noche."""
    total = db.query(func.sum(models.Consumo.valor_total)).scalar()
    return total or 0
```

**DESPUÉS:**
```python
def get_total_ingresos(db: Session):
    """Calcula la suma total de todos los pagos recibidos durante la noche."""
    total = db.query(func.sum(models.Pago.monto)).scalar()
    return total or 0
```

---

### 2. Función `get_ingresos_por_mesa` (líneas 482-496)

**ANTES:**
```python
def get_ingresos_por_mesa(db: Session):
    """
    Calcula los ingresos totales agrupados por cada mesa.
    """
    return (
        db.query(
            models.Mesa.nombre,
            func.sum(models.Consumo.valor_total).label("ingresos_totales")
        )
        .join(models.Usuario, models.Mesa.id == models.Usuario.mesa_id)
        .join(models.Consumo, models.Usuario.id == models.Consumo.usuario_id)
        .group_by(models.Mesa.nombre)
        .order_by(func.sum(models.Consumo.valor_total).desc())
        .all()
    )
```

**DESPUÉS:**
```python
def get_ingresos_por_mesa(db: Session):
    """
    Calcula los ingresos totales (pagos recibidos) agrupados por cada mesa.
    """
    return (
        db.query(
            models.Mesa.nombre,
            func.sum(models.Pago.monto).label("ingresos_totales")
        )
        .join(models.Pago, models.Mesa.id == models.Pago.mesa_id)
        .group_by(models.Mesa.nombre)
        .order_by(func.sum(models.Pago.monto).desc())
        .all()
    )
```

---

### 3. Función `get_ingresos_por_categoria` (líneas 820-833)

Esta función NO PUEDE calcularse con pagos porque los pagos no tienen categoría.
Los pagos son por mesa, no por producto.

**OPCIÓN 1: Eliminar esta función** (ya que no tiene sentido con el modelo de pagos)

**OPCIÓN 2: Mantenerla pero cambiar su nombre y documentación:**

```python
def get_consumos_por_categoria(db: Session):
    """
    Calcula el VALOR DE CONSUMOS (no ingresos) agrupados por categoría.
    NOTA: Esto NO representa ingresos reales, solo consumos pedidos.
    """
    return (
        db.query(
            models.Producto.categoria,
            func.sum(models.Consumo.valor_total).label("valor_consumido")
        )
        .join(models.Producto, models.Consumo.producto_id == models.Producto.id)
        .group_by(models.Producto.categoria)
        .order_by(func.sum(models.Consumo.valor_total).desc())
        .all()
    )
```

---

## RESUMEN

**Concepto clave:**
- **Consumo** = Lo que el cliente pidió (puede o no pagarse)
- **Pago** = El dinero que realmente ingresó
- **Ingresos** = Suma de PAGOS, no de consumos

**Cambios mínimos necesarios:**
1. ✅ Cambiar `get_total_ingresos` para sumar `Pago.monto` en lugar de `Consumo.valor_total`
2. ✅ Cambiar `get_ingresos_por_mesa` para sumar `Pago.monto` en lugar de `Consumo.valor_total`
3. ⚠️ Decidir qué hacer con `get_ingresos_por_categoria` (eliminar o renombrar)

**Impacto:**
- Los reportes de "Ingresos Totales" ahora mostrarán solo el dinero que realmente ingresó
- Las mesas sin pagos registrados mostrarán $0 en ingresos (correcto)
- Las mesas con consumos pero sin pagos NO contarán como ingresos (correcto)
