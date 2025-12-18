from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
import logging

# ===============================
# CARGA DE VARIABLES DE ENTORNO
# ===============================
load_dotenv()

print("YOUTUBE_API_KEY cargada:", os.getenv("YOUTUBE_API_KEY"))

# ===============================
# BASE DE DATOS
# ===============================
from database import engine, SessionLocal
import models

models.Base.metadata.create_all(bind=engine)

import crud, schemas, broadcast, thumbnails
import mesas, canciones, youtube, consumos, usuarios, admin, productos, websocket_manager
from admin_settings_router import router as settings_router
from admin_extra_router import router as admin_extra_router

# ===============================
# LOGGING
# ===============================
log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

file_handler = logging.FileHandler(
    "karaoke_debug.log", mode='a', encoding='utf-8'
)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)

# ===============================
# APP FASTAPI
# ===============================
app = FastAPI(title="Karaoke 'LA CANTA QUE RANA'")

# ===============================
# ✅ HEALTH CHECK PARA RENDER
# ===============================
@app.get("/salud", include_in_schema=False)
def health_check():
    return {"status": "ok"}

# ===============================
# DATOS INICIALES
# ===============================
def setup_initial_data():
    db = SessionLocal()
    try:
        crud.get_or_create_dj_user(db)
    finally:
        db.close()

setup_initial_data()

# ===============================
# MIDDLEWARE
# ===============================
@app.middleware("http")
async def add_referrer_policy_header(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["Referrer-Policy"] = "origin"
    return response

# ===============================
# EVENTO STARTUP
# ===============================
@app.on_event("startup")
def startup_event():
    db = SessionLocal()

    mesas_a_crear = []
    for i in range(1, 31):
        mesas_a_crear.append({
            "nombre": f"Mesa {i}",
            "qr_code": f"karaoke-mesa-{i:02d}"
        })

    for mesa_data in mesas_a_crear:
        mesa_existente = crud.get_mesa_by_qr(db, mesa_data["qr_code"])
        if not mesa_existente:
            crud.create_mesa(
                db=db,
                mesa=schemas.MesaCreate(**mesa_data)
            )
            print(f"[OK] Mesa creada: {mesa_data['nombre']}")
        else:
            print(f"[INFO] Mesa ya existente: {mesa_data['nombre']}")

    db.close()

# ===============================
# FRONTEND
# ===============================
@app.get("/", response_class=FileResponse, include_in_schema=False)
async def read_index():
    return FileResponse(os.path.join("static", "index.html"))

@app.get("/bees", response_class=FileResponse, include_in_schema=False)
async def read_bees_index():
    return FileResponse(os.path.join("static", "index_bees.html"))

@app.get("/admin", response_class=FileResponse, include_in_schema=False)
async def read_admin_index():
    return FileResponse(os.path.join("static", "admin.html"))

@app.get("/admin/dashboard", response_class=FileResponse, include_in_schema=False)
async def read_admin_dashboard():
    return FileResponse(os.path.join("static", "admin_dashboard.html"))

@app.get("/player", response_class=FileResponse, include_in_schema=False)
async def read_player():
    return FileResponse(os.path.join("static", "player.html"))

# ===============================
# WEBSOCKET
# ===============================
@app.websocket("/ws/cola")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.manager.connect(websocket)
    await websocket_manager.manager.broadcast_queue_update()
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.manager.disconnect(websocket)

# ===============================
# ROUTERS API
# ===============================
app.include_router(mesas.router, prefix="/api/v1/mesas", tags=["Mesas"])
app.include_router(canciones.router, prefix="/api/v1/canciones", tags=["Canciones"])
app.include_router(youtube.router, prefix="/api/v1/youtube", tags=["YouTube"])
app.include_router(consumos.router, prefix="/api/v1/consumos", tags=["Consumos"])
app.include_router(usuarios.router, prefix="/api/v1/usuarios", tags=["Usuarios"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administración"])
app.include_router(admin.public_router, prefix="/api/v1", tags=["Público"])
app.include_router(productos.router, prefix="/api/v1/productos", tags=["Productos"])
app.include_router(broadcast.router, prefix="/api/v1/broadcast", tags=["Broadcast"])
app.include_router(thumbnails.router)
app.include_router(settings_router)
app.include_router(admin_extra_router)

# ===============================
# STATIC FILES
# ===============================
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join("static", "favicon.ico"))