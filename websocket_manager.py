import json
from typing import List
from fastapi import WebSocket
import models
from fastapi.encoders import jsonable_encoder

import schemas, crud
from database import SessionLocal

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            # already removed
            pass

    async def _broadcast(self, message: str):
        """Método auxiliar para enviar un mensaje a todas las conexiones activas."""
        dead_connections = []
        # Hacemos una copia de la lista para poder modificarla mientras iteramos
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(message)
            except Exception:
                # Si el envío falla, marcamos la conexión para eliminarla.
                dead_connections.append(connection)

        # Eliminamos las conexiones muertas de la lista activa.
        for connection in dead_connections:
            try:
                self.active_connections.remove(connection)
            except ValueError:
                # La conexión ya fue eliminada, lo ignoramos.
                pass

    async def broadcast_queue_update(self):
        """Obtiene la cola actualizada y la envía a todos los clientes."""
        db = SessionLocal()
        try:
            # Buscamos la canción que se está reproduciendo y la cola de las próximas
            now_playing = db.query(crud.models.Cancion).filter(crud.models.Cancion.estado == "reproduciendo").first()
            upcoming = crud.get_cola_priorizada(db)

            # Si la canción que se está reproduciendo sigue en la lista de 'upcoming', la quitamos.
            if now_playing:
                upcoming = [song for song in upcoming if song.id != now_playing.id]

            # Creamos el objeto de respuesta
            cola_view = schemas.ColaView(now_playing=now_playing, upcoming=upcoming)

            # CORRECCIÓN: Usamos jsonable_encoder para convertir el objeto a un diccionario serializable
            # y luego json.dumps para crear la cadena JSON. Esto maneja correctamente los objetos de la DB.
            json_payload = json.dumps(jsonable_encoder(cola_view))

            await self._broadcast(json_payload)
        finally:
            db.close()

    async def broadcast_notification(self, mensaje: str):
        """Envía un mensaje de notificación general a todos los clientes."""
        payload = {"type": "notification", "payload": {"mensaje": mensaje}}
        await self._broadcast(json.dumps(payload))

    async def broadcast_product_update(self):
        """Envía una notificación para que los clientes recarguen el catálogo de productos."""
        payload = {"type": "product_update"}
        await self._broadcast(json.dumps(payload))

    async def broadcast_consumo_created(self, consumo_payload: dict):
        """
        Envía un evento indicando que se creó un nuevo consumo.
        """
        payload = {"type": "consumo_created", "payload": consumo_payload}
        await self._broadcast(json.dumps(payload, default=str))

    async def broadcast_pedido_created(self, pedido_payload: dict):
        """
        Envía un evento indicando que se creó un nuevo pedido consolidado.
        """
        payload = {"type": "pedido_created", "payload": pedido_payload}
        await self._broadcast(json.dumps(payload, default=str))

    async def broadcast_consumo_deleted(self, consumo_payload: dict):
        """
        Envía un evento indicando que un consumo fue eliminado.
        """
        payload = {"type": "consumo_deleted", "payload": consumo_payload}
        await self._broadcast(json.dumps(payload))

    async def broadcast_reaction(self, reaction_payload: dict):
        """
        Envía una reacción (emoticono) a todos los clientes.
        """
        payload = {"type": "reaction", "payload": reaction_payload}
        await self._broadcast(json.dumps(payload))

    async def broadcast_song_finished(self, cancion: models.Cancion):
        """
        Envía un evento indicando que una canción ha terminado y su puntuación.
        """
        # Determinar el nombre del cantante (mesa o nick)
        cantante = cancion.usuario.mesa.nombre if (cancion.usuario and cancion.usuario.mesa) else (cancion.usuario.nick if cancion.usuario else "N/A")
        payload = {
            "type": "song_finished",
            "payload": {
                "titulo": cancion.titulo,
                "usuario_nick": cantante, # Reutilizamos el campo 'usuario_nick' que espera el frontend
                "puntuacion_ia": cancion.puntuacion_ia
            }
        }
        await self._broadcast(json.dumps(payload))

    async def broadcast_play_song(self, youtube_id: str):
        """
        Envía un evento para reproducir una canción en el reproductor,
        utilizando el dominio de youtube-nocookie para mayor privacidad.
        """
        video_url = f"https://www.youtube-nocookie.com/embed/{youtube_id}"
        payload = {"type": "play_song", "payload": {"youtube_url": video_url}}
        await self._broadcast(json.dumps(payload))

manager = ConnectionManager()