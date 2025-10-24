import os
import logging
import json
import subprocess
from typing import List, Tuple

# --- Importaciones de librerías ---
import librosa
import numpy as np
import yt_dlp

logger = logging.getLogger(__name__)

# --- Rutas para almacenar archivos temporales y procesados ---
TEMP_DIR = "temp_audio"
PROCESSED_DIR = "processed_songs"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

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

def _hz_a_nota(frecuencia: float) -> str | None:
    """Convierte una frecuencia en Hz a una nota musical (ej: A4)."""
    if not frecuencia or frecuencia <= 0:
        return None
    try:
        return librosa.hz_to_note(frecuencia)
    except Exception:
        return None

def _get_pitch_sequence(audio_path: str) -> List[str]:
    """
    Analiza un archivo de audio con Librosa (usando YIN) y devuelve una secuencia de notas.
    """
    if not os.path.exists(audio_path):
        return []
    try:
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        
        # Obtener el pitch a lo largo del tiempo
        pitches, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        
        # Convertir frecuencias a notas y filtrar Nones
        notes = [_hz_a_nota(p) for p in pitches if not np.isnan(p)]
        return [n for n in notes if n is not None]

    except Exception as e:
        logger.error(f"Error al procesar el audio '{audio_path}' con Librosa: {e}")
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

        # Demucs crea una subcarpeta con el nombre del modelo, ej: 'htdemucs'.
        # Dentro de esta, crea otra subcarpeta con el nombre base del archivo de entrada,
        # y ahí guarda los stems (ej: vocals.wav).
        # El archivo de audio original sin extensión es la base para el nombre del archivo de salida.
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        # La ruta esperada para las vocales es dentro de la carpeta del modelo.
        expected_vocals_path = os.path.join(output_dir, "htdemucs", base_name, "vocals.wav")
        return expected_vocals_path if os.path.exists(expected_vocals_path) else None
    except subprocess.CalledProcessError as e:
        logger.error(f"Error ejecutando Demucs: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al separar vocales con Demucs: {e}")
        return None

def _get_original_vocals_pitch(youtube_id: str) -> List[str]:
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
    # Usamos una comparación de secuencias simple.
    # Esto es una aproximación y puede mejorarse con algoritmos más avanzados
    # como Dynamic Time Warping (DTW), pero es un buen punto de partida.
    matches = 0
    len_user = len(user_pitch)
    len_orig = len(original_pitch)
    
    # Recorremos la secuencia más corta para evitar IndexError
    min_len = min(len_user, len_orig)
    for i in range(min_len):
        # Comparamos la nota (ej: 'C#4')
        if user_pitch[i] == original_pitch[i]:
            matches += 1

    # El puntaje es el porcentaje de coincidencias sobre la longitud de la secuencia original.
    # Esto penaliza si el usuario canta mucho menos de lo que debería.
    score = (matches / len_orig) * 100 if len_orig > 0 else 0
    
    logger.info(f"Puntaje calculado: {int(score)}")
    return int(score)