from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_
from sqlalchemy.orm import joinedload # Importar joinedload
import secrets
from typing import List, Optional
import datetime
import models, schemas
from decimal import Decimal # Importar Decimal

def get_mesa_by_qr(db: Session, qr_code: str):
    """Busca una mesa por su código QR."""
    return db.query(models.Mesa).filter(models.Mesa.qr_code == qr_code).first()

def get_mesas(db: Session):
    """Devuelve todas las mesas de la base de datos."""
    return db.query(models.Mesa).order_by(models.Mesa.id).all()

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

def get_usuario_by_nick(db: Session, nick: str):
    """Busca un usuario por su nick (case-insensitive)."""
    return db.query(models.Usuario).filter(func.lower(models.Usuario.nick) == func.lower(nick)).first()

def get_total_consumido_por_usuario(db: Session, usuario_id: int):
    """Calcula el total consumido por un usuario."""
    return db.query(func.sum(models.Consumo.valor_total)).filter(models.Consumo.usuario_id == usuario_id).scalar() or 0

def get_canciones_por_usuario(db: Session, usuario_id: int):
    """Busca todas las canciones de un usuario específico."""
    return db.query(models.Cancion).filter(models.Cancion.usuario_id == usuario_id).order_by(models.Cancion.created_at.desc()).all()

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
    3. Orden manual establecido por el administrador.
    """
    hora_limite = datetime.datetime.utcnow() - datetime.timedelta(hours=1)

    # Subconsulta única para obtener estadísticas de consumo por usuario
    user_consumption_stats_subq = (
        db.query(
            models.Usuario.id.label("usuario_id"),
            func.sum(models.Consumo.valor_total).label("total_consumido"),
            func.max(models.Consumo.created_at).label("ultimo_consumo_ts"),
        )
        .join(models.Consumo, models.Usuario.id == models.Consumo.usuario_id)
        .group_by(models.Usuario.id)
        .subquery()
    )

    # Expresión 'case' para determinar la prioridad de actividad del usuario
    prioridad_actividad = case((user_consumption_stats_subq.c.ultimo_consumo_ts > hora_limite, 1), else_=0).label("prioridad_actividad")

    # Consulta principal que une canciones con el consumo del usuario
    return (
        db.query(models.Cancion)
        .join(models.Usuario, models.Cancion.usuario_id == models.Usuario.id)
        .outerjoin(user_consumption_stats_subq, models.Usuario.id == user_consumption_stats_subq.c.usuario_id)
        .filter(models.Cancion.estado == "aprobado")
        .order_by(models.Cancion.orden_manual.asc().nulls_last(), prioridad_actividad.desc(), func.coalesce(user_consumption_stats_subq.c.total_consumido, 0).desc(), models.Cancion.id.asc())
        .all()
    )

def get_producto_by_nombre(db: Session, nombre: str):
    """Busca un producto por su nombre."""
    return db.query(models.Producto).filter(models.Producto.nombre == nombre).first()

def get_productos(db: Session, skip: int = 0, limit: int = 100):
    """Obtiene una lista de todos los productos del catálogo."""
    return db.query(models.Producto).offset(skip).limit(limit).all()

def create_producto(db: Session, producto: schemas.ProductoCreate):
    """Crea un nuevo producto en el catálogo."""
    # Aseguramos que el producto se cree como activo por defecto.
    producto_data = producto.dict()
    # El schema ProductoCreate ya tiene `is_active` con un valor por defecto.
    # Al pasarlo directamente, evitamos el error de "multiple values for keyword argument".
    # Si el schema no lo tuviera, podríamos hacer `producto_data.pop('is_active', None)`
    # antes de pasarlo como argumento extra.
    db_producto = models.Producto(**producto_data)
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

def get_producto_by_id(db: Session, producto_id: int):
    """Busca un producto por su ID."""
    return db.query(models.Producto).filter(models.Producto.id == producto_id).first()

def update_producto_imagen(db: Session, producto_id: int, imagen_url: str):
    """Actualiza solo la URL de la imagen de un producto."""
    db_producto = get_producto_by_id(db, producto_id)
    if db_producto:
        db_producto.imagen_url = imagen_url
        db.commit()
        db.refresh(db_producto)
    return db_producto

def create_consumo_para_usuario(db: Session, consumo: schemas.ConsumoCreate, usuario_id: int):
    """Crea un nuevo consumo, lo asocia a un usuario y actualiza su nivel."""
    # Definimos los umbrales para cada nivel
    SILVER_THRESHOLD = 50.0
    GOLD_THRESHOLD = 150.0

    # 1. Obtener el producto del catálogo para saber su precio
    db_producto = db.query(models.Producto).filter(models.Producto.id == consumo.producto_id).first()
    if not db_producto:
        return None, "Producto no encontrado en el catálogo."

    if db_producto.stock < consumo.cantidad:
        return None, f"No hay suficiente stock para '{db_producto.nombre}'. Disponible: {db_producto.stock}"

    if consumo.cantidad <= 0:
        return None, "La cantidad debe ser mayor que cero."

    if not db_producto.is_active:
        return None, "El producto no está disponible actualmente."

    # 2. Calcular el valor total de la transacción
    valor_total_transaccion = db_producto.valor * consumo.cantidad

    # 3. Crear el registro de consumo
    db_consumo = models.Consumo(
        producto_id=consumo.producto_id,
        cantidad=consumo.cantidad,
        valor_total=valor_total_transaccion,
        usuario_id=usuario_id
    )

    # Obtenemos el usuario para poder actualizarlo
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_usuario:
        db.rollback()
        return None, "Usuario no encontrado."

    # 5. Descontar del stock
    db_producto.stock -= consumo.cantidad

    # 6. Otorgar puntos al usuario (ej: 1 punto por cada 10 de moneda gastados)
    db_usuario.puntos += int(valor_total_transaccion / 10)

    db.add(db_consumo)
    db.commit()
    db.refresh(db_consumo)

    # 4. Actualizar el nivel del usuario
    total_consumido = db.query(func.sum(models.Consumo.valor_total)).filter(models.Consumo.usuario_id == usuario_id).scalar() or 0

    if total_consumido >= GOLD_THRESHOLD:
        db_usuario.nivel = "oro"
    elif total_consumido >= SILVER_THRESHOLD:
        db_usuario.nivel = "plata"

    db.commit()
    db.refresh(db_usuario)
    return db_consumo, None

def create_pedido_from_carrito(db: Session, carrito: schemas.CarritoCreate, usuario_id: int):
    """
    Crea múltiples registros de consumo a partir de un carrito de compras.
    Toda la operación se maneja como una única transacción.
    """
    SILVER_THRESHOLD = 50.0
    GOLD_THRESHOLD = 150.0

    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_usuario:
        return None, "Usuario no encontrado."

    consumos_creados = []
    valor_total_pedido = Decimal(0)

    try:
        # Iteramos sobre una copia para poder modificarla si es necesario
        for item in carrito.items:
            if item.cantidad <= 0:
                raise ValueError("La cantidad de cada producto debe ser mayor que cero.")

            db_producto = db.query(models.Producto).filter(models.Producto.id == item.producto_id).first()
            if not db_producto:
                raise ValueError(f"Producto con ID {item.producto_id} no encontrado.")
            if not db_producto.is_active:
                raise ValueError(f"El producto '{db_producto.nombre}' no está disponible.")
            if db_producto.stock < item.cantidad:
                raise ValueError(f"No hay stock suficiente para '{db_producto.nombre}'. Disponible: {db_producto.stock}.")

            # Calculamos el valor de esta línea del pedido
            valor_linea = db_producto.valor * item.cantidad
            valor_total_pedido += valor_linea

            # Creamos el objeto Consumo pero aún no lo guardamos (sin db.add o db.commit)
            db_consumo = models.Consumo(
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                valor_total=valor_linea,
                usuario_id=usuario_id
            )
            db.add(db_consumo)
            consumos_creados.append(db_consumo)

            # Descontamos el stock
            db_producto.stock -= item.cantidad

        # Si todo fue bien, actualizamos los puntos y el nivel del usuario
        db_usuario.puntos += int(valor_total_pedido / 10)
        total_consumido_historico = (db.query(func.sum(models.Consumo.valor_total)).filter(models.Consumo.usuario_id == usuario_id).scalar() or 0) + valor_total_pedido

        if total_consumido_historico >= GOLD_THRESHOLD:
            db_usuario.nivel = "oro"
        elif total_consumido_historico >= SILVER_THRESHOLD:
            db_usuario.nivel = "plata"

        db.commit() # Guardamos todos los cambios a la vez
        for consumo in consumos_creados:
            db.refresh(consumo)
        return consumos_creados, None
    except ValueError as e:
        db.rollback() # Si algo falla, revertimos TODOS los cambios de esta transacción
        return None, str(e)

def marcar_cancion_actual_como_cantada(db: Session):
    """
    Busca la canción que se está reproduciendo, la marca como 'cantada' y le da puntos al usuario.
    Simula una puntuación de IA.
    """
    import os
    import ia_scorer # Importamos nuestro nuevo módulo de IA

    # 1. Buscar la canción que está actualmente en estado 'reproduciendo'
    cancion_actual = db.query(models.Cancion).filter(models.Cancion.estado == "reproduciendo").first()
    
    if not cancion_actual:
        return None  # No hay ninguna canción reproduciéndose
    
    # --- INICIO DE LA INTEGRACIÓN CON IA ---
    # 2. Calcular el puntaje usando el módulo de IA.
    #    Asumimos que el audio del usuario se sube a una carpeta temporal con el ID de la canción.
    #    Este es un paso que el frontend deberá implementar en el futuro.
    user_audio_path = os.path.join(ia_scorer.TEMP_DIR, f"user_recording_{cancion_actual.id}.wav")
    
    if os.path.exists(user_audio_path):
        puntuacion = ia_scorer.calculate_score(cancion_actual.youtube_id, user_audio_path)
        # Opcional: eliminar el audio del usuario después de procesarlo
        # os.remove(user_audio_path)
    else:
        # Si no se subió audio, la puntuación es 0.
        puntuacion = 0
    # --- FIN DE LA INTEGRACIÓN CON IA ---
    
    cancion_actual.puntuacion_ia = puntuacion

    # 3. Actualizar el estado de la canción a 'cantada'
    cancion_actual.estado = "cantada"
    cancion_actual.finished_at = datetime.datetime.utcnow()

    # 4. Dar puntos al usuario por cantar (puntos base + puntaje de IA)
    if cancion_actual.usuario:
        cancion_actual.usuario.puntos += (10 + puntuacion) # 10 puntos base + el puntaje de la IA

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
            func.sum(models.Consumo.valor_total).label("total_consumido"),
        )
        .group_by(models.Consumo.usuario_id)
        .subquery()
    )

    # Consulta principal que une usuarios con su consumo total y ordena
    return db.query(models.Usuario, func.coalesce(consumo_total_subq.c.total_consumido, 0).label("total_consumido_calc")).outerjoin(consumo_total_subq, models.Usuario.id == consumo_total_subq.c.usuario_id).order_by(func.coalesce(consumo_total_subq.c.total_consumido, 0).desc()).all()

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
            models.Producto.nombre,
            func.sum(models.Consumo.cantidad).label("cantidad_total"),
        )
        .join(models.Producto, models.Consumo.producto_id == models.Producto.id)
        .group_by(models.Producto.nombre)
        .order_by(func.sum(models.Consumo.cantidad).desc())
        .limit(limit)
        .all()
    )

def delete_producto(db: Session, producto_id: int):
    """Elimina un producto de la base de datos por su ID."""
    db_producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if db_producto:
        # Opcional: verificar si tiene consumos asociados antes de borrar
        db.delete(db_producto)
        db.commit()
        return db_producto
    return None

def get_total_ingresos(db: Session):
    """Calcula la suma total de todos los consumos de la noche."""
    total = db.query(func.sum(models.Consumo.valor_total)).scalar()
    return total or 0

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

def get_usuarios_sin_consumo(db: Session):
    """
    Obtiene una lista de todos los usuarios que no han realizado ningún consumo.
    """
    return (
        db.query(models.Usuario)
        .outerjoin(models.Consumo)
        .group_by(models.Usuario.id)
        .having(func.count(models.Consumo.id) == 0)
        .all()
    )

def get_mesa_by_id(db: Session, mesa_id: int):
    """Busca una mesa por su ID."""
    return db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()

def delete_mesa(db: Session, mesa_id: int):
    """Elimina una mesa de la base de datos por su ID."""
    db_mesa = db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()
    if db_mesa:
        db.delete(db_mesa)
        db.commit()

def move_song_to_top(db: Session, cancion_id: int):
    """
    Mueve una canción específica al principio de la cola manual.
    """
    # 1. Validar que la canción existe y está aprobada
    cancion_a_mover = db.query(models.Cancion).filter(
        models.Cancion.id == cancion_id,
        models.Cancion.estado == 'aprobado'
    ).first()

    if not cancion_a_mover:
        return None

    # 2. Encontrar el valor de orden manual más bajo actual
    min_orden = db.query(func.min(models.Cancion.orden_manual)).scalar()

    nuevo_orden = 1
    if min_orden is not None:
        nuevo_orden = min_orden - 1
    
    # 3. Asignar el nuevo orden a la canción
    cancion_a_mover.orden_manual = nuevo_orden
    db.commit()
    db.refresh(cancion_a_mover)
    return cancion_a_mover

def get_canciones_cantadas_por_usuario(db: Session):
    """
    Obtiene un reporte de la cantidad de canciones cantadas por cada usuario.
    """
    return (
        db.query(
            models.Usuario.nick,
            func.count(models.Cancion.id).label("canciones_cantadas"),
        )
        .join(models.Cancion, models.Usuario.id == models.Cancion.usuario_id)
        .filter(models.Cancion.estado == "cantada")
        .group_by(models.Usuario.nick)
        .order_by(func.count(models.Cancion.id).desc())
        .all()
    )

def update_usuario_nick(db: Session, usuario_id: int, nuevo_nick: str):
    """
    Actualiza el nick de un usuario específico.
    """
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if db_usuario:
        db_usuario.nick = nuevo_nick
        db.commit()
        db.refresh(db_usuario)
    return db_usuario

def get_ingresos_promedio_por_usuario(db: Session):
    """
    Calcula los ingresos promedio por cada usuario que ha consumido.
    """
    # Calcular ingresos totales
    total_ingresos = db.query(func.sum(models.Consumo.valor_total)).scalar() or 0

    # Contar el número de usuarios únicos con consumo
    usuarios_con_consumo = db.query(models.Consumo.usuario_id).distinct().count()

    if usuarios_con_consumo == 0:
        return 0

    return total_ingresos / usuarios_con_consumo

def update_usuario_mesa(db: Session, usuario_id: int, nueva_mesa_id: int):
    """
    Actualiza la mesa de un usuario específico.
    """
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if db_usuario:
        db_usuario.mesa_id = nueva_mesa_id
        db.commit()
        db.refresh(db_usuario)
    return db_usuario

def get_usuarios_una_cancion(db: Session):
    """
    Obtiene una lista de usuarios que han cantado exactamente una canción.
    """
    return (
        db.query(models.Usuario)
        .join(models.Cancion, models.Usuario.id == models.Cancion.usuario_id)
        .filter(models.Cancion.estado == "cantada")
        .group_by(models.Usuario.id)
        .having(func.count(models.Cancion.id) == 1)
        .all()
    )

def add_puntos_a_usuario(db: Session, usuario_id: int, puntos_a_anadir: int):
    """
    Añade una cantidad de puntos a un usuario específico.
    """
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if db_usuario:
        db_usuario.puntos += puntos_a_anadir
        db.commit()
        db.refresh(db_usuario)
    return db_usuario

def get_mesas_vacias(db: Session):
    """
    Obtiene una lista de todas las mesas que no tienen usuarios conectados.
    """
    return (
        db.query(models.Mesa)
        .outerjoin(models.Usuario)
        .group_by(models.Mesa.id)
        .having(func.count(models.Usuario.id) == 0)
        .all()
    )

def delete_usuario(db: Session, usuario_id: int):
    """
    Elimina un usuario y todos sus datos asociados (canciones, consumos).
    """
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_usuario:
        return None

    # Borrar datos dependientes primero para evitar errores de clave foránea
    db.query(models.Consumo).filter(models.Consumo.usuario_id == usuario_id).delete(synchronize_session=False)
    db.query(models.Cancion).filter(models.Cancion.usuario_id == usuario_id).delete(synchronize_session=False)

    # Finalmente, borrar el usuario
    db.delete(db_usuario)
    db.commit()
    return db_usuario

def get_ingresos_promedio_por_usuario_por_mesa(db: Session):
    """
    Calcula los ingresos promedio por usuario para cada mesa.
    """
    # Consulta que calcula el total consumido y el número de usuarios únicos por mesa
    return (
        db.query(
            models.Mesa.nombre,
            (
                func.coalesce(func.sum(models.Consumo.valor_total), 0) / 
                func.greatest(func.count(func.distinct(models.Usuario.id)), 1)
            ).label("ingresos_promedio")
        )
        .select_from(models.Mesa)
        .outerjoin(models.Usuario, models.Mesa.id == models.Usuario.mesa_id)
        .outerjoin(models.Consumo, models.Usuario.id == models.Consumo.usuario_id)
        .group_by(models.Mesa.nombre)
        .order_by(func.coalesce(func.sum(models.Consumo.valor_total), 0).desc())
        .all()
    )

def is_nick_banned(db: Session, nick: str):
    """Verifica si un nick está en la lista de baneados (case-insensitive)."""
    return db.query(models.BannedNick).filter(models.BannedNick.nick.ilike(nick)).first() is not None

def ban_usuario(db: Session, usuario_id: int):
    """
    Banea a un usuario: añade su nick a la lista de baneados y luego lo elimina.
    """
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_usuario:
        return None

    # 1. Añadir el nick a la lista de baneados si no existe
    nick_baneado_existente = db.query(models.BannedNick).filter(models.BannedNick.nick.ilike(db_usuario.nick)).first()
    if not nick_baneado_existente:
        banned_nick_entry = models.BannedNick(nick=db_usuario.nick)
        db.add(banned_nick_entry)
        # Hacemos un commit intermedio para asegurar que el nick baneado se guarde
        # antes de proceder con el borrado del usuario.
        db.commit()

    # 2. Eliminar al usuario y sus datos asociados (reutilizamos la función existente)
    delete_usuario(db, usuario_id=usuario_id)

    return db_usuario

def get_tiempo_promedio_espera(db: Session):
    """
    Calcula el tiempo promedio en segundos desde que una canción se añade hasta que se canta.
    """
    # Para SQLite, usamos julianday para calcular la diferencia en días y luego convertimos a segundos.
    # Para PostgreSQL, sería: func.avg(func.extract('epoch', models.Cancion.finished_at - models.Cancion.created_at))
    avg_seconds = db.query(func.avg((func.julianday(models.Cancion.finished_at) - func.julianday(models.Cancion.created_at)) * 86400)).filter(
        models.Cancion.estado == "cantada",
        models.Cancion.finished_at.isnot(None)
    ).scalar()
    return avg_seconds or 0

def get_actividad_por_hora(db: Session):
    """
    Obtiene un reporte de la cantidad de canciones cantadas por cada hora del día.
    """
    return (
        db.query(
            # Usamos strftime para SQLite para extraer la hora.
            # Para PostgreSQL sería: extract('hour', models.Cancion.started_at)
            func.strftime('%H', models.Cancion.started_at).label("hora"),
            func.count(models.Cancion.id).label("canciones_cantadas"),
        )
        .filter(models.Cancion.estado == "cantada", models.Cancion.started_at.isnot(None))
        .group_by(func.strftime('%H', models.Cancion.started_at))
        .order_by(func.count(models.Cancion.id).desc())
        .all()
    )

def get_canciones_cantadas_por_mesa(db: Session):
    """
    Obtiene un reporte de la cantidad de canciones cantadas por cada mesa.
    """
    return (
        db.query(
            models.Mesa.nombre,
            func.count(models.Cancion.id).label("canciones_cantadas"),
        )
        .join(models.Usuario, models.Mesa.id == models.Usuario.mesa_id)
        .join(models.Cancion, models.Usuario.id == models.Cancion.usuario_id)
        .filter(models.Cancion.estado == "cantada")
        .group_by(models.Mesa.nombre)
        .order_by(func.count(models.Cancion.id).desc())
        .all()
    )

def set_usuario_silenciado(db: Session, usuario_id: int, silenciar: bool):
    """
    Actualiza el estado 'silenciado' de un usuario.
    """
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if db_usuario:
        db_usuario.is_silenced = silenciar
        db.commit()
        db.refresh(db_usuario)
    return db_usuario

def unban_nick(db: Session, nick: str):
    """
    Elimina un nick de la lista de baneados para permitir que se vuelva a registrar.
    """
    banned_nick_entry = db.query(models.BannedNick).filter(models.BannedNick.nick.ilike(nick)).first()
    if banned_nick_entry:
        db.delete(banned_nick_entry)
        db.commit()
    return banned_nick_entry

def get_banned_nicks(db: Session):
    """
    Obtiene una lista de todos los nicks baneados.
    """
    return db.query(models.BannedNick).order_by(models.BannedNick.banned_at.desc()).all()

def get_canciones_mas_rechazadas(db: Session, limit: int = 10):
    """
    Obtiene un reporte de las canciones más rechazadas, agrupadas y contadas.
    """
    return (
        db.query(
            models.Cancion.titulo,
            models.Cancion.youtube_id,
            func.count(models.Cancion.id).label("veces_rechazada"),
        )
        .filter(models.Cancion.estado == "rechazada")
        .group_by(models.Cancion.titulo, models.Cancion.youtube_id)
        .order_by(func.count(models.Cancion.id).desc())
        .limit(limit)
        .all()
    )

def get_usuarios_mas_rechazados(db: Session, limit: int = 10):
    """
    Obtiene un reporte de los usuarios a los que más se les han rechazado canciones.
    """
    return (
        db.query(
            models.Usuario.nick,
            func.count(models.Cancion.id).label("canciones_rechazadas"),
        )
        .join(models.Cancion, models.Usuario.id == models.Cancion.usuario_id)
        .filter(models.Cancion.estado == "rechazada")
        .group_by(models.Usuario.nick)
        .order_by(func.count(models.Cancion.id).desc())
        .limit(limit)
        .all()
    )

def get_ingresos_por_categoria(db: Session):
    """
    Calcula los ingresos totales agrupados por cada categoría de producto.
    """
    return (
        db.query(
            models.Producto.categoria,
            func.sum(models.Consumo.valor_total).label("ingresos_totales")
        )
        .join(models.Producto, models.Consumo.producto_id == models.Producto.id)
        .group_by(models.Producto.categoria)
        .order_by(func.sum(models.Consumo.valor_total).desc())
        .all()
    )

def create_admin_log_entry(db: Session, action: str, details: Optional[str] = None):
    """Crea una nueva entrada en el log de administración."""
    log_entry = models.AdminLog(action=action, details=details)
    db.add(log_entry)
    db.commit()
    return log_entry

def get_admin_logs(db: Session, limit: int = 100):
    """Obtiene las últimas entradas del log de administración."""
    return db.query(models.AdminLog).order_by(models.AdminLog.timestamp.desc()).limit(limit).all()

def get_productos_menos_consumidos(db: Session, limit: int = 5):
    """
    Obtiene un reporte de los productos menos consumidos, agrupados y sumada su cantidad.
    """
    return (
        db.query(
            models.Producto.nombre,
            func.sum(models.Consumo.cantidad).label("cantidad_total"),
        )
        .join(models.Producto, models.Consumo.producto_id == models.Producto.id)
        .group_by(models.Producto.nombre)
        .order_by(func.sum(models.Consumo.cantidad).asc())  # Orden ascendente
        .limit(limit)
        .all()
    )

def get_productos_no_consumidos(db: Session):
    """
    Obtiene una lista de productos del catálogo que nunca han sido consumidos.
    """
    return (
        db.query(models.Producto)
        .outerjoin(models.Consumo)
        .group_by(models.Producto.id)
        .having(func.count(models.Consumo.id) == 0)
        .all()
    )

def update_producto(db: Session, producto_id: int, producto_update: schemas.ProductoCreate):
    """
    Actualiza los datos de un producto específico.
    """
    db_producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if db_producto:
        for key, value in producto_update.dict().items():
            setattr(db_producto, key, value)
        db.commit()
        db.refresh(db_producto)
    return db_producto

def update_producto_valor(db: Session, producto_id: int, nuevo_valor: Decimal):
    """
    Actualiza el valor de un producto específico en el catálogo.
    """
    db_producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if db_producto:
        db_producto.valor = nuevo_valor
        db.commit()
        db.refresh(db_producto)
    return db_producto

def update_producto_active_status(db: Session, producto_id: int, is_active: bool):
    """
    Actualiza el estado de activación de un producto.
    """
    db_producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if db_producto:
        db_producto.is_active = is_active
        db.commit()
        db.refresh(db_producto)
    return db_producto

def get_usuarios_por_nivel(db: Session, nivel: str):
    """
    Obtiene una lista de todos los usuarios que tienen un nivel específico.
    """
    return db.query(models.Usuario).filter(models.Usuario.nivel == nivel).all()

def get_resumen_noche(db: Session):
    """
    Obtiene un resumen de las métricas clave de la noche.
    """
    ingresos_totales = db.query(func.sum(models.Consumo.valor_total)).scalar() or 0
    canciones_cantadas = db.query(func.count(models.Cancion.id)).filter(models.Cancion.estado == "cantada").scalar() or 0
    usuarios_activos = db.query(func.count(models.Usuario.id)).scalar() or 0
    return {
        "ingresos_totales": ingresos_totales,
        "canciones_cantadas": canciones_cantadas,
        "usuarios_activos": usuarios_activos,
    }

def get_resumen_mesa(db: Session, mesa_id: int):
    """
    Obtiene un resumen detallado de una mesa específica, incluyendo usuarios,
    consumo total y canciones pendientes/reproduciéndose.
    """
    db_mesa = db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()
    if not db_mesa:
        return None

    # Usuarios en la mesa
    usuarios_mesa = db.query(models.Usuario).filter(models.Usuario.mesa_id == mesa_id).all()

    # Consumo total de la mesa
    consumo_total_mesa = (
        db.query(func.sum(models.Consumo.valor_total))
        .join(models.Usuario)
        .filter(models.Usuario.mesa_id == mesa_id)
        .scalar() or 0
    )

    # Canciones pendientes y reproduciendo de la mesa
    canciones_mesa = (
        db.query(models.Cancion)
        .join(models.Usuario)
        .filter(models.Usuario.mesa_id == mesa_id, models.Cancion.estado.in_(['pendiente', 'aprobado', 'reproduciendo']))
        .all()
    )
    canciones_pendientes = [c for c in canciones_mesa if c.estado in ['pendiente', 'aprobado']]
    cancion_reproduciendo = next((c for c in canciones_mesa if c.estado == 'reproduciendo'), None)

    return {
        "mesa_nombre": db_mesa.nombre,
        "usuarios": usuarios_mesa,
        "consumo_total_mesa": consumo_total_mesa,
        "canciones_pendientes_mesa": canciones_pendientes,
        "canciones_reproduciendo_mesa": cancion_reproduciendo,
    }

def get_usuarios_sin_canciones_cantadas(db: Session):
    """
    Obtiene una lista de usuarios que no han cantado ninguna canción.
    """
    # Subconsulta para obtener los IDs de los usuarios que SÍ han cantado.
    subquery = db.query(models.Usuario.id).join(models.Cancion).filter(models.Cancion.estado == 'cantada').distinct()

    # Consulta principal para obtener los usuarios cuyo ID NO ESTÁ en la subconsulta.
    return db.query(models.Usuario).filter(models.Usuario.id.notin_(subquery)).all()

def get_estado_mesas(db: Session):
    """
    Obtiene un listado de todas las mesas con su estado (ocupada/vacía),
    número de usuarios y consumo total.
    """
    # Subconsulta para el conteo de usuarios por mesa
    user_count_subq = (
        db.query(
            models.Mesa.id.label("mesa_id"),
            func.count(models.Usuario.id).label("user_count")
        )
        .outerjoin(models.Usuario)
        .group_by(models.Mesa.id)
        .subquery()
    )

    # Subconsulta para el consumo total por mesa
    consumo_total_subq = (
        db.query(
            models.Mesa.id.label("mesa_id"),
            func.sum(models.Consumo.valor_total).label("total_consumido")
        )
        .outerjoin(models.Usuario).outerjoin(models.Consumo)
        .group_by(models.Mesa.id)
        .subquery()
    )

    # Consulta principal que une los datos
    return db.query(
        models.Mesa,
        func.coalesce(user_count_subq.c.user_count, 0),
        func.coalesce(consumo_total_subq.c.total_consumido, 0)
    ).outerjoin(user_count_subq, models.Mesa.id == user_count_subq.c.mesa_id).outerjoin(consumo_total_subq, models.Mesa.id == consumo_total_subq.c.mesa_id).order_by(models.Mesa.nombre).all()

def get_ranking_puntos_usuarios(db: Session, limit: int = 10):
    """
    Obtiene un ranking de usuarios ordenado por la cantidad de puntos acumulados.
    """
    return (
        db.query(models.Usuario)
        .order_by(models.Usuario.puntos.desc())
        .limit(limit)
        .all()
    )

def get_usuarios_cantan_pero_no_consumen(db: Session):
    """
    Obtiene una lista de usuarios que han cantado al menos una canción
    pero no han realizado ningún consumo.
    """
    # Subconsulta para obtener los IDs de los usuarios que SÍ han cantado.
    subquery_cantan = db.query(models.Cancion.usuario_id).filter(models.Cancion.estado == 'cantada').distinct()

    # Subconsulta para obtener los IDs de los usuarios que SÍ han consumido.
    subquery_consumen = db.query(models.Consumo.usuario_id).distinct()

    # Consulta principal para obtener los usuarios que están en la primera subconsulta pero NO en la segunda.
    return db.query(models.Usuario).filter(
        models.Usuario.id.in_(subquery_cantan),
        models.Usuario.id.notin_(subquery_consumen)
    ).all()

def get_consumos_por_usuario(db: Session, usuario_id: int):
    """
    Obtiene el historial de consumo de un usuario específico.
    """
    return db.query(models.Consumo).filter(models.Consumo.usuario_id == usuario_id).order_by(models.Consumo.created_at.desc()).all()


def get_recent_consumos(db: Session, limit: int = 10):
    """
    Devuelve los consumos más recientes junto con el nombre del producto,
    nick del usuario y nombre de la mesa (si existe).
    """
    # Hacemos las uniones necesarias para obtener la info deseada
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
        .order_by(models.Consumo.created_at.desc())
        .limit(limit)
        .all()
    )

    # Mapear a diccionarios/objetos que Pydantic pueda serializar fácilmente
    result = []
    for r in rows:
        result.append({
            'id': r.id,
            'cantidad': r.cantidad,
            'valor_total': r.valor_total,
            'producto_nombre': r.producto_nombre,
            'usuario_nick': r.usuario_nick,
            'mesa_nombre': r.mesa_nombre,
            'created_at': r.created_at,
        })
    return result

def get_usuarios_mayor_gasto_por_categoria(db: Session, categoria: str, limit: int = 10):
    """
    Obtiene un reporte de los usuarios que más han gastado en una categoría de producto específica.
    """
    return (
        db.query(
            models.Usuario.nick,
            func.sum(models.Consumo.valor_total).label("total_gastado")
        )
        .join(models.Consumo, models.Usuario.id == models.Consumo.usuario_id)
        .join(models.Producto, models.Consumo.producto_id == models.Producto.id)
        .filter(models.Producto.categoria.ilike(categoria))
        .group_by(models.Usuario.nick)
        .order_by(func.sum(models.Consumo.valor_total).desc())
        .limit(limit)
        .all()
    )

def get_productos_mas_consumidos_por_mesa(db: Session, mesa_id: int, limit: int = 5):
    """
    Obtiene un reporte de los productos más consumidos en una mesa específica.
    """
    return (
        db.query(
            models.Producto.nombre,
            func.sum(models.Consumo.cantidad).label("cantidad_total"),
        )
        .join(models.Consumo, models.Producto.id == models.Consumo.producto_id)
        .join(models.Usuario, models.Consumo.usuario_id == models.Usuario.id)
        .filter(models.Usuario.mesa_id == mesa_id)
        .group_by(models.Producto.nombre)
        .order_by(func.sum(models.Consumo.cantidad).desc())
        .limit(limit)
        .all()
    )

def get_usuarios_oro_activos(db: Session):
    """
    Obtiene una lista de usuarios de nivel "Oro" que han cantado más de 5 canciones.
    """
    return (
        db.query(models.Usuario)
        .join(models.Cancion, models.Usuario.id == models.Cancion.usuario_id)
        .filter(
            models.Usuario.nivel == "oro",
            models.Cancion.estado == "cantada"
        )
        .group_by(models.Usuario.id)
        .having(func.count(models.Cancion.id) > 5)
        .all()
    )

def get_canciones_mas_pedidas_por_mesa(db: Session, mesa_id: int, limit: int = 5):
    """
    Obtiene un reporte de las canciones más pedidas en una mesa específica.
    """
    return (
        db.query(
            models.Cancion.titulo,
            models.Cancion.youtube_id,
            func.count(models.Cancion.id).label("veces_pedida"),
        )
        .join(models.Usuario, models.Cancion.usuario_id == models.Usuario.id)
        .filter(models.Usuario.mesa_id == mesa_id)
        .group_by(models.Cancion.titulo, models.Cancion.youtube_id)
        .order_by(func.count(models.Cancion.id).desc())
        .limit(limit)
        .all()
    )

def get_usuarios_consumen_pero_no_cantan(db: Session, umbral_consumo: float = 100.0):
    """
    Obtiene una lista de usuarios que han consumido más de un umbral
    pero no han cantado ninguna canción.
    """
    # Subconsulta para obtener los IDs de los usuarios que SÍ han cantado.
    subquery_cantan = db.query(models.Cancion.usuario_id).filter(models.Cancion.estado == 'cantada').distinct()

    # Subconsulta para obtener los IDs de los usuarios que han consumido más del umbral.
    subquery_consumen_mas_de = db.query(models.Usuario.id).join(models.Consumo).group_by(models.Usuario.id).having(func.sum(models.Consumo.valor_total) > umbral_consumo).subquery()

    # Consulta principal para obtener los usuarios que están en la segunda subconsulta pero NO en la primera.
    return db.query(models.Usuario).filter(
        models.Usuario.id.in_(subquery_consumen_mas_de),
        models.Usuario.id.notin_(subquery_cantan)
    ).all()

def get_categorias_mas_consumidas_por_mesa(db: Session, mesa_id: int, limit: int = 5):
    """
    Obtiene un reporte de las categorías de productos más consumidas en una mesa específica.
    """
    return (
        db.query(
            models.Producto.categoria,
            func.sum(models.Consumo.cantidad).label("cantidad_total"),
        )
        .join(models.Consumo, models.Producto.id == models.Consumo.producto_id)
        .join(models.Usuario, models.Consumo.usuario_id == models.Usuario.id)
        .filter(models.Usuario.mesa_id == mesa_id)
        .group_by(models.Producto.categoria)
        .order_by(func.sum(models.Consumo.cantidad).desc())
        .limit(limit)
        .all()
    )

def get_top_consumers_one_song(db: Session, limit: int = 10):
    """
    Obtiene un reporte de los usuarios que más han consumido pero que solo han cantado una canción.
    """
    # Subconsulta para obtener los IDs de los usuarios que han cantado exactamente una canción.
    subquery_una_cancion = (
        db.query(models.Cancion.usuario_id)
        .filter(models.Cancion.estado == 'cantada')
        .group_by(models.Cancion.usuario_id)
        .having(func.count(models.Cancion.id) == 1)
        .subquery()
    )

    # Consulta principal que filtra por esos usuarios y los ordena por consumo
    return (
        db.query(models.Usuario.nick, func.sum(models.Consumo.valor_total).label("total_gastado"))
        .join(models.Consumo, models.Usuario.id == models.Consumo.usuario_id)
        .filter(models.Usuario.id.in_(subquery_una_cancion))
        .group_by(models.Usuario.nick)
        .order_by(func.sum(models.Consumo.valor_total).desc())
        .limit(limit)
        .all()
    )

def get_usuarios_inactivos_consumo(db: Session, horas: int = 2):
    """
    Obtiene una lista de usuarios cuyo último consumo fue hace más de X horas,
    o que no han consumido nada.
    """
    hora_limite = datetime.datetime.utcnow() - datetime.timedelta(hours=horas)

    # Subconsulta para obtener el último consumo de cada usuario
    ultimo_consumo_subq = (
        db.query(
            models.Consumo.usuario_id.label("usuario_id"),
            func.max(models.Consumo.created_at).label("ultimo_consumo_ts"),
        )
        .group_by(models.Consumo.usuario_id)
        .subquery()
    )

    # Consulta principal que une usuarios con su último consumo
    return db.query(models.Usuario).outerjoin(ultimo_consumo_subq, models.Usuario.id == ultimo_consumo_subq.c.usuario_id).filter(
        (ultimo_consumo_subq.c.ultimo_consumo_ts < hora_limite) |
        (ultimo_consumo_subq.c.ultimo_consumo_ts == None)
    ).all()


def get_admin_api_key(db: Session, key: str) -> Optional[models.AdminApiKey]:
    """
    Busca una clave de API de administrador en la base de datos,
    verifica que esté activa y actualiza su último uso.
    """
    db_key = db.query(models.AdminApiKey).filter(
        models.AdminApiKey.key == key,
        models.AdminApiKey.is_active == True
    ).first()

    if db_key:
        db_key.last_used = datetime.datetime.utcnow()
        db.commit()

    return db_key

def get_all_admin_api_keys(db: Session) -> List[models.AdminApiKey]:
    """Obtiene todas las claves de API de administrador de la base de datos."""
    return db.query(models.AdminApiKey).order_by(models.AdminApiKey.created_at.desc()).all()

def create_admin_api_key(db: Session, description: str) -> models.AdminApiKey:
    """Genera y almacena una nueva clave de API de administrador."""
    new_key = secrets.token_urlsafe(32)
    db_key = models.AdminApiKey(key=new_key, description=description)
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key

def delete_admin_api_key(db: Session, key_id: int) -> Optional[models.AdminApiKey]:
    """Elimina una clave de API de administrador por su ID."""
    db_key = db.query(models.AdminApiKey).filter(models.AdminApiKey.id == key_id).first()
    if db_key:
        db.delete(db_key)
        db.commit()
    return db_key


def get_consumo_por_mesa(db: Session, mesa_id: int):
    """
    Obtiene el historial de consumo de una mesa específica.
    """
    return (
        db.query(models.Consumo)
        .join(models.Usuario)
        .filter(models.Usuario.mesa_id == mesa_id)
        .order_by(models.Consumo.created_at.desc())
        .all()
    )


def delete_consumo(db: Session, consumo_id: int):
    """
    Elimina un consumo, restaura el stock del producto asociado y recalcula
    los puntos y nivel del usuario correspondiente.
    Devuelve True si se eliminó, o None si no se encontró.
    """
    SILVER_THRESHOLD = 50.0
    GOLD_THRESHOLD = 150.0

    db_consumo = db.query(models.Consumo).filter(models.Consumo.id == consumo_id).first()
    if not db_consumo:
        return None

    # Restaurar stock del producto
    if db_consumo.producto:
        try:
            db_consumo.producto.stock += db_consumo.cantidad
        except Exception:
            # En casos raros, ignoramos
            pass

    usuario = db_consumo.usuario

    # Borramos el registro de consumo
    db.delete(db_consumo)
    db.commit()

    # Recalcular puntos y nivel del usuario
    if usuario:
        total_consumido = db.query(func.sum(models.Consumo.valor_total)).filter(models.Consumo.usuario_id == usuario.id).scalar() or 0
        usuario.puntos = int(total_consumido / 10)
        if total_consumido >= GOLD_THRESHOLD:
            usuario.nivel = 'oro'
        elif total_consumido >= SILVER_THRESHOLD:
            usuario.nivel = 'plata'
        else:
            usuario.nivel = 'bronce'
        db.commit()

    return True

def get_config(db: Session, key: str):
    """Obtiene un valor de configuración por su clave."""
    return db.query(models.Config).filter(models.Config.key == key).first()

def update_config(db: Session, key: str, value: str):
    """Establece o actualiza un valor de configuración."""
    db_config = db.query(models.Config).filter(models.Config.key == key).first()
    if db_config:
        db_config.value = value
    else:
        db_config = models.Config(key=key, value=value)
        db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

def get_or_create_dj_user(db: Session) -> models.Usuario:
    """
    Busca al usuario 'DJ'. Si no existe, lo crea sin asociarlo a una mesa.
    Este usuario se usa para las canciones añadidas por el administrador.
    """
    dj_user = db.query(models.Usuario).filter(models.Usuario.nick == "DJ").first()
    if not dj_user:
        dj_user = models.Usuario(nick="DJ", mesa_id=None) # No pertenece a ninguna mesa
        db.add(dj_user)
        db.commit()
        db.refresh(dj_user)
    return dj_user

def get_cola_completa(db: Session):
    """
    Obtiene la cola completa, incluyendo la canción que está sonando y las próximas.
    """
    now_playing = db.query(models.Cancion).filter(models.Cancion.estado == "reproduciendo").first()
    upcoming = get_cola_priorizada(db)

    # Si la canción que se está reproduciendo sigue en la lista de 'upcoming', la quitamos.
    if now_playing:
        upcoming = [song for song in upcoming if song.id != now_playing.id]

    return {"now_playing": now_playing, "upcoming": upcoming}

def set_mesa_active_status(db: Session, mesa_id: int, is_active: bool) -> Optional[models.Mesa]:
    """
    Actualiza el estado de activación de una mesa.
    """
    db_mesa = db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()
    if db_mesa:
        db_mesa.is_active = is_active
        db.commit()
        db.refresh(db_mesa)
    return db_mesa

def get_all_tables_consumption_summaries(db: Session) -> List[dict]:
    """
    Obtiene un resumen detallado del consumo para todas las mesas,
    incluyendo el valor total y los productos consumidos.
    """
    # Obtener todas las mesas
    mesas = db.query(models.Mesa).order_by(models.Mesa.nombre).all()
    
    results = []
    for mesa in mesas:
        # Calcular el consumo total para esta mesa
        total_consumido = (
            db.query(func.sum(models.Consumo.valor_total))
            .join(models.Usuario, models.Consumo.usuario_id == models.Usuario.id)
            .filter(models.Usuario.mesa_id == mesa.id)
            .scalar() or Decimal('0.00')
        )
        
        # Obtener los detalles de cada consumo para esta mesa
        consumos_detalle = (
            db.query(
                models.Producto.nombre.label('producto_nombre'),
                models.Consumo.cantidad,
                models.Consumo.valor_total,
                models.Consumo.created_at
            )
            .join(models.Producto, models.Consumo.producto_id == models.Producto.id)
            .join(models.Usuario, models.Consumo.usuario_id == models.Usuario.id)
            .filter(models.Usuario.mesa_id == mesa.id)
            .order_by(models.Consumo.created_at.desc())
            .all()
        )
        
        results.append({
            "mesa_id": mesa.id,
            "mesa_nombre": mesa.nombre,
            "total_consumido": total_consumido,
            "consumos": [
                {"producto_nombre": c.producto_nombre, "cantidad": c.cantidad, "valor_total": c.valor_total, "created_at": c.created_at}
                for c in consumos_detalle
            ]
        })
        
    return results

def create_pago_for_mesa(db: Session, pago: schemas.PagoCreate) -> models.Pago:
    """
    Registra un nuevo pago para una mesa específica.
    """
    db_mesa = get_mesa_by_id(db, mesa_id=pago.mesa_id)
    if not db_mesa:
        return None

    db_pago = models.Pago(
        monto=pago.monto,
        metodo_pago=pago.metodo_pago,
        mesa_id=pago.mesa_id
    )
    db.add(db_pago)
    db.commit()
    db.refresh(db_pago)
    return db_pago

def get_all_tables_payment_status(db: Session) -> List[dict]:
    """
    Obtiene un estado de cuenta detallado para todas las mesas, incluyendo
    consumos, pagos y saldo pendiente.
    """
    mesas = db.query(models.Mesa).order_by(models.Mesa.nombre).all()
    
    results = []
    for mesa in mesas:
        # 1. Calcular total consumido
        total_consumido = (
            db.query(func.sum(models.Consumo.valor_total))
            .join(models.Usuario, models.Consumo.usuario_id == models.Usuario.id)
            .filter(models.Usuario.mesa_id == mesa.id)
            .scalar() or Decimal('0.00')
        )

        # 2. Calcular total pagado
        total_pagado = (
            db.query(func.sum(models.Pago.monto))
            .filter(models.Pago.mesa_id == mesa.id)
            .scalar() or Decimal('0.00')
        )

        # 3. Calcular saldo pendiente
        saldo_pendiente = total_consumido - total_pagado

        # 4. Obtener detalles de consumos y pagos
        consumos_detalle = db.query(models.Consumo).join(models.Usuario).filter(models.Usuario.mesa_id == mesa.id).all()
        pagos_detalle = db.query(models.Pago).filter(models.Pago.mesa_id == mesa.id).order_by(models.Pago.created_at.desc()).all()

        # Mapear consumos a ConsumoItemDetalle
        consumos_items = [
            schemas.ConsumoItemDetalle(
                producto_nombre=c.producto.nombre,
                cantidad=c.cantidad,
                valor_total=c.valor_total,
                created_at=c.created_at
            ) for c in consumos_detalle
        ]

        results.append({
            "mesa_id": mesa.id,
            "mesa_nombre": mesa.nombre,
            "total_consumido": total_consumido,
            "total_pagado": total_pagado,
            "saldo_pendiente": saldo_pendiente,
            "consumos": consumos_items,
            "pagos": pagos_detalle
        })
        
    return results

def get_table_payment_status(db: Session, mesa_id: int) -> Optional[dict]:
    """
    Obtiene un estado de cuenta detallado para una mesa específica.
    """
    mesa = get_mesa_by_id(db, mesa_id=mesa_id)
    if not mesa:
        return None

    # 1. Calcular total consumido
    total_consumido = (
        db.query(func.sum(models.Consumo.valor_total))
        .join(models.Usuario, models.Consumo.usuario_id == models.Usuario.id)
        .filter(models.Usuario.mesa_id == mesa.id)
        .scalar() or Decimal('0.00')
    )

    # 2. Calcular total pagado
    total_pagado = (
        db.query(func.sum(models.Pago.monto))
        .filter(models.Pago.mesa_id == mesa.id)
        .scalar() or Decimal('0.00')
    )

    # 3. Calcular saldo pendiente
    saldo_pendiente = total_consumido - total_pagado

    # 4. Obtener detalles de consumos y pagos
    consumos_detalle = db.query(models.Consumo).join(models.Usuario).filter(models.Usuario.mesa_id == mesa.id).order_by(models.Consumo.created_at.asc()).all()
    pagos_detalle = db.query(models.Pago).filter(models.Pago.mesa_id == mesa.id).order_by(models.Pago.created_at.asc()).all()

    consumos_items = [
        schemas.ConsumoItemDetalle(
            producto_nombre=c.producto.nombre,
            cantidad=c.cantidad,
            valor_total=c.valor_total,
            created_at=c.created_at
        ) for c in consumos_detalle
    ]

    return schemas.MesaEstadoPago(
        mesa_id=mesa.id, mesa_nombre=mesa.nombre, total_consumido=total_consumido, total_pagado=total_pagado, saldo_pendiente=saldo_pendiente, consumos=consumos_items, pagos=pagos_detalle
    ).dict()

async def start_next_song_if_autoplay_and_idle(db: Session):
    """
    Verifica si el autoplay está activado, si no hay nada sonando y si hay
    canciones en la cola. Si se cumplen las condiciones, inicia la siguiente canción.
    """
    import config
    import websocket_manager

    if not config.settings.AUTOPLAY_ENABLED:
        return

    # Verificamos si ya hay una canción en estado 'reproduciendo'
    is_playing = db.query(models.Cancion).filter(models.Cancion.estado == "reproduciendo").first()
    if is_playing:
        return

    # Si no hay nada sonando, marcamos la siguiente como 'reproduciendo'
    next_song = marcar_siguiente_como_reproduciendo(db)

    if next_song:
        # Si se encontró una siguiente canción, notificamos a todos los clientes
        # para que la cola se actualice y el reproductor comience a reproducir.
        await websocket_manager.manager.broadcast_queue_update()
        await websocket_manager.manager.broadcast_play_song(next_song.youtube_id)
        create_admin_log_entry(db, action="AUTOPLAY_START", details=f"Autoplay inició la canción '{next_song.titulo}'.")

async def avanzar_cola_automaticamente(db: Session):
    """
    Función central para avanzar la cola: marca la canción actual como cantada,
    inicia la siguiente y notifica a todos los clientes.
    Esta función es llamada tanto por el autoplay como por el botón manual.
    """
    import websocket_manager

    # 1. Marcar la canción actual como 'cantada' y obtener sus datos
    cancion_cantada = marcar_cancion_actual_como_cantada(db)
    if cancion_cantada:
        # Notificar a todos que la canción terminó (para mostrar puntajes, etc.)
        await websocket_manager.manager.broadcast_song_finished(cancion_cantada)

    # 2. Marcar la siguiente canción como 'reproduciendo'
    siguiente_cancion = marcar_siguiente_como_reproduciendo(db)

    # 3. Notificar a todos los clientes sobre la actualización de la cola
    await websocket_manager.manager.broadcast_queue_update()

    # 4. Si hay una nueva canción, enviar la orden de reproducción al player
    if siguiente_cancion:
        await websocket_manager.manager.broadcast_play_song(siguiente_cancion.youtube_id)

    return siguiente_cancion