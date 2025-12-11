import json
from pathlib import Path

SETTINGS_FILE = Path("settings.json")

DEFAULT_SETTINGS = {
    "closing_hour": 3,
    "closing_minute": 0,
    "app_name": "QR Karaoke",
    "theme": "dark",
    "enable_notifications": True
}

def load_settings():
    """Carga la configuración desde el archivo JSON"""
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_SETTINGS

def save_settings(data: dict):
    """Guarda la configuración en el archivo JSON"""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_setting(key: str, default=None):
    """Obtiene un valor específico de la configuración"""
    settings = load_settings()
    return settings.get(key, default)

def set_setting(key: str, value):
    """Actualiza un valor específico de la configuración"""
    settings = load_settings()
    settings[key] = value
    save_settings(settings)
