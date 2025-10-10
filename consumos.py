from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud, schemas
from database import SessionLocal
import websocket_manager
from security import api_key_auth

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
    await websocket_manager.manager.broadcast_queue_update()
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
    await websocket_manager.manager.broadcast_queue_update()
    return db_consumo