// Settings Page Module
// Manejo: configuración de cierre nocturno, claves API, parámetros generales

async function loadSettingsPage() {
    const settingsContainer = document.getElementById('settings-container');
    if (!settingsContainer) return;

    try {
        // Nota: /admin/settings puede no existir en el backend.
        // Intentamos cargar; si falla, usamos valores por defecto.
        let settings = { closing_hour: 3, closing_minute: 0, app_name: 'QR Karaoke', theme: 'dark', enable_notifications: true };
        try {
            const response = await apiFetch('/admin/settings');
            if (response) settings = { ...settings, ...response };
        } catch (e) {
            console.warn('Settings endpoint not available, using defaults:', e.message);
        }
        renderSettings(settings, settingsContainer);
    } catch (error) {
        settingsContainer.innerHTML = `<p style="color: var(--error-color);">${error.message}</p>`;
    }
}

function renderSettings(settings, container) {
    container.innerHTML = '';

    // Closing Time Settings
    const closingDiv = document.createElement('div');
    closingDiv.className = 'settings-section';
    closingDiv.innerHTML = `
        <h3>Configuración de Cierre Nocturno</h3>
        <form id="closing-time-form">
            <div class="form-group">
                <label for="closing-hour">Hora de Cierre (24h):</label>
                <input type="number" id="closing-hour" name="closing_hour" min="0" max="23" value="${settings.closing_hour || 3}">
            </div>
            <div class="form-group">
                <label for="closing-minute">Minuto:</label>
                <input type="number" id="closing-minute" name="closing_minute" min="0" max="59" value="${settings.closing_minute || 0}">
            </div>
            <button type="submit" class="btn-primary">Guardar Hora de Cierre</button>
        </form>
    `;
    container.appendChild(closingDiv);

    // API Keys Settings
    const apiKeysDiv = document.createElement('div');
    apiKeysDiv.className = 'settings-section';
    apiKeysDiv.innerHTML = `
        <h3>Claves de API</h3>
        <div class="api-keys-list">
            <div class="api-key-item">
                <label>Clave API Admin:</label>
                <div class="key-display">
                    <input type="password" id="admin-api-key" value="${settings.admin_api_key || 'No configurada'}" readonly>
                    <button class="btn-secondary toggle-visibility" data-target="admin-api-key">Mostrar</button>
                    <button class="btn-secondary copy-to-clipboard" data-target="admin-api-key">Copiar</button>
                </div>
            </div>
            <div class="api-key-item">
                <label>Clave API YouTube:</label>
                <div class="key-display">
                    <input type="password" id="youtube-api-key" value="${settings.youtube_api_key || 'No configurada'}" readonly>
                    <button class="btn-secondary toggle-visibility" data-target="youtube-api-key">Mostrar</button>
                    <button class="btn-secondary copy-to-clipboard" data-target="youtube-api-key">Copiar</button>
                </div>
            </div>
        </div>
        <h4 style="margin-top: 20px;">Actualizar Claves</h4>
        <form id="api-keys-form">
            <div class="form-group">
                <label for="new-admin-api-key">Nueva Clave Admin:</label>
                <input type="text" id="new-admin-api-key" name="admin_api_key" placeholder="Dejar en blanco para no cambiar">
            </div>
            <div class="form-group">
                <label for="new-youtube-api-key">Nueva Clave YouTube:</label>
                <input type="text" id="new-youtube-api-key" name="youtube_api_key" placeholder="Dejar en blanco para no cambiar">
            </div>
            <button type="submit" class="btn-primary">Actualizar Claves</button>
        </form>
    `;
    container.appendChild(apiKeysDiv);

    // General Settings
    const generalDiv = document.createElement('div');
    generalDiv.className = 'settings-section';
    generalDiv.innerHTML = `
        <h3>Configuración General</h3>
        <form id="general-settings-form">
            <div class="form-group">
                <label for="app-name">Nombre de la App:</label>
                <input type="text" id="app-name" name="app_name" value="${settings.app_name || 'QR Karaoke'}">
            </div>
            <div class="form-group">
                <label for="theme">Tema:</label>
                <select id="theme" name="theme">
                    <option value="dark" ${(settings.theme || 'dark') === 'dark' ? 'selected' : ''}>Oscuro</option>
                    <option value="light" ${(settings.theme || 'dark') === 'light' ? 'selected' : ''}>Claro</option>
                    <option value="auto" ${(settings.theme || 'dark') === 'auto' ? 'selected' : ''}>Auto</option>
                </select>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="enable-notifications" ${settings.enable_notifications !== false ? 'checked' : ''}>
                    Habilitar Notificaciones
                </label>
            </div>
            <button type="submit" class="btn-primary">Guardar Configuración</button>
        </form>
    `;
    container.appendChild(generalDiv);
}

async function handleClosingTimeUpdate(event, form) {
    event.preventDefault();
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    data.closing_hour = parseInt(data.closing_hour, 10);
    data.closing_minute = parseInt(data.closing_minute, 10);

    try {
        // Intentar /admin/settings/closing-time primero; si falla, usar /admin/set-closing-time
        let success = false;
        try {
            await apiFetch('/admin/settings/closing-time', { method: 'POST', body: JSON.stringify(data) });
            success = true;
        } catch (e) {
            // Fallback a /admin/set-closing-time con payload diferente
            const fallbackData = { hora_cierre: `${String(data.closing_hour).padStart(2, '0')}:${String(data.closing_minute).padStart(2, '0')}` };
            await apiFetch('/admin/set-closing-time', { method: 'POST', body: JSON.stringify(fallbackData) });
            success = true;
        }
        if (success) {
            showNotification(`Hora de cierre actualizada a ${data.closing_hour}:${String(data.closing_minute).padStart(2, '0')}.`);
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleApiKeysUpdate(event, form) {
    event.preventDefault();
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Remove empty fields
    if (!data.admin_api_key) delete data.admin_api_key;
    if (!data.youtube_api_key) delete data.youtube_api_key;

    if (Object.keys(data).length === 0) {
        showNotification('Por favor ingresa al menos una clave nueva.', 'warning');
        return;
    }

    try {
        await apiFetch('/admin/settings/api-keys', { method: 'POST', body: JSON.stringify(data) });
        showNotification('Claves API actualizadas con éxito.');
        form.reset();
        loadSettingsPage();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleGeneralSettingsUpdate(event, form) {
    event.preventDefault();
    const formData = new FormData(form);
    const data = {
        app_name: formData.get('app_name'),
        theme: formData.get('theme'),
        enable_notifications: formData.get('enable_notifications') === 'on'
    };

    try {
        await apiFetch('/admin/settings/general', { method: 'POST', body: JSON.stringify(data) });
        showNotification('Configuración general actualizada.');
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

function handleToggleVisibility(event) {
    const button = event.target;
    if (!button.matches('.toggle-visibility')) return;

    const targetId = button.dataset.target;
    const input = document.getElementById(targetId);
    if (!input) return;

    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    button.textContent = isPassword ? 'Ocultar' : 'Mostrar';
}

function handleCopyToClipboard(event) {
    const button = event.target;
    if (!button.matches('.copy-to-clipboard')) return;

    const targetId = button.dataset.target;
    const input = document.getElementById(targetId);
    if (!input) return;

    const text = input.value;
    if (text === 'No configurada') {
        showNotification('Esta clave no está configurada.', 'warning');
        return;
    }

    navigator.clipboard.writeText(text).then(() => {
        showNotification('Clave copiada al portapapeles.', 'success');
    }).catch(err => {
        showNotification('Error al copiar clave.', 'error');
        console.error('Clipboard error:', err);
    });
}

function setupSettingsListeners() {
    const closingTimeForm = document.getElementById('closing-time-form');
    const apiKeysForm = document.getElementById('api-keys-form');
    const generalSettingsForm = document.getElementById('general-settings-form');
    const settingsContainer = document.getElementById('settings-container');

    if (closingTimeForm) {
        closingTimeForm.addEventListener('submit', (e) => handleClosingTimeUpdate(e, e.target));
    }
    if (apiKeysForm) {
        apiKeysForm.addEventListener('submit', (e) => handleApiKeysUpdate(e, e.target));
    }
    if (generalSettingsForm) {
        generalSettingsForm.addEventListener('submit', (e) => handleGeneralSettingsUpdate(e, e.target));
    }
    if (settingsContainer) {
        settingsContainer.addEventListener('click', handleToggleVisibility);
        settingsContainer.addEventListener('click', handleCopyToClipboard);
    }
}
