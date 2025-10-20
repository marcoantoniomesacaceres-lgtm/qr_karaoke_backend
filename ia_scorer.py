import os
import logging
import json
import subprocess
from typing import List, Tuple

# --- Importaciones de las nuevas librerías ---
from basic_pitch.inference import predict
from basic_pitch.inference import predict, predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH
import yt_dlp

logger = logging.getLogger(__name__)

# --- Rutas para almacenar archivos temporales y procesados ---
TEMP_DIR = "temp_audio"
PROCESSED_DIR = "processed_songs"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# --- Inicialización de modelos (se hace una sola vez) ---
try:
    basic_pitch_model = ICASSP_2022_MODEL_PATH
except Exception as e:
    logger.error(f"Error inicializando modelo de Basic Pitch. Error: {e}")
    basic_pitch_model = None

def _download_audio_from_youtube(youtube_id: str) -> str | None:
    """Descarga el audio de un video de YouTube y lo guarda como MP3."""
    output_path = os.path.join(TEMP_DIR, f"{youtube_id}.mp3")
    if os.path.exists(output_path):
        logger.info(f"El audio para {youtube_id} ya existe. Saltando descarga.")
        return output_path

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(TEMP_DIR, f'{youtube_id}.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={youtube_id}"])
        return output_path
    except Exception as e:
        logger.error(f"Error al descargar audio de YouTube para {youtube_id}: {e}")
        return None

def _get_pitch_sequence(audio_path: str) -> List[Tuple[float, float, int]]:
    """Analiza un archivo de audio con Basic Pitch y devuelve una secuencia de notas."""
    if not basic_pitch_model or not os.path.exists(audio_path):
        return []
    try:
        model_output, _, notes = predict(audio_path, basic_pitch_model)
        model_output, _, notes = predict(audio_path, basic_pitch_model, False, False, False, False)
        # Devolvemos una tupla simple: (inicio, fin, nota_midi)
        return [(note['start_time_s'], note['end_time_s'], note['pitch_midi']) for note in notes]
    except Exception as e:
        logger.error(f"Error al procesar el audio '{audio_path}' con Basic Pitch: {e}")
        return []

def _separate_vocals_with_demucs(audio_path: str, output_dir: str) -> str | None:
    """
    Usa Demucs para separar las vocales de un archivo de audio.
    Ejecuta demucs como un proceso de línea de comandos.
    """
    try:
        # Comando para ejecutar Demucs. Separa en dos pistas (vocales y no-vocales)
        # y guarda el resultado en el directorio de salida.
        command = [
            "python", "-m", "demucs",
            "--two-stems", "vocals",
            "-o", output_dir,
            audio_path
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)

        # Demucs crea una subcarpeta con el nombre del modelo, ej: 'htdemucs'
        # y dentro el archivo de audio con el nombre original.
        vocals_path = os.path.join(output_dir, "htdemucs", os.path.basename(audio_path).replace(".mp3", ".wav"))
        return vocals_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Error ejecutando Demucs: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al separar vocales con Demucs: {e}")
        return None

def _get_original_vocals_pitch(youtube_id: str) -> List[Tuple[float, float, int]]:
    """
    Procesa la canción original: la descarga, separa la voz y analiza su pitch.
    Usa un sistema de caché para no reprocesar la misma canción.
    """
    pitch_cache_path = os.path.join(PROCESSED_DIR, f"{youtube_id}_pitch.json")
    if os.path.exists(pitch_cache_path):
        with open(pitch_cache_path, 'r') as f:
            return json.load(f)

    audio_path = _download_audio_from_youtube(youtube_id)
    if not audio_path:
        return []

    try:
        # Separar la voz del instrumental usando Demucs
        vocals_path = _separate_vocals_with_demucs(audio_path, PROCESSED_DIR)
        
        if not os.path.exists(vocals_path):
            logger.error(f"Demucs no generó el archivo de vocales para {youtube_id}")
            return []

        # Analizar el pitch de la voz original
        pitch_sequence = _get_pitch_sequence(vocals_path)

        # Guardar en caché para futuras ejecuciones
        with open(pitch_cache_path, 'w') as f:
            json.dump(pitch_sequence, f)

        return pitch_sequence
    except Exception as e:
        logger.error(f"Error en el pipeline de Demucs para {youtube_id}: {e}")
        return []

def calculate_score(original_youtube_id: str, user_audio_path: str) -> int:
    """
    Función principal que calcula el puntaje comparando el audio del usuario
    con la voz original de la canción.
    """
    logger.info(f"Calculando puntaje para la canción {original_youtube_id} con el audio del usuario {user_audio_path}")
    original_pitch = _get_original_vocals_pitch(original_youtube_id)
    user_pitch = _get_pitch_sequence(user_audio_path)

    if not original_pitch or not user_pitch:
        logger.warning("No se pudo obtener la secuencia de pitch para la canción original o la del usuario. Puntaje: 0")
        return 0

    # --- Lógica de Comparación Simple ---
    # Comparamos cuántas notas del usuario coinciden en tiempo y tono con las originales.
    matches = 0
    for user_note in user_pitch:
        user_start, user_end, user_midi = user_note
        for original_note in original_pitch:
            orig_start, orig_end, orig_midi = original_note
            # Si la nota del usuario está dentro del rango de una nota original y el tono es el mismo
            if user_midi == orig_midi and max(user_start, orig_start) < min(user_end, orig_end):
                matches += 1
                break # Contamos solo una coincidencia por nota de usuario

    # Calculamos el puntaje como un porcentaje de notas coincidentes sobre el total de notas del usuario
    score = (matches / len(user_pitch)) * 100 if len(user_pitch) > 0 else 0
    
    logger.info(f"Puntaje calculado: {int(score)}")
    return int(score)