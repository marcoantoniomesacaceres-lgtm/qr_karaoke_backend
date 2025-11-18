from fastapi import APIRouter, Response, HTTPException
import requests
from functools import lru_cache

router = APIRouter(prefix="/proxy_thumbnail", tags=["Thumbnails"])

@lru_cache(maxsize=100)
def fetch_thumbnail(youtube_id: str) -> bytes:
    """
    Función auxiliar para obtener la miniatura de YouTube con caché.
    """
    url = f"https://i.ytimg.com/vi/{youtube_id}/mqdefault.jpg"
    r = requests.get(url, timeout=5)
    r.raise_for_status()  # lanza error si no encuentra la imagen
    return r.content

@router.get("/{youtube_id}")
def proxy_thumbnail(youtube_id: str):
    """
    Sirve la miniatura de YouTube desde el backend (evita el aviso de Tracking Prevention).
    """
    try:
        image_data = fetch_thumbnail(youtube_id)
        return Response(content=image_data, media_type="image/jpeg")
    except Exception:
        raise HTTPException(status_code=404, detail="Miniatura no encontrada")