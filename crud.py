
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, or_, and_, desc
import secrets
from typing import List, Optional
import datetime
import models, schemas
from timezone_utils import now_bogota
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
    Verifica si ALGÚN USUARIO DE LA MISMA MESA ya tiene esta canción en la cola.
    CAMBIO: Ahora verifica a nivel de mesa para evitar duplicados entre usuarios de la misma mesa.
    """
    # Obtener el usuario y su mesa
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario or not usuario.mesa_id:
        return None
    
    # Buscar si algún usuario de la misma mesa ya tiene esta canción en cola
    return db.query(models.Cancion).join(
        models.Usuario, models.Cancion.usuario_id == models.Usuario.id
    ).filter(
        models.Usuario.mesa_id == usuario.mesa_id,
        models.Cancion.youtube_id == youtube_id,
        models.Cancion.estado.in_(['pendiente', 'aprobado', 'reproduciendo'])
    ).first()
def get_cancion_by_id(db: Session, cancion_id: int):
    """Busca una canción por su ID."""
    return db.query(models.Cancion).filter(models.Cancion.id == cancion_id).first()

def get_cancion_actual(db: Session):
    """
    Retorna la canción que está actualmente en reproducción,
    o None si no hay ninguna activa.
    """
    return db.query(models.Cancion).filter(models.Cancion.estado == "reproduciendo").first()


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
    Obtiene la lista de canciones aprobadas, ordenadas por el algoritmo de "Cola Justa".
    
    Reglas:
    1. Orden Manual: Las canciones con `orden_manual` tienen prioridad absoluta y mantienen su orden relativo.
    2. Agrupación por Mesa: El resto de canciones se agrupan por su mesa de origen.
    3. Categorías de Mesa (basado en consumo total de la mesa):
        - ORO (> $150.000): Cupo de 3 canciones por turno.
        - PLATA (> $50.000): Cupo de 2 canciones por turno.
        - BRONCE (<= $50.000): Cupo de 1 canción por turno.
    4. Round Robin: Se iteran las mesas (ordenadas por la hora de llegada de su primera canción pendiente)
       y se toman N canciones (según su cupo) en cada turno.
    """
    from collections import deque
    
    # 1. Obtener todas las canciones aprobadas
    # Ordenamos por ID ascendente para respetar el orden de llegada "natural" dentro de cada mesa
    todas_canciones = (
        db.query(models.Cancion)
        .join(models.Usuario, models.Cancion.usuario_id == models.Usuario.id)
        .filter(models.Cancion.estado == "aprobado")
        .order_by(models.Cancion.orden_manual.asc().nulls_last(), models.Cancion.id.asc())
        .all()
    )

    # 2. Separar canciones con orden manual (Prioridad Absoluta)
    cola_manual = []
    cola_pool = []
    
    for cancion in todas_canciones:
        if cancion.orden_manual is not None:
            # Insertar respetando el valor de orden_manual si es posible, o simplemente al principio
            cola_manual.append(cancion)
        else:
            cola_pool.append(cancion)
            
    # Si solo hay canciones manuales, retornamos
    if not cola_pool:
        return cola_manual

    # 3. Agrupar canciones por Mesa
    match_mesa_canciones = {} # {mesa_id: deque([canciones])}
    mesa_arrival_time = {} # {mesa_id: primer_id_cancion} para ordenar turnos
    
    mesas_involucradas_ids = set()

    for cancion in cola_pool:
        mesa_id = cancion.usuario.mesa_id
        if not mesa_id:
            # Si un usuario no tiene mesa (ej. DJ), lo tratamos como una mesa "ficticia" con ID negativo
            # o lo agrupamos en un grupo especial. Asumamos ID 0 para "Sin Mesa"
            mesa_id = 0
            
        if mesa_id not in match_mesa_canciones:
            match_mesa_canciones[mesa_id] = deque()
            mesa_arrival_time[mesa_id] = cancion.id # El ID más bajo es el primero que llegó
            mesas_involucradas_ids.add(mesa_id)
            
        match_mesa_canciones[mesa_id].append(cancion)

    # 4. Calcular Categoría (Tier) de cada Mesa
    # Necesitamos el consumo total de cada mesa involucrada
    # Definimos umbrales
    UMBRAL_ORO = 150000
    UMBRAL_PLATA = 50000
    
    mesa_tiers = {} # {mesa_id: 'oro'|'plata'|'bronce'}
    mesa_quotas = {} # {mesa_id: int}
    
    if mesas_involucradas_ids:
        # Consulta eficiente para obtener consumos de las mesas relevantes
        # Excluimos la mesa 0 (sin mesa/DJ) de la consulta de base de datos
        ids_reales = [mid for mid in mesas_involucradas_ids if mid != 0]
        
        consumos_mesas = {}
        if ids_reales:
            rows = (
                db.query(
                    models.Usuario.mesa_id,
                    func.sum(models.Consumo.valor_total)
                )
                .join(models.Consumo, models.Usuario.id == models.Consumo.usuario_id)
                .filter(models.Usuario.mesa_id.in_(ids_reales))
                .group_by(models.Usuario.mesa_id)
                .all()
            )
            for mid, total in rows:
                consumos_mesas[mid] = total or 0
        
        # Asignar quotas
        for mid in mesas_involucradas_ids:
            total = consumos_mesas.get(mid, 0)
            
            # DJ / Sin Mesa (ID 0) recibe trato Preferencial o Estándar?
            # Vamos a darle trato de ORO al DJ si se usa para poner música activamente.
            if mid == 0: 
                quota = 3 
            elif total >= UMBRAL_ORO:
                quota = 3
            elif total >= UMBRAL_PLATA:
                quota = 2
            else:
                quota = 1
                
            mesa_quotas[mid] = quota

    # 5. Construir la Cola Round-Robin
    cola_justa = []
    
    # Ordenamos las mesas por orden de llegada (quién puso canción primero)
    orden_turnos_mesas = sorted(mesas_involucradas_ids, key=lambda mid: mesa_arrival_time[mid])
    
    # Bucle Round Robin
    while match_mesa_canciones:
        # Iterar sobre una copia de la lista de mesas para poder borrar claves del diccionario principal
        for mesa_id in orden_turnos_mesas:
            if mesa_id not in match_mesa_canciones:
                continue
                
            queue_de_mesa = match_mesa_canciones[mesa_id]
            cupo = mesa_quotas.get(mesa_id, 1)
            
            # Tomar hasta 'cupo' canciones
            tomadas = 0
            while tomadas < cupo and queue_de_mesa:
                cancion = queue_de_mesa.popleft()
                cola_justa.append(cancion)
                tomadas += 1
            
            # Si la mesa se queda sin canciones, la eliminamos del diccionario
            if not queue_de_mesa:
                del match_mesa_canciones[mesa_id]
    
    # 6. Fusionar: Manual + Justa
    return cola_manual + cola_justa

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
    """
    Crea un nuevo consumo. CAMBIO: El consumo se asigna a la MESA, no al usuario individual.
    Todos los consumos de los 10 usuarios en una mesa se consolidan en la cuenta de la mesa.
    """
    # 1. Obtener el usuario y su mesa
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_usuario:
        return None, "Usuario no encontrado."
    
    if not db_usuario.mesa_id:
        return None, "El usuario no está asociado a ninguna mesa."

    # 2. Obtener el producto del catálogo para saber su precio
    db_producto = db.query(models.Producto).filter(models.Producto.id == consumo.producto_id).first()
    if not db_producto:
        return None, "Producto no encontrado en el catálogo."

    if db_producto.stock < consumo.cantidad:
        return None, f"No hay suficiente stock para '{db_producto.nombre}'. Disponible: {db_producto.stock}"

    if consumo.cantidad <= 0:
        return None, "La cantidad debe ser mayor que cero."

    if not db_producto.is_active:
        return None, "El producto no está disponible actualmente."

    # 3. Calcular el valor total de la transacción
    valor_total_transaccion = db_producto.valor * consumo.cantidad

    # 4. Crear el registro de consumo ASIGNADO A LA MESA (no al usuario)
    # Obtener o crear cuenta activa
    active_cuenta = get_active_cuenta(db, db_usuario.mesa_id)
    if not active_cuenta:
         active_cuenta = create_new_active_cuenta(db, db_usuario.mesa_id)

    db_consumo = models.Consumo(
        producto_id=consumo.producto_id,
        cantidad=consumo.cantidad,
        valor_total=valor_total_transaccion,
        mesa_id=db_usuario.mesa_id,  # CAMBIO: Asignar a mesa
        usuario_id=usuario_id,  # Mantener referencia al usuario que pidió (tracking)
        cuenta_id=active_cuenta.id
    )

    # 5. Descontar del stock
    db_producto.stock -= consumo.cantidad

    # 6. Otorgar puntos al usuario individual (ej: 1 punto por cada 10 de moneda gastados)
    db_usuario.puntos += int(valor_total_transaccion / 10)

    db.add(db_consumo)
    db.commit()
    db.refresh(db_consumo)

    # 7. Actualizar el nivel del usuario basado en su consumo individual
    total_consumido_usuario = db.query(func.sum(models.Consumo.valor_total)).filter(
        models.Consumo.usuario_id == usuario_id
    ).scalar() or 0

    SILVER_THRESHOLD = 50.0
    GOLD_THRESHOLD = 150.0

    if total_consumido_usuario >= GOLD_THRESHOLD:
        db_usuario.nivel = "oro"
    elif total_consumido_usuario >= SILVER_THRESHOLD:
        db_usuario.nivel = "plata"

    db.commit()
    db.refresh(db_usuario)
    return db_consumo, None

def create_pedido_from_carrito(db: Session, carrito: schemas.CarritoCreate, usuario_id: int):
    """
    Crea múltiples registros de consumo a partir de un carrito de compras.
    CAMBIO: Los consumos se asignan a la MESA, no al usuario individual.
    Toda la operación se maneja como una única transacción.
    """
    SILVER_THRESHOLD = 50.0
    GOLD_THRESHOLD = 150.0

    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_usuario:
        return None, "Usuario no encontrado."
    
    if not db_usuario.mesa_id:
        return None, "El usuario no está asociado a ninguna mesa."

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

            # Asegurar cuenta activa (solo una vez)
            active_cuenta = get_active_cuenta(db, db_usuario.mesa_id)
            if not active_cuenta:
                active_cuenta = create_new_active_cuenta(db, db_usuario.mesa_id)

            # Creamos el objeto Consumo ASIGNADO A LA MESA
            db_consumo = models.Consumo(
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                valor_total=valor_linea,
                mesa_id=db_usuario.mesa_id,  # CAMBIO: Asignar a mesa
                usuario_id=usuario_id,  # Mantener referencia al usuario que pidió
                cuenta_id=active_cuenta.id
            )
            db.add(db_consumo)
            consumos_creados.append(db_consumo)

            # Descontamos el stock
            db_producto.stock -= item.cantidad

        # Si todo fue bien, actualizamos los puntos y el nivel del usuario INDIVIDUAL
        db_usuario.puntos += int(valor_total_pedido / 10)
        total_consumido_historico = (db.query(func.sum(models.Consumo.valor_total)).filter(
            models.Consumo.usuario_id == usuario_id
        ).scalar() or 0) + valor_total_pedido

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
    cancion_actual.finished_at = now_bogota()

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
    siguiente_cancion[0].started_at = now_bogota()
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
        tiempo_transcurrido = (now_bogota() - cancion_actual.started_at).total_seconds()
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
    db_producto = db.query(models.Producto).options(joinedload(models.Producto.consumos)).filter(models.Producto.id == producto_id).first()
    if not db_producto:
        return None, "Producto no encontrado."

    # Si el producto tiene consumos asociados, no lo borramos, solo lo desactivamos.
    if db_producto.consumos:
        db_producto.is_active = False
        db.commit()
        db.refresh(db_producto)
        return db_producto, "El producto tiene consumos asociados y ha sido desactivado en lugar de borrado."
    else:
        # Si no hay consumos, se puede borrar de forma segura.
        db.delete(db_producto)
        db.commit()
        return None, "Producto eliminado permanentemente."

def get_total_ingresos(db: Session):
    """Calcula la suma total de todos los pagos recibidos durante la noche."""
    total = db.query(func.sum(models.Pago.monto)).scalar()
    return total or 0

def get_ganancias_totales(db: Session):
    """
    Calcula las ganancias reales: (precio_venta - costo) * cantidad
    Solo de productos que ya fueron pagados (mesas con pagos registrados).
    """
    from decimal import Decimal
    
    # Obtener todas las mesas que tienen al menos un pago
    mesas_con_pagos = db.query(models.Pago.mesa_id).distinct().all()
    mesas_ids = [mesa_id for (mesa_id,) in mesas_con_pagos]
    
    if not mesas_ids:
        return Decimal("0")
    
    # Obtener todos los consumos de esas mesas
    consumos = (
        db.query(models.Consumo)
        .join(models.Usuario)
        .filter(models.Usuario.mesa_id.in_(mesas_ids))
        .all()
    )
    
    ganancias_total = Decimal("0")
    for consumo in consumos:
        producto = consumo.producto
        # Ganancia = (precio_venta - costo) * cantidad
        ganancia_item = (producto.valor - producto.costo) * consumo.cantidad
        ganancias_total += ganancia_item
    
    return ganancias_total


def get_ingresos_por_mesa(db: Session):
    """
    Calcula los ingresos totales (pagos recibidos) agrupados por cada mesa.
    """
    return (
        db.query(
            models.Mesa.nombre,
            func.sum(models.Pago.monto).label("ingresos_totales")
        )
        .join(models.Pago, models.Mesa.id == models.Pago.mesa_id)
        .group_by(models.Mesa.nombre)
        .order_by(func.sum(models.Pago.monto).desc())
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
        for key, value in producto_update.dict(exclude_unset=True).items():
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

def registrar_compra_producto(db: Session, compra: schemas.CompraProducto):
    """
    Registra una compra para un producto existente, aumentando su stock.
    Opcionalmente, actualiza el precio de compra.
    """
    db_producto = db.query(models.Producto).filter(models.Producto.id == compra.producto_id).first()
    if not db_producto:
        return None, f"Producto con ID {compra.producto_id} no encontrado."

    if compra.cantidad_comprada <= 0:
        return None, "La cantidad comprada debe ser mayor que cero."

    db_producto.stock += compra.cantidad_comprada
    if compra.nuevo_precio_compra is not None:
        db_producto.precio_compra = compra.nuevo_precio_compra

    db.commit()
    db.refresh(db_producto)
    return db_producto, "Compra registrada y stock actualizado correctamente."

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
    """Obtiene un valor de configuración por su clave (clave)."""
    return db.query(models.ConfiguracionGlobal).filter(models.ConfiguracionGlobal.clave == key).first()

def update_config(db: Session, key: str, value: str):
    """Establece o actualiza un valor de configuración (clave)."""
    db_config = db.query(models.ConfiguracionGlobal).filter(models.ConfiguracionGlobal.clave == key).first()
    if db_config:
        db_config.value = value
    else:
        db_config = models.ConfiguracionGlobal(clave=key, valor=value)
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

def get_o_crear_usuario_admin_para_mesa(db: Session, mesa_id: int) -> models.Usuario:
    """
    Busca o crea un usuario administrador para una mesa específica.
    Este usuario se utiliza para las canciones añadidas por el admin a través del dashboard.
    El nick será "ADMIN_Mesa_{mesa_id}".
    """
    admin_nick = f"ADMIN_Mesa_{mesa_id}"
    admin_user = db.query(models.Usuario).filter(models.Usuario.nick == admin_nick).first()
    
    if not admin_user:
        admin_user = models.Usuario(nick=admin_nick, mesa_id=mesa_id)
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
    
    return admin_user

def get_canciones_pendientes_por_aprobar(db: Session):
    """
    Obtiene las canciones que están en estado 'pendiente' (no aprobadas aún).
    Ordenadas por fecha de creación.
    """
    return db.query(models.Cancion).filter(
        models.Cancion.estado == 'pendiente'
    ).order_by(models.Cancion.created_at.asc()).all()

def auto_approve_songs_after_10_minutes(db: Session):
    """
    Aprueba automáticamente las primeras 2 canciones pendientes que ya han pasado 10 minutos desde su creación.
    Las demás canciones permanecen en estado 'pendiente' esperando aprobación manual.
    """
    from datetime import timedelta
    
    # Obtener canciones pendientes que tienen más de 10 minutos
    time_threshold = now_bogota() - timedelta(minutes=10)
    
    songs_to_auto_approve = db.query(models.Cancion).filter(
        models.Cancion.estado == 'pendiente',
        models.Cancion.created_at <= time_threshold
    ).order_by(models.Cancion.created_at.asc()).limit(2).all()
    
    # Aprobar las primeras 2 canciones
    for cancion in songs_to_auto_approve:
        cancion.estado = 'aprobado'
        cancion.approved_at = now_bogota()
        db.add(cancion)
    
    if songs_to_auto_approve:
        db.commit()
    
    return songs_to_auto_approve

def approve_song_by_admin(db: Session, cancion_id: int):
    """
    Aprueba una canción manualmente desde el admin.
    Cambia el estado de 'pendiente' a 'aprobado'.
    """
    db_cancion = db.query(models.Cancion).filter(
        models.Cancion.id == cancion_id,
        models.Cancion.estado == 'pendiente'
    ).first()
    
    if db_cancion:
        db_cancion.estado = 'aprobado'
        db_cancion.approved_at = now_bogota()
        db.commit()
        db.refresh(db_cancion)
    
    return db_cancion

def get_cola_completa(db: Session):
    """
    Obtiene la cola completa, incluyendo:
    - Canción actualmente reproduciendo
    - Cola aprobada (upcoming)
    - Cola pendiente por aprobar
    """
    # Aplicar aprobación automática después de 10 minutos
    auto_approve_songs_after_10_minutes(db)
    
    now_playing = db.query(models.Cancion).filter(models.Cancion.estado == "reproduciendo").first()
    approved_queue = get_cola_priorizada(db)
    pending_queue = get_canciones_pendientes_por_aprobar(db)

    # Si la canción que se está reproduciendo sigue en la lista de 'upcoming', la quitamos.
    if now_playing:
        approved_queue = [song for song in approved_queue if song.id != now_playing.id]

    return {
        "now_playing": now_playing, 
        "upcoming": approved_queue,
        "pending": pending_queue
    }

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

    # Obtener o crear cuenta activa
    active_cuenta = get_active_cuenta(db, pago.mesa_id)
    if not active_cuenta:
         active_cuenta = create_new_active_cuenta(db, pago.mesa_id)

    db_pago = models.Pago(
        monto=pago.monto,
        metodo_pago=pago.metodo_pago,
        mesa_id=pago.mesa_id,
        cuenta_id=active_cuenta.id
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
    CAMBIO: Se obtiene el estado de la CUENTA ACTIVA de la mesa.
    """
    # 1. Obtener la cuenta activa
    # Nota: Usamos la función helper definida abajo. Como Python permite referencias forward en runtime,
    # esto funcionará siempre que se llame después de definir get_active_cuenta.
    # Pero para estar seguros, la importaremos o asumiremos que está en el scope global del módulo.
    # Dado que get_active_cuenta está en este mismo archivo, está bien.
    
    active_cuenta = get_active_cuenta(db, mesa_id)
    
    if not active_cuenta:
         # Si no hay cuenta activa, devolvemos un estado vacío pero válido
         mesa = get_mesa_by_id(db, mesa_id)
         if not mesa: return None
         return schemas.MesaEstadoPago(
             mesa_id=mesa.id, mesa_nombre=mesa.nombre, 
             total_consumido=Decimal(0), total_pagado=Decimal(0), saldo_pendiente=Decimal(0), consumos=[], pagos=[]
         ).dict()
         
    return get_cuenta_payment_status(db, active_cuenta.id)

async def start_next_song_if_autoplay_and_idle(db: Session):
    """
    Verifica si no hay nada sonando y si hay canciones en la cola.
    Si se cumplen las condiciones, inicia la siguiente canción automáticamente.
    """
    import websocket_manager

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
        create_admin_log_entry(db, action="AUTO_START", details=f"Iniciada automáticamente la canción '{next_song.titulo}'.")

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


    # 5. Aprobar la siguiente canci�n lazy si es necesario
    check_and_approve_next_lazy_song(db)


    # 5. Aprobar la siguiente canci�n lazy si es necesario
    check_and_approve_next_lazy_song(db)

    return siguiente_cancion

def registrar_compra_producto(db: Session, compra: schemas.CompraProducto):
    """
    Registra una compra para un producto existente, aumentando su stock.
    Opcionalmente, actualiza el precio de compra.
    """
    db_producto = db.query(models.Producto).filter(models.Producto.id == compra.producto_id).first()
    if not db_producto:
        return None, f"Producto con ID {compra.producto_id} no encontrado."

    if compra.cantidad_comprada <= 0:
        return None, "La cantidad comprada debe ser mayor que cero."

    db_producto.stock += compra.cantidad_comprada
    if compra.nuevo_precio_compra is not None:
        db_producto.precio_compra = compra.nuevo_precio_compra

    db.commit()
    db.refresh(db_producto)
    return db_producto, "Compra registrada y stock actualizado correctamente."

def get_consumos_por_usuario(db: Session, usuario_id: int):
    """
    Obtiene el historial de consumo de un usuario específico.
    """
    return db.query(models.Consumo).filter(models.Consumo.usuario_id == usuario_id).order_by(models.Consumo.created_at.desc()).all()


def get_recent_consumos(db: Session, limit: int = 10):
    """
    Devuelve los consumos más recientes junto con el nombre del producto,
    nick del usuario y nombre de la mesa (si existe).
    Filtra los consumos que ya han sido despachados.
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
        .filter(models.Consumo.is_dispatched == False)
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

# --- Admin API Key Management ---
def create_admin_api_key(db: Session, description: str):
    """
    Creates a new admin API key with a secure random key.
    Returns the full key object including the key itself (shown only once).
    """
    # Generate a secure random API key (32 bytes = 64 hex characters)
    new_key = secrets.token_hex(32)
    
    db_api_key = models.AdminApiKey(
        key=new_key,
        description=description,
        is_active=True
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    return db_api_key

def get_all_admin_api_keys(db: Session):
    """
    Returns all admin API keys without revealing the actual key values.
    """
    return db.query(models.AdminApiKey).all()

def delete_admin_api_key(db: Session, key_id: int):
    """
    Deletes an admin API key by ID.
    Returns the deleted key object or None if not found.
    """
    db_key = db.query(models.AdminApiKey).filter(models.AdminApiKey.id == key_id).first()
    if db_key:
        db.delete(db_key)
        db.commit()
    return db_key

def get_admin_api_key(db: Session, key: str):
    """
    Retrieves an admin API key by its key value.
    Updates the last_used timestamp when found.
    Returns the key object if found and active, None otherwise.
    """
    db_key = db.query(models.AdminApiKey).filter(
        models.AdminApiKey.key == key,
        models.AdminApiKey.is_active == True
    ).first()
    
    if db_key:
        # Update last_used timestamp
        db_key.last_used = datetime.datetime.utcnow()
        db.commit()
    
    return db_key

# --- Account (Cuenta) Management ---

def get_active_cuenta(db: Session, mesa_id: int) -> Optional[models.Cuenta]:
    """Obtiene la cuenta activa actual de una mesa."""
    return db.query(models.Cuenta).filter(models.Cuenta.mesa_id == mesa_id, models.Cuenta.is_active == True).first()

def create_new_active_cuenta(db: Session, mesa_id: int):
    """
    Cierra la cuenta activa actual (si existe) y crea una nueva.
    """
    # 1. Buscar y cerrar cuenta activa existente
    active = get_active_cuenta(db, mesa_id)
    if active:
        active.is_active = False
        active.closed_at = now_bogota()
    
    # 2. Crear nueva cuenta activa
    new_cuenta = models.Cuenta(mesa_id=mesa_id, is_active=True, created_at=now_bogota())
    db.add(new_cuenta)
    db.commit()
    db.refresh(new_cuenta)
    return new_cuenta

def get_previous_cuentas(db: Session, mesa_id: int):
    """Obtiene el historial de cuentas cerradas de una mesa."""
    return db.query(models.Cuenta).filter(models.Cuenta.mesa_id == mesa_id, models.Cuenta.is_active == False).order_by(models.Cuenta.closed_at.desc()).all()

def get_cuenta_by_id(db: Session, cuenta_id: int):
    """Busca una cuenta por su ID."""
    return db.query(models.Cuenta).filter(models.Cuenta.id == cuenta_id).first()

def get_cuenta_payment_status(db: Session, cuenta_id: int) -> Optional[dict]:
    """
    Obtiene el estado de pago de una CUENTA específica (activa o cerrada).
    """
    cuenta = get_cuenta_by_id(db, cuenta_id)
    if not cuenta:
        return None
    
    mesa = cuenta.mesa
    
    # 1. Calcular total consumido EN ESTA CUENTA
    total_consumido = (
        db.query(func.sum(models.Consumo.valor_total))
        .filter(models.Consumo.cuenta_id == cuenta.id)
        .scalar() or Decimal('0.00')
    )

    # 2. Calcular total pagado EN ESTA CUENTA
    total_pagado = (
        db.query(func.sum(models.Pago.monto))
        .filter(models.Pago.cuenta_id == cuenta.id)
        .scalar() or Decimal('0.00')
    )

    # 3. Calcular saldo pendiente
    saldo_pendiente = total_consumido - total_pagado

    # 4. Obtener detalles
    consumos_detalle = db.query(models.Consumo).filter(
        models.Consumo.cuenta_id == cuenta.id
    ).order_by(models.Consumo.created_at.asc()).all()
    
    pagos_detalle = db.query(models.Pago).filter(models.Pago.cuenta_id == cuenta.id).order_by(models.Pago.created_at.asc()).all()

    consumos_items = [
        schemas.ConsumoItemDetalle(
            producto_nombre=c.producto.nombre,
            cantidad=c.cantidad,
            valor_total=c.valor_total,
            created_at=c.created_at
        ) for c in consumos_detalle
    ]

    return schemas.MesaEstadoPago(
        mesa_id=mesa.id, 
        mesa_nombre=mesa.nombre, 
        total_consumido=total_consumido, 
        total_pagado=total_pagado, 
        saldo_pendiente=saldo_pendiente, 
        consumos=consumos_items, 
        pagos=pagos_detalle
    ).dict()#   C � � d i g o   p a r a   a g r e g a r   a l   f i n a l   d e   c r u d . p y 
 
 
 
 #   - - -   L a z y   A p p r o v a l   Q u e u e   F u n c t i o n s   - - - 
 
 
 
 d e f   g e t _ c o l a _ l a z y ( d b :   S e s s i o n ) : 
 
         " " " 
 
         O b t i e n e   t o d a s   l a s   c a n c i o n e s   e n   e s t a d o   p e n d i e n t e _ l a z y ,   o r d e n a d a s   p o r   p r i o r i d a d . 
 
         U s a   e l   m i s m o   a l g o r i t m o   d e   c o l a   j u s t a   q u e   g e t _ c o l a _ p r i o r i z a d a . 
 
         " " " 
 
         f r o m   c o l l e c t i o n s   i m p o r t   d e q u e 
 
         
 
         #   O b t e n e r   t o d a s   l a s   c a n c i o n e s   e n   e s t a d o   p e n d i e n t e _ l a z y 
 
         t o d a s _ c a n c i o n e s   =   ( 
 
                 d b . q u e r y ( m o d e l s . C a n c i o n ) 
 
                 . j o i n ( m o d e l s . U s u a r i o ,   m o d e l s . C a n c i o n . u s u a r i o _ i d   = =   m o d e l s . U s u a r i o . i d ) 
 
                 . f i l t e r ( m o d e l s . C a n c i o n . e s t a d o   = =   " p e n d i e n t e _ l a z y " ) 
 
                 . o r d e r _ b y ( m o d e l s . C a n c i o n . o r d e n _ m a n u a l . a s c ( ) . n u l l s _ l a s t ( ) ,   m o d e l s . C a n c i o n . i d . a s c ( ) ) 
 
                 . a l l ( ) 
 
         ) 
 
         
 
         i f   n o t   t o d a s _ c a n c i o n e s : 
 
                 r e t u r n   [ ] 
 
         
 
         #   A p l i c a r   e l   m i s m o   a l g o r i t m o   d e   c o l a   j u s t a 
 
         c o l a _ m a n u a l   =   [ ] 
 
         c o l a _ p o o l   =   [ ] 
 
         
 
         f o r   c a n c i o n   i n   t o d a s _ c a n c i o n e s : 
 
                 i f   c a n c i o n . o r d e n _ m a n u a l   i s   n o t   N o n e : 
 
                         c o l a _ m a n u a l . a p p e n d ( c a n c i o n ) 
 
                 e l s e : 
 
                         c o l a _ p o o l . a p p e n d ( c a n c i o n ) 
 
         
 
         i f   n o t   c o l a _ p o o l : 
 
                 r e t u r n   c o l a _ m a n u a l 
 
         
 
         #   A g r u p a r   p o r   m e s a 
 
         m a t c h _ m e s a _ c a n c i o n e s   =   { } 
 
         m e s a _ a r r i v a l _ t i m e   =   { } 
 
         m e s a s _ i n v o l u c r a d a s _ i d s   =   s e t ( ) 
 
         
 
         f o r   c a n c i o n   i n   c o l a _ p o o l : 
 
                 m e s a _ i d   =   c a n c i o n . u s u a r i o . m e s a _ i d   o r   0 
 
                 i f   m e s a _ i d   n o t   i n   m a t c h _ m e s a _ c a n c i o n e s : 
 
                         m a t c h _ m e s a _ c a n c i o n e s [ m e s a _ i d ]   =   d e q u e ( ) 
 
                         m e s a _ a r r i v a l _ t i m e [ m e s a _ i d ]   =   c a n c i o n . i d 
 
                         m e s a s _ i n v o l u c r a d a s _ i d s . a d d ( m e s a _ i d ) 
 
                 m a t c h _ m e s a _ c a n c i o n e s [ m e s a _ i d ] . a p p e n d ( c a n c i o n ) 
 
         
 
         #   C a l c u l a r   q u o t a s 
 
         U M B R A L _ O R O   =   1 5 0 0 0 0 
 
         U M B R A L _ P L A T A   =   5 0 0 0 0 
 
         m e s a _ q u o t a s   =   { } 
 
         
 
         i f   m e s a s _ i n v o l u c r a d a s _ i d s : 
 
                 i d s _ r e a l e s   =   [ m i d   f o r   m i d   i n   m e s a s _ i n v o l u c r a d a s _ i d s   i f   m i d   ! =   0 ] 
 
                 c o n s u m o s _ m e s a s   =   { } 
 
                 
 
                 i f   i d s _ r e a l e s : 
 
                         r o w s   =   ( 
 
                                 d b . q u e r y ( 
 
                                         m o d e l s . U s u a r i o . m e s a _ i d , 
 
                                         f u n c . s u m ( m o d e l s . C o n s u m o . v a l o r _ t o t a l ) 
 
                                 ) 
 
                                 . j o i n ( m o d e l s . C o n s u m o ,   m o d e l s . U s u a r i o . i d   = =   m o d e l s . C o n s u m o . u s u a r i o _ i d ) 
 
                                 . f i l t e r ( m o d e l s . U s u a r i o . m e s a _ i d . i n _ ( i d s _ r e a l e s ) ) 
 
                                 . g r o u p _ b y ( m o d e l s . U s u a r i o . m e s a _ i d ) 
 
                                 . a l l ( ) 
 
                         ) 
 
                         f o r   m i d ,   t o t a l   i n   r o w s : 
 
                                 c o n s u m o s _ m e s a s [ m i d ]   =   t o t a l   o r   0 
 
                 
 
                 f o r   m i d   i n   m e s a s _ i n v o l u c r a d a s _ i d s : 
 
                         t o t a l   =   c o n s u m o s _ m e s a s . g e t ( m i d ,   0 ) 
 
                         i f   m i d   = =   0 : 
 
                                 q u o t a   =   3 
 
                         e l i f   t o t a l   > =   U M B R A L _ O R O : 
 
                                 q u o t a   =   3 
 
                         e l i f   t o t a l   > =   U M B R A L _ P L A T A : 
 
                                 q u o t a   =   2 
 
                         e l s e : 
 
                                 q u o t a   =   1 
 
                         m e s a _ q u o t a s [ m i d ]   =   q u o t a 
 
         
 
         #   R o u n d   R o b i n 
 
         c o l a _ j u s t a   =   [ ] 
 
         o r d e n _ t u r n o s _ m e s a s   =   s o r t e d ( m e s a s _ i n v o l u c r a d a s _ i d s ,   k e y = l a m b d a   m i d :   m e s a _ a r r i v a l _ t i m e [ m i d ] ) 
 
         
 
         w h i l e   m a t c h _ m e s a _ c a n c i o n e s : 
 
                 f o r   m e s a _ i d   i n   o r d e n _ t u r n o s _ m e s a s : 
 
                         i f   m e s a _ i d   n o t   i n   m a t c h _ m e s a _ c a n c i o n e s : 
 
                                 c o n t i n u e 
 
                         q u e u e _ d e _ m e s a   =   m a t c h _ m e s a _ c a n c i o n e s [ m e s a _ i d ] 
 
                         c u p o   =   m e s a _ q u o t a s . g e t ( m e s a _ i d ,   1 ) 
 
                         t o m a d a s   =   0 
 
                         w h i l e   t o m a d a s   <   c u p o   a n d   q u e u e _ d e _ m e s a : 
 
                                 c a n c i o n   =   q u e u e _ d e _ m e s a . p o p l e f t ( ) 
 
                                 c o l a _ j u s t a . a p p e n d ( c a n c i o n ) 
 
                                 t o m a d a s   + =   1 
 
                         i f   n o t   q u e u e _ d e _ m e s a : 
 
                                 d e l   m a t c h _ m e s a _ c a n c i o n e s [ m e s a _ i d ] 
 
         
 
         r e t u r n   c o l a _ m a n u a l   +   c o l a _ j u s t a 
 
 
 
 d e f   a p r o b a r _ s i g u i e n t e _ c a n c i o n _ l a z y ( d b :   S e s s i o n ) : 
 
         " " " 
 
         A p r u e b a   l a   s i g u i e n t e   c a n c i � � n   d e   l a   c o l a   l a z y . 
 
         L l a m a d a   a u t o m � � t i c a m e n t e   c u a n d o   l a   c a n c i � � n   a c t u a l   l l e g a   a l   5 0 % . 
 
         " " " 
 
         c o l a _ l a z y   =   g e t _ c o l a _ l a z y ( d b ) 
 
         i f   n o t   c o l a _ l a z y : 
 
                 r e t u r n   N o n e 
 
         
 
         s i g u i e n t e   =   c o l a _ l a z y [ 0 ] 
 
         s i g u i e n t e . e s t a d o   =   " a p r o b a d o " 
 
         s i g u i e n t e . a p p r o v e d _ a t   =   n o w _ b o g o t a ( ) 
 
         d b . c o m m i t ( ) 
 
         d b . r e f r e s h ( s i g u i e n t e ) 
 
         
 
         c r e a t e _ a d m i n _ l o g _ e n t r y ( d b ,   a c t i o n = " L A Z Y _ A P P R O V A L " ,   d e t a i l s = f " C a n c i � � n   ' { s i g u i e n t e . t i t u l o } '   a p r o b a d a   a u t o m � � t i c a m e n t e   ( l a z y ) . " ) 
 
         r e t u r n   s i g u i e n t e 
 
 
 
 d e f   g e t _ c o l a _ c o m p l e t a _ c o n _ l a z y ( d b :   S e s s i o n ) : 
 
         " " " 
 
         V e r s i � � n   e x t e n d i d a   d e   g e t _ c o l a _ c o m p l e t a   q u e   i n c l u y e   l a   c o l a   l a z y . 
 
         R e t o r n a : 
 
         -   n o w _ p l a y i n g :   C a n c i � � n   a c t u a l 
 
         -   u p c o m i n g :   S o l o   l a   s i g u i e n t e   c a n c i � � n   a p r o b a d a   ( m � � x i m o   1 ) 
 
         -   l a z y _ q u e u e :   C a n c i o n e s   e n   p e n d i e n t e _ l a z y 
 
         -   p e n d i n g :   C a n c i o n e s   p e n d i e n t e s   d e   a p r o b a c i � � n   m a n u a l 
 
         " " " 
 
         #   A p l i c a r   a p r o b a c i � � n   a u t o m � � t i c a   d e s p u � � s   d e   1 0   m i n u t o s 
 
         a u t o _ a p p r o v e _ s o n g s _ a f t e r _ 1 0 _ m i n u t e s ( d b ) 
 
         
 
         n o w _ p l a y i n g   =   d b . q u e r y ( m o d e l s . C a n c i o n ) . f i l t e r ( m o d e l s . C a n c i o n . e s t a d o   = =   " r e p r o d u c i e n d o " ) . f i r s t ( ) 
 
         a p p r o v e d _ q u e u e   =   g e t _ c o l a _ p r i o r i z a d a ( d b ) 
 
         l a z y _ q u e u e   =   g e t _ c o l a _ l a z y ( d b ) 
 
         p e n d i n g _ q u e u e   =   g e t _ c a n c i o n e s _ p e n d i e n t e s _ p o r _ a p r o b a r ( d b ) 
 
         
 
         #   S i   l a   c a n c i � � n   q u e   s e   e s t � �   r e p r o d u c i e n d o   s i g u e   e n   l a   l i s t a   d e   u p c o m i n g ,   l a   q u i t a m o s 
 
         i f   n o w _ p l a y i n g : 
 
                 a p p r o v e d _ q u e u e   =   [ s o n g   f o r   s o n g   i n   a p p r o v e d _ q u e u e   i f   s o n g . i d   ! =   n o w _ p l a y i n g . i d ] 
 
         
 
         #   L i m i t a r   u p c o m i n g   a   m � � x i m o   1   c a n c i � � n   ( l a   s i g u i e n t e ) 
 
         u p c o m i n g _ l i m i t e d   =   a p p r o v e d _ q u e u e [ : 1 ]   i f   a p p r o v e d _ q u e u e   e l s e   [ ] 
 
         
 
         r e t u r n   { 
 
                 " n o w _ p l a y i n g " :   n o w _ p l a y i n g , 
 
                 " u p c o m i n g " :   u p c o m i n g _ l i m i t e d , 
 
                 " l a z y _ q u e u e " :   l a z y _ q u e u e , 
 
                 " p e n d i n g " :   p e n d i n g _ q u e u e 
 
         } 
 
 
 
 d e f   c h e c k _ a n d _ a p p r o v e _ n e x t _ l a z y _ s o n g ( d b :   S e s s i o n ) : 
 
         " " " 
 
         V e r i f i c a   s i   l a   c a n c i � � n   a c t u a l   h a   l l e g a d o   a l   5 0 %   y   a p r u e b a   l a   s i g u i e n t e   l a z y . 
 
         E s t a   f u n c i � � n   e s   l l a m a d a   p o r   u n   b a c k g r o u n d   t a s k   p e r i � � d i c a m e n t e . 
 
         " " " 
 
         n o w _ p l a y i n g   =   d b . q u e r y ( m o d e l s . C a n c i o n ) . f i l t e r ( m o d e l s . C a n c i o n . e s t a d o   = =   " r e p r o d u c i e n d o " ) . f i r s t ( ) 
 
         
 
         i f   n o t   n o w _ p l a y i n g   o r   n o t   n o w _ p l a y i n g . s t a r t e d _ a t : 
 
                 r e t u r n   N o n e 
 
         
 
         #   C a l c u l a r   e l   p r o g r e s o 
 
         t i e m p o _ t r a n s c u r r i d o   =   ( n o w _ b o g o t a ( )   -   n o w _ p l a y i n g . s t a r t e d _ a t ) . t o t a l _ s e c o n d s ( ) 
 
         d u r a c i o n _ t o t a l   =   n o w _ p l a y i n g . d u r a c i o n _ s e c o n d s   o r   0 
 
         
 
         i f   d u r a c i o n _ t o t a l   = =   0 : 
 
                 r e t u r n   N o n e 
 
         
 
         p r o g r e s o _ p o r c e n t a j e   =   ( t i e m p o _ t r a n s c u r r i d o   /   d u r a c i o n _ t o t a l )   *   1 0 0 
 
         
 
         #   S i   h a   l l e g a d o   a l   5 0 %   o   m � � s ,   a p r o b a r   l a   s i g u i e n t e 
 
         i f   p r o g r e s o _ p o r c e n t a j e   > =   5 0 : 
 
                 #   V e r i f i c a r   q u e   n o   h a y a   y a   u n a   c a n c i � � n   a p r o b a d a   e s p e r a n d o 
 
                 a p p r o v e d _ c o u n t   =   d b . q u e r y ( m o d e l s . C a n c i o n ) . f i l t e r ( m o d e l s . C a n c i o n . e s t a d o   = =   " a p r o b a d o " ) . c o u n t ( ) 
 
                 
 
                 i f   a p p r o v e d _ c o u n t   = =   0 : 
 
                         #   A p r o b a r   l a   s i g u i e n t e   c a n c i � � n   l a z y 
 
                         r e t u r n   a p r o b a r _ s i g u i e n t e _ c a n c i o n _ l a z y ( d b ) 
 
         
 
         r e t u r n   N o n e 
 
 

# --- Lazy Approval Queue Functions ---

def get_cola_lazy(db: Session):
    """
    Obtiene todas las canciones en estado pendiente_lazy, ordenadas por prioridad.
    Usa el mismo algoritmo de cola justa que get_cola_priorizada.
    """
    from collections import deque
    
    # Obtener todas las canciones en estado pendiente_lazy
    todas_canciones = (
        db.query(models.Cancion)
        .join(models.Usuario, models.Cancion.usuario_id == models.Usuario.id)
        .filter(models.Cancion.estado == "pendiente_lazy")
        .order_by(models.Cancion.orden_manual.asc().nulls_last(), models.Cancion.id.asc())
        .all()
    )
    
    if not todas_canciones:
        return []
    
    # Aplicar el mismo algoritmo de cola justa
    cola_manual = []
    cola_pool = []
    
    for cancion in todas_canciones:
        if cancion.orden_manual is not None:
            cola_manual.append(cancion)
        else:
            cola_pool.append(cancion)
    
    if not cola_pool:
        return cola_manual
    
    # Agrupar por mesa
    match_mesa_canciones = {}
    mesa_arrival_time = {}
    mesas_involucradas_ids = set()
    
    for cancion in cola_pool:
        mesa_id = cancion.usuario.mesa_id or 0
        if mesa_id not in match_mesa_canciones:
            match_mesa_canciones[mesa_id] = deque()
            mesa_arrival_time[mesa_id] = cancion.id
            mesas_involucradas_ids.add(mesa_id)
        match_mesa_canciones[mesa_id].append(cancion)
    
    # Calcular quotas
    UMBRAL_ORO = 150000
    UMBRAL_PLATA = 50000
    mesa_quotas = {}
    
    if mesas_involucradas_ids:
        ids_reales = [mid for mid in mesas_involucradas_ids if mid != 0]
        consumos_mesas = {}
        
        if ids_reales:
            rows = (
                db.query(
                    models.Usuario.mesa_id,
                    func.sum(models.Consumo.valor_total)
                )
                .join(models.Consumo, models.Usuario.id == models.Consumo.usuario_id)
                .filter(models.Usuario.mesa_id.in_(ids_reales))
                .group_by(models.Usuario.mesa_id)
                .all()
            )
            for mid, total in rows:
                consumos_mesas[mid] = total or 0
        
        for mid in mesas_involucradas_ids:
            total = consumos_mesas.get(mid, 0)
            if mid == 0:
                quota = 3
            elif total >= UMBRAL_ORO:
                quota = 3
            elif total >= UMBRAL_PLATA:
                quota = 2
            else:
                quota = 1
            mesa_quotas[mid] = quota
    
    # Round Robin
    cola_justa = []
    orden_turnos_mesas = sorted(mesas_involucradas_ids, key=lambda mid: mesa_arrival_time[mid])
    
    while match_mesa_canciones:
        for mesa_id in orden_turnos_mesas:
            if mesa_id not in match_mesa_canciones:
                continue
            queue_de_mesa = match_mesa_canciones[mesa_id]
            cupo = mesa_quotas.get(mesa_id, 1)
            tomadas = 0
            while tomadas < cupo and queue_de_mesa:
                cancion = queue_de_mesa.popleft()
                cola_justa.append(cancion)
                tomadas += 1
            if not queue_de_mesa:
                del match_mesa_canciones[mesa_id]
    
    return cola_manual + cola_justa

def aprobar_siguiente_cancion_lazy(db: Session):
    """
    Aprueba la siguiente canción de la cola lazy.
    Llamada automáticamente cuando la canción actual llega al 50%.
    """
    cola_lazy = get_cola_lazy(db)
    if not cola_lazy:
        return None
    
    siguiente = cola_lazy[0]
    siguiente.estado = "aprobado"
    siguiente.approved_at = now_bogota()
    db.commit()
    db.refresh(siguiente)
    
    create_admin_log_entry(db, action="LAZY_APPROVAL", details=f"Cancion '{siguiente.titulo}' aprobada automaticamente (lazy).")
    return siguiente

def get_cola_completa_con_lazy(db: Session):
    """
    Versión extendida de get_cola_completa que incluye la cola lazy.
    Retorna:
    - now_playing: Canción actual
    - upcoming: Solo la siguiente canción aprobada (máximo 1)
    - lazy_queue: Canciones en pendiente_lazy
    - pending: Canciones pendientes de aprobación manual
    """
    # Aplicar aprobación automática después de 10 minutos
    auto_approve_songs_after_10_minutes(db)
    
    now_playing = db.query(models.Cancion).filter(models.Cancion.estado == "reproduciendo").first()
    approved_queue = get_cola_priorizada(db)
    lazy_queue = get_cola_lazy(db)
    pending_queue = get_canciones_pendientes_por_aprobar(db)
    
    # Si la canción que se está reproduciendo sigue en la lista de upcoming, la quitamos
    if now_playing:
        approved_queue = [song for song in approved_queue if song.id != now_playing.id]
    
    # Limitar upcoming a máximo 1 canción (la siguiente)
    upcoming_limited = approved_queue[:1] if approved_queue else []
    
    return {
        "now_playing": now_playing,
        "upcoming": upcoming_limited,
        "lazy_queue": lazy_queue,
        "pending": pending_queue
    }

def check_and_approve_next_lazy_song(db: Session):
    """
    Verifica si la canción actual ha llegado al 50% y aprueba la siguiente lazy.
    Esta función es llamada por un background task periódicamente.
    """
    now_playing = db.query(models.Cancion).filter(models.Cancion.estado == "reproduciendo").first()
    
    if not now_playing or not now_playing.started_at:
        return None
    
    # Calcular el progreso
    tiempo_transcurrido = (now_bogota() - now_playing.started_at).total_seconds()
    duracion_total = now_playing.duracion_seconds or 0
    
    if duracion_total == 0:
        return None
    
    progreso_porcentaje = (tiempo_transcurrido / duracion_total) * 100
    
    # Si ha llegado al 50% o más, aprobar la siguiente
    if progreso_porcentaje >= 50:
        # Verificar que no haya ya una canción aprobada esperando
        approved_count = db.query(models.Cancion).filter(models.Cancion.estado == "aprobado").count()
        
        if approved_count == 0:
            # Aprobar la siguiente canción lazy
            return aprobar_siguiente_cancion_lazy(db)
    
    return None
