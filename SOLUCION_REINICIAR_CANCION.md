--- Resumen del problema ---

El botón de "Reiniciar canción" en el panel de administración no está funcionando porque:

1. El backend envía un mensaje WebSocket con type: "restart_song"
2. El player.html NO está escuchando este evento

--- Cambios necesarios en static/player.html ---

CAMBIO 1: Agregar variables globales (después de la línea 260)
```javascript
// Variables para el autoplay automático
let autoplayTimer = null;

// Variables para rastrear el video actual (necesarias para reiniciar)
let currentVideoId = null;
let currentVideoDuration = 0;
```

CAMBIO 2: Modificar la función playVideo para guardar el video actual (líneas 354-365)
Agregar al inicio de la función:
```javascript
// Guardar el video actual para poder reiniciarlo
currentVideoId = videoId;
currentVideoDuration = duration;
```

CAMBIO 3: Agregar manejador para restart_song en socket.onmessage (después de la línea 449, antes del else)
```javascript
// --- NUEVO: Escuchar el evento de reiniciar canción ---
if (data.type === 'restart_song') {
    console.log('🔄 Recibida orden de reiniciar canción');
    if (currentVideoId) {
        console.log(`🔄 Reiniciando video: ${currentVideoId}`);
        playVideo(currentVideoId, currentVideoDuration);
    } else {
        console.warn('⚠️ No hay video actual para reiniciar');
    }
}
```

CAMBIO 4: Modificar el else final para no procesar restart_song como actualización de cola (línea 450-453)
Cambiar:
```javascript
} else {
    // Si no es un tipo específico, asumimos que es la actualización de la cola
    updateQueueUI(data);
}
```

Por:
```javascript
// Si no es un tipo específico, asumimos que es la actualización de la cola
if (!['play_song', 'song_finished', 'notification', 'reaction', 'restart_song'].includes(data.type)) {
    updateQueueUI(data);
}
```
