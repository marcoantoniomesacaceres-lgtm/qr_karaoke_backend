from fastapi import APIRouter
from pydantic import BaseModel
from settings_storage import load_settings, save_settings

router = APIRouter(prefix="/api/v1/admin/settings", tags=["Admin Settings"])


# ============= MODELOS =============
class GeneralSettings(BaseModel):
    app_name: str
    theme: str
    enable_notifications: bool


class ClosingTime(BaseModel):
    closing_hour: int
    closing_minute: int


# ============= ENDPOINTS =============

@router.get("/")
def get_all_settings():
    """Obtiene toda la configuración"""
    return load_settings()


@router.get("/general")
def get_general_settings():
    """Obtiene la configuración general (nombre, tema, notificaciones)"""
    settings = load_settings()
    return {
        "app_name": settings.get("app_name", "QR Karaoke"),
        "theme": settings.get("theme", "dark"),
        "enable_notifications": settings.get("enable_notifications", True)
    }


@router.post("/general")
def update_general_settings(data: GeneralSettings):
    """Actualiza la configuración general"""
    settings = load_settings()
    
    settings["app_name"] = data.app_name
    settings["theme"] = data.theme
    settings["enable_notifications"] = data.enable_notifications
    
    save_settings(settings)
    
    return {
        "status": "success",
        "message": "General settings updated",
        "data": {
            "app_name": data.app_name,
            "theme": data.theme,
            "enable_notifications": data.enable_notifications
        }
    }


@router.post("/closing-time")
def update_closing_time(data: ClosingTime):
    """Actualiza la hora de cierre"""
    settings = load_settings()
    
    # Validar horas válidas
    if not (0 <= data.closing_hour <= 23):
        return {"status": "error", "message": "Hora debe estar entre 0 y 23"}
    
    if not (0 <= data.closing_minute <= 59):
        return {"status": "error", "message": "Minuto debe estar entre 0 y 59"}
    
    settings["closing_hour"] = data.closing_hour
    settings["closing_minute"] = data.closing_minute
    
    save_settings(settings)
    
    return {
        "status": "success",
        "message": "Closing time updated",
        "data": {
            "closing_hour": data.closing_hour,
            "closing_minute": data.closing_minute
        }
    }


@router.get("/closing-time")
def get_closing_time():
    """Obtiene la hora de cierre actual"""
    settings = load_settings()
    return {
        "closing_hour": settings.get("closing_hour", 3),
        "closing_minute": settings.get("closing_minute", 0)
    }
