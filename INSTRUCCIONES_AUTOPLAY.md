# INSTRUCCIONES PARA IMPLEMENTAR AUTOPLAY AUTOMÁTICO

## Problema Identificado
El sistema de autoplay no avanza automáticamente a la siguiente canción cuando una termina porque:
1. El player.html no detecta cuando un video de YouTube termina (limitación de iframes)
2. El WebSocket no envía la duración de las canciones
3. No hay temporizador que llame al endpoint `/siguiente` automáticamente

## Solución: 3 Cambios Necesarios

---

### CAMBIO 1: Modificar websocket_manager.py

**Archivo:** `websocket_manager.py`

**Buscar** (línea 112-117):
```python
    async def broadcast_play_song(self, youtube_id: str):
        """
        Envía un evento para reproducir una canción en el reproductor.
        """
        payload = {"type": "play_song", "payload": {"youtube_id": youtube_id}}
        await self._broadcast(json.dumps(payload))
```

**Reemplazar con:**
```python
    async def broadcast_play_song(self, youtube_id: str, duration_seconds: int = 0):
        """
        Envía un evento para reproducir una canción en el reproductor.
        Incluye la duración para permitir el autoplay automático.
        """
        payload = {
            "type": "play_song", 
            "payload": {
                "youtube_id": youtube_id,
                "duracion_seconds": duration_seconds
            }
        }
        await self._broadcast(json.dumps(payload))
```

---

### CAMBIO 2: Modificar crud.py para enviar la duración

**Archivo:** `crud.py`

**Buscar** (línea 1634):
```python
        await websocket_manager.manager.broadcast_play_song(next_song.youtube_id)
```

**Reemplazar con:**
```python
        await websocket_manager.manager.broadcast_play_song(next_song.youtube_id, next_song.duracion_seconds or 0)
```

**Buscar** (línea 1659):
```python
        await websocket_manager.manager.broadcast_play_song(siguiente_cancion.youtube_id)
```

**Reemplazar con:**
```python
        await websocket_manager.manager.broadcast_play_song(siguiente_cancion.youtube_id, siguiente_cancion.duracion_seconds or 0)
```

---

### CAMBIO 3: Modificar player.html para usar temporizador

**Archivo:** `static/player.html`

#### 3.1 - Agregar variables globales

**Buscar** (línea 250-256):
```javascript
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const WEBSOCKET_URL = `${wsProtocol}//${window.location.host}/ws/cola`;
        let standbyScreen = document.getElementById('standby-screen');
        let backgroundCarousel = document.getElementById('background-carousel');
        let infoOverlay = document.getElementById('info-overlay');
        let notificationBanner = document.getElementById('notification-banner');
```

**Reemplazar con:**
```javascript
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const WEBSOCKET_URL = `${wsProtocol}//${window.location.host}/ws/cola`;
        const API_BASE_URL = `${window.location.protocol}//${window.location.host}/api/v1`;
        let standbyScreen = document.getElementById('standby-screen');
        let backgroundCarousel = document.getElementById('background-carousel');
        let infoOverlay = document.getElementById('info-overlay');
        let notificationBanner = document.getElementById('notification-banner');
        
        // Variables para el autoplay automático
        let autoplayTimer = null;
```

#### 3.2 - Agregar función de avance automático

**Buscar** (línea 325):
```javascript
        function playVideo(videoId) {
```

**Insertar ANTES de esa línea:**
```javascript
        // Función para avanzar automáticamente a la siguiente canción
        async function advanceToNextSong() {
            console.log('⏭️ Avanzando automáticamente a la siguiente canción...');
            try {
                const response = await fetch(`${API_BASE_URL}/canciones/siguiente`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (response.status === 204) {
                    console.log('✅ No hay más canciones en la cola');
                    const container = document.getElementById('player-container');
                    if (container) container.innerHTML = '';
                    startCarousel();
                } else if (response.ok) {
                    console.log('✅ Siguiente canción iniciada automáticamente');
                } else {
                    console.error('❌ Error al avanzar:', response.status);
                }
            } catch (error) {
                console.error('❌ Error en advanceToNextSong:', error);
            }
        }
        
```

#### 3.3 - Modificar función playVideo

**Buscar** (línea 325-329):
```javascript
        function playVideo(videoId) {
            console.log('playVideo called with:', videoId);
            stopCarousel();
            insertYouTubeIframe(videoId);
        }
```

**Reemplazar con:**
```javascript
        function playVideo(videoId, duration = 0) {
            console.log('🎵 playVideo called with:', videoId, 'duration:', duration);
            
            // Limpiar temporizador anterior si existe
            if (autoplayTimer) {
                clearTimeout(autoplayTimer);
                autoplayTimer = null;
                console.log('🔄 Temporizador anterior limpiado');
            }
            
            stopCarousel();
            insertYouTubeIframe(videoId);
            
            // Si tenemos la duración, configurar temporizador
            if (duration && duration > 0) {
                const timerDuration = (duration + 3) * 1000; // +3 segundos de buffer
                console.log(`⏱️ Configurando temporizador de autoplay para ${timerDuration}ms (${duration + 3}s)`);
                
                autoplayTimer = setTimeout(() => {
                    console.log('⏰ Temporizador de autoplay activado');
                    advanceToNextSong();
                }, timerDuration);
            } else {
                console.warn('⚠️ No se proporcionó duración, autoplay automático deshabilitado');
            }
        }
```

#### 3.4 - Modificar llamada a playVideo en WebSocket

**Buscar** (línea 355-360):
```javascript
                    if (videoId) {
                        console.log('Recibida orden de reproducir:', videoId);
                        playVideo(videoId);
                    } else {
                        console.error('No se pudo extraer el ID de YouTube:', data.payload);
                    }
```

**Reemplazar con:**
```javascript
                    if (videoId) {
                        console.log('Recibida orden de reproducir:', videoId);
                        const duration = data.payload.duracion_seconds || data.payload.duration || 0;
                        playVideo(videoId, duration);
                    } else {
                        console.error('No se pudo extraer el ID de YouTube:', data.payload);
                    }
```

---

## Cómo Probar

1. Guarda todos los archivos modificados
2. El servidor con `--reload` detectará los cambios automáticamente
3. Abre el dashboard de admin
4. Activa el autoplay
5. Agrega varias canciones a la cola
6. Observa la consola del navegador en el player - deberías ver logs como:
   - "⏱️ Configurando temporizador de autoplay para XXXXms"
   - "⏰ Temporizador de autoplay activado"
   - "⏭️ Avanzando automáticamente a la siguiente canción..."
7. Las canciones deberían reproducirse una tras otra automáticamente

## Notas Importantes

- El temporizador usa la duración de la canción + 3 segundos de buffer
- Si una canción no tiene duración registrada, el autoplay automático no funcionará para esa canción
- Asegúrate de que las canciones tengan el campo `duracion_seconds` poblado cuando se agregan
