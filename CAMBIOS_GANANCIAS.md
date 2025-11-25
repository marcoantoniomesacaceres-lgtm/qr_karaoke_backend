# ✅ CAMBIOS APLICADOS: GANANCIAS REALES

## Fecha: 2025-11-25

## Cambios Implementados

### 1. ✅ Modelo de Datos Actualizado (`models.py`)
- **Agregado campo `costo`** al modelo `Producto`
  - `costo = Column(Numeric(10, 2), default=0)  # Precio de compra`
  - Permite almacenar el precio de compra de cada producto
  - Los productos existentes tienen `costo = 0` por defecto

### 2. ✅ Base de Datos Actualizada
- **Migración aplicada**: Columna `costo` agregada a la tabla `productos`
- Todos los productos existentes tienen `costo = 0`
- **Deberás actualizar manualmente el costo de cada producto**

### 3. ✅ Schemas Actualizados (`schemas.py`)
- **`ProductoBase`**: Agregado campo `costo: Decimal = Decimal("0")`
- **`ResumenNoche`**: Agregado campo `ganancias_totales: Decimal`

### 4. ✅ Lógica de Negocio (`crud.py`)
- **Nueva función `get_ganancias_totales()`**:
  ```python
  def get_ganancias_totales(db: Session):
      """
      Calcula las ganancias reales: (precio_venta - costo) * cantidad
      Solo de productos que ya fueron pagados (mesas con pagos registrados).
      """
  ```
  - Calcula: `(producto.valor - producto.costo) * consumo.cantidad`
  - **Solo cuenta productos de mesas que YA PAGARON**
  - Si una mesa no ha pagado, sus consumos NO cuentan para ganancias

### 5. ✅ API Actualizada (`admin.py`)
- **Endpoint `/admin/summary`** ahora retorna:
  ```json
  {
    "ingresos_totales": 15000.00,
    "ganancias_totales": 8500.00,
    "canciones_cantadas": 25,
    "usuarios_activos": 12
  }
  ```

### 6. ✅ Dashboard Actualizado
- **`dashboard.html`**: Cambiado "Ganancias Totales" → "Ganancias"
- **`dashboard.js`**: Ahora usa `summary.ganancias_totales` del backend

---

## Cómo Funciona

### Ejemplo Práctico:

**Producto: Cerveza**
- Precio de compra (costo): $4,000
- Precio de venta (valor): $7,000
- Ganancia por unidad: $3,000

**Escenario:**
1. Mesa 1 pide 5 cervezas → Consumo registrado ($35,000)
2. Mesa 1 **NO ha pagado** → Ganancia = $0 (no cuenta todavía)
3. Mesa 1 **paga su cuenta** → Pago registrado ($35,000)
4. **Ahora sí** se calcula la ganancia: 5 × $3,000 = **$15,000**

### Fórmula:
```
Ganancias Totales = Σ (precio_venta - costo) × cantidad
                    (solo de mesas que ya pagaron)
```

---

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `models.py` | ✅ Agregado campo `costo` a `Producto` |
| `schemas.py` | ✅ Actualizado `ProductoBase` y `ResumenNoche` |
| `crud.py` | ✅ Agregada función `get_ganancias_totales()` |
| `admin.py` | ✅ Actualizado endpoint `/admin/summary` |
| `dashboard.html` | ✅ Cambiado "Ganancias Totales" → "Ganancias" |
| `dashboard.js` | ✅ Usa `ganancias_totales` del backend |
| `karaoke.db` | ✅ Agregada columna `costo` a tabla `productos` |

---

## 📋 Próximos Pasos IMPORTANTES

### 1. Actualizar el Costo de Cada Producto
Debes ir a la sección de **Productos** en el dashboard y actualizar el **costo** (precio de compra) de cada producto.

**Ejemplo:**
- Cerveza Corona: costo = $4,000, valor = $7,000
- Whisky: costo = $15,000, valor = $25,000
- Hamburguesa: costo = $8,000, valor = $15,000

### 2. Verificar en el Dashboard
- Los "Ingresos" mostrarán el total de pagos recibidos
- Las "Ganancias" mostrarán la ganancia real (venta - costo)
- Si todos los productos tienen costo = 0, las ganancias serán iguales a los ingresos

---

## ⚠️ Notas Importantes

1. **Productos sin costo definido**: Si un producto tiene `costo = 0`, toda la venta se contará como ganancia
2. **Solo mesas que pagaron**: Las ganancias solo se calculan de mesas con pagos registrados
3. **Actualización en tiempo real**: El servidor se recargará automáticamente con los cambios

---

## Verificación

Para verificar que todo funciona:

1. ✅ El dashboard muestra "Ganancias" (no "Ganancias Totales")
2. ✅ El valor de ganancias se calcula correctamente
3. ✅ Solo se cuentan productos de mesas que ya pagaron
4. ✅ La fórmula es: (precio_venta - costo) × cantidad

---

## Backups Creados

- `models.py.backup2`
- `schemas.py.backup2`
- `crud.py.backup` (del cambio anterior de ingresos)

Si necesitas revertir algún cambio, estos archivos contienen las versiones anteriores.
