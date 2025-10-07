import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

# Definimos el nombre del header que esperamos recibir
api_key_header = APIKeyHeader(name="X-API-Key")

# Obtenemos la clave secreta desde las variables de entorno
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

def api_key_auth(api_key: str = Security(api_key_header)):
    """
    Dependencia que valida la API Key enviada en el header X-API-Key.
    """
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clave de API de administración no está configurada en el servidor."
        )
    if api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Clave de API inválida o ausente."
        )