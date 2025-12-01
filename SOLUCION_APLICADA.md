# Solución Aplicada: Ocultar Pedidos Despachados en el Dashboard de Admin

## Problema
Los pedidos marcados como "despachado" o "no despachado" volvían a aparecer en la sección "Últimos Pedidos" del dashboard de administración después de actualizar la página.

## Solución Implementada

### 1. Modelo de Datos (`models.py`)
Se agregó un nuevo campo `is_dispatched` al modelo `Consumo`:

```python
class Consumo(Base):
    __tablename__ = "consumos"
    
    id = Column(Integer, primary_key=True, index=True)
    cantidad = Column(Integer, default=1)
    valor_total = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_dispatched = Column(Boolean, default=False)  # NUEVO CAMPO
    
    producto_id = Column(Integer, ForeignKey("productos.id"))
    mesa_id = Column(Integer, ForeignKey("mesas.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # ... relaciones ...
```

### 2. Migración de Base de Datos
Se ejecutó el script `apply_despachado_migration.py` para agregar la columna `is_dispatched` a la tabla `consumos` en la base de datos existente.

### 3. Backend - Filtrado de Consultas (`crud.py`)
Se modificó la función `get_recent_consumos` para filtrar los consumos que ya han sido despachados:

```python
def get_recent_consumos(db: Session, limit: int = 10):
    """
    Devuelve los consumos más recientes junto con el nombre del producto,
    nick del usuario y nombre de la mesa (si existe).
    Filtra los consumos que ya han sido despachados.
    """
    rows = (
        db.query(
            models.Consumo.id,
            models.Consumo.cantidad,
            models.Consumo.valor_total,
            models.Producto.nombre.label('producto_nombre'),
            models.Usuario.nick.label('usuario_nick'),
            models.Mesa.nombre.label('mesa_nombre'),
            models.Consumo.created_at
        )
        .join(models.Producto, models.Consumo.producto_id == models.Producto.id)
        .join(models.Usuario, models.Consumo.usuario_id == models.Usuario.id)
        .outerjoin(models.Mesa, models.Usuario.mesa_id == models.Mesa.id)
        .filter(models.Consumo.is_dispatched == False)  # FILTRO AGREGADO
        .order_by(models.Consumo.created_at.desc())
        .limit(limit)
        .all()
    )
    
    # ... mapeo de resultados ...
    return result
```

### 4. Backend - Endpoint de Marcado (`admin.py`)
Se actualizó el endpoint `admin_mark_consumo_despachado` para marcar el consumo como despachado en la base de datos:

```python
@router.post('/consumos/{consumo_id}/mark-despachado', status_code=200)
async def admin_mark_consumo_despachado(consumo_id: int, db: Session = Depends(get_db)):
    """
    Marca un consumo como despachado.
    No elimina el consumo de la base de datos, solo lo marca como despachado 
    para que no aparezca en "pedidos recientes".
    """
    db_consumo = db.query(models.Consumo).filter(models.Consumo.id == consumo_id).first()
    if not db_consumo:
        raise HTTPException(status_code=404, detail='Consumo no encontrado')

    # Marcar como despachado en la BD
    db_consumo.is_dispatched = True
    db.commit()

    # Registrar la acción en el log
    crud.create_admin_log_entry(db, action="MARK_CONSUMO_DESPACHADO", 
                                details=f"Consumo ID {consumo_id} marcado como despachado.")

    # Notificar a los clientes vía WebSocket
    try:
        await websocket_manager.manager.broadcast_consumo_deleted({'id': consumo_id})
    except Exception:
        pass

    return {"message": f"Consumo {consumo_id} marcado como despachado."}
```

### 5. Frontend (`static/admin_pages/dashboard.js`)
El frontend ya tenía la lógica correcta:
- Al hacer clic en "Despachado", llama al endpoint POST `/admin/consumos/{id}/mark-despachado`
- Al hacer clic en "No Despachado", llama al endpoint DELETE `/admin/consumos/{id}`
- Después de cada acción, recarga la lista de pedidos con `loadDashboardPage()`

## Flujo Completo

1. **Usuario hace clic en "Despachado"**:
   - Frontend envía POST a `/admin/consumos/{id}/mark-despachado`
   - Backend marca `is_dispatched = True` en la base de datos
   - Backend envía notificación WebSocket
   - Frontend elimina visualmente el elemento de la lista
   - Frontend recarga la lista de pedidos

2. **Recarga de la lista**:
   - Frontend llama a `/admin/recent-consumos?limit=25`
   - Backend ejecuta `get_recent_consumos()` que filtra `is_dispatched == False`
   - Solo se devuelven pedidos NO despachados
   - El pedido marcado como despachado ya no aparece

3. **Usuario hace clic en "No Despachado"**:
   - Frontend envía DELETE a `/admin/consumos/{id}`
   - Backend elimina completamente el registro de la base de datos
   - El pedido ya no aparece en ninguna consulta

## Archivos Modificados

1. `models.py` - Agregado campo `is_dispatched`
2. `apply_despachado_migration.py` - Script de migración (ejecutado)
3. `crud.py` - Modificada función `get_recent_consumos()`
4. `admin.py` - Modificado endpoint `admin_mark_consumo_despachado()`

## Resultado

Ahora, cuando un administrador marca un pedido como "despachado":
- El pedido se marca en la base de datos con `is_dispatched = True`
- El pedido desaparece inmediatamente de la vista
- Al recargar la página, el pedido NO vuelve a aparecer
- El registro permanece en la base de datos para fines de auditoría e historial

Los pedidos marcados como "No Despachado" se eliminan completamente de la base de datos.
