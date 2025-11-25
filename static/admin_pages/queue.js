// Queue Page Module
// Manejo: cola de canciones, búsqueda de canciones, añadir canciones

function renderApprovedSongs(songs, listElement) {
    if (!listElement) return;

    // Handle both array input and object with now_playing/upcoming structure
    let songArray = [];
    if (Array.isArray(songs)) {
        songArray = songs;
    } else if (songs && typeof songs === 'object') {
        if (songs.now_playing) {
            songArray.push(songs.now_playing);
        }
        if (songs.upcoming && Array.isArray(songs.upcoming)) {
            songArray = songArray.concat(songs.upcoming);
        }
    }

    listElement.innerHTML = '';
    if (!songArray || songArray.length === 0) {
        listElement.innerHTML = '<p>La cola de canciones está vacía.</p>';
        return;
    }
    songArray.forEach((song, index) => {
        const li = document.createElement('li');
        li.className = 'item';

        let addedBy = 'Desconocido';
        if (song.usuario) {
            addedBy = song.usuario.mesa ? song.usuario.mesa.nombre : song.usuario.nick;
        }

        const restartButton = index === 0
            ? `<button class="btn-action" data-id="${song.id}" data-action="restart" title="Reiniciar la canción actual">Reiniciar</button>`
            : '';

        li.innerHTML = `
            <div class="item-details song-item-info">
                <img src="https://i.ytimg.com/vi/${song.youtube_id}/mqdefault.jpg" alt="Miniatura">
                <div>
                    <div class="item-title">${song.titulo}</div>
                    <div class="item-meta">
                        Por: <strong>${addedBy}</strong>
                        ${index === 0 ? '<span class="status-badge status-reproduciendo" style="margin-left: 10px;">Reproduciendo</span>' : ''}
                    </div>
                </div>
            </div>
            <div class="item-actions">
                <button class="btn-approve" data-id="${song.id}" data-action="play" title="Marcar como 'Reproduciendo'">Reproducir</button>
                <button class="btn-action" data-id="${song.id}" data-action="move-up" title="Mover un puesto hacia arriba">Subir</button>
                <button class="btn-action" data-id="${song.id}" data-action="move-down" title="Mover un puesto hacia abajo">Bajar</button>
                <button class="btn-reject" data-id="${song.id}" data-action="remove" title="Eliminar de la cola">Eliminar</button>
                ${restartButton}
            </div>
        `;
        listElement.appendChild(li);
    });
}


async function loadQueuePage() {
    try {
        // Si ya tenemos datos en caché (por WebSocket), usarlos primero
        let queueData = currentQueueData || { now_playing: null, upcoming: [] };

        // Si el caché está vacío, cargar desde servidor
        if (!queueData.now_playing && (!queueData.upcoming || queueData.upcoming.length === 0)) {
            queueData = await apiFetch('/canciones/cola');
        }

        // Actualizar el caché con los datos más recientes
        currentQueueData = queueData;

        const approvedSongsList = document.getElementById('approved-songs-list');
        // Renderizar directamente desde el objeto (que puede tener now_playing/upcoming)
        renderApprovedSongs(queueData, approvedSongsList);
    } catch (error) {
        showNotification(`Error al cargar cola: ${error.message}`, 'error');
    }

    try {
        const tables = await apiFetch('/mesas/');
        const targetTableSelect = document.getElementById('admin-target-table');
        if (targetTableSelect) {
            targetTableSelect.innerHTML = '<option value="">DJ (Cola General)</option>';
            const activeTables = tables.filter(t => t.is_active);
            activeTables.forEach(table => {
                targetTableSelect.innerHTML += `<option value="${table.id}">${table.nombre}</option>`;
            });
        }
    } catch (error) {
        showNotification(`Error al cargar mesas: ${error.message}`, 'error');
    }
}

async function handleAdminSearch(event, karaokeMode = false) {
    event.preventDefault();
    const query = document.getElementById('admin-search-input').value.trim();
    if (!query) return;

    const songsButton = document.getElementById('admin-search-songs-btn');
    const karaokeButton = document.getElementById('admin-search-karaoke-btn');
    songsButton.disabled = true;
    karaokeButton.disabled = true;

    const clickedButton = karaokeMode ? karaokeButton : songsButton;
    const originalText = clickedButton.textContent;
    clickedButton.textContent = 'Buscando...';

    const resultsContainer = document.getElementById('admin-search-results');
    resultsContainer.innerHTML = '<p>Buscando...</p>';

    try {
        const url = `/youtube/search?q=${encodeURIComponent(query)}${karaokeMode ? '&karaoke_mode=true' : ''}`;
        const results = await apiFetch(url);

        resultsContainer.innerHTML = '';
        if (results.length > 0) {
            results.forEach(song => {
                resultsContainer.innerHTML += `
                    <li class="item">
                        <div class="item-details song-item-info">
                            <img src="${song.thumbnail}" alt="Miniatura">
                            <div>
                                <div class="item-title">${song.title}</div>
                            </div>
                        </div>
                        <button class="btn-approve admin-add-song-btn" data-title="${song.title}" data-youtube-id="${song.video_id}" data-duration="${song.duration_seconds}">Añadir</button>
                    </li>
                `;
            });
        } else {
            resultsContainer.innerHTML = '<p>No se encontraron resultados.</p>';
        }
    } catch (error) {
        resultsContainer.innerHTML = `<p class="error-msg">Error: ${error.message}</p>`;
    } finally {
        songsButton.disabled = false;
        karaokeButton.disabled = false;
        clickedButton.textContent = originalText;
    }
}

async function handleAdminAddSong(event) {
    if (!event.target.classList.contains('admin-add-song-btn')) return;

    const button = event.target;
    button.disabled = true;
    button.textContent = 'Añadiendo...';

    const songData = {
        titulo: button.dataset.title,
        youtube_id: button.dataset.youtubeId,
        duracion_seconds: parseInt(button.dataset.duration, 10)
    };

    const targetTableId = document.getElementById('admin-target-table').value;
    let endpoint;
    let body = JSON.stringify(songData);

    if (targetTableId) {
        endpoint = `/admin/mesas/${targetTableId}/add-song`;
    } else {
        endpoint = '/canciones/admin/add';
    }

    try {
        await apiFetch(endpoint, {
            method: 'POST',
            body: body
        });
        const targetName = targetTableId ? `la mesa seleccionada` : 'la cola general';
        showNotification(`'${songData.titulo}' añadida a ${targetName}.`, 'success');

        // Limpiar resultados de búsqueda
        document.getElementById('admin-search-results').innerHTML = '';

        // IMPORTANTE: Recargar la cola aprobada para mostrar la canción recién agregada
        await reloadApprovedQueue();

    } catch (error) {
        showNotification(error.message, 'error');
    } finally {
        button.disabled = false;
        button.textContent = 'Añadir';
    }
}

// Nueva función para recargar solo la cola aprobada sin recargar toda la página
async function reloadApprovedQueue() {
    try {
        // Obtener los datos más recientes de la cola desde el servidor
        const queueData = await apiFetch('/canciones/cola');

        // Actualizar el caché global
        currentQueueData = queueData;

        // Actualizar la vista de la cola aprobada
        const approvedSongsList = document.getElementById('approved-songs-list');
        if (approvedSongsList) {
            renderApprovedSongs(queueData, approvedSongsList);
        }
    } catch (error) {
        console.error('Error al recargar la cola aprobada:', error);
        // No mostrar notificación de error aquí para no molestar al usuario
        // La canción ya fue agregada exitosamente
    }
}

async function handleQueueActions(event) {
    const button = event.target.closest('button[data-action]');
    if (!button) return;

    const songId = button.dataset.id;
    const action = button.dataset.action;

    if (!songId || !action) return;

    button.disabled = true;
    let shouldReloadQueue = false; // Flag para saber si debemos recargar la cola

    try {
        if (action === 'play') {
            const response = await fetch(`${API_BASE_URL}/canciones/siguiente`, {
                method: "POST",
                headers: {
                    "X-API-Key": apiKey
                }
            });

            if (response.status === 204) {
                showNotification('No hay más canciones en la cola.', 'info');
            } else if (response.ok) {
                const data = await response.json();
                showNotification(`Reproduciendo ahora: ${data.cancion.titulo}`, 'success');
                shouldReloadQueue = true;
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al intentar reproducir la canción.');
            }

        } else if (action === 'remove') {
            if (confirm('¿Seguro que quieres eliminar esta canción de la cola?')) {
                await apiFetch(`/canciones/${songId}/rechazar`, { method: 'POST' });
                showNotification('Canción eliminada de la cola.', 'info');
                shouldReloadQueue = true;
            } else {
                button.disabled = false;
                return;
            }
        } else if (action === 'move-up' || action === 'move-down') {
            const listElement = document.getElementById('approved-songs-list');
            const songItems = Array.from(listElement.querySelectorAll('li.item'));
            const songIds = songItems.map(item => item.querySelector('button').dataset.id);
            const currentIndex = songIds.indexOf(songId);

            if (action === 'move-up' && currentIndex > 0) {
                [songIds[currentIndex - 1], songIds[currentIndex]] = [songIds[currentIndex], songIds[currentIndex - 1]];
            } else if (action === 'move-down' && currentIndex < songIds.length - 1) {
                [songIds[currentIndex], songIds[currentIndex + 1]] = [songIds[currentIndex + 1], songIds[currentIndex]];
            } else {
                button.disabled = false;
                return;
            }

            await apiFetch('/admin/reorder-queue', { method: 'POST', body: JSON.stringify({ canciones_ids: songIds }) });
            showNotification('Cola reordenada.', 'info');
            shouldReloadQueue = true;
        } else if (action === 'restart') {
            await apiFetch(`/admin/canciones/restart`, { method: 'POST' }).catch(async () => {
                // Fallback: /admin/canciones/restart doesn't exist, try alternative or skip
                console.warn('Restart endpoint not available');
                showNotification('Función de reinicio no disponible en el backend.', 'warning');
            });
            showNotification('Reiniciando la canción actual.', 'info');
            // No recargar la cola para restart, ya que no cambia el orden
        }

        // Recargar la cola si hubo cambios
        if (shouldReloadQueue) {
            await reloadApprovedQueue();
        }

    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        button.disabled = false;
    }
}

function setupQueueListeners() {
    const searchForm = document.getElementById('admin-search-form');
    const songsBtn = document.getElementById('admin-search-songs-btn');
    const karaokeBtn = document.getElementById('admin-search-karaoke-btn');
    const resultsContainer = document.getElementById('admin-search-results');
    const songsList = document.getElementById('approved-songs-list');
    const autoplayToggle = document.getElementById('autoplay-toggle-queue');

    if (songsBtn) songsBtn.addEventListener('click', (e) => handleAdminSearch(e, false));
    if (karaokeBtn) karaokeBtn.addEventListener('click', (e) => handleAdminSearch(e, true));
    if (resultsContainer) resultsContainer.addEventListener('click', handleAdminAddSong);
    if (songsList) songsList.addEventListener('click', handleQueueActions);
    if (autoplayToggle) autoplayToggle.addEventListener('change', handleToggleAutoplay);
}
