import os
import datetime
from fastapi import APIRouter, Depends, HTTPException, Response, Body
from sqlalchemy.orm import Session
from typing import List

import crud, schemas, models, config
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

@router.post("/{usuario_id}", response_model=schemas.Cancion, summary="Añadir una canción a la lista de un usuario")
async def anadir_cancion(
    usuario_id: int, cancion: schemas.CancionCreate, db: Session = Depends(get_db) # Convertido a async
):
    """
    Añade una nueva canción a la lista personal de un usuario, si hay tiempo.
    La canción se crea en estado 'pendiente' y verifica si hay tiempo suficiente antes de la hora de cierre.
    """
    # 0. Verificar si el usuario está silenciado
    db_usuario = crud.get_usuario_by_id(db, usuario_id=usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if db_usuario.is_silenced:
        raise HTTPException(status_code=403, detail="No tienes permiso para añadir más canciones.")

    # 1. Obtener la hora de cierre (configurable)
    hora_cierre_str = config.settings.KARAOKE_CIERRE
    try:
        h, m = map(int, hora_cierre_str.split(':'))
        ahora = datetime.datetime.now()
        hora_cierre = ahora.replace(hour=h, minute=m, second=0, microsecond=0)

        # --- INICIO DE LA CORRECCIÓN ---
        # Si la hora de cierre calculada es anterior a la hora actual,
        # significa que el cierre es al día siguiente.
        if hora_cierre < ahora:
            hora_cierre += datetime.timedelta(days=1)
        # --- FIN DE LA CORRECCIÓN ---
    except (ValueError, TypeError):
        raise HTTPException(status_code=500, detail="Formato de hora de cierre inválido en la configuración.")

    # 2. Si ya pasó la hora de cierre, no se aceptan más canciones.
    if ahora >= hora_cierre:
        raise HTTPException(status_code=400, detail="Lo sentimos, ya no se aceptan más canciones por hoy.")

    # 3. Calcular el tiempo restante hasta el cierre
    tiempo_restante_segundos = (hora_cierre - ahora).total_seconds()

    # 4. Calcular la duración actual de la cola + la nueva canción
    duracion_cola_actual = crud.get_duracion_total_cola_aprobada(db)
    duracion_total_proyectada = duracion_cola_actual + (cancion.duracion_seconds or 0)

    # 5. Comparar y decidir
    if duracion_total_proyectada > tiempo_restante_segundos:
        raise HTTPException(
            status_code=400,
            detail="No hay tiempo suficiente para añadir esta canción antes del cierre. Intenta con una más corta."
        )

    # 6. Verificar si la canción ya está en la lista del usuario
    cancion_existente = crud.check_if_song_in_user_list(db, usuario_id=usuario_id, youtube_id=cancion.youtube_id)
    if cancion_existente:
        raise HTTPException(
            status_code=409,  # 409 Conflict
            detail=f"Ya tienes '{cancion.titulo}' en tu lista de espera."
        )

    # 7. Crear la canción (aún en estado 'pendiente' por defecto)
    db_cancion = crud.create_cancion_para_usuario(db=db, cancion=cancion, usuario_id=usuario_id)
    
    # 8. Aprobarla inmediatamente y notificar a los clientes para que la cola se actualice
    cancion_aprobada = crud.update_cancion_estado(db, cancion_id=db_cancion.id, nuevo_estado="aprobado")
    await websocket_manager.manager.broadcast_queue_update()
    return cancion_aprobada

@router.get("/{usuario_id}/lista", response_model=List[schemas.Cancion], summary="Ver la lista de canciones de un usuario")
def ver_lista_de_canciones(usuario_id: int, db: Session = Depends(get_db)):
    """
    Devuelve todas las canciones que un usuario ha añadido a su lista.
    """
    return crud.get_canciones_por_usuario(db=db, usuario_id=usuario_id)

@router.get("/pendientes", response_model=List[schemas.CancionAdminView], summary="Ver todas las canciones pendientes de aprobación")
def ver_canciones_pendientes(db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    """
    **[Admin]** Devuelve una lista de todas las canciones que están en estado 'pendiente',
    incluyendo la información del usuario que la solicitó.
    """
    return crud.get_canciones_pendientes(db=db)

@router.post("/{cancion_id}/aprobar", response_model=schemas.Cancion, summary="Aprobar una canción")
async def aprobar_cancion(cancion_id: int, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    """
    **[Admin]** Cambia el estado de una canción a 'aprobado'.
    Una vez aprobada, la canción entra en la cola para ser reproducida.
    """
    db_cancion = crud.update_cancion_estado(db, cancion_id=cancion_id, nuevo_estado="aprobado")
    if not db_cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    crud.create_admin_log_entry(db, action="APPROVE_SONG", details=f"Canción '{db_cancion.titulo}' (ID: {cancion_id}) aprobada.")
    await websocket_manager.manager.broadcast_queue_update()
    return db_cancion

@router.post("/{cancion_id}/rechazar", response_model=schemas.Cancion, summary="Rechazar una canción")
async def rechazar_cancion(cancion_id: int, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    """
    **[Admin]** Cambia el estado de una canción a 'rechazada'.
    La canción no será reproducida.
    """
    db_cancion = crud.update_cancion_estado(db, cancion_id=cancion_id, nuevo_estado="rechazada")
    if not db_cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    crud.create_admin_log_entry(db, action="REJECT_SONG", details=f"Canción '{db_cancion.titulo}' (ID: {cancion_id}) rechazada.")
    # También notificamos al rechazar, para que desaparezca de la lista de pendientes en el admin
    await websocket_manager.manager.broadcast_queue_update()
    return db_cancion

@router.post("/admin/add", response_model=schemas.Cancion, summary="[Admin] Añadir una canción como DJ")
async def admin_anadir_cancion(
    cancion: schemas.CancionCreate, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)
):
    """
    **[Admin]** Añade una canción directamente a la cola de aprobados.
    La canción se asigna al usuario especial 'DJ'.
    """
    # 1. Obtener o crear el usuario 'DJ'
    dj_user = crud.get_or_create_dj_user(db)

    # 2. Crear y aprobar la canción inmediatamente
    db_cancion = crud.create_cancion_para_usuario(db=db, cancion=cancion, usuario_id=dj_user.id)
    cancion_aprobada = crud.update_cancion_estado(db, cancion_id=db_cancion.id, nuevo_estado="aprobado")

    # 3. Notificar a todos los clientes
    await websocket_manager.manager.broadcast_queue_update()
    return cancion_aprobada

@router.get("/cola", response_model=schemas.ColaView, summary="Ver la cola de canciones (público y admin)")
def ver_cola_de_canciones(db: Session = Depends(get_db)):
    """
    Devuelve la canción que está sonando y la lista de las próximas.
    """
    cola_data = crud.get_cola_completa(db)
    return schemas.ColaView(now_playing=cola_data["now_playing"], upcoming=cola_data["upcoming"])

@router.post("/siguiente",
             response_model=schemas.PlayNextResponse,
             responses={204: {"description": "No hay más canciones en la cola."}},
             summary="Avanzar la cola y obtener la siguiente canción para reproducir")
async def avanzar_cola(db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    """
    **[Admin/Player]** Orquesta el avance de la cola:
    1. Marca la canción actual ('reproduciendo') como 'cantada'.
    2. Marca la siguiente canción de la cola ('aprobado') como 'reproduciendo'.
    3. Notifica a todos los clientes de la nueva cola.
    """
    # Primero, marcamos la que terminó como 'cantada'
    cancion_cantada = crud.marcar_cancion_actual_como_cantada(db)
    
    # Si una canción fue marcada como cantada, notificamos su puntaje
    if cancion_cantada:
        await websocket_manager.manager.broadcast_song_finished(cancion_cantada)

    # Luego, marcamos la siguiente en la cola como 'reproduciendo'
    nueva_cancion_reproduciendo = crud.marcar_siguiente_como_reproduciendo(db)

    # Notificamos a todos los clientes (móviles, dashboard) que la cola ha cambiado
    await websocket_manager.manager.broadcast_queue_update()

    if not nueva_cancion_reproduciendo:
        # Si no hay más canciones, podemos devolver la última que se cantó o un mensaje.
        return Response(status_code=204)

    # Notificamos al reproductor para que reproduzca la canción
    await websocket_manager.manager.broadcast_play_song(nueva_cancion_reproduciendo.youtube_id)

    # Construimos la URL de YouTube en modo embed para pantalla completa
    youtube_url = f"https://www.youtube.com/embed/{nueva_cancion_reproduciendo.youtube_id}?autoplay=1&fs=1"

    return schemas.PlayNextResponse(
        play_url=youtube_url,
        cancion=nueva_cancion_reproduciendo
    )

@router.get("/{cancion_id}/tiempo-espera", response_model=dict, summary="Calcular tiempo de espera para una canción")
def calcular_tiempo_espera(cancion_id: int, db: Session = Depends(get_db)):
    """
    Devuelve el tiempo estimado en segundos que falta para que una canción específica
    sea reproducida.
    """
    tiempo_segundos = crud.get_tiempo_espera_para_cancion(db, cancion_id=cancion_id)
    if tiempo_segundos == -1:
        raise HTTPException(status_code=404, detail="La canción no está en la cola de espera.")
    
    return {"tiempo_espera_segundos": tiempo_segundos}

@router.delete("/{cancion_id}", status_code=204, summary="Eliminar una canción de la lista personal")
def eliminar_cancion(cancion_id: int, usuario_id: int, db: Session = Depends(get_db)):
    """
    Permite a un usuario eliminar una canción que ha añadido, siempre y
    cuando la canción siga en estado 'pendiente'.
    """
    db_cancion = crud.get_cancion_by_id(db, cancion_id=cancion_id)

    if not db_cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada")

    if db_cancion.usuario_id != usuario_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta canción")

    if db_cancion.estado != 'pendiente':
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar la canción porque ya ha sido procesada por un administrador"
        )

    crud.delete_cancion(db, cancion_id=cancion_id)
    return Response(status_code=204)