from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import crud, schemas
from database import SessionLocal
import websocket_manager
from security import api_key_auth
import asyncio
import datetime

router = APIRouter()

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{usuario_id}", response_model=schemas.Consumo, summary="Registrar un consumo para un usuario")
async def registrar_consumo(
    usuario_id: int, consumo: schemas.ConsumoCreate, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)
):
    """
    **[Admin/Staff]** Añade un producto al registro de consumo de un usuario.
    Esto afectará directamente la prioridad del usuario en la cola de canciones.
    """
    db_consumo, error_detail = crud.create_consumo_para_usuario(db=db, consumo=consumo, usuario_id=usuario_id)
    if error_detail:
        raise HTTPException(status_code=400, detail=error_detail)
    # Notificamos la actualización de la cola
    asyncio.create_task(websocket_manager.manager.broadcast_queue_update())

    # También programamos una notificación específica de "consumo creado" en background.
    try:
        mesa_nombre = None
        if db_consumo.usuario and db_consumo.usuario.mesa:
            mesa_nombre = db_consumo.usuario.mesa.nombre

        consumo_payload = {
            'id': db_consumo.id,
            'cantidad': db_consumo.cantidad,
            'valor_total': float(db_consumo.valor_total),
            'producto_nombre': db_consumo.producto.nombre if db_consumo.producto else None,
            'usuario_nick': db_consumo.usuario.nick if db_consumo.usuario else None,
            'mesa_nombre': mesa_nombre,
            'created_at': db_consumo.created_at.isoformat()
        }
        # Fire-and-forget the notification to avoid affecting the HTTP response
        asyncio.create_task(websocket_manager.manager.broadcast_consumo_created(consumo_payload))
    except Exception:
        # Nunca permitir que la notificación rompa la respuesta principal
        pass
    return db_consumo

@router.post("/pedir/{usuario_id}", response_model=schemas.Consumo, summary="Un usuario pide un producto para sí mismo")
async def usuario_pide_producto(
    usuario_id: int, consumo: schemas.ConsumoCreate, db: Session = Depends(get_db)
):
    """
    **[Público]** Permite que un usuario registrado en una mesa pida un producto.
    No requiere clave de API de administrador.
    """
    # La lógica es la misma que para el admin, solo que sin la autenticación de admin
    db_consumo, error_detail = crud.create_consumo_para_usuario(db=db, consumo=consumo, usuario_id=usuario_id)
    if error_detail:
        raise HTTPException(status_code=400, detail=error_detail)
    # Notificamos a todos para que la cola se actualice (por si cambia la prioridad)
    asyncio.create_task(websocket_manager.manager.broadcast_queue_update())

    # Notificamos en background que se creó un consumo (para la UI del admin)
    try:
        mesa_nombre = None
        if db_consumo.usuario and db_consumo.usuario.mesa:
            mesa_nombre = db_consumo.usuario.mesa.nombre

        consumo_payload = {
            'id': db_consumo.id,
            'cantidad': db_consumo.cantidad,
            'valor_total': float(db_consumo.valor_total),
            'producto_nombre': db_consumo.producto.nombre if db_consumo.producto else None,
            'usuario_nick': db_consumo.usuario.nick if db_consumo.usuario else None,
            'mesa_nombre': mesa_nombre,
            'created_at': db_consumo.created_at.isoformat()
        }
        asyncio.create_task(websocket_manager.manager.broadcast_consumo_created(consumo_payload))
    except Exception:
        pass
    return db_consumo

@router.post("/pedir/carrito/{usuario_id}", response_model=List[schemas.Consumo], summary="Un usuario pide un carrito de compras completo")
async def usuario_pide_carrito(
    usuario_id: int, carrito: schemas.CarritoCreate, db: Session = Depends(get_db)
):
    """
    **[Público]** Permite que un usuario envíe un pedido consolidado (carrito).
    Si algún producto falla (stock, etc.), todo el pedido es rechazado.
    """
    if not carrito.items:
        raise HTTPException(status_code=400, detail="El carrito no puede estar vacío.")

    # La nueva función crud maneja la transacción completa
    consumos_creados, error_detail = crud.create_pedido_from_carrito(db=db, carrito=carrito, usuario_id=usuario_id)

    if error_detail:
        raise HTTPException(status_code=400, detail=error_detail)

    # Notificamos a todos para que la cola se actualice (por si cambia la prioridad)
    asyncio.create_task(websocket_manager.manager.broadcast_queue_update())

    # Notificamos al admin sobre el NUEVO PEDIDO CONSOLIDADO
    try:
        # Reutilizamos el payload de consumo_created, pero ahora lo llenamos con los detalles del pedido completo
        # En una futura mejora, podríamos crear un tipo de evento 'pedido_created'
        for db_consumo in consumos_creados:
             consumo_payload = websocket_manager.create_consumo_payload(db_consumo)
             asyncio.create_task(websocket_manager.manager.broadcast_consumo_created(consumo_payload))
    except Exception:
        pass # No dejar que la notificación rompa la respuesta

    return consumos_creados