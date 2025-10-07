import json
from typing import List
from fastapi import WebSocket

from . import schemas, crud
from .database import SessionLocal

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

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

            # Enviamos el JSON a todos los clientes conectados
            for connection in self.active_connections:
                await connection.send_text(cola_view.json())
        finally:
            db.close()

    async def broadcast_notification(self, mensaje: str):
        """Envía un mensaje de notificación general a todos los clientes."""
        payload = {
            "type": "notification",
            "payload": {"mensaje": mensaje}
        }
        for connection in self.active_connections:
            await connection.send_text(json.dumps(payload))

manager = ConnectionManager()