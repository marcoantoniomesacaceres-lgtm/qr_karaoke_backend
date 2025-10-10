import httpx
import os
import isodate
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from fastapi import Depends # Importar Depends
import re
from urllib.parse import urlparse, parse_qs
import logging

from security import api_key_auth # Importar la función de autenticación
logger = logging.getLogger(__name__)

router = APIRouter()

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

async def _perform_youtube_search(q: str) -> List[Dict[str, Any]]:
    """Función interna que contiene la lógica de búsqueda en YouTube."""
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "TU_API_KEY_DE_YOUTUBE_AQUI":
        logger.error("La API Key de YouTube no está configurada en las variables de entorno.")
        raise HTTPException(
            status_code=500,
            detail="La API Key de YouTube no está configurada en el servidor."
        )

    # Aumentamos el timeout a 30 segundos para evitar errores en redes lentas
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            video_id_from_url = extract_video_id_from_url(q)
            logger.info(f"¿Es una URL? ID extraído: {video_id_from_url}")
            video_ids = []

            if video_id_from_url:
                # Si 'q' es una URL, usamos el ID extraído directamente
                video_ids = [video_id_from_url]
                logger.info(f"Búsqueda por ID de URL: {video_ids}")
            else:
                logger.info(f"Búsqueda por texto: '{q}'")
                # Si 'q' es texto, realizamos una búsqueda normal
                search_params = {
                    "part": "id",
                    "q": q,
                    "key": YOUTUBE_API_KEY,
                    "type": "video",
                    "videoCategoryId": "10",  # Categoría de Música
                    "maxResults": 10
                }
                logger.info("Realizando primera llamada a la API de YouTube (search)...")
                search_response = await client.get(YOUTUBE_SEARCH_URL, params=search_params)
                search_response.raise_for_status()
                search_results = search_response.json()
                logger.info("Respuesta de la API (search) recibida con éxito.")
                video_ids = [item["id"]["videoId"] for item in search_results.get("items", [])]
                logger.info(f"IDs de video encontrados: {video_ids}")

            # Si después de buscar por ID o por texto no encontramos nada, devolvemos una lista vacía.
            # Esto evita un error en la siguiente llamada a la API.
            if not video_ids:
                logger.warning("No se encontraron IDs de video. Devolviendo lista vacía.")
                return []

            # Ahora, obtenemos los detalles (como la duración) de esos videos
            video_params = {
                "part": "contentDetails,snippet",
                "id": ",".join(video_ids),
                "key": YOUTUBE_API_KEY,
            }
            logger.info("Realizando segunda llamada a la API de YouTube (videos)...")
            videos_response = await client.get(YOUTUBE_VIDEOS_URL, params=video_params)
            videos_response.raise_for_status()
            videos_results = videos_response.json()
            logger.info("Respuesta de la API (videos) recibida con éxito. Procesando resultados...")

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
            logger.info(f"Procesamiento finalizado. Se encontraron {len(formatted_results)} resultados formateados.")

        except httpx.HTTPStatusError as exc:
            # Captura errores de estado HTTP, como 4xx o 5xx de la API de YouTube.
            try:
                error_details = exc.response.json().get("error", {}).get("message", "Sin detalles.")
            except Exception:
                error_details = exc.response.text

            logger.error(f"Error de estado HTTP desde la API de YouTube: {exc.response.status_code} - {error_details}")

            # Si el error es un 403 (Forbidden), es muy probable que sea un problema con la API Key.
            if exc.response.status_code == 403:
                raise HTTPException(
                    status_code=403,
                    detail="Acceso denegado por YouTube. Verifica que la API Key sea correcta, no haya expirado y no tenga restricciones de IP."
                )
            
            raise HTTPException(status_code=502, detail=f"Error al comunicarse con YouTube: {error_details}")
        except httpx.RequestError as exc:
            logger.error(f"Error de red al conectar con YouTube: {exc}")
            raise HTTPException(status_code=503, detail=f"Error de red al conectar con YouTube: {exc}")
        except Exception as e:
             logger.error(f"Error inesperado procesando la respuesta de YouTube: {e}", exc_info=True)
             raise HTTPException(status_code=500, detail=f"Error procesando la respuesta de YouTube: {str(e)}")

    return formatted_results

@router.get("/search", summary="[Admin] Buscar videos en YouTube")
async def search_youtube(q: str, api_key: str = Depends(api_key_auth, use_cache=False)) -> List[Dict[str, Any]]:
    """
    Realiza una búsqueda de videos en YouTube utilizando la API oficial.
    Este endpoint actúa como un proxy para no exponer la API Key en el cliente.
    """
    logger.info(f"Búsqueda [Admin] en YouTube con el término: '{q}'")
    return await _perform_youtube_search(q)

@router.get("/public-search", summary="[Público] Buscar videos en YouTube para usuarios")
async def public_search_youtube(q: str) -> List[Dict[str, Any]]:
    """
    Endpoint público para que los usuarios de las mesas busquen videos.
    No requiere API Key. Reutiliza la misma lógica de búsqueda que el endpoint de admin.
    """
    logger.info(f"Búsqueda [Pública] en YouTube con el término: '{q}'")
    return await _perform_youtube_search(q)