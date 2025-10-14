from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

import crud, schemas, models
from database import SessionLocal
from security import api_key_auth, optional_api_key_auth
import websocket_manager # Importamos el gestor de websockets

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Producto, summary="Crear un nuevo producto en el catálogo")
async def create_product(producto: schemas.ProductoCreate, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    """
    **[Admin]** Añade un nuevo producto al catálogo del karaoke.
    """
    try:
        db_producto = crud.get_producto_by_nombre(db, nombre=producto.nombre)
        if db_producto:
            raise HTTPException(status_code=400, detail="Un producto con este nombre ya existe.")

        new_product = crud.create_producto(db=db, producto=producto)
        crud.create_admin_log_entry(db, action="CREATE_PRODUCT", details=f"Producto '{new_product.nombre}' creado.")
        # Lanzamos el broadcast como tarea de fondo para evitar que fallos en WS provoquen 500s
        try:
            import asyncio
            asyncio.create_task(websocket_manager.manager.broadcast_product_update())
        except Exception:
            # Si no es posible programar la tarea, lo registramos y seguimos
            import logging
            logging.getLogger(__name__).exception("No se pudo programar broadcast de producto")
        return new_product
    except HTTPException:
        # Re-raise HTTP exceptions (client errors)
        raise
    except Exception as e:
        # Log and return a JSON-friendly error so the frontend can parse it
        import logging, traceback
        logging.getLogger(__name__).exception("Error creando producto")
        # As a fallback, also dump the full traceback to a dedicated file so it's easier to find.
        try:
            with open("product_errors.log", "a", encoding="utf-8") as f:
                f.write("--- Product creation exception ---\n")
                traceback.print_exc(file=f)
                f.write("\n")
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Error interno al crear el producto.")

@router.get("/", response_model=List[schemas.Producto], summary="Obtener el catálogo de productos (para admin y usuarios)")
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), api_key: Optional[str] = Depends(optional_api_key_auth)):
    """
    Devuelve una lista de todos los productos disponibles en el catálogo.
    - Si se provee una API Key de admin válida, devuelve todos los productos.
    - Si no, devuelve solo los productos activos y con stock.
    """
    # If api_key is provided and valid (admin), return full catalog; otherwise return only active items with stock
    if not api_key:
        productos = db.query(models.Producto).filter(models.Producto.is_active == True, models.Producto.stock > 0).offset(skip).limit(limit).all()
    else:
        productos = crud.get_productos(db, skip=skip, limit=limit)

    return productos

@router.put("/{producto_id}", response_model=schemas.Producto, summary="Actualizar un producto existente")
async def update_product(producto_id: int, producto: schemas.ProductoCreate, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    """
    **[Admin]** Actualiza todos los detalles de un producto existente en el catálogo.
    """
    db_producto = crud.update_producto(db, producto_id=producto_id, producto_update=producto)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    crud.create_admin_log_entry(db, action="UPDATE_PRODUCT", details=f"Producto '{db_producto.nombre}' (ID: {producto_id}) actualizado.")
    await websocket_manager.manager.broadcast_product_update() # Notificamos
    return db_producto

@router.delete("/{producto_id}", status_code=204, summary="Eliminar un producto del catálogo")
async def delete_product(producto_id: int, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    """
    **[Admin]** Elimina un producto del catálogo permanentemente.
    """
    deleted_product = crud.delete_producto(db, producto_id=producto_id)
    if not deleted_product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    crud.create_admin_log_entry(db, action="DELETE_PRODUCT", details=f"Producto '{deleted_product.nombre}' (ID: {producto_id}) eliminado.")
    await websocket_manager.manager.broadcast_product_update() # Notificamos
    return Response(status_code=204)

@router.put("/{producto_id}/edit-price", response_model=schemas.Producto, summary="Editar el precio de un producto")
async def edit_product_price(producto_id: int, valor_update: schemas.ProductoValorUpdate, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    """
    **[Admin]** Permite editar el precio de un producto del catálogo.
    """
    db_producto = crud.update_producto_valor(db, producto_id=producto_id, nuevo_valor=valor_update.valor)
    if not db_producto:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado."
        )
    
    crud.create_admin_log_entry(db, action="EDIT_PRODUCT_PRICE", details=f"Precio del producto '{db_producto.nombre}' (ID: {producto_id}) cambiado a {valor_update.valor}.")
    await websocket_manager.manager.broadcast_product_update() # Notificamos
    return db_producto

@router.post("/{producto_id}/deactivate", response_model=schemas.Producto, summary="Desactivar un producto")
async def deactivate_product(producto_id: int, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    """
    **[Admin]** Desactiva un producto del catálogo para que no pueda ser pedido.
    """
    db_producto = crud.update_producto_active_status(db, producto_id=producto_id, is_active=False)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    crud.create_admin_log_entry(db, action="DEACTIVATE_PRODUCT", details=f"Producto '{db_producto.nombre}' (ID: {producto_id}) desactivado.")
    await websocket_manager.manager.broadcast_product_update() # Notificamos
    return db_producto

@router.post("/{producto_id}/activate", response_model=schemas.Producto, summary="Reactivar un producto")
async def activate_product(producto_id: int, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    """
    **[Admin]** Reactiva un producto previamente desactivado.
    """
    db_producto = crud.update_producto_active_status(db, producto_id=producto_id, is_active=True)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    crud.create_admin_log_entry(db, action="ACTIVATE_PRODUCT", details=f"Producto '{db_producto.nombre}' (ID: {producto_id}) reactivado.")
    await websocket_manager.manager.broadcast_product_update() # Notificamos
    return db_producto