from sqlalchemy.orm import Session
from sqlalchemy import func, case
import datetime
from . import models, schemas

def get_mesa_by_qr(db: Session, qr_code: str):
    """Busca una mesa por su código QR."""
    return db.query(models.Mesa).filter(models.Mesa.qr_code == qr_code).first()

def create_mesa(db: Session, mesa: schemas.MesaCreate):
    """Crea una nueva mesa en la base de datos."""
    db_mesa = models.Mesa(nombre=mesa.nombre, qr_code=mesa.qr_code)
    db.add(db_mesa)
    db.commit()
    db.refresh(db_mesa)
    return db_mesa

def create_usuario_en_mesa(db: Session, usuario: schemas.UsuarioCreate, mesa_id: int):
    """Crea un nuevo usuario y lo asocia a una mesa."""
    db_usuario = models.Usuario(nick=usuario.nick, mesa_id=mesa_id)
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def get_usuario_by_id(db: Session, usuario_id: int):
    """Busca un usuario por su ID."""
    return db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()

def get_total_consumido_por_usuario(db: Session, usuario_id: int):
    """Calcula el total consumido por un usuario."""
    return db.query(func.sum(models.Consumo.valor)).filter(models.Consumo.usuario_id == usuario_id).scalar() or 0

def get_canciones_por_usuario(db: Session, usuario_id: int):
    """Busca todas las canciones de un usuario específico."""
    return db.query(models.Cancion).filter(models.Cancion.usuario_id == usuario_id).all()

def create_cancion_para_usuario(db: Session, cancion: schemas.CancionCreate, usuario_id: int):
    """Crea una nueva canción y la asocia a un usuario."""
    db_cancion = models.Cancion(**cancion.dict(), usuario_id=usuario_id)
    db.add(db_cancion)
    db.commit()
    db.refresh(db_cancion)
    return db_cancion

def check_if_song_in_user_list(db: Session, usuario_id: int, youtube_id: str):
    """
    Verifica si un usuario ya tiene una canción en su lista que no esté cantada o rechazada.
    """
    return db.query(models.Cancion).filter(
        models.Cancion.usuario_id == usuario_id,
        models.Cancion.youtube_id == youtube_id,
        models.Cancion.estado.in_(['pendiente', 'aprobado', 'reproduciendo'])
    ).first()

def get_cancion_by_id(db: Session, cancion_id: int):
    """Busca una canción por su ID."""
    return db.query(models.Cancion).filter(models.Cancion.id == cancion_id).first()

def get_canciones_pendientes(db: Session):
    """Busca todas las canciones en estado 'pendiente'."""
    return db.query(models.Cancion).filter(models.Cancion.estado == 'pendiente').order_by(models.Cancion.id).all()

def get_duracion_total_cola_aprobada(db: Session) -> int:
    """Calcula la suma de la duración de todas las canciones aprobadas."""
    total_seconds = db.query(func.sum(models.Cancion.duracion_seconds)).filter(models.Cancion.estado == 'aprobado').scalar()
    return total_seconds or 0

def update_cancion_estado(db: Session, cancion_id: int, nuevo_estado: str):
    """Actualiza el estado de una canción específica."""
    db_cancion = db.query(models.Cancion).filter(models.Cancion.id == cancion_id).first()
    if db_cancion:
        db_cancion.estado = nuevo_estado
        db.commit()
        db.refresh(db_cancion)
    return db_cancion

def get_cola_priorizada(db: Session):
    """
    Obtiene la lista de canciones aprobadas, ordenadas por prioridad.
    La prioridad se basa en:
    1. Si el último consumo fue hace menos de 1 hora.
    2. El consumo total del usuario.
    """
    hora_limite = datetime.datetime.utcnow() - datetime.timedelta(hours=1)

    # Subconsulta para calcular el consumo total por usuario
    consumo_total_subq = (
        db.query(
            models.Usuario.id.label("usuario_id"),
            func.sum(models.Consumo.valor).label("total_consumido"),
        )
        .join(models.Consumo, models.Usuario.id == models.Consumo.usuario_id)
        .group_by(models.Usuario.id)
        .subquery()
    )

    # Subconsulta para obtener el último consumo de cada usuario
    ultimo_consumo_subq = (
        db.query(
            models.Usuario.id.label("usuario_id"),
            func.max(models.Consumo.created_at).label("ultimo_consumo_ts"),
        )
        .join(models.Consumo, models.Usuario.id == models.Consumo.usuario_id)
        .group_by(models.Usuario.id)
        .subquery()
    )

    # Case para determinar si el usuario está activo (prioridad 1) o inactivo (prioridad 0)
    prioridad_actividad = case(
        (ultimo_consumo_subq.c.ultimo_consumo_ts > hora_limite, 1),
        else_=0
    ).label("prioridad_actividad")

    # Consulta principal que une canciones con el consumo del usuario
    return (
        db.query(models.Cancion)
        .join(models.Usuario, models.Cancion.usuario_id == models.Usuario.id)
        .join(consumo_total_subq, models.Usuario.id == consumo_total_subq.c.usuario_id, isouter=True)
        .join(ultimo_consumo_subq, models.Usuario.id == ultimo_consumo_subq.c.usuario_id, isouter=True)
        .filter(models.Cancion.estado == "aprobado")
        .order_by(models.Cancion.orden_manual.asc().nulls_last(), prioridad_actividad.desc(), func.coalesce(consumo_total_subq.c.total_consumido, 0).desc(), models.Cancion.id.asc())
        .all()
    )

def create_consumo_para_usuario(db: Session, consumo: schemas.ConsumoCreate, usuario_id: int):
    """Crea un nuevo consumo, lo asocia a un usuario y actualiza su nivel."""
    # Definimos los umbrales para cada nivel
    SILVER_THRESHOLD = 50.0
    GOLD_THRESHOLD = 150.0

    # Creamos el objeto de consumo y lo añadimos a la sesión
    db_consumo = models.Consumo(**consumo.dict(), usuario_id=usuario_id)
    db.add(db_consumo)

    # Obtenemos el usuario para poder actualizarlo
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_usuario:
        # En un caso real, esto debería lanzar una excepción, pero por ahora lo dejamos pasar.
        db.rollback()
        return None

    # Sumamos el valor del nuevo consumo al total que ya tenía el usuario
    # Para obtener el total, sumamos todos los consumos del usuario en la BD
    # Nota: Hacemos commit del consumo nuevo primero para que la suma sea correcta.
    db.commit()
    db.refresh(db_consumo)

    total_consumido = db.query(func.sum(models.Consumo.valor)).filter(models.Consumo.usuario_id == usuario_id).scalar() or 0

    if total_consumido >= GOLD_THRESHOLD:
        db_usuario.nivel = "oro"
    elif total_consumido >= SILVER_THRESHOLD:
        db_usuario.nivel = "plata"

    db.commit()
    db.refresh(db_usuario)
    return db_consumo

def marcar_cancion_actual_como_cantada(db: Session):
    """
    Busca la canción que se está reproduciendo, la marca como 'cantada' y le da puntos al usuario.
    """
    # 1. Buscar la canción que está actualmente en estado 'reproduciendo'
    cancion_actual = db.query(models.Cancion).filter(models.Cancion.estado == "reproduciendo").first()
    
    if not cancion_actual:
        return None  # No hay ninguna canción reproduciéndose

    # 2. Actualizar el estado de la canción a 'cantada'
    cancion_actual.estado = "cantada"

    # 3. Dar puntos al usuario por cantar
    if cancion_actual.usuario:
        cancion_actual.usuario.puntos += 10  # Otorgamos 10 puntos por canción

    db.commit()
    db.refresh(cancion_actual)
    return cancion_actual

def marcar_siguiente_como_reproduciendo(db: Session):
    """Busca la siguiente canción en la cola y la marca como 'reproduciendo'."""
    siguiente_cancion = get_cola_priorizada(db)
    if not siguiente_cancion:
        return None
    
    siguiente_cancion[0].estado = "reproduciendo"
    siguiente_cancion[0].started_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(siguiente_cancion[0])
    return siguiente_cancion[0]

def get_tiempo_espera_para_cancion(db: Session, cancion_id: int) -> int:
    """
    Calcula el tiempo de espera estimado en segundos para una canción específica.
    """
    # 1. Obtener la canción que se está reproduciendo
    cancion_actual = db.query(models.Cancion).filter(models.Cancion.estado == "reproduciendo").first()
    
    tiempo_espera_total = 0
    if cancion_actual:
        tiempo_transcurrido = (datetime.datetime.utcnow() - cancion_actual.started_at).total_seconds()
        tiempo_restante_actual = max(0, cancion_actual.duracion_seconds - tiempo_transcurrido)
        tiempo_espera_total += tiempo_restante_actual

    # 2. Obtener la cola de canciones aprobadas
    cola_aprobada = get_cola_priorizada(db)

    # 3. Sumar la duración de las canciones que están antes de la nuestra
    for cancion_en_cola in cola_aprobada:
        if cancion_en_cola.id == cancion_id:
            # Llegamos a nuestra canción, dejamos de sumar
            break
        tiempo_espera_total += cancion_en_cola.duracion_seconds
    else:
        # Si la canción no se encuentra en la cola (ya se cantó, fue rechazada, etc.)
        # devolvemos -1 para indicar que no hay tiempo de espera.
        return -1

    return int(tiempo_espera_total)

def get_ranking_usuarios(db: Session):
    """
    Obtiene un ranking de todos los usuarios ordenado por su consumo total.
    Devuelve una lista de tuplas (Usuario, total_consumido).
    """
    # Subconsulta para calcular el consumo total por cada usuario
    consumo_total_subq = (
        db.query(
            models.Consumo.usuario_id.label("usuario_id"),
            func.sum(models.Consumo.valor).label("total_consumido"),
        )
        .group_by(models.Consumo.usuario_id)
        .subquery()
    )

    # Consulta principal que une usuarios con su consumo total y ordena
    return db.query(models.Usuario, func.coalesce(consumo_total_subq.c.total_consumido, 0).label("total_consumido_calc")).join(consumo_total_subq, models.Usuario.id == consumo_total_subq.c.usuario_id, isouter=True).order_by(func.coalesce(consumo_total_subq.c.total_consumido, 0).desc()).all()

def reset_database_for_new_night(db: Session):
    """
    Borra todos los datos de las tablas transaccionales para empezar una nueva noche.
    El orden es importante para respetar las restricciones de clave foránea.
    """
    # El orden de borrado es inverso al de creación de dependencias
    db.query(models.Consumo).delete()
    db.query(models.Cancion).delete()
    db.query(models.Usuario).delete()
    db.query(models.Mesa).delete()
    
    db.commit()

def get_canciones_mas_cantadas(db: Session, limit: int = 10):
    """
    Obtiene un reporte de las canciones más cantadas, agrupadas y contadas.
    """
    return (
        db.query(
            models.Cancion.titulo,
            models.Cancion.youtube_id,
            func.count(models.Cancion.id).label("veces_cantada"),
        )
        .filter(models.Cancion.estado == "cantada")
        .group_by(models.Cancion.titulo, models.Cancion.youtube_id)
        .order_by(func.count(models.Cancion.id).desc())
        .limit(limit)
        .all()
    )

def delete_cancion(db: Session, cancion_id: int):
    """Elimina una canción de la base de datos por su ID."""
    db_cancion = db.query(models.Cancion).filter(models.Cancion.id == cancion_id).first()
    if db_cancion:
        db.delete(db_cancion)
        db.commit()

def get_productos_mas_consumidos(db: Session, limit: int = 10):
    """
    Obtiene un reporte de los productos más consumidos, agrupados y sumada su cantidad.
    """
    return (
        db.query(
            models.Consumo.producto,
            func.sum(models.Consumo.cantidad).label("cantidad_total"),
        )
        .group_by(models.Consumo.producto)
        .order_by(func.sum(models.Consumo.cantidad).desc())
        .limit(limit)
        .all()
    )

def get_total_ingresos(db: Session):
    """Calcula la suma total de todos los consumos de la noche."""
    total = db.query(func.sum(models.Consumo.valor)).scalar()
    return total or 0

def get_ingresos_por_mesa(db: Session):
    """
    Calcula los ingresos totales agrupados por cada mesa.
    """
    return (
        db.query(
            models.Mesa.nombre,
            func.sum(models.Consumo.valor).label("ingresos_totales")
        )
        .join(models.Usuario, models.Mesa.id == models.Usuario.mesa_id)
        .join(models.Consumo, models.Usuario.id == models.Consumo.usuario_id)
        .group_by(models.Mesa.nombre)
        .order_by(func.sum(models.Consumo.valor).desc())
        .all()
    )

def reordenar_cola_manual(db: Session, canciones_ids: List[int]):
    """
    Actualiza el orden manual de las canciones en la cola.
    """
    # Primero, reseteamos el orden manual de todas las canciones aprobadas
    db.query(models.Cancion).filter(models.Cancion.estado == 'aprobado').update({"orden_manual": None})
    
    # Luego, asignamos el nuevo orden
    for i, cancion_id in enumerate(canciones_ids):
        db.query(models.Cancion).filter(models.Cancion.id == cancion_id).update({"orden_manual": i + 1})
    
    db.commit()