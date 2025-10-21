from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud, schemas
import crud, schemas, config
from database import SessionLocal
from security import api_key_auth

router = APIRouter()

# Dependencia para obtener la sesión de la base de datos en cada request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Mesa, status_code=201, summary="Crear una nueva mesa", dependencies=[Depends(api_key_auth)])
def create_mesa_endpoint(
    mesa: schemas.MesaCreate, 
    db: Session = Depends(get_db)
):
    """
    Crea una nueva mesa en el sistema con un nombre y un código QR único.
    """
    db_mesa = crud.get_mesa_by_qr(db, qr_code=mesa.qr_code)
    if db_mesa:
        raise HTTPException(status_code=400, detail="El código QR ya está registrado")
    return crud.create_mesa(db=db, mesa=mesa)

@router.post("/{qr_code}/conectar", response_model=schemas.Usuario, summary="Conectar un usuario a una mesa")
def conectar_usuario_a_mesa(
    qr_code: str, usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)
):
    """
    Busca una mesa por su QR y crea un nuevo usuario asociado a ella.
    Este es el endpoint que el cliente usa al escanear el QR.
    """
    db_mesa = crud.get_mesa_by_qr(db, qr_code=qr_code)
    if not db_mesa:
        raise HTTPException(status_code=404, detail=f"El código QR '{qr_code}' no corresponde a ninguna mesa válida.")
    
    if crud.is_nick_banned(db, nick=usuario.nick):
        raise HTTPException(status_code=403, detail="Este nick de usuario ha sido bloqueado y no puede registrarse.")

    # Verificamos si el nick ya está en uso por otro usuario
    db_usuario_existente = crud.get_usuario_by_nick(db, nick=usuario.nick)
    if db_usuario_existente:
        raise HTTPException(status_code=409, detail=f"El apodo '{usuario.nick}' ya está en uso. Por favor, elige otro.")

    return crud.create_usuario_en_mesa(db=db, usuario=usuario, mesa_id=db_mesa.id)