// Queue Page Module - BEES Style
// Manejo: cola de canciones, búsqueda de canciones, añadir canciones

// Estado de reproducción para el control de pausa/reanudación
let playerState = {
    isPlaying: true,  // false = pausado, true = reproduciendo
    currentSongId: null
};

// Muestra un toast temporal con acción "Deshacer" que ejecuta undoCallback
function showUndoNotification(message, undoCallback, timeout = 15000) {
    try {
        const id = `undo-toast-${Date.now()}`;
        const container = document.createElement('div');
        container.id = id;
        container.style.position = 'fixed';
        container.style.right = '20px';
        container.style.bottom = '20px';
        container.style.background = 'var(--page-input-bg)';
        container.style.color = 'var(--page-text)';
        container.style.padding = '12px 14px';
        container.style.borderRadius = '8px';
        container.style.boxShadow = '0 6px 18px rgba(0,0,0,0.12)';
        container.style.zIndex = 9999;
        container.style.display = 'flex';
        container.style.gap = '10px';
        container.style.alignItems = 'center';

        const msg = document.createElement('div');
        msg.style.flex = '1';
        msg.style.fontSize = '14px';
        msg.textContent = message;

        const undoBtn = document.createElement('button');
        undoBtn.className = 'bees-btn bees-btn-secondary bees-btn-small';
        undoBtn.textContent = 'Deshacer';
        undoBtn.style.cursor = 'pointer';

        container.appendChild(msg);
        container.appendChild(undoBtn);
        document.body.appendChild(container);

        const timer = setTimeout(() => {
            if (document.getElementById(id)) document.getElementById(id).remove();
        }, timeout);

        undoBtn.addEventListener('click', async () => {
            clearTimeout(timer);
            try {
                undoBtn.disabled = true;
                undoBtn.textContent = '⏳';
                await undoCallback();
            } catch (err) {
                console.error('Error en deshacer:', err);
                showNotification('Error al deshacer la aprobación.', 'error');
            } finally {
                if (document.getElementById(id)) document.getElementById(id).remove();
            }
        });
    } catch (err) {
        console.warn('showUndoNotification falló:', err);
    }
}

async function loadQueuePage() {
    const queueContainer = document.getElementById('queue');
    if (!queueContainer) return;

    try {
        queueContainer.innerHTML = '';

        // Encabezado
        const header = document.createElement('div');
        header.className = 'bees-header';
        header.innerHTML = `
            <div class="bees-header-icon">🎵</div>
            <div class="bees-header-content">
                <h1>Cola de Canciones</h1>
                <p>Gestión de la reproducción</p>
            </div>
        `;
        queueContainer.appendChild(header);

        // Contenedor de dos columnas
        const mainContainer = document.createElement('div');
        mainContainer.style.display = 'grid';
        mainContainer.style.gridTemplateColumns = 'repeat(auto-fit, minmax(500px, 1fr))';
        mainContainer.style.gap = '24px';
        mainContainer.style.marginBottom = '30px';

        // Tarjeta de cola
        const queueCard = document.createElement('div');
        queueCard.className = 'bees-card';

        const queueHeader = document.createElement('div');
        queueHeader.className = 'bees-card-header';
        queueHeader.innerHTML = `
            <div class="bees-card-icon">▶️</div>
            <div class="bees-card-header-content">
                <h3>Cola Aprobada</h3>
                <p>Canciones en reproducción</p>
            </div>
        `;
        queueCard.appendChild(queueHeader);

        const queueList = document.createElement('ul');
        queueList.id = 'approved-songs-list';
        queueList.style.listStyle = 'none';
        queueList.style.padding = '0';
        queueList.style.margin = '0';

        const loadingItem = document.createElement('li');
        loadingItem.innerHTML = '<div class="bees-alert bees-alert-info"><span class="bees-alert-icon">⏳</span><div>Cargando cola...</div></div>';
        queueList.appendChild(loadingItem);

        queueCard.appendChild(queueList);
        mainContainer.appendChild(queueCard);

        // Tarjeta de cola lazy (esperando turno)
        const lazyQueueCard = document.createElement('div');
        lazyQueueCard.className = 'bees-card';

        const lazyQueueHeader = document.createElement('div');
        lazyQueueHeader.className = 'bees-card-header';
        lazyQueueHeader.innerHTML = `
            <div class="bees-card-icon">🎯</div>
            <div class="bees-card-header-content">
                <h3>Cola Lazy (Esperando Turno)</h3>
                <p>Se aprobarán automáticamente al 50% de la canción actual</p>
            </div>
        `;
        lazyQueueCard.appendChild(lazyQueueHeader);

        const lazyQueueList = document.createElement('ul');
        lazyQueueList.id = 'lazy-songs-list';
        lazyQueueList.style.listStyle = 'none';
        lazyQueueList.style.padding = '0';
        lazyQueueList.style.margin = '0';

        const lazyLoadingItem = document.createElement('li');
        lazyLoadingItem.innerHTML = '<div class="bees-alert bees-alert-info"><span class="bees-alert-icon">⏳</span><div>Cargando cola lazy...</div></div>';
        lazyQueueList.appendChild(lazyLoadingItem);

        lazyQueueCard.appendChild(lazyQueueList);
        mainContainer.appendChild(lazyQueueCard);



        // Tarjeta de búsqueda
        const searchCard = document.createElement('div');
        searchCard.className = 'bees-card';

        const searchHeader = document.createElement('div');
        searchHeader.className = 'bees-card-header';
        searchHeader.innerHTML = `
            <div class="bees-card-icon">🔍</div>
            <div class="bees-card-header-content">
                <h3>Añadir Canción (DJ)</h3>
                <p>Busca y agrega música</p>
            </div>
        `;
        searchCard.appendChild(searchHeader);

        const searchForm = document.createElement('form');
        searchForm.id = 'admin-search-form';
        searchForm.innerHTML = `
            <div class="bees-form-group">
                <label for="admin-search-input">Buscar en YouTube</label>
                <input type="text" id="admin-search-input" placeholder="Artista, canción o URL" required>
            </div>
            <div class="bees-form-group">
                <label for="admin-target-table">Destino</label>
                <select id="admin-target-table" style="border: 2px solid var(--page-border); border-radius: 8px; padding: 12px; width: 100%; background: var(--page-input-bg); color: var(--page-text); box-sizing: border-box;">
                    <option value="">🎵 Cola General</option>
                </select>
            </div>
            <div style="display: flex; gap: 8px;">
                <button type="button" class="bees-btn bees-btn-primary bees-btn-small" id="admin-search-songs-btn" style="flex: 1; padding: 12px;">🎶 Canciones</button>
                <button type="button" class="bees-btn bees-btn-success bees-btn-small" id="admin-search-karaoke-btn" style="flex: 1; padding: 12px;">🎤 Karaoke</button>
            </div>
        `;
        searchCard.appendChild(searchForm);

        const resultsContainer = document.createElement('div');
        resultsContainer.id = 'admin-search-results';
        resultsContainer.style.listStyle = 'none';
        resultsContainer.style.padding = '0';
        resultsContainer.style.margin = '16px 0 0 0';
        resultsContainer.style.maxHeight = '500px';
        resultsContainer.style.overflowY = 'auto';
        searchCard.appendChild(resultsContainer);

        mainContainer.appendChild(searchCard);
        queueContainer.appendChild(mainContainer);

        // Cargar datos
        await loadQueueData();
        setupQueueListeners();
    } catch (error) {
        const queueContainer = document.getElementById('queue');
        if (queueContainer) {
            queueContainer.innerHTML = `
                <div class="bees-alert bees-alert-danger">
                    <span class="bees-alert-icon">❌</span>
                    <div>Error al cargar cola: ${error.message}</div>
                </div>
            `;
        }
    }
}

async function loadQueueData() {
    try {
        // Cargar cola extendida con lazy queue
        // Cargar cola extendida con lazy queue
        let queueData = await apiFetch('/canciones/cola/extended');

        // Si no hay canción aprobada pero sí hay en la cola lazy, solicitar que se apruebe la siguiente
        if ((!queueData.now_playing || queueData.now_playing === null) && queueData.lazy_queue && queueData.lazy_queue.length > 0) {
            try {
                const approved = await apiFetch('/admin/canciones/lazy/approve-next', { method: 'POST' });
                if (approved && approved.titulo) {
                    // Mostrar toast con opción de deshacer
                    showUndoNotification(`Se aprobó automáticamente: ${approved.titulo}`, async () => {
                        // Llamar endpoint para revertir la aprobación
                        await apiFetch(`/admin/canciones/${approved.id}/revert-approve`, { method: 'POST' });
                        showNotification('Aprobación revertida.', 'info');
                        // Recargar la cola en pantalla
                        await loadQueueData();
                    });
                } else {
                    showUndoNotification('Se aprobó automáticamente la siguiente canción lazy.', async () => {
                        // Si no conocemos el id, recargamos la cola y confiamos en el admin para revertir manualmente
                        await loadQueueData();
                    });
                }
                // Recargar la cola luego de aprobar la siguiente lazy
                queueData = await apiFetch('/canciones/cola/extended');
            } catch (approveErr) {
                console.warn('No se pudo aprobar la siguiente canción lazy automáticamente:', approveErr);
                showNotification('No se pudo aprobar automáticamente la siguiente canción lazy.', 'error');
            }
        }
        currentQueueData = queueData;

        const approvedSongsList = document.getElementById('approved-songs-list');
        if (approvedSongsList) {
            renderApprovedSongs(queueData, approvedSongsList);
        }

        // Cargar cola lazy
        const lazySongsList = document.getElementById('lazy-songs-list');
        if (lazySongsList) {
            renderLazySongs(queueData.lazy_queue || [], lazySongsList);
        }


    } catch (error) {
        console.error('Error loading queue:', error);
        showNotification(`Error al cargar cola: ${error.message}`, 'error');
    }

    try {
        // Cargar mesas
        const tables = await apiFetch('/mesas/');
        const targetTableSelect = document.getElementById('admin-target-table');
        if (targetTableSelect) {
            targetTableSelect.innerHTML = '<option value="">🎵 Cola General</option>';
            const activeTables = tables.filter(t => t.is_active);
            activeTables.forEach(table => {
                targetTableSelect.innerHTML += `<option value="${table.id}">🏠 ${table.nombre}</option>`;
            });
        }
    } catch (error) {
        console.error('Error loading tables:', error);
    }
}

function renderApprovedSongs(songs, listElement) {
    if (!listElement) return;

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
        const emptyItem = document.createElement('li');
        emptyItem.innerHTML = '<div class="bees-alert bees-alert-info"><span class="bees-alert-icon">ℹ️</span><div>La cola de canciones está vacía.</div></div>';
        listElement.appendChild(emptyItem);
        return;
    }

    songArray.forEach((song, index) => {
        const li = document.createElement('li');
        li.style.marginBottom = '16px';

        let addedBy = 'Desconocido';
        if (song.usuario) {
            addedBy = song.usuario.mesa ? song.usuario.mesa.nombre : song.usuario.nick;
        }

        const isPlaying = index === 0;
        const statusBadge = isPlaying
            ? '<span class="bees-badge bees-badge-success">▶️ Reproduciendo</span>'
            : `<span class="bees-badge bees-badge-info">#${index}</span>`;

        let buttonsHtml = '';
        if (isPlaying) {
            const pauseButtonText = playerState.isPlaying ? '⏸️ Pausar' : '▶️ Reproducir';
            buttonsHtml = `
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 12px;">
                    <button class="bees-btn bees-btn-primary bees-btn-small" data-id="${song.id}" data-action="play-song" title="Reproducir en player">▶️ Reproducir</button>
                    <button class="bees-btn bees-btn-info bees-btn-small" data-action="pause-resume-toggle" title="Pausar/Reanudar">${pauseButtonText}</button>
                    <button class="bees-btn bees-btn-warning bees-btn-small" data-action="restart" title="Reiniciar">🔄 Reiniciar</button>
                    <button class="bees-btn bees-btn-success bees-btn-small" data-action="play-next" title="Siguiente canción">⏭️ Siguiente</button>
                </div>
            `;
        }
        else {
            // Botones para canciones en espera (no reproduciendo)
            buttonsHtml = `
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 12px;">
                    <button class="bees-btn bees-btn-info bees-btn-small" data-id="${song.id}" data-action="move-up" title="Subir">⬆️ Subir</button>
                    <button class="bees-btn bees-btn-warning bees-btn-small" data-id="${song.id}" data-action="move-down" title="Bajar">⬇️ Bajar</button>
                    <button class="bees-btn bees-btn-danger bees-btn-small" data-id="${song.id}" data-action="remove" title="Eliminar">❌ Eliminar</button>
                </div>
                </div>
            `;
        }

        // Ocultar botones SOLO para la segunda canción (la próxima en sonar)
        if (index === 1) {
            buttonsHtml = '';
        }

        li.innerHTML = `
            <div style="background: var(--page-input-bg); border-radius: 12px; padding: 16px; border-left: 4px solid ${isPlaying ? 'var(--bees-green)' : 'var(--bees-yellow)'};">
                <div style="display: flex; gap: 12px; margin-bottom: 12px;">
                    <img src="https://i.ytimg.com/vi/${song.youtube_id}/mqdefault.jpg" alt="Miniatura" style="width: 60px; height: 45px; border-radius: 6px; object-fit: cover;">
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: var(--page-text); margin-bottom: 4px; word-break: break-word;">${song.titulo}</div>
                        <div style="font-size: 12px; color: var(--page-text-secondary);">Agregada por: <strong>${addedBy}</strong></div>
                    </div>
                </div>
                <div style="display: flex; gap: 8px; margin-bottom: 12px;">
                    ${statusBadge}
                </div>
                ${buttonsHtml}
            </div>
        `;
        listElement.appendChild(li);
    });
}

function renderLazySongs(songs, listElement) {
    listElement.innerHTML = '';

    if (!songs || songs.length === 0) {
        const emptyItem = document.createElement('li');
        emptyItem.innerHTML = '<div class="bees-alert bees-alert-info"><span class="bees-alert-icon">✅</span><div>No hay canciones en cola lazy.</div></div>';
        listElement.appendChild(emptyItem);
        return;
    }

    songs.forEach((song, index) => {
        const li = document.createElement('li');
        li.style.marginBottom = '16px';

        let addedBy = 'Desconocido';
        if (song.usuario) {
            addedBy = song.usuario.mesa ? song.usuario.mesa.nombre : song.usuario.nick;
        }

        // Indicador de posición en la cola lazy
        const positionBadge = index === 0
            ? '<span class="bees-badge bees-badge-success">🎯 Siguiente en aprobarse</span>'
            : `<span class="bees-badge bees-badge-info">#${index + 1} en cola lazy</span>`;

        // Botones para gestionar la canción lazy
        const buttonsHtml = `
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 12px;">
                <button class="bees-btn bees-btn-info bees-btn-small" data-id="${song.id}" data-action="move-lazy-up" title="Subir">⬆️ Subir</button>
                <button class="bees-btn bees-btn-warning bees-btn-small" data-id="${song.id}" data-action="move-lazy-down" title="Bajar">⬇️ Bajar</button>
                <button class="bees-btn bees-btn-danger bees-btn-small" data-id="${song.id}" data-action="remove-lazy" title="Eliminar">❌ Eliminar</button>
            </div>
        `;

        li.innerHTML = `
            <div style="background: var(--page-input-bg); border-radius: 12px; padding: 16px; border-left: 4px solid var(--bees-blue);">
                <div style="display: flex; gap: 12px; margin-bottom: 12px;">
                    <img src="https://i.ytimg.com/vi/${song.youtube_id}/mqdefault.jpg" alt="Miniatura" style="width: 60px; height: 45px; border-radius: 6px; object-fit: cover;">
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: var(--page-text); margin-bottom: 4px; word-break: break-word;">${song.titulo}</div>
                        <div style="font-size: 12px; color: var(--page-text-secondary);">Agregada por: <strong>${addedBy}</strong></div>
                    </div>
                </div>
                <div style="display: flex; gap: 8px; margin-bottom: 12px;">
                    ${positionBadge}
                </div>
                ${buttonsHtml}
            </div>
        `;
        listElement.appendChild(li);
    });
}



async function handleAdminSearch(event, karaokeMode = false) {
    event.preventDefault();
    const query = document.getElementById('admin-search-input').value.trim();
    if (!query) {
        showNotification('Escribe algo para buscar', 'error');
        return;
    }

    const songsButton = document.getElementById('admin-search-songs-btn');
    const karaokeButton = document.getElementById('admin-search-karaoke-btn');
    songsButton.disabled = true;
    karaokeButton.disabled = true;

    const clickedButton = karaokeMode ? karaokeButton : songsButton;
    const originalText = clickedButton.textContent;
    clickedButton.textContent = '⏳ Buscando...';

    const resultsContainer = document.getElementById('admin-search-results');
    resultsContainer.innerHTML = '';

    try {
        const url = `/youtube/search?q=${encodeURIComponent(query)}${karaokeMode ? '&karaoke_mode=true' : ''}`;
        const results = await apiFetch(url);

        if (results.length > 0) {
            results.forEach(song => {
                const resultItem = document.createElement('li');
                resultItem.style.marginBottom = '12px';
                resultItem.innerHTML = `
                    <div style="background: var(--page-input-bg); border-radius: 12px; padding: 12px; border-left: 4px solid var(--bees-blue); display: flex; gap: 8px; align-items: center;">
                        <img src="${song.thumbnail}" alt="Miniatura" style="width: 50px; height: 40px; border-radius: 6px; object-fit: cover; flex-shrink: 0;">
                        <div style="flex: 1; min-width: 0;">
                            <div style="font-weight: 600; color: var(--page-text); font-size: 13px; word-break: break-word;">${song.title}</div>
                            <div style="color: var(--page-text-muted); font-size: 11px;">⏱️ ${Math.floor(song.duration_seconds / 60)}:${(song.duration_seconds % 60).toString().padStart(2, '0')}</div>
                        </div>
                        <button class="bees-btn bees-btn-primary admin-add-song-btn" data-title="${song.title}" data-youtube-id="${song.video_id}" data-duration="${song.duration_seconds}" style="flex-shrink: 0; padding: 4px 8px; font-size: 11px; white-space: nowrap; max-width: 85px; min-width: 70px;">➕ Añadir</button>
                    </div>
                `;
                resultsContainer.appendChild(resultItem);
            });
        } else {
            const noResults = document.createElement('li');
            noResults.innerHTML = '<div class="bees-alert bees-alert-warning"><span class="bees-alert-icon">🔍</span><div>No se encontraron resultados</div></div>';
            resultsContainer.appendChild(noResults);
        }
    } catch (error) {
        const errorItem = document.createElement('li');
        errorItem.innerHTML = `<div class="bees-alert bees-alert-danger"><span class="bees-alert-icon">❌</span><div>Error: ${error.message}</div></div>`;
        resultsContainer.appendChild(errorItem);
    } finally {
        songsButton.disabled = false;
        karaokeButton.disabled = false;
        clickedButton.textContent = originalText;
    }
}

async function handleAdminAddSong(event) {
    const button = event.target.closest('.admin-add-song-btn');
    if (!button) return;

    button.disabled = true;
    button.textContent = '⏳ Añadiendo...';

    const songData = {
        titulo: button.dataset.title,
        youtube_id: button.dataset.youtubeId,
        duracion_seconds: parseInt(button.dataset.duration, 10)
    };

    const targetTableId = document.getElementById('admin-target-table').value;
    let endpoint;

    if (targetTableId) {
        endpoint = `/admin/mesas/${targetTableId}/add-song`;
    } else {
        endpoint = '/canciones/admin/add';
    }

    try {
        await apiFetch(endpoint, {
            method: 'POST',
            body: JSON.stringify(songData)
        });

        const targetName = targetTableId ? 'la mesa' : 'la cola general';
        showNotification(`✅ '${songData.titulo}' añadida a ${targetName}`, 'success');

        // Limpiar
        document.getElementById('admin-search-results').innerHTML = '';
        document.getElementById('admin-search-input').value = '';

        // Recargar
        await reloadApprovedQueue();

    } catch (error) {
        showNotification(error.message, 'error');
    } finally {
        button.disabled = false;
        button.textContent = '➕ Añadir';
    }
}

async function reloadApprovedQueue() {
    try {
        const queueData = await apiFetch(`/canciones/cola/extended?_=${Date.now()}`);
        currentQueueData = queueData;

        const approvedSongsList = document.getElementById('approved-songs-list');
        if (approvedSongsList) {
            renderApprovedSongs(queueData, approvedSongsList);
        }

        const lazySongsList = document.getElementById('lazy-songs-list');
        if (lazySongsList) {
            renderLazySongs(queueData.lazy_queue || [], lazySongsList);
        }


    } catch (error) {
        console.error('Error al recargar cola:', error);
    }
}

async function handleQueueActions(event) {
    const button = event.target.closest('button[data-action]');
    if (!button) return;

    const songId = button.dataset.id;
    const action = button.dataset.action;

    if (!action) return;

    button.disabled = true;
    const originalText = button.textContent;
    let shouldReloadQueue = false;

    try {
        if (action === 'play-song') {
            // Enviar orden de reproducir al player
            try {
                await apiFetch(`/canciones/${songId}/play`, { method: 'POST' });
                showNotification('▶️ Reproduciendo en player', 'success');
            } catch (error) {
                showNotification(`Error al reproducir: ${error.message}`, 'error');
            }

        } else if (action === 'remove') {
            if (!confirm('¿Eliminar esta canción?')) {
                button.disabled = false;
                return;
            }
            await apiFetch(`/canciones/${songId}/rechazar`, { method: 'POST' });
            showNotification('❌ Canción eliminada', 'info');
            shouldReloadQueue = true;

        } else if (action === 'restart') {
            try {
                await apiFetch(`/admin/canciones/restart`, { method: 'POST' });
                showNotification('🔄 Canción reiniciada', 'info');
            } catch (e) {
                showNotification('Función no disponible', 'warning');
            }

        } else if (action === 'play-next') {
            if (!confirm('¿Pasar a la siguiente canción?')) {
                button.disabled = false;
                return;
            }
            try {
                // Endpoint para avanzar cola
                await apiFetch('/canciones/siguiente', { method: 'POST' });
                showNotification('⏭️ Cambiando a la siguiente canción...', 'success');
                // No necesitamos reload manual si el websocket hace su trabajo,
                // pero por seguridad podemos activarlo o esperar el broadcast.
            } catch (error) {
                showNotification(`Error al cambiar de canción: ${error.message}`, 'error');
            }

        } else if (action === 'pause-resume-toggle') {
            await handlePauseResume();

        } else if (action === 'move-up') {
            // Mover canción aprobada hacia arriba
            try {
                await apiFetch(`/admin/canciones/${songId}/move-up`, { method: 'POST' });
                showNotification('⬆️ Canción movida hacia arriba', 'info');
                shouldReloadQueue = true;
            } catch (error) {
                showNotification(`Error al mover: ${error.message}`, 'error');
            }

        } else if (action === 'move-down') {
            // Mover canción aprobada hacia abajo
            try {
                await apiFetch(`/admin/canciones/${songId}/move-down`, { method: 'POST' });
                showNotification('⬇️ Canción movida hacia abajo', 'info');
                shouldReloadQueue = true;
            } catch (error) {
                showNotification(`Error al mover: ${error.message}`, 'error');
            }

        } else if (action === 'move-lazy-up') {
            // Mover canción lazy hacia arriba
            try {
                await apiFetch(`/admin/canciones/lazy/${songId}/move-up`, { method: 'POST' });
                showNotification('⬆️ Canción movida hacia arriba en cola lazy', 'info');
                shouldReloadQueue = true;
            } catch (error) {
                showNotification(`Error al mover: ${error.message}`, 'error');
            }

        } else if (action === 'move-lazy-down') {
            // Mover canción lazy hacia abajo
            try {
                await apiFetch(`/admin/canciones/lazy/${songId}/move-down`, { method: 'POST' });
                showNotification('⬇️ Canción movida hacia abajo en cola lazy', 'info');
                shouldReloadQueue = true;
            } catch (error) {
                showNotification(`Error al mover: ${error.message}`, 'error');
            }

        } else if (action === 'remove-lazy') {
            // Eliminar una canción lazy
            if (!confirm('¿Eliminar esta canción de la cola lazy?')) {
                button.disabled = false;
                return;
            }
            try {
                await apiFetch(`/canciones/${songId}/rechazar`, { method: 'POST' });
                showNotification('❌ Canción eliminada de cola lazy', 'info');
                shouldReloadQueue = true;
            } catch (error) {
                showNotification(`Error: ${error.message}`, 'error');
            }

        }

        if (shouldReloadQueue) {
            await reloadApprovedQueue();
        }

    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

async function handlePauseResume() {
    const pauseBtn = document.querySelector('button[data-action="pause-resume-toggle"]');
    const originalText = pauseBtn ? pauseBtn.textContent : '';

    try {
        // 1. Determine Intent based on current local state
        const isCurrentlyPlaying = playerState.isPlaying;
        const newIsPlaying = !isCurrentlyPlaying;

        // 2. Optimistic UI Update
        playerState.isPlaying = newIsPlaying; // Toggle state immediately
        if (pauseBtn) {
            pauseBtn.textContent = newIsPlaying ? '⏸️ Pausar' : '▶️ Reanudar';
        }

        // 3. API Call
        const endpoint = isCurrentlyPlaying ? '/admin/player/pause' : '/admin/player/resume';
        await apiFetch(endpoint, { method: 'POST' });

        showNotification(newIsPlaying ? '▶️ Reproducción reanudada' : '⏸️ Reproducción pausada', 'info');

        // 4. Reload Queue (Updates UI fully and ensures sync)
        await reloadApprovedQueue();

    } catch (error) {
        console.error('Error toggling pause/resume:', error);

        // Revert on error
        playerState.isPlaying = !playerState.isPlaying;
        if (pauseBtn) {
            pauseBtn.textContent = originalText;
        }
        showNotification(`Error: ${error.message}`, 'error');
    }
}

function setupQueueListeners() {
    const songsBtn = document.getElementById('admin-search-songs-btn');
    const karaokeBtn = document.getElementById('admin-search-karaoke-btn');
    const resultsContainer = document.getElementById('admin-search-results');
    const songsList = document.getElementById('approved-songs-list');
    const lazySongsList = document.getElementById('lazy-songs-list');

    if (songsBtn) {
        songsBtn.addEventListener('click', (e) => handleAdminSearch(e, false));
    }
    if (karaokeBtn) {
        karaokeBtn.addEventListener('click', (e) => handleAdminSearch(e, true));
    }
    if (resultsContainer) {
        resultsContainer.addEventListener('click', handleAdminAddSong);
    }
    if (songsList) {
        songsList.addEventListener('click', handleQueueActions);
    }
    // Agregar listener para los botones de la cola lazy (Esperando Turno)
    if (lazySongsList) {
        lazySongsList.addEventListener('click', handleQueueActions);
    }
}
