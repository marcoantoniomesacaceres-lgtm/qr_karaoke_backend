import os
import datetime
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import List

import crud, schemas, models, config
from database import SessionLocal # get_db se importará desde aquí
import websocket_manager
from security import api_key_auth

router = APIRouter() # El prefijo y las etiquetas se pueden definir aquí o al incluir el router en main.py

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- AUTOPLAY: tarea en segundo plano ---
async def check_and_trigger_autoplay(db: Session):
    """
    Tarea en segundo plano que se ejecuta después de un tiempo.
    Verifica si el autoplay está activado y si es así, avanza la cola.
    """
    # Pequeña espera para que se completen transacciones anteriores
    await asyncio.sleep(2)

    if config.settings.AUTOPLAY_ENABLED:
        await crud.avanzar_cola_automaticamente(db)
        crud.create_admin_log_entry(
            db,
            action="AUTOPLAY_ADVANCE",
            details="Autoplay avanzó la cola a la siguiente canción."
        )

# --- ENDPOINT: Avanzar la cola manualmente ---
@router.post(
    "/siguiente",
    response_model=schemas.PlayNextResponse,
    responses={204: {"description": "No hay más canciones en la cola."}},
    summary="Avanzar la cola y obtener la siguiente canción para reproducir"
)
async def avanzar_cola(db: Session = Depends(get_db)):
    """
    Si el autoplay está desactivado, este endpoint actúa como un botón manual
    para avanzar la cola a la siguiente canción.
    """
    if config.settings.AUTOPLAY_ENABLED:
        # Si autoplay está activo, no forzamos el avance, pero devolvemos
        # la canción actual para que el frontend pueda mostrarla.
        cancion_actual = crud.get_cancion_actual(db)
        if not cancion_actual:
            return Response(status_code=204)

        youtube_url = f"https://www.youtube.com/embed/{cancion_actual.youtube_id}?autoplay=1&fs=1"
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"message": "Autoplay está activo. El avance ocurre automáticamente.",
                     "play_url": youtube_url, "cancion": jsonable_encoder(schemas.Cancion.from_orm(cancion_actual))}
        )

    # Avanzamos la cola manualmente
    nueva_cancion = await crud.avanzar_cola_automaticamente(db)

    if not nueva_cancion:
        # Si no hay más canciones
        return Response(status_code=204)

    # Construimos la URL de YouTube en modo embed
    youtube_url = f"https://www.youtube.com/embed/{nueva_cancion.youtube_id}?autoplay=1&fs=1"

    return schemas.PlayNextResponse(
        play_url=youtube_url,
        cancion=nueva_cancion
    )

# --- ENDPOINT: Añadir canción ---
@router.post(
    "/{usuario_id}",
    response_model=schemas.Cancion,
    summary="Añadir una canción a la lista de un usuario"
)
async def anadir_cancion(
    usuario_id: int,
    cancion: schemas.CancionCreate,
    db: Session = Depends(get_db)
):
    """
    Añade una nueva canción a la lista personal de un usuario, si hay tiempo disponible.
    """
    db_usuario = crud.get_usuario_by_id(db, usuario_id=usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if db_usuario.is_silenced:
        raise HTTPException(status_code=403, detail="No tienes permiso para añadir más canciones.")

    # Validar hora de cierre
    hora_cierre_str = config.settings.KARAOKE_CIERRE
    try:
        h, m = map(int, hora_cierre_str.split(':'))
        ahora = datetime.datetime.now()
        hora_cierre = ahora.replace(hour=h, minute=m, second=0, microsecond=0)
        if hora_cierre < ahora:
            hora_cierre += datetime.timedelta(days=1)
    except (ValueError, TypeError):
        raise HTTPException(status_code=500, detail="Formato de hora de cierre inválido.")

    if ahora >= hora_cierre:
        raise HTTPException(status_code=400, detail="Ya no se aceptan más canciones por hoy.")

    # Verificar duración proyectada
    tiempo_restante_segundos = (hora_cierre - ahora).total_seconds()
    duracion_cola_actual = crud.get_duracion_total_cola_aprobada(db)
    duracion_total_proyectada = duracion_cola_actual + (cancion.duracion_seconds or 0)

    if duracion_total_proyectada > tiempo_restante_segundos:
        raise HTTPException(
            status_code=400,
            detail="No hay tiempo suficiente para añadir esta canción antes del cierre."
        )

    # Verificar duplicados
    cancion_existente = crud.check_if_song_in_user_list(db, usuario_id=usuario_id, youtube_id=cancion.youtube_id)
    if cancion_existente:
        raise HTTPException(
            status_code=409,
            detail=f"Ya tienes '{cancion.titulo}' en tu lista."
        )

    # Crear y aprobar canción
    db_cancion = crud.create_cancion_para_usuario(db=db, cancion=cancion, usuario_id=usuario_id)
    cancion_aprobada = crud.update_cancion_estado(db, cancion_id=db_cancion.id, nuevo_estado="aprobado")

    # Si autoplay está activo, iniciar reproducción si la cola estaba vacía
    await crud.start_next_song_if_autoplay_and_idle(db)
    await websocket_manager.manager.broadcast_queue_update()

    return cancion_aprobada

@router.get("/{usuario_id}/lista", response_model=List[schemas.Cancion], summary="Ver la lista de canciones de un usuario")
def ver_lista_de_canciones(usuario_id: int, db: Session = Depends(get_db)):
    return crud.get_canciones_por_usuario(db=db, usuario_id=usuario_id)

@router.get("/pendientes", response_model=List[schemas.CancionAdminView], summary="Ver todas las canciones pendientes")
def ver_canciones_pendientes(db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    return crud.get_canciones_pendientes(db=db)

@router.post("/{cancion_id}/aprobar", response_model=schemas.Cancion, summary="Aprobar una canción")
async def aprobar_cancion(cancion_id: int, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    db_cancion = crud.update_cancion_estado(db, cancion_id=cancion_id, nuevo_estado="aprobado")
    if not db_cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    crud.create_admin_log_entry(db, action="APPROVE_SONG", details=f"Canción '{db_cancion.titulo}' aprobada.")
    await crud.start_next_song_if_autoplay_and_idle(db)
    await websocket_manager.manager.broadcast_queue_update()
    return db_cancion

@router.post("/{cancion_id}/rechazar", response_model=schemas.Cancion, summary="Rechazar una canción")
async def rechazar_cancion(cancion_id: int, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    db_cancion = crud.update_cancion_estado(db, cancion_id=cancion_id, nuevo_estado="rechazada")
    if not db_cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    crud.create_admin_log_entry(db, action="REJECT_SONG", details=f"Canción '{db_cancion.titulo}' rechazada.")
    await websocket_manager.manager.broadcast_queue_update()
    return db_cancion

@router.post("/admin/add", response_model=schemas.Cancion, summary="[Admin] Añadir una canción como DJ")
async def admin_anadir_cancion(cancion: schemas.CancionCreate, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    dj_user = crud.get_or_create_dj_user(db)
    db_cancion = crud.create_cancion_para_usuario(db=db, cancion=cancion, usuario_id=dj_user.id)
    # La canción se aprueba automáticamente
    cancion_aprobada = crud.update_cancion_estado(db, cancion_id=db_cancion.id, nuevo_estado="aprobado")
    
    # Si el autoplay está activo, intentamos iniciar la reproducción si la cola estaba vacía
    await crud.start_next_song_if_autoplay_and_idle(db)
    await websocket_manager.manager.broadcast_queue_update()
    return cancion_aprobada

@router.get("/cola", response_model=schemas.ColaView, summary="Ver la cola de canciones")
def ver_cola_de_canciones(db: Session = Depends(get_db)):
    cola_data = crud.get_cola_completa(db)
    return schemas.ColaView(now_playing=cola_data["now_playing"], upcoming=cola_data["upcoming"])

@router.get("/{cancion_id}/tiempo-espera", response_model=dict, summary="Calcular tiempo de espera")
def calcular_tiempo_espera(cancion_id: int, db: Session = Depends(get_db)):
    tiempo_segundos = crud.get_tiempo_espera_para_cancion(db, cancion_id=cancion_id)
    if tiempo_segundos == -1:
        raise HTTPException(status_code=404, detail="La canción no está en la cola.")
    return {"tiempo_espera_segundos": tiempo_segundos}

@router.delete("/{cancion_id}", status_code=204, summary="Eliminar una canción de la lista personal")
async def eliminar_cancion(cancion_id: int, usuario_id: int, db: Session = Depends(get_db)):
    """
    [Usuario] Elimina una canción de su propia lista.
    Solo se puede eliminar si la canción pertenece al usuario y está en estado 'pendiente'.
    """
    db_cancion = db.query(models.Cancion).filter(models.Cancion.id == cancion_id, models.Cancion.usuario_id == usuario_id).first()

    if not db_cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada o no te pertenece.")
    if db_cancion.estado != 'pendiente':
        raise HTTPException(status_code=400, detail="No se puede eliminar una canción que ya ha sido procesada.")

    crud.delete_cancion(db, cancion_id=cancion_id)
    await websocket_manager.manager.broadcast_queue_update() # Notificar por si estaba en la cola de pendientes
    return Response(status_code=204) 