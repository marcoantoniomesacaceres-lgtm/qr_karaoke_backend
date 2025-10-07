from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from typing import List

from app import crud, config, schemas
from app.database import SessionLocal
from app.websockets import manager
from app.security import api_key_auth

router = APIRouter(dependencies=[Depends(api_key_auth)])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/reset-night", status_code=204, summary="Reiniciar el sistema para una nueva noche")
async def reset_night(db: Session = Depends(get_db)):
    """
    **[Admin - ¡ACCIÓN DESTRUCTIVA!]** Borra todos los datos de la noche:
    mesas, usuarios, canciones y consumos.
    Útil para empezar de cero al día siguiente.
    """
    crud.reset_database_for_new_night(db)
    # Después de borrar todo, notificamos a los clientes para que la cola se vacíe
    await manager.broadcast_queue_update()
    return Response(status_code=204)

@router.post("/set-closing-time", status_code=200, summary="Establecer la hora de cierre")
def set_closing_time(closing_time: schemas.ClosingTimeUpdate):
    """
    **[Admin]** Actualiza la hora de cierre del karaoke en tiempo real.
    El formato debe ser "HH:MM".
    """
    # Aquí se podría añadir una validación del formato de la hora
    config.settings.KARAOKE_CIERRE = closing_time.hora_cierre
    return {"mensaje": f"La hora de cierre ha sido actualizada a {config.settings.KARAOKE_CIERRE}"}

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
            producto=producto,
            cantidad_total=cantidad_total
        )
        for producto, cantidad_total in top_products_data
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
    await manager.broadcast_queue_update()
    return {"mensaje": "La cola ha sido reordenada manualmente."}

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