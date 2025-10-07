from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .database import engine
from . import models
from .api.v1.endpoints import mesas, canciones, youtube, consumos, usuarios, admin
from .websockets import manager

# Esto crea las tablas en la base de datos si no existen
# En un entorno de producción, es mejor usar migraciones (ej. Alembic)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Karaoke 'La Rana que Canta'")

@app.get("/")
def read_root():
    return {"mensaje": "¡Bienvenido a la API de La Rana que Canta!"}

# Endpoint de WebSocket para la cola en tiempo real
@app.websocket("/ws/cola")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Envía la cola actual tan pronto como el cliente se conecta
    await manager.broadcast_queue_update()
    try:
        while True:
            # Mantenemos la conexión abierta esperando mensajes (aunque no los usemos)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Opcional: podrías querer notificar una desconexión
        # await manager.broadcast_queue_update()

# Incluimos los routers de la API REST
app.include_router(mesas.router, prefix="/api/v1/mesas", tags=["Mesas"])
app.include_router(canciones.router, prefix="/api/v1/canciones", tags=["Canciones"])
app.include_router(youtube.router, prefix="/api/v1/youtube", tags=["YouTube"])
app.include_router(consumos.router, prefix="/api/v1/consumos", tags=["Consumos"])
app.include_router(usuarios.router, prefix="/api/v1/usuarios", tags=["Usuarios"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administración"])
