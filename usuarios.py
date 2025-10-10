from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from security import api_key_auth # Importamos la seguridad

import crud, schemas
from database import SessionLocal

router = APIRouter()

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/by-nick/{nick}", response_model=schemas.UsuarioPublico, summary="Buscar un usuario por su nick")
def get_user_by_nick(nick: str, db: Session = Depends(get_db), api_key: str = Depends(api_key_auth)):
    """
    **[Admin]** Busca y devuelve un usuario específico por su nick.
    Es útil para encontrar usuarios del sistema como 'DJ'.
    """
    db_usuario = crud.get_usuario_by_nick(db, nick=nick)
    if not db_usuario:
        raise HTTPException(status_code=404, detail=f"Usuario con nick '{nick}' no encontrado.")
    
    return db_usuario

@router.get("/{usuario_id}", response_model=schemas.UsuarioPublico, summary="Ver el perfil público de un usuario")
def ver_perfil_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """
    Devuelve la información pública de un usuario, como su nivel y puntos.
    No incluye información sensible como el consumo total.
    """
    db_usuario = crud.get_usuario_by_id(db, usuario_id=usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return db_usuario

@router.get("/", response_model=List[schemas.UsuarioPerfil], summary="Ver el ranking de usuarios")
def ver_ranking_usuarios(db: Session = Depends(get_db)):
    """
    Devuelve una lista de todos los usuarios ordenados por su consumo total
    de mayor a menor (ranking de clientes).
    """
    ranking_data = crud.get_ranking_usuarios(db)
    
    # Convertimos la lista de tuplas a una lista de objetos UsuarioPerfil, añadiendo la posición
    ranking_list = []
    for i, (usuario, total) in enumerate(ranking_data):
        perfil = schemas.UsuarioPerfil(
            **usuario.__dict__, 
            total_consumido=total,
            rank=i + 1,  # El ranking empieza en 1
            mesa=usuario.mesa  # Añadimos la información de la mesa
        )
        ranking_list.append(perfil)
    
    return ranking_list