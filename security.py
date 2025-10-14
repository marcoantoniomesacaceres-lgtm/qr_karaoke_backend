import os
from typing import Optional
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from fastapi import Depends

import crud
from database import SessionLocal

# Definimos el nombre del header que esperamos recibir
api_key_header = APIKeyHeader(name="X-API-Key")
# Variante que no lanza error si el header no está presente (para endpoints públicos)
api_key_header_optional = APIKeyHeader(name="X-API-Key", auto_error=False)

# --- Clave Maestra ---
# Esta clave está fija en el código y siempre funcionará.
# Es tu acceso de emergencia.
MASTER_API_KEY = "zxc12345"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def api_key_auth(api_key: str = Security(api_key_header), db: Session = Depends(get_db)):
    """
    Dependencia que valida la API Key.
    Verifica si la clave coincide con la MAESTRA o si es una clave válida
    y activa en la base de datos.
    """
    # 1. Comprobar si es la clave maestra
    if api_key == MASTER_API_KEY:
        return api_key

    # 2. Si no es la maestra, buscar en la base de datos si es una clave válida
    db_api_key = crud.get_admin_api_key(db, key=api_key)
    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Clave de API inválida o ausente."
        )
    # Devuelve la clave válida para que los endpoints puedan saber que es admin
    return api_key


def optional_api_key_auth(api_key: Optional[str] = Security(api_key_header_optional), db: Session = Depends(get_db)) -> Optional[str]:
    """
    Variante de validación de API key que no falla si no se proporciona la cabecera.
    - Si no se proporciona, devuelve None.
    - Si se proporciona y es válida (maestra o en la BBDD), devuelve la clave.
    - Si se proporciona y es inválida, lanza 403.
    """
    if not api_key:
        return None

    # Comprobar clave maestra
    if api_key == MASTER_API_KEY:
        return api_key

    db_api_key = crud.get_admin_api_key(db, key=api_key)
    if not db_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clave de API inválida o ausente.")

    return api_key