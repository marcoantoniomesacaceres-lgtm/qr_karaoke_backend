from fastapi import APIRouter, Depends, Response, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import models 
import crud, schemas
import config
from database import SessionLocal
import websocket_manager
from security import api_key_auth, MASTER_API_KEY

router = APIRouter(dependencies=[Depends(api_key_auth)])

# Creamos un nuevo router para las rutas públicas que no necesitan clave de API
public_router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Auth Endpoints (Logging In) ---
@public_router.post("/auth/login", response_model=schemas.AdminLoginResponse, summary="Iniciar sesión como administrador")
def admin_login(login_data: schemas.AdminLoginRequest, db: Session = Depends(get_db)):
    """
    Verifica la clave de API y registra el inicio de sesión.
    """
    key = login_data.api_key.strip()
    
    # 1. Verificar Clave Maestra
    if key == MASTER_API_KEY:
        crud.create_admin_log_entry(db, action="LOGIN", details="Inicio de sesión con SUPER CLAVE MAESTRA.")
        return {"success": True, "description": "Super Admin", "token": key}

    # 2. Verificar Clave de Base de Datos
    db_key = crud.get_admin_api_key(db, key=key)
    if db_key:
        crud.create_admin_log_entry(db, action="LOGIN", details=f"Inicio de sesión: {db_key.description}")
        # Opcional: actualizar last_used
        db_key.last_used = crud.now_bogota()
        db.commit()
        return {"success": True, "description": db_key.description, "token": key}
    
    create_admin_log_error(db, "LOGIN_FAILED", "Intento de login fallido con clave incorrecta.")
    raise HTTPException(status_code=403, detail="Clave de API inválida.")

def create_admin_log_error(db: Session, action: str, details: str):
    """Helper local para loguear errores sin exponer crud si no es necesario"""
    try:
        crud.create_admin_log_entry(db, action=action, details=details)
    except:
        pass

# --- Rutas Públicas (para usuarios en mesas) ---


@public_router.get("/consumos/mis-pedidos/{usuario_id}", response_model=List[schemas.ConsumoHistorial], summary="Obtener los pedidos de un usuario", tags=["Usuarios"])
def get_mis_pedidos(usuario_id: int, db: Session = Depends(get_db)):
    """
    **[Usuario]** Devuelve el historial de consumos (pedidos) de un usuario específico.
    """
    # Reutilizamos la función existente en crud.py
    consumos = crud.get_consumos_por_usuario(db, usuario_id=usuario_id)
    return consumos

@public_router.get("/mi-cuenta/{usuario_id}", response_model=schemas.MesaEstadoPago, summary="Obtener el estado de cuenta de mi mesa", tags=["Usuarios", "Cuentas"])
def get_my_table_account_status_public(usuario_id: int, db: Session = Depends(get_db)):
    """
    **[Usuario]** Devuelve el estado de cuenta completo de la mesa a la que
    pertenece el usuario, incluyendo consumos, pagos y saldo.
    """
    db_usuario = crud.get_usuario_by_id(db, usuario_id=usuario_id)
    if not db_usuario or not db_usuario.mesa_id:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o no está en una mesa.")

    status = crud.get_table_payment_status(db, mesa_id=db_usuario.mesa_id)
    if not status:
        raise HTTPException(status_code=404, detail="No se pudo obtener el estado de la mesa.")
    return status



# --- Rutas de Administrador (protegidas por API Key) ---

@router.post("/reset-night", status_code=204, summary="Reiniciar el sistema para una nueva noche")
async def reset_night(db: Session = Depends(get_db)):
    """
    **[Admin - ¡ACCIÓN DESTRUCTIVA!]** Borra todos los datos de la noche:
    mesas, usuarios, canciones y consumos.
    Útil para empezar de cero al día siguiente.
    """
    crud.reset_database_for_new_night(db)
    crud.create_admin_log_entry(db, action="RESET_NIGHT", details="El sistema ha sido reiniciado para una nueva noche.")
    # Después de borrar todo, notificamos a los clientes para que la cola se vacíe
    await websocket_manager.manager.broadcast_queue_update()
    return Response(status_code=204)

@router.post("/set-closing-time", status_code=200, summary="Establecer la hora de cierre")
def set_closing_time(closing_time: schemas.ClosingTimeUpdate, db: Session = Depends(get_db)):
    """
    **[Admin]** Actualiza la hora de cierre del karaoke en tiempo real.
    El formato debe ser "HH:MM".
    """
    # Aquí se podría añadir una validación del formato de la hora
    config.settings.KARAOKE_CIERRE = closing_time.hora_cierre # Actualiza la hora de cierre en la configuración
    crud.create_admin_log_entry(db, action="SET_CLOSING_TIME", details=f"Hora de cierre actualizada a {config.settings.KARAOKE_CIERRE}")
    return {"mensaje": f"La hora de cierre ha sido actualizada a {config.settings.KARAOKE_CIERRE}"}

@router.get("/get-closing-time", response_model=schemas.ClosingTimeUpdate, summary="Obtener la hora de cierre actual")
def get_closing_time(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve la hora de cierre del karaoke actualmente configurada.
    """
    return schemas.ClosingTimeUpdate(hora_cierre=config.settings.KARAOKE_CIERRE)



@router.post("/broadcast-message", status_code=202, summary="Enviar mensaje global a todos los usuarios")
async def broadcast_message(notificacion: schemas.Notificacion, db: Session = Depends(get_db)):
    """
    **[Admin]** Envía un mensaje de notificación global a todas las pantallas conectadas
    (usuarios y reproductor) mediante WebSocket.
    """
    import asyncio
    # Enviamos la notificación en segundo plano
    asyncio.create_task(
        websocket_manager.manager.broadcast_notification(notificacion.mensaje)
    )
    crud.create_admin_log_entry(db, action="BROADCAST_MESSAGE", details=f"Mensaje enviado: '{notificacion.mensaje}'")
    return {"message": "Mensaje enviado a todos los usuarios."}


@router.get("/reports/top-songs", response_model=List[schemas.CancionMasCantada], summary="Obtener las canciones más cantadas")
def get_top_songs_report(db: Session = Depends(get_db), limit: int = 10):
    """
    **[Admin]** Devuelve un reporte de las canciones más cantadas de la noche,
    ordenadas por popularidad.
    """
    top_songs_data = crud.get_canciones_mas_cantadas(db, limit=limit)
    
    # Mapeamos el resultado de la consulta al schema de respuesta
    report = [
        schemas.CancionMasCantada(
            titulo=titulo,
            youtube_id=youtube_id,
            veces_cantada=veces_cantada
        )
        for titulo, youtube_id, veces_cantada in top_songs_data
    ]
    
    return report

@router.get("/reports/top-products", response_model=List[schemas.ProductoMasConsumido], summary="Obtener los productos más consumidos")
def get_top_products_report(db: Session = Depends(get_db), limit: int = 10):
    """
    **[Admin]** Devuelve un reporte de los productos más consumidos de la noche,
    ordenados por la cantidad total vendida.
    """
    top_products_data = crud.get_productos_mas_consumidos(db, limit=limit)
    
    report = [
        schemas.ProductoMasConsumido(
            nombre=nombre,
            cantidad_total=cantidad_total
        )
        for nombre, cantidad_total in top_products_data
    ]
    
    return report

@router.get("/reports/average-wait-time", response_model=schemas.ReporteTiempoEsperaPromedio, summary="Obtener tiempo de espera promedio de canciones")
def get_average_wait_time_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve el tiempo promedio en segundos que tarda una canción
    desde que es añadida por un usuario hasta que es marcada como 'cantada'.
    """
    avg_wait_time = crud.get_tiempo_promedio_espera(db)
    return schemas.ReporteTiempoEsperaPromedio(tiempo_espera_promedio_segundos=int(avg_wait_time))

@router.post("/unban-nick", status_code=200, summary="Perdonar un nick baneado")
def unban_user_nick(unban_data: schemas.NickUnban, db: Session = Depends(get_db)):
    """
    **[Admin]** Elimina un nick de la lista de baneados, permitiendo que
    un usuario pueda volver a registrarse con él.
    """
    unbanned_nick = crud.unban_nick(db, nick=unban_data.nick)
    if not unbanned_nick:
        raise HTTPException(
            status_code=404, detail=f"El nick '{unban_data.nick}' no se encontraba en la lista de baneados."
        )
    crud.create_admin_log_entry(db, action="UNBAN_NICK", details=f"Nick '{unban_data.nick}' perdonado.")
    return {"mensaje": f"El nick '{unban_data.nick}' ha sido perdonado y puede volver a registrarse."}

@router.get("/banned-nicks", response_model=List[schemas.BannedNickView], summary="Ver la lista de nicks baneados")
def get_banned_nicks_list(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve una lista de todos los nicks que han sido baneados.
    """
    return crud.get_banned_nicks(db)

@router.get("/reports/hourly-activity", response_model=List[schemas.ReporteActividadPorHora], summary="Obtener actividad por hora")
def get_hourly_activity_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un reporte de las horas del día con más canciones cantadas,
    ordenado de mayor a menor actividad.
    """
    activity_data = crud.get_actividad_por_hora(db)
    
    report = [
        schemas.ReporteActividadPorHora(
            hora=int(hora),
            canciones_cantadas=count
        )
        for hora, count in activity_data
    ]
    
    return report

@router.delete("/tables/{mesa_id}", status_code=204, summary="Eliminar una mesa")
def delete_table(mesa_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Elimina una mesa del sistema.
    Solo se puede eliminar si no tiene usuarios conectados.
    """
    db_mesa = crud.get_mesa_by_id(db, mesa_id=mesa_id)
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada.")

    if db_mesa.usuarios:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar la mesa porque tiene usuarios conectados."
        )

    crud.delete_mesa(db, mesa_id=mesa_id)
    crud.create_admin_log_entry(db, action="DELETE_TABLE", details=f"Mesa '{db_mesa.nombre}' (ID: {mesa_id}) eliminada.")
    return Response(status_code=204)

@router.post("/tables/{mesa_id}/activate", response_model=schemas.Mesa, summary="Activar una mesa")
def activate_table(mesa_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Activa una mesa, permitiendo que los usuarios se conecten a ella.
    """
    db_mesa = crud.set_mesa_active_status(db, mesa_id=mesa_id, is_active=True)
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada.")
    crud.create_admin_log_entry(db, action="ACTIVATE_TABLE", details=f"Mesa '{db_mesa.nombre}' (ID: {mesa_id}) activada.")
    return db_mesa

@router.post("/tables/{mesa_id}/deactivate", response_model=schemas.Mesa, summary="Desactivar una mesa")
def deactivate_table(mesa_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Desactiva una mesa, impidiendo que nuevos usuarios se conecten.
    """
    db_mesa = crud.set_mesa_active_status(db, mesa_id=mesa_id, is_active=False)
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada.")
    crud.create_admin_log_entry(db, action="DEACTIVATE_TABLE", details=f"Mesa '{db_mesa.nombre}' (ID: {mesa_id}) desactivada.")
    return db_mesa

@router.get("/reports/income-by-category", response_model=List[schemas.ReporteIngresosPorCategoria], summary="Obtener los ingresos por categoría de producto")
def get_income_by_category_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un reporte de los ingresos totales generados por cada
    categoría de producto (ej: Licores, Comidas, Snacks), ordenado de mayor a menor.
    """
    income_data = crud.get_ingresos_por_categoria(db)
    
    report = [
        schemas.ReporteIngresosPorCategoria(
            categoria=categoria,
            ingresos_totales=total
        )
        for categoria, total in income_data
    ]
    
    return report

@router.get("/reports/top-rejected-users", response_model=List[schemas.ReporteUsuarioRechazado], summary="Obtener usuarios con más canciones rechazadas")
def get_top_rejected_users_report(db: Session = Depends(get_db), limit: int = 10):
    """
    **[Admin]** Devuelve un reporte de los usuarios a los que más se les han
    rechazado canciones, ordenados de mayor a menor.
    """
    rejected_users_data = crud.get_usuarios_mas_rechazados(db, limit=limit)
    
    report = [
        schemas.ReporteUsuarioRechazado(
            nick=nick,
            canciones_rechazadas=count
        )
        for nick, count in rejected_users_data
    ]
    
    return report

@router.get("/users/{usuario_id}/song-history", response_model=List[schemas.Cancion], summary="Ver el historial de canciones de un usuario")
def get_user_song_history(usuario_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve el historial completo de canciones de un usuario,
    incluyendo pendientes, aprobadas, cantadas y rechazadas.
    """
    # La función crud ya maneja el caso de un usuario inexistente devolviendo una lista vacía.
    return crud.get_canciones_por_usuario(db, usuario_id=usuario_id)

@router.get("/reports/top-rejected-songs", response_model=List[schemas.ReporteCancionesRechazadas], summary="Obtener las canciones más rechazadas")
def get_top_rejected_songs_report(db: Session = Depends(get_db), limit: int = 10):
    """
    **[Admin]** Devuelve un reporte de las canciones que más se han rechazado,
    ordenadas por la cantidad de veces que fueron rechazadas.
    """
    rejected_songs_data = crud.get_canciones_mas_rechazadas(db, limit=limit)
    
    report = [
        schemas.ReporteCancionesRechazadas(
            titulo=titulo,
            youtube_id=youtube_id,
            veces_rechazada=veces_rechazada
        )
        for titulo, youtube_id, veces_rechazada in rejected_songs_data
    ]
    
    return report

@router.get("/reports/empty-tables", response_model=List[schemas.MesaSimple], summary="Obtener mesas sin usuarios")
def get_empty_tables_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve una lista de todas las mesas que no tienen
    ningún usuario conectado.
    """
    empty_tables = crud.get_mesas_vacias(db)
    return empty_tables

@router.delete("/users/{usuario_id}", status_code=204, summary="Eliminar un usuario de una mesa")
async def delete_user(usuario_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Elimina a un usuario del sistema, junto con todas sus
    canciones y consumos registrados.
    """
    usuario_eliminado = crud.delete_usuario(db, usuario_id=usuario_id)
    if not usuario_eliminado:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado."
        )
    
    crud.create_admin_log_entry(db, action="DELETE_USER", details=f"Usuario '{usuario_eliminado.nick}' (ID: {usuario_id}) eliminado.")
    await websocket_manager.manager.broadcast_queue_update()
    return Response(status_code=204)

@router.post("/users/{usuario_id}/ban", status_code=204, summary="Banear a un usuario")
async def ban_user(usuario_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Banea a un usuario: lo elimina del sistema y bloquea su nick
    para que no pueda volver a registrarse.
    """
    usuario_baneado = crud.ban_usuario(db, usuario_id=usuario_id)
    if not usuario_baneado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    crud.create_admin_log_entry(db, action="BAN_USER", details=f"Usuario '{usuario_baneado.nick}' (ID: {usuario_id}) baneado.")
    await websocket_manager.manager.broadcast_queue_update()
    return Response(status_code=204)

@router.get("/reports/average-income-per-table", response_model=List[schemas.ReporteIngresosPromedioPorMesa], summary="Obtener los ingresos promedio por usuario en cada mesa")
def get_average_income_per_table_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un reporte con el ingreso promedio por usuario para cada mesa,
    ordenado por el ingreso total de la mesa.
    """
    income_data = crud.get_ingresos_promedio_por_usuario_por_mesa(db)
    
    report = [schemas.ReporteIngresosPromedioPorMesa(mesa_nombre=nombre, ingresos_promedio_por_usuario=promedio) for nombre, promedio in income_data]
    
    return report

@router.get("/reports/songs-by-table", response_model=List[schemas.ReporteCancionesPorMesa], summary="Obtener cantidad de canciones por mesa")
def get_songs_by_table_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un reporte de cuántas canciones se han cantado en cada mesa,
    ordenado de mayor a menor.
    """
    songs_data = crud.get_canciones_cantadas_por_mesa(db)
    
    report = [
        schemas.ReporteCancionesPorMesa(
            mesa_nombre=nombre,
            canciones_cantadas=count
        )
        for nombre, count in songs_data
    ]
    
    return report

@router.post("/users/{usuario_id}/silence", response_model=schemas.UsuarioPublico, summary="Silenciar a un usuario")
def silence_user(usuario_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Impide que un usuario pueda añadir más canciones.
    """
    db_usuario = crud.set_usuario_silenciado(db, usuario_id=usuario_id, silenciar=True)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return db_usuario

@router.post("/users/{usuario_id}/un-silence", response_model=schemas.UsuarioPublico, summary="Reactivar a un usuario silenciado")
def un_silence_user(usuario_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Permite que un usuario previamente silenciado pueda volver a añadir canciones.
    """
    db_usuario = crud.set_usuario_silenciado(db, usuario_id=usuario_id, silenciar=False)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return db_usuario

@router.get("/reports/average-income-per-user", response_model=schemas.ReporteIngresosPromedio, summary="Obtener los ingresos promedio por usuario")
def get_average_income_per_user_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un reporte con el ingreso promedio por cada usuario
    que ha realizado al menos un consumo.
    """
    ingreso_promedio = crud.get_ingresos_promedio_por_usuario(db)
    return schemas.ReporteIngresosPromedio(ingresos_promedio_por_usuario=ingreso_promedio)

@router.put("/users/{usuario_id}/move-table", response_model=schemas.UsuarioPublico, summary="Mover un usuario a otra mesa")
def move_user_to_table(usuario_id: int, mover_data: schemas.UsuarioMoverMesa, db: Session = Depends(get_db)):
    """
    **[Admin]** Mueve un usuario de su mesa actual a una nueva mesa
    especificada por su código QR.
    """
    db_usuario = crud.get_usuario_by_id(db, usuario_id=usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    nueva_mesa = crud.get_mesa_by_qr(db, qr_code=mover_data.nuevo_qr_code)
    if not nueva_mesa:
        raise HTTPException(status_code=404, detail="Mesa de destino no encontrada.")

    usuario_actualizado = crud.update_usuario_mesa(db, usuario_id=usuario_id, nueva_mesa_id=nueva_mesa.id)
    
    # Aquí podrías notificar por WebSocket si el frontend necesita saber del cambio de mesa.

    return usuario_actualizado

@router.get("/reports/one-hit-wonders", response_model=List[schemas.UsuarioPublico], summary="Obtener usuarios que han cantado una sola canción")
def get_one_hit_wonders_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve una lista de todos los usuarios que han cantado
    exactamente una canción durante la noche.
    """
    one_hit_wonders = crud.get_usuarios_una_cancion(db)
    return one_hit_wonders

@router.post("/users/{usuario_id}/add-points", response_model=schemas.UsuarioPublico, summary="Añadir puntos a un usuario")
def add_points_to_user(usuario_id: int, puntos_update: schemas.UsuarioPuntosUpdate, db: Session = Depends(get_db)):
    """
    **[Admin]** Añade una cantidad de puntos manualmente a un usuario.
    Puede usarse para premiar o en concursos.
    """
    db_usuario = crud.add_puntos_a_usuario(db, usuario_id=usuario_id, puntos_a_anadir=puntos_update.puntos)
    if not db_usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado."
        )
    crud.create_admin_log_entry(db, action="ADD_POINTS", details=f"Añadidos {puntos_update.puntos} puntos al usuario '{db_usuario.nick}' (ID: {usuario_id}).")
    return db_usuario

@router.put("/users/{usuario_id}/edit-nick", response_model=schemas.UsuarioPublico, summary="Editar el nick de un usuario")
def edit_user_nick(usuario_id: int, nick_update: schemas.UsuarioNickUpdate, db: Session = Depends(get_db)):
    """
    **[Admin]** Permite editar el nick de un usuario específico.
    """
    db_usuario = crud.update_usuario_nick(db, usuario_id=usuario_id, nuevo_nick=nick_update.nick)
    if not db_usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado."
        )
    crud.create_admin_log_entry(db, action="EDIT_NICK", details=f"Nick del usuario ID {usuario_id} cambiado a '{nick_update.nick}'.")
    return db_usuario

@router.get("/reports/songs-by-user", response_model=List[schemas.ReporteCancionesPorUsuario], summary="Obtener cantidad de canciones por usuario")
def get_songs_by_user_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un reporte de cuántas canciones ha cantado cada usuario,
    ordenado de mayor a menor.
    """
    songs_data = crud.get_canciones_cantadas_por_usuario(db)
    
    report = [
        schemas.ReporteCancionesPorUsuario(
            nick=nick,
            canciones_cantadas=count
        )
        for nick, count in songs_data
    ]
    
    return report

@router.post("/reorder-queue", status_code=200, summary="Reordenar manualmente la cola de canciones")
async def reorder_queue(orden: schemas.ReordenarCola, db: Session = Depends(get_db)):
    """
    **[Admin]** Establece un orden manual para la cola de canciones aprobadas.
    La lista de IDs debe contener las canciones en el orden deseado.
    Cualquier canción aprobada no incluida en la lista irá después,
    siguiendo la prioridad automática.
    """
    crud.reordenar_cola_manual(db, canciones_ids=orden.canciones_ids)
    # Notificamos a todos los clientes de la nueva cola
    crud.create_admin_log_entry(db, action="REORDER_QUEUE", details=f"Cola reordenada manualmente. Nuevo orden: {orden.canciones_ids}")
    await websocket_manager.manager.broadcast_queue_update()
    return {"mensaje": "La cola ha sido reordenada manualmente."}

@router.get("/reports/inactive-users", response_model=List[schemas.UsuarioPublico], summary="Obtener usuarios sin consumo")
def get_inactive_users_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve una lista de todos los usuarios que no han
    realizado ningún consumo durante la noche.
    """
    inactive_users = crud.get_usuarios_sin_consumo(db)
    return inactive_users

@router.post("/songs/{cancion_id}/move-to-top", status_code=200, summary="Mover una canción al principio de la cola")
async def move_song_to_top_endpoint(cancion_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Mueve una canción específica al principio de la cola,
    dándole la máxima prioridad manual.
    """
    cancion_movida = crud.move_song_to_top(db, cancion_id=cancion_id)
    if not cancion_movida:
        raise HTTPException(
            status_code=404,
            detail="La canción no fue encontrada o no está en estado 'aprobado'."
        )
    
    crud.create_admin_log_entry(db, action="MOVE_SONG_TOP", details=f"Canción '{cancion_movida.titulo}' (ID: {cancion_id}) movida al principio.")
    await websocket_manager.manager.broadcast_queue_update()
    return {"mensaje": f"La canción '{cancion_movida.titulo}' ha sido movida al principio de la cola."}

@router.post("/canciones/restart", status_code=200, summary="Reiniciar la canción actual")
async def restart_current_song(db: Session = Depends(get_db)):
    """
    **[Admin]** Reinicia la canción que se está reproduciendo actualmente.
    """
    await websocket_manager.manager.broadcast_restart_song()
    crud.create_admin_log_entry(db, action="RESTART_SONG", details="Canción actual reiniciada.")
    return {"mensaje": "Canción reiniciada."}

@router.post("/player/pause", status_code=200, summary="Pausar la reproducción")
async def pause_playback(db: Session = Depends(get_db)):
    """
    **[Admin]** Pausa la reproducción en el player.
    """
    await websocket_manager.manager.broadcast_pause()
    crud.create_admin_log_entry(db, action="PAUSE_PLAYBACK", details="Reproducción pausada por admin.")
    return {"mensaje": "Reproducción pausada."}

@router.post("/player/resume", status_code=200, summary="Reanudar la reproducción")
async def resume_playback(db: Session = Depends(get_db)):
    """
    **[Admin]** Reanuda la reproducción en el player.
    """
    await websocket_manager.manager.broadcast_resume()
    crud.create_admin_log_entry(db, action="RESUME_PLAYBACK", details="Reproducción reanudada por admin.")
    return {"mensaje": "Reproducción reanudada."}

@router.get("/reports/total-income", response_model=schemas.ReporteIngresos, summary="Obtener los ingresos totales de la noche")
def get_total_income_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un reporte con la suma total de los ingresos por consumos.
    """
    total_ingresos = crud.get_total_ingresos(db)
    return schemas.ReporteIngresos(ingresos_totales=total_ingresos)

@router.get("/reports/income-by-table", response_model=List[schemas.ReporteIngresosPorMesa], summary="Obtener los ingresos por mesa")
def get_income_by_table_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un reporte de los ingresos totales generados por cada mesa,
    ordenado de mayor a menor.
    """
    income_data = crud.get_ingresos_por_mesa(db)
    
    report = [
        schemas.ReporteIngresosPorMesa(
            mesa_nombre=nombre,
            ingresos_totales=total
        )
        for nombre, total in income_data
    ]
    
    return report

@router.get("/reports/least-sold-products", response_model=List[schemas.ProductoMasConsumido], summary="Obtener los productos menos vendidos")
def get_least_sold_products_report(db: Session = Depends(get_db), limit: int = 5):
    """
    **[Admin]** Devuelve un reporte de los productos que menos se han vendido,
    ordenados de menor a mayor cantidad.
    """
    least_sold_data = crud.get_productos_menos_consumidos(db, limit=limit)
    
    report = [
        schemas.ProductoMasConsumido(
            nombre=nombre,
            cantidad_total=cantidad_total
        )
        for nombre, cantidad_total in least_sold_data
    ]
    
    return report

@router.get("/reports/inactive-consumers", response_model=List[schemas.UsuarioPublico], summary="Obtener usuarios con consumo inactivo")
def get_inactive_consumers_report(db: Session = Depends(get_db), horas: int = 2):
    """
    **[Admin]** Devuelve una lista de todos los usuarios cuyo último consumo
    fue hace más de X horas (por defecto 2), o que nunca han consumido.
    """
    users = crud.get_usuarios_inactivos_consumo(db, horas=horas)
    return users

@router.get("/reports/top-consumers-one-song", response_model=List[schemas.ReporteGastoUsuarioPorCategoria], summary="Obtener 'One-Hit Wonders' con mayor consumo")
def get_top_consumers_one_song_report(db: Session = Depends(get_db), limit: int = 10):
    """
    **[Admin]** Devuelve un ranking de los usuarios que más han consumido
    pero que solo han cantado una canción.
    """
    users_data = crud.get_top_consumers_one_song(db, limit=limit)
    
    report = [
        schemas.ReporteGastoUsuarioPorCategoria(
            nick=nick,
            total_gastado=total
        )
        for nick, total in users_data
    ]
    
    return report

@router.get("/reports/consumers-no-singers", response_model=List[schemas.UsuarioPublico], summary="Obtener usuarios que consumen pero no cantan")
def get_consumers_no_singers_report(db: Session = Depends(get_db), umbral: float = 100.0):
    """
    **[Admin]** Devuelve una lista de todos los usuarios que han gastado más
    del umbral especificado pero no han cantado ninguna canción.
    """
    users = crud.get_usuarios_consumen_pero_no_cantan(db, umbral_consumo=umbral)
    return users

@router.get("/tables/{mesa_id}/top-categories", response_model=List[schemas.ReporteCategoriaMasVendida], summary="Obtener categorías más vendidas en una mesa")
def get_top_categories_by_table_report(mesa_id: int, db: Session = Depends(get_db), limit: int = 5):
    """
    **[Admin]** Devuelve un reporte de las categorías de productos más vendidas en una mesa específica.
    """
    # Verificamos que la mesa exista
    db_mesa = crud.get_mesa_by_id(db, mesa_id=mesa_id)
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada.")

    top_categories_data = crud.get_categorias_mas_consumidas_por_mesa(db, mesa_id=mesa_id, limit=limit)
    
    report = [
        schemas.ReporteCategoriaMasVendida(
            categoria=categoria,
            cantidad_total=cantidad_total
        ) for categoria, cantidad_total in top_categories_data
    ]
    
    return report

@router.get("/reports/active-gold-users", response_model=List[schemas.UsuarioPublico], summary="Obtener usuarios 'Oro' más activos")
def get_active_gold_users_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve una lista de los usuarios de nivel "Oro" que han
    cantado más de 5 canciones.
    """
    active_gold_users = crud.get_usuarios_oro_activos(db)
    return active_gold_users

@router.get("/tables/{mesa_id}/top-requested-songs", response_model=List[schemas.ReporteCancionMasPedida], summary="Obtener canciones más pedidas en una mesa")
def get_top_requested_songs_by_table_report(mesa_id: int, db: Session = Depends(get_db), limit: int = 5):
    """
    **[Admin]** Devuelve un reporte de las canciones más pedidas en una mesa específica.
    """
    # Verificamos que la mesa exista
    db_mesa = crud.get_mesa_by_id(db, mesa_id=mesa_id)
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada.")

    top_songs_data = crud.get_canciones_mas_pedidas_por_mesa(db, mesa_id=mesa_id, limit=limit)
    
    report = [
        schemas.ReporteCancionMasPedida(
            titulo=titulo,
            youtube_id=youtube_id,
            veces_pedida=veces_pedida
        ) for titulo, youtube_id, veces_pedida in top_songs_data
    ]
    
    return report

@router.get("/tables/{mesa_id}/top-products", response_model=List[schemas.ProductoMasConsumido], summary="Obtener productos más vendidos en una mesa")
def get_top_products_by_table_report(mesa_id: int, db: Session = Depends(get_db), limit: int = 5):
    """
    **[Admin]** Devuelve un reporte de los productos más vendidos en una mesa específica.
    """
    # Verificamos que la mesa exista
    db_mesa = crud.get_mesa_by_id(db, mesa_id=mesa_id)
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada.")

    top_products_data = crud.get_productos_mas_consumidos_por_mesa(db, mesa_id=mesa_id, limit=limit)
    
    report = [
        schemas.ProductoMasConsumido(
            nombre=nombre,
            cantidad_total=cantidad_total
        )
        for nombre, cantidad_total in top_products_data
    ]
    
    return report

@router.get("/reports/unsold-products", response_model=List[schemas.Producto], summary="Obtener productos nunca vendidos")
def get_unsold_products_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un reporte de los productos del catálogo que
    nunca han sido consumidos durante la noche.
    """
    unsold_products = crud.get_productos_no_consumidos(db)
    return unsold_products


@router.get("/recent-consumos", response_model=List[schemas.ConsumoReciente], summary="Obtener consumos recientes")
def get_recent_consumos_endpoint(db: Session = Depends(get_db), limit: int = 10):
    """
    **[Admin]** Devuelve los consumos más recientes (últimos N) para mostrar
    en el dashboard del administrador.
    """
    recent = crud.get_recent_consumos(db, limit=limit)
    return recent


@router.delete('/consumos/{consumo_id}', status_code=204, summary='Eliminar un consumo')
async def admin_delete_consumo(consumo_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Permite al administrador cancelar un consumo previamente registrado.
    Restaura el stock y recalcula puntos del usuario.
    Notifica vía WebSocket a los clientes sobre la eliminación.
    """
    deleted = crud.delete_consumo(db, consumo_id=consumo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Consumo no encontrado')

    # Notificar a los clientes que un consumo fue eliminado
    try:
        await websocket_manager.manager.broadcast_consumo_deleted({'id': consumo_id})
    except Exception:
        # No romper la respuesta si la notificación falla
        pass

    return Response(status_code=204)

@router.post('/consumos/{consumo_id}/mark-despachado', status_code=200, summary='Marcar consumo como despachado')
async def admin_mark_consumo_despachado(consumo_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Marca un consumo como despachado.
    No elimina el consumo de la base de datos, solo lo marca como despachado para que no aparezca en "pedidos recientes".
    """
    db_consumo = db.query(models.Consumo).filter(models.Consumo.id == consumo_id).first()
    if not db_consumo:
        raise HTTPException(status_code=404, detail='Consumo no encontrado')

    # Mark as dispatched in DB
    db_consumo.is_dispatched = True
    db.commit()

    # Log the action
    crud.create_admin_log_entry(db, action="MARK_CONSUMO_DESPACHADO", details=f"Consumo ID {consumo_id} marcado como despachado.")

    # Notify clients that this consumption should be removed from recent lists
    try:
        await websocket_manager.manager.broadcast_consumo_deleted({'id': consumo_id})
    except Exception:
        pass # Don't break the response if notification fails

    return {"message": f"Consumo {consumo_id} marcado como despachado."}

@router.get("/reports/gold-users", response_model=List[schemas.UsuarioPublico], summary="Obtener usuarios de nivel Oro")
def get_gold_users_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve una lista de todos los usuarios que actualmente
    tienen el nivel "Oro".
    """
    gold_users = crud.get_usuarios_por_nivel(db, nivel="oro")
    return gold_users

@router.get("/summary", response_model=schemas.ResumenNoche, summary="Obtener un resumen general de la noche")
def get_night_summary(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un resumen con las métricas clave de la noche:
    ingresos totales, total de canciones cantadas y número de usuarios activos.
    """
    summary_data = crud.get_resumen_noche(db)
    ganancias = crud.get_ganancias_totales(db)
    
    # Aseguramos que los tipos sean primitivos JSON-serializables (float/int)
    ingresos = summary_data.get('ingresos_totales', 0)
    try:
        ingresos_val = float(ingresos)
    except Exception:
        ingresos_val = 0.0

    try:
        ganancias_val = float(ganancias)
    except Exception:
        ganancias_val = 0.0

    canciones = summary_data.get('canciones_cantadas', 0)
    try:
        canciones_val = int(canciones)
    except Exception:
        canciones_val = 0

    usuarios = summary_data.get('usuarios_activos', 0)
    try:
        usuarios_val = int(usuarios)
    except Exception:
        usuarios_val = 0

    return schemas.ResumenNoche(
        ingresos_totales=ingresos_val,
        ganancias_totales=ganancias_val,
        canciones_cantadas=canciones_val,
        usuarios_activos=usuarios_val
    )

@router.get("/reports/table-consumption-summaries", response_model=List[schemas.MesaConsumoResumen], summary="Obtener resumen de consumo por mesa")
def get_table_consumption_summaries_endpoint(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un resumen detallado del consumo de cada mesa,
    incluyendo el valor total consumido y la lista de productos pedidos.
    """
    summaries = crud.get_all_tables_consumption_summaries(db)
    return summaries

@router.get("/reports/table-payment-status", response_model=List[schemas.MesaEstadoPago], summary="Obtener estado de cuenta de todas las mesas", tags=["Reportes", "Cuentas"])
async def get_table_payment_status_endpoint(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un estado de cuenta detallado para cada mesa,
    incluyendo total consumido, total pagado, saldo pendiente, y listas
    de consumos y pagos realizados.
    """
    status_list = crud.get_all_tables_payment_status(db)
    return status_list

@router.get("/tables/{mesa_id}/payment-status", response_model=schemas.MesaEstadoPago, summary="Obtener estado de cuenta de una mesa específica", tags=["Cuentas"])
def get_single_table_payment_status(mesa_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un estado de cuenta detallado para una mesa específica,
    incluyendo total consumido, total pagado, saldo pendiente, y listas
    de consumos y pagos realizados.
    """
    status = crud.get_table_payment_status(db, mesa_id=mesa_id)
    if not status:
        raise HTTPException(status_code=404, detail="Mesa no encontrada.")
    return status
@router.post("/pagos", response_model=schemas.PagoView, summary="Registrar un nuevo pago para una mesa", tags=["Cuentas"])
async def create_pago_endpoint(pago: schemas.PagoCreate, db: Session = Depends(get_db)):
    """
    **[Admin]** Registra un nuevo pago para una mesa específica.
    """
    db_pago = crud.create_pago_for_mesa(db, pago=pago)
    if not db_pago:
        raise HTTPException(status_code=404, detail="La mesa especificada no fue encontrada.")
    
    crud.create_admin_log_entry(db, action="CREATE_PAGO", details=f"Registrado pago de ${pago.monto} para la mesa ID {pago.mesa_id}.")
    
    # Podríamos emitir un evento por WebSocket si quisiéramos actualizar la vista en tiempo real
    # await websocket_manager.manager.broadcast_payment_update(pago.mesa_id)
    return db_pago

@router.get("/tables/{mesa_id}/summary", response_model=schemas.ResumenMesa, summary="Obtener resumen de una mesa específica")
def get_table_summary(mesa_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un resumen detallado de una mesa específica, incluyendo:
    usuarios conectados, consumo total de la mesa, y canciones pendientes/reproduciéndose.
    """
    summary_data = crud.get_resumen_mesa(db, mesa_id=mesa_id)
    if not summary_data:
        raise HTTPException(
            status_code=404,
            detail="Mesa no encontrada."
        )
    return summary_data


@router.get("/logs", response_model=List[schemas.AdminLogView], summary="Ver el log de acciones administrativas")
def get_admin_logs_endpoint(db: Session = Depends(get_db), limit: int = 100):
    """
    **[Admin]** Devuelve un log de las últimas acciones realizadas por administradores.
    """
    return crud.get_admin_logs(db, limit=limit)

@router.get("/reports/silver-users", response_model=List[schemas.UsuarioPublico], summary="Obtener usuarios de nivel Plata")
def get_silver_users_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve una lista de todos los usuarios que actualmente
    tienen el nivel "Plata".
    """
    silver_users = crud.get_usuarios_por_nivel(db, nivel="plata")
    return silver_users

@router.get("/reports/users-without-sung-songs", response_model=List[schemas.UsuarioPublico], summary="Obtener usuarios que no han cantado")
def get_users_without_sung_songs_report(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve una lista de todos los usuarios que no han cantado
    ninguna canción durante la noche.
    """
    users = crud.get_usuarios_sin_canciones_cantadas(db)
    return users

@router.get("/users/{usuario_id}/history", response_model=schemas.HistorialUsuario, summary="Obtener historial de acciones de un usuario")
def get_user_history(usuario_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un historial completo de las acciones de un usuario,
    incluyendo todas sus canciones añadidas y todos sus consumos.
    """
    # Verificamos que el usuario exista
    db_usuario = crud.get_usuario_by_id(db, usuario_id=usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Obtenemos los datos
    historial_canciones = crud.get_canciones_por_usuario(db, usuario_id=usuario_id)
    historial_consumos = crud.get_consumos_por_usuario(db, usuario_id=usuario_id)

    return schemas.HistorialUsuario(
        canciones=historial_canciones,
        consumos=historial_consumos
    )

@router.get("/tables/status", response_model=List[schemas.MesaEstado], summary="Obtener estado de todas las mesas")
def get_all_tables_status(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve un listado de todas las mesas del sistema con su
    estado actual (Ocupada/Vacía), el número de usuarios conectados y el
    consumo total acumulado.
    """
    mesas_data = crud.get_estado_mesas(db)
    
    report = []
    for mesa, num_usuarios, consumo_total in mesas_data:
        report.append(schemas.MesaEstado(
            id=mesa.id,
            nombre=mesa.nombre,
            qr_code=mesa.qr_code,
            estado="Ocupada" if num_usuarios > 0 else "Vacía",
            numero_usuarios=num_usuarios,
            consumo_total=consumo_total
        ))
    return report

@router.get("/reports/top-points-users", response_model=List[schemas.UsuarioPublico], summary="Obtener ranking de usuarios por puntos")
def get_top_points_users_report(db: Session = Depends(get_db), limit: int = 10):
    """
    **[Admin]** Devuelve un ranking de los usuarios con más puntos acumulados,
    ordenado de mayor a menor.
    """
    top_users = crud.get_ranking_puntos_usuarios(db, limit=limit)
    return top_users

@router.get("/tables/{mesa_id}/consumption-history", response_model=List[schemas.ConsumoHistorial], summary="Obtener historial de consumo de una mesa")
def get_table_consumption_history(mesa_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve el historial completo de consumos de una mesa específica,
    ordenado del más reciente al más antiguo.
    """
    # Primero, verificamos que la mesa exista
    db_mesa = crud.get_mesa_by_id(db, mesa_id=mesa_id)
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada.")

    consumos = crud.get_consumo_por_mesa(db, mesa_id=mesa_id)
    return consumos

@router.post("/mesas/{mesa_id}/add-song", response_model=schemas.Cancion, summary="Añadir una canción a una mesa específica")
async def admin_add_song_to_mesa(
    mesa_id: int,
    cancion: schemas.CancionCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_auth)
):
    """
    **[Admin]** Permite al administrador añadir una canción directamente a la cola
    de una mesa específica. La canción se aprueba automáticamente.
    """
    # Verificar que la mesa existe
    db_mesa = crud.get_mesa_by_id(db, mesa_id=mesa_id)
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada.")

    # Obtener o crear un usuario DJ para la mesa
    # Primero buscamos si hay un usuario admin/DJ ya asociado a esta mesa
    db_usuario = crud.get_o_crear_usuario_admin_para_mesa(db, mesa_id=mesa_id)
    
    # Crear la canción asociada a este usuario
    db_cancion = crud.create_cancion_para_usuario(db=db, cancion=cancion, usuario_id=db_usuario.id)
    
    # Aprobar automáticamente la canción
    cancion_aprobada = crud.update_cancion_estado(db, cancion_id=db_cancion.id, nuevo_estado="aprobado")
    
    # Si autoplay está activo, intentar iniciar la reproducción si estaba vacío
    import asyncio
    await crud.start_next_song_if_autoplay_and_idle(db)
    
    # Notificar a todos los clientes sobre la nueva cola
    await websocket_manager.manager.broadcast_queue_update()
    
    crud.create_admin_log_entry(db, action="ADMIN_ADD_SONG_TO_TABLE", details=f"Canción '{cancion_aprobada.titulo}' añadida a la mesa ID {mesa_id}.")
    
    return cancion_aprobada

# --- Gestión de Claves de API ---

@router.post("/api-keys", response_model=schemas.AdminApiKeyView, status_code=201, summary="Crear una nueva clave de API")
def create_new_api_key(key_data: schemas.AdminApiKeyCreate, db: Session = Depends(get_db)):
    """
    **[Admin]** Genera una nueva clave de API para administradores.
    La clave solo se mostrará una vez, ¡guárdala en un lugar seguro!
    """
    new_key = crud.create_admin_api_key(db, description=key_data.description)
    crud.create_admin_log_entry(db, action="CREATE_API_KEY", details=f"Nueva clave de API creada: '{key_data.description}'")
    return new_key

@router.get("/api-keys", response_model=List[schemas.AdminApiKeyInfo], summary="Listar todas las claves de API")
def list_api_keys(db: Session = Depends(get_db)):
    """
    **[Admin]** Muestra una lista de todas las claves de API de administrador,
    sin revelar las claves en sí.
    """
    return crud.get_all_admin_api_keys(db)

@router.delete("/api-keys/{key_id}", status_code=204, summary="Eliminar una clave de API")
def delete_api_key(key_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Elimina permanentemente una clave de API de administrador.
    """
    deleted_key = crud.delete_admin_api_key(db, key_id=key_id)
    if not deleted_key:
        raise HTTPException(status_code=404, detail="Clave de API no encontrada.")
    crud.create_admin_log_entry(db, action="DELETE_API_KEY", details=f"Clave de API ID {key_id} ('{deleted_key.description}') eliminada.")
    return Response(status_code=204)

# --- Cuentas por Mesa endpoints ---

@router.post("/tables/{mesa_id}/new-account", summary="Abrir una nueva cuenta para la mesa")
def open_new_account(mesa_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Cierra la cuenta actual de la mesa (si hay) y abre una nueva.
    Los usuarios no se borran, pero los consumos futuros irán a la nueva cuenta.
    **VALIDACIÓN:** No permite crear una nueva cuenta si la actual tiene saldo pendiente.
    """
    # 1. Verificar si la cuenta actual está a paz y salvo
    status_dict = crud.get_table_payment_status(db, mesa_id=mesa_id)
    
    # Si devuelve dict, lo revisamos. Si es None, es que no hay cuenta o mesa, dejamos pasar al create para que maneje o cree desde cero.
    if status_dict:
        saldo_pendiente = status_dict.get("saldo_pendiente", 0)
        # Aseguramos que sea numérico para la comparación
        try:
             saldo_val = float(saldo_pendiente)
        except:
             saldo_val = 0.0
             
        if saldo_val > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"No se puede abrir una nueva cuenta. La mesa tiene un saldo pendiente de ${saldo_val:,.0f}."
            )

    new_cuenta = crud.create_new_active_cuenta(db, mesa_id)
    return {"message": "Nueva cuenta creada exitosamente.", "cuenta_id": new_cuenta.id}

@router.get("/tables/{mesa_id}/previous-accounts", response_model=List[schemas.CuentaInfo], summary="Obtener cuentas anteriores de la mesa")
def get_previous_accounts(mesa_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Listado de cuentas cerradas de la mesa.
    """
    cuentas = crud.get_previous_cuentas(db, mesa_id)
    return cuentas

@router.get("/accounts/{cuenta_id}", response_model=schemas.MesaEstadoPago, summary="Obtener detalle de una cuenta (activa o pasada)")
def get_account_details(cuenta_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Obtiene el estado de cuenta completo de una cuenta específica (activa o cerrada).
    """
    status = crud.get_cuenta_payment_status(db, cuenta_id)
    if not status:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada.")
    return status