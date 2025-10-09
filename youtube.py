import httpx
import os
import isodate
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import re
from urllib.parse import urlparse, parse_qs

router = APIRouter()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

def extract_video_id_from_url(url: str) -> str | None:
    """
    Extrae el ID de un video de YouTube desde varios formatos de URL.
    """
    if not url:
        return None
    # Expresión regular para encontrar el ID en diferentes tipos de URLs de YouTube
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

@router.get("/search", summary="Buscar videos en YouTube")
async def search_youtube(q: str) -> List[Dict[str, Any]]:
    """
    Realiza una búsqueda de videos en YouTube utilizando la API oficial.
    Este endpoint actúa como un proxy para no exponer la API Key en el cliente.
    """
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "TU_API_KEY_DE_YOUTUBE_AQUI":
        raise HTTPException(
            status_code=500,
            detail="La API Key de YouTube no está configurada en el servidor."
        )

    async with httpx.AsyncClient() as client:
        try:
            video_id_from_url = extract_video_id_from_url(q)
            video_ids = []

            if video_id_from_url:
                # Si 'q' es una URL, usamos el ID extraído directamente
                video_ids = [video_id_from_url]
            else:
                # Si 'q' es texto, realizamos una búsqueda normal
                search_params = {
                    "part": "id",
                    "q": q,
                    "key": YOUTUBE_API_KEY,
                    "type": "video",
                    "videoCategoryId": "10",  # Categoría de Música
                    "maxResults": 10
                }
                search_response = await client.get(YOUTUBE_SEARCH_URL, params=search_params)
                search_response.raise_for_status()
                search_results = search_response.json()
                video_ids = [item["id"]["videoId"] for item in search_results.get("items", [])]

            if not video_ids:
                return []

            # Ahora, obtenemos los detalles (como la duración) de esos videos
            video_params = {
                "part": "contentDetails,snippet",
                "id": ",".join(video_ids),
                "key": YOUTUBE_API_KEY,
            }
            videos_response = await client.get(YOUTUBE_VIDEOS_URL, params=video_params)
            videos_response.raise_for_status()
            videos_results = videos_response.json()

            # Mapeamos los resultados a un formato simple
            formatted_results = []
            for item in videos_results.get("items", []):
                content_details = item.get("contentDetails", {})
                try:
                    duration_iso = content_details.get("duration", "PT0S") # "PT0S" es duración cero
                    duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())
                except (isodate.ISO8601Error, KeyError):
                    duration_seconds = 0

                snippet = item.get("snippet", {})
                title = snippet.get("title", "Título no disponible")

                # Hacemos la obtención de la miniatura más robusta
                thumbnails = snippet.get("thumbnails", {})
                thumbnail_url = "https://via.placeholder.com/120x90.png?text=No+Image" # Imagen por defecto
                if "default" in thumbnails:
                    thumbnail_url = thumbnails["default"]["url"]
                elif "medium" in thumbnails:
                    thumbnail_url = thumbnails["medium"]["url"]

                formatted_results.append({
                    "video_id": item["id"],
                    "title": title,
                    "thumbnail": thumbnail_url,
                    "duration_seconds": duration_seconds,
                })

        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Error de red al conectar con YouTube: {exc}")
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Error procesando la respuesta de YouTube: {str(e)}")

    return formatted_results