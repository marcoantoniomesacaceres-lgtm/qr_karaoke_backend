import httpx
import os
from fastapi import APIRouter, HTTPException
from typing import Any

router = APIRouter()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"

@router.get("/search", summary="Buscar videos en YouTube")
async def search_youtube(q: str) -> Any:
    """
    Realiza una búsqueda de videos en YouTube utilizando la API oficial.
    Este endpoint actúa como un proxy para no exponer la API Key en el cliente.
    """
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "TU_API_KEY_DE_YOUTUBE_AQUI":
        raise HTTPException(
            status_code=500,
            detail="La API Key de YouTube no está configurada en el servidor."
        )

    params = {
        "part": "snippet",
        "q": q,
        "key": YOUTUBE_API_KEY,
        "type": "video",
        "videoCategoryId": "10",  # Categoría de Música
        "maxResults": 15
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(YOUTUBE_API_URL, params=params)
            response.raise_for_status()  # Lanza una excepción para errores 4xx/5xx
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Error de red al conectar con YouTube: {exc}")

    return response.json()