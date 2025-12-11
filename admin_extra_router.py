from fastapi import APIRouter
from settings_storage import load_settings, save_settings

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Extra"])


@router.post("/set-closing-time")
def set_closing_time(data: dict):
    """
    Fallback endpoint para establecer la hora de cierre
    Acepta formato: {"hora_cierre": "HH:MM"}
    """
    try:
        hora = data.get("hora_cierre")
        
        if not hora or ":" not in hora:
            return {
                "status": "error",
                "message": "Formato inválido. Use HH:MM"
            }
        
        hour, minute = map(int, hora.split(":"))
        
        # Validar rangos
        if not (0 <= hour <= 23):
            return {"status": "error", "message": "Hora debe estar entre 0 y 23"}
        
        if not (0 <= minute <= 59):
            return {"status": "error", "message": "Minuto debe estar entre 0 y 59"}
        
        settings = load_settings()
        settings["closing_hour"] = hour
        settings["closing_minute"] = minute
        save_settings(settings)
        
        return {
            "status": "success",
            "message": "Closing time updated",
            "data": {
                "closing_hour": hour,
                "closing_minute": minute
            }
        }
    except ValueError as e:
        return {
            "status": "error",
            "message": f"Error al procesar la hora: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error interno: {str(e)}"
        }
