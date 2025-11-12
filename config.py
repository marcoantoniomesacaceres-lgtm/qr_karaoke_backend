import os
from dotenv import load_dotenv
from database import SessionLocal # Importar SessionLocal
import crud # Importar crud para acceder a las funciones de configuración

load_dotenv() # Carga las variables del archivo .env

class AppSettings:
    """
    Clase para almacenar configuraciones de la aplicación que pueden cambiar en tiempo de ejecución.
    Ahora también carga y persiste el estado de AUTOPLAY_ENABLED desde la base de datos.
    """
    def __init__(self):
        self.KARAOKE_CIERRE = os.getenv("KARAOKE_CIERRE", "02:00") # Leemos del .env, con un valor por defecto
        self.AUTOPLAY_ENABLED: bool = False # Valor inicial para el modo autoplay

        # --- Al iniciar la app, intentamos cargar el valor desde DB ---
        try:
            db = SessionLocal()
            db_config = crud.get_config(db, "AUTOPLAY_ENABLED")
            if db_config:
                self.AUTOPLAY_ENABLED = db_config.valor.lower() == "true"
            db.close()
        except Exception as e:
            print("⚠️ No se pudo cargar configuración de la base de datos:", e)

settings = AppSettings()