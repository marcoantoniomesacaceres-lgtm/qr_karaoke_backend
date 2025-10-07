from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from . import crud, schemas
from .database import SessionLocal
from .security import api_key_auth

router = APIRouter(dependencies=[Depends(api_key_auth)])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Producto, summary="Crear un nuevo producto en el catálogo")
def create_product(producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    """
    **[Admin]** Añade un nuevo producto al catálogo del karaoke.
    """
    db_producto = crud.get_producto_by_nombre(db, nombre=producto.nombre)
    if db_producto:
        raise HTTPException(status_code=400, detail="Un producto con este nombre ya existe.")
    
    new_product = crud.create_producto(db=db, producto=producto)
    crud.create_admin_log_entry(db, action="CREATE_PRODUCT", details=f"Producto '{new_product.nombre}' creado.")
    return new_product

@router.get("/", response_model=List[schemas.Producto], summary="Obtener el catálogo de productos")
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve una lista de todos los productos disponibles en el catálogo.
    """
    productos = crud.get_productos(db, skip=skip, limit=limit)
    return productos

@router.put("/{producto_id}/edit-price", response_model=schemas.Producto, summary="Editar el precio de un producto")
def edit_product_price(producto_id: int, valor_update: schemas.ProductoValorUpdate, db: Session = Depends(get_db)):
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
    return db_producto

@router.post("/{producto_id}/deactivate", response_model=schemas.Producto, summary="Desactivar un producto")
def deactivate_product(producto_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Desactiva un producto del catálogo para que no pueda ser pedido.
    """
    db_producto = crud.update_producto_active_status(db, producto_id=producto_id, is_active=False)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    crud.create_admin_log_entry(db, action="DEACTIVATE_PRODUCT", details=f"Producto '{db_producto.nombre}' (ID: {producto_id}) desactivado.")
    return db_producto

@router.post("/{producto_id}/activate", response_model=schemas.Producto, summary="Reactivar un producto")
def activate_product(producto_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Reactiva un producto previamente desactivado.
    """
    db_producto = crud.update_producto_active_status(db, producto_id=producto_id, is_active=True)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    crud.create_admin_log_entry(db, action="ACTIVATE_PRODUCT", details=f"Producto '{db_producto.nombre}' (ID: {producto_id}) reactivado.")
    return db_producto