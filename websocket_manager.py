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
            now_playing = db.query(models.Cancion).filter(models.Cancion.estado == "reproduciendo").first()
            upcoming = db.query(models.Cancion).filter(models.Cancion.estado == "pendiente").order_by(models.Cancion.created_at).all()
            
            queue_data = {
                "now_playing": jsonable_encoder(now_playing),
                "upcoming": jsonable_encoder(upcoming)
            }
            
            payload = {"type": "queue_update", "payload": queue_data}
            await self._broadcast(json.dumps(payload, default=str))
        except Exception as e:
            print(f"Error broadcasting queue update: {e}")
        finally:
            db.close()

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

    async def broadcast_play_song(self, youtube_id: str, duration_seconds: int = 0):
        """
        Envía un evento para reproducir una canción en el reproductor.
        Incluye la duración para permitir el autoplay automático.
        """
        payload = {
            "type": "play_song", 
            "payload": {
                "youtube_id": youtube_id,
                "duracion_seconds": duration_seconds
            }
        }
        await self._broadcast(json.dumps(payload))

    async def broadcast_restart_song(self):
        """
        Envía un evento para reiniciar la canción actual en el reproductor.
        """
        payload = {"type": "restart_song"}
        await self._broadcast(json.dumps(payload))

    async def broadcast_notification(self, mensaje: str):
        """
        Envía un mensaje de notificación global a todas las pantallas conectadas.
        """
        payload = {
            "type": "notification",
            "payload": {
                "mensaje": mensaje
            }
        }
        await self._broadcast(json.dumps(payload))

manager = ConnectionManager()