import os
from dotenv import load_dotenv

load_dotenv() # Carga las variables del archivo .env

class AppSettings:
    """
    Clase para almacenar configuraciones de la aplicación que pueden cambiar en tiempo de ejecución.
    """
    def __init__(self):
        self.KARAOKE_CIERRE = os.getenv("KARAOKE_CIERRE", "02:00") # Leemos del .env, con un valor por defecto

settings = AppSettings()