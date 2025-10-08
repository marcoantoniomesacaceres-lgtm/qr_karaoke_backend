from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from database import engine
import models
import mesas, canciones, youtube, consumos, usuarios, admin, productos, websocket_manager

# Esto crea las tablas en la base de datos si no existen
# En un entorno de producción, es mejor usar migraciones (ej. Alembic)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Karaoke 'La Rana que Canta'")

@app.get("/", response_class=FileResponse, include_in_schema=False)
async def read_index():
    """
    Sirve la aplicación de frontend (el archivo index.html).
    """
    return FileResponse(os.path.join("static", "index.html"))

# Endpoint de WebSocket para la cola en tiempo real
@app.websocket("/ws/cola")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.manager.connect(websocket)
    # Envía la cola actual tan pronto como el cliente se conecta
    await websocket_manager.manager.broadcast_queue_update()
    try:
        while True:
            # Mantenemos la conexión abierta esperando mensajes (aunque no los usemos)
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.manager.disconnect(websocket)
        # Opcional: podrías querer notificar una desconexión
        # await websocket_manager.manager.broadcast_queue_update()

# Incluimos los routers de la API REST
app.include_router(mesas.router, prefix="/api/v1/mesas", tags=["Mesas"])
app.include_router(canciones.router, prefix="/api/v1/canciones", tags=["Canciones"])
app.include_router(youtube.router, prefix="/api/v1/youtube", tags=["YouTube"])
app.include_router(consumos.router, prefix="/api/v1/consumos", tags=["Consumos"])
app.include_router(usuarios.router, prefix="/api/v1/usuarios", tags=["Usuarios"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administración"])
app.include_router(productos.router, prefix="/api/v1/productos", tags=["Productos"])

# Monta la carpeta 'static' (sirve archivos estáticos en /static)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Sirve el favicon en la ruta /favicon.ico
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join("static", "favicon.ico"))