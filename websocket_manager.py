import json
from typing import List
from fastapi import WebSocket

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
            # Si una conexión falla, la eliminamos para evitar que futuras emisiones fallen.
            dead = []
            for connection in list(self.active_connections):
                try:
                    await connection.send_text(cola_view.json())
                except Exception:
                    # Intentamos desconectar y marcamos como muerta
                    try:
                        # close() is async on WebSocket so await it if possible
                        await connection.close()
                    except Exception:
                        pass
                    dead.append(connection)
            # Remove any dead connections from the active list
            for d in dead:
                if d in self.active_connections:
                    try:
                        self.active_connections.remove(d)
                    except ValueError:
                        pass

            # return number removed for observability (not required)
            return len(dead)
        finally:
            db.close()

    async def broadcast_notification(self, mensaje: str):
        """Envía un mensaje de notificación general a todos los clientes."""
        payload = {
            "type": "notification",
            "payload": {"mensaje": mensaje}
        }
        dead = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(payload))
            except Exception:
                try:
                    await connection.close()
                except Exception:
                    pass
                dead.append(connection)
        for d in dead:
            if d in self.active_connections:
                try:
                    self.active_connections.remove(d)
                except ValueError:
                    pass
        return len(dead)

    async def broadcast_product_update(self):
        """Envía una notificación para que los clientes recarguen el catálogo de productos."""
        payload = {
            "type": "product_update"
        }
        dead = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(payload))
            except Exception:
                try:
                    await connection.close()
                except Exception:
                    pass
                dead.append(connection)
        for d in dead:
            if d in self.active_connections:
                try:
                    self.active_connections.remove(d)
                except ValueError:
                    pass
        return len(dead)

    async def broadcast_consumo_created(self, consumo_payload: dict):
        """
        Envía un evento indicando que se creó un nuevo consumo.
        El payload debe ser un diccionario serializable que contenga
        fields como producto_nombre, usuario_nick, mesa_nombre, cantidad, created_at, etc.
        """
        payload = {
            "type": "consumo_created",
            "payload": consumo_payload
        }
        dead = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(payload))
            except Exception:
                try:
                    await connection.close()
                except Exception:
                    pass
                dead.append(connection)
        for d in dead:
            if d in self.active_connections:
                try:
                    self.active_connections.remove(d)
                except ValueError:
                    pass
        return len(dead)

    async def broadcast_consumo_deleted(self, consumo_payload: dict):
        """
        Envía un evento indicando que un consumo fue eliminado.
        El payload típicamente contiene al menos {'id': consumo_id}.
        """
        payload = {
            "type": "consumo_deleted",
            "payload": consumo_payload
        }
        dead = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(payload))
            except Exception:
                try:
                    await connection.close()
                except Exception:
                    pass
                dead.append(connection)
        for d in dead:
            if d in self.active_connections:
                try:
                    self.active_connections.remove(d)
                except ValueError:
                    pass
        return len(dead)

    async def broadcast_consumo_deleted(self, consumo_id: int):
        """
        Envía un evento indicando que se eliminó un consumo.
        """
        payload = {
            "type": "consumo_deleted",
            "payload": {"id": consumo_id}
        }
        dead = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(payload))
            except Exception:
                try:
                    await connection.close()
                except Exception:
                    pass
                dead.append(connection)
        for d in dead:
            if d in self.active_connections:
                try:
                    self.active_connections.remove(d)
                except ValueError:
                    pass
        return len(dead)

manager = ConnectionManager()