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

# --- ENDPOINT: Avanzar la cola manualmente ---
@router.post(
    "/siguiente",
    response_model=schemas.PlayNextResponse,
    responses={204: {"description": "No hay más canciones en la cola."}},
    summary="Avanzar la cola y obtener la siguiente canción para reproducir"
)
async def avanzar_cola(db: Session = Depends(get_db)):
    """
    Avanza la cola a la siguiente canción.
    """
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
        from timezone_utils import now_bogota
        ahora = now_bogota()
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

    # Verificar duplicados a nivel de mesa (evita que usuarios de la misma mesa agreguen la misma canción)
    cancion_existente = crud.check_if_song_in_user_list(db, usuario_id=usuario_id, youtube_id=cancion.youtube_id)
    if cancion_existente:
        raise HTTPException(
            status_code=409,
            detail=f"Esta canción ya está en la cola de tu mesa. '{cancion.titulo}' fue agregada por otro usuario de tu mesa."
        )

    # Crear canción
    db_cancion = crud.create_cancion_para_usuario(db=db, cancion=cancion, usuario_id=usuario_id)
    
    # LAZY APPROVAL: Solo aprobar si no hay más de 1 canción aprobada en espera
    # Si ya hay 1 o más canciones aprobadas (más la que suena), la nueva va a pendiente_lazy
    approved_count = db.query(models.Cancion).filter(models.Cancion.estado == "aprobado").count()
    
    if approved_count >= 1:
        # Ya hay una canción aprobada esperando, poner en cola lazy
        cancion_final = crud.update_cancion_estado(db, cancion_id=db_cancion.id, nuevo_estado="pendiente_lazy")
    else:
        # Primera canción, aprobar inmediatamente
        cancion_final = crud.update_cancion_estado(db, cancion_id=db_cancion.id, nuevo_estado="aprobado")
        # Si autoplay está activo, iniciar reproducción si la cola estaba vacía
        await crud.start_next_song_if_autoplay_and_idle(db)
    
    await websocket_manager.manager.broadcast_queue_update()

    return cancion_final

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
    db_cancion = db.query(models.Cancion).filter(models.Cancion.id == cancion_id).first()
    
    if not db_cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    
    # Validar que la canción no haya sido aprobada
    if db_cancion.estado == 'aprobado' or db_cancion.approved_at is not None:
        raise HTTPException(status_code=403, detail="No se puede eliminar: la canción ya fue aprobada por el sistema")
    
    # Solo se pueden rechazar canciones en estado 'pendiente' o 'pendiente_lazy'
    if db_cancion.estado not in ['pendiente', 'pendiente_lazy']:
        raise HTTPException(status_code=403, detail="Solo se pueden eliminar canciones pendientes o en cola lazy")
    
    db_cancion = crud.update_cancion_estado(db, cancion_id=cancion_id, nuevo_estado="rechazada")
    crud.create_admin_log_entry(db, action="REJECT_SONG", details=f"Canción '{db_cancion.titulo}' rechazada.")
    await websocket_manager.manager.broadcast_queue_update()
    return db_cancion

@router.post("/admin/add", response_model=schemas.Cancion, summary="[Admin] Añadir una canción como DJ")
async def admin_anadir_cancion(cancion: schemas.CancionCreate, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    dj_user = crud.get_or_create_dj_user(db)
    db_cancion = crud.create_cancion_para_usuario(db=db, cancion=cancion, usuario_id=dj_user.id)
    
    # LAZY APPROVAL: Solo aprobar si no hay nada en la cola
    hay_cancion_activa = db.query(models.Cancion).filter(
        models.Cancion.estado.in_(["reproduciendo", "aprobado"])
    ).first()
    
    if hay_cancion_activa:
        cancion_final = crud.update_cancion_estado(db, cancion_id=db_cancion.id, nuevo_estado="pendiente_lazy")
    else:
        cancion_final = crud.update_cancion_estado(db, cancion_id=db_cancion.id, nuevo_estado="aprobado")
        await crud.start_next_song_if_autoplay_and_idle(db)
    
    await websocket_manager.manager.broadcast_queue_update()
    return cancion_final


@router.get("/cola", response_model=schemas.ColaView, summary="Ver la cola de canciones")
def ver_cola_de_canciones(db: Session = Depends(get_db)):
    cola_data = crud.get_cola_completa(db)
    return schemas.ColaView(now_playing=cola_data["now_playing"], upcoming=cola_data["upcoming"])

@router.get("/cola/extended", response_model=schemas.ColaViewExtended, summary="Ver la cola de canciones con lazy queue")
def ver_cola_extendida(db: Session = Depends(get_db)):
    """
    Retorna la cola completa incluyendo:
    - now_playing: Canción actual
    - upcoming: Siguiente canción aprobada (máximo 1)
    - lazy_queue: Canciones en espera de aprobación lazy
    - pending: Canciones pendientes de aprobación manual
    """
    cola_data = crud.get_cola_completa_con_lazy(db)
    return schemas.ColaViewExtended(
        now_playing=cola_data["now_playing"],
        upcoming=cola_data["upcoming"],
        lazy_queue=cola_data["lazy_queue"],
        pending=cola_data["pending"]
    )


@router.get("/{cancion_id}/tiempo-espera", response_model=dict, summary="Calcular tiempo de espera")
def calcular_tiempo_espera(cancion_id: int, db: Session = Depends(get_db)):
    tiempo_segundos = crud.get_tiempo_espera_para_cancion(db, cancion_id=cancion_id)
    if tiempo_segundos == -1:
        raise HTTPException(status_code=404, detail="La canción no está en la cola.")
    return {"tiempo_espera_segundos": tiempo_segundos}

@router.post("/{cancion_id}/play", status_code=200, summary="Reproducir una canción en el player")
async def play_song_now(cancion_id: int, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    """
    **[Admin]** Envía la orden de reproducir una canción específica en el player.
    """
    db_cancion = db.query(models.Cancion).filter(models.Cancion.id == cancion_id).first()
    if not db_cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada.")

    # Marcar la canción seleccionada como 'reproduciendo' en la base de datos
    # y actualizar el estado de la canción previamente en reproducción si existe.
    from timezone_utils import now_bogota

    # Marcar la canción que estaba reproduciéndose como 'cantada' (si aplica)
    current_playing = db.query(models.Cancion).filter(models.Cancion.estado == 'reproduciendo').first()
    if current_playing and current_playing.id != db_cancion.id:
        current_playing.estado = 'cantada'
        current_playing.finished_at = now_bogota()

    # Marcar la nueva canción como reproduciendo
    db_cancion.estado = 'reproduciendo'
    db_cancion.started_at = now_bogota()
    db.commit()
    db.refresh(db_cancion)

    # Notificar a los clientes que la cola cambió y pedir al player que reproduzca
    await websocket_manager.manager.broadcast_queue_update()
    await websocket_manager.manager.broadcast_play_song(
        youtube_id=db_cancion.youtube_id,
        duration_seconds=db_cancion.duracion_seconds or 0
    )

    # Registrar la acción en logs de admin
    try:
        import crud as _crud
        _crud.create_admin_log_entry(db, action="PLAY_SONG", details=f"Reproduciendo manualmente: {db_cancion.titulo}")
    except Exception:
        pass

    return {"mensaje": f"Reproduciendo: {db_cancion.titulo}"}

@router.delete("/{cancion_id}", status_code=204, summary="Eliminar una canción de la lista personal")
async def eliminar_cancion(cancion_id: int, usuario_id: int, db: Session = Depends(get_db)):
    """
    [Usuario] Elimina una canción de su propia lista.
    Solo se puede eliminar si la canción pertenece al usuario y está en estado 'pendiente' o 'aprobado'.
    No se puede eliminar si ya está 'reproduciendo' o 'cantada'.
    """
    db_cancion = db.query(models.Cancion).filter(models.Cancion.id == cancion_id, models.Cancion.usuario_id == usuario_id).first()

    if not db_cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada o no te pertenece.")
    if db_cancion.estado not in ['pendiente', 'aprobado', 'pendiente_lazy']:
        raise HTTPException(status_code=400, detail="No se puede eliminar una canción que ya está reproduciendo o ha sido cantada.")

    crud.delete_cancion(db, cancion_id=cancion_id)
    await websocket_manager.manager.broadcast_queue_update() # Notificar actualización de la cola
    return Response(status_code=204)