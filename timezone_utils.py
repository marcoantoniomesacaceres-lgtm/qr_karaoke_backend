from datetime import datetime
import pytz

# Zona horaria de Bogotá, Colombia
BOGOTA_TZ = pytz.timezone('America/Bogota')

def now_bogota():
    """Retorna la fecha y hora actual en zona horaria de Bogotá"""
    return datetime.now(BOGOTA_TZ)

def to_bogota(dt):
    """Convierte un datetime a zona horaria de Bogotá"""
    if dt.tzinfo is None:
        # Si no tiene timezone, asumimos que es UTC
        dt = pytz.utc.localize(dt)
    return dt.astimezone(BOGOTA_TZ)
