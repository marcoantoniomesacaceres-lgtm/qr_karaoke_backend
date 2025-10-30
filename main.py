from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv
import logging

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# --- Bloque de prueba para verificar variables de entorno ---
print("YOUTUBE_API_KEY cargada:", os.getenv("YOUTUBE_API_KEY"))

from database import engine
import models, crud, schemas, broadcast
import mesas, canciones, youtube, consumos, usuarios, admin, productos, websocket_manager

# --- Configuración de Logging a un archivo ---
# Esto crea un logger que guarda todo en 'karaoke_debug.log'
# y también lo muestra en la consola.
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Handler para el archivo
file_handler = logging.FileHandler("karaoke_debug.log", mode='a', encoding='utf-8') # 'a' para añadir (append), no reescribir.
file_handler.setFormatter(log_formatter)

# Handler para la consola
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
logger = logging.getLogger(__name__)
# ------------------------------------------------

# Esto crea las tablas en la base de datos si no existen
# En un entorno de producción, es mejor usar migraciones (ej. Alembic)
models.Base.metadata.create_all(bind=engine)

# --- Creación de entidades iniciales (como el usuario DJ) ---
from database import SessionLocal

def setup_initial_data():
    db = SessionLocal()
    try:
        crud.get_or_create_dj_user(db)
    finally:
        db.close()

setup_initial_data()
app = FastAPI(title="Karaoke 'LA CANTA QUE RANA'")

@app.on_event("startup")
def startup_event():
    """
    Asegura que la mesa base 'karaoke-mesa-01' exista al iniciar la aplicación.
    Ahora crea las primeras 30 mesas si no existen.
    """
    db = SessionLocal()

    mesas_a_crear = []
    for i in range(1, 31): # Crear 30 mesas
        mesas_a_crear.append({"nombre": f"Mesa {i}", "qr_code": f"karaoke-mesa-{i:02d}"})

    for mesa_data in mesas_a_crear:
        mesa_existente = crud.get_mesa_by_qr(db, mesa_data["qr_code"])
        if not mesa_existente:
            crud.create_mesa(db=db, mesa=schemas.MesaCreate(**mesa_data))
            print(f"✅ Mesa creada: {mesa_data['nombre']} ({mesa_data['qr_code']})")
        else:
            print(f"ℹ️ Mesa ya existente: {mesa_data['nombre']} ({mesa_data['qr_code']})")
    db.close()

@app.get("/", response_class=FileResponse, include_in_schema=False)
async def read_index():
    """
    Sirve la aplicación de frontend (el archivo index.html).
    """
    return FileResponse(os.path.join("static", "index.html"))

@app.get("/admin", response_class=FileResponse, include_in_schema=False)
async def read_admin_index():
    """
    Sirve la página de login para administradores.
    """
    return FileResponse(os.path.join("static", "admin.html"))

@app.get("/admin/dashboard", response_class=FileResponse, include_in_schema=False)
async def read_admin_dashboard():
    """Sirve el panel de control del administrador."""
    return FileResponse(os.path.join("static", "admin_dashboard.html"))

@app.get("/player", response_class=FileResponse, include_in_schema=False)
async def read_player():
    """Sirve la página del reproductor de video."""
    return FileResponse(os.path.join("static", "player.html"))

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
app.include_router(broadcast.router, prefix="/api/v1/broadcast", tags=["Broadcast"])

# Monta la carpeta 'static' (sirve archivos estáticos en /static)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Sirve el favicon en la ruta /favicon.ico
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join("static", "favicon.ico"))