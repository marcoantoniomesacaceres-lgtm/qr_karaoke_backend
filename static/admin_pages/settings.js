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
        <h3>Claves de API para Administradores</h3>
        <p style="color: var(--text-secondary); margin-bottom: 20px;">
            Gestiona las claves de API que permiten acceder al panel de administración.
        </p>
        <div id="api-keys-list" style="margin-bottom: 20px;">
            <p style="color: var(--text-secondary);">Cargando claves...</p>
        </div>
        <h4 style="margin-top: 20px;">Crear Nueva Clave</h4>
        <form id="create-api-key-form">
            <div class="form-group">
                <label for="key-description">Descripción:</label>
                <input type="text" id="key-description" name="description" placeholder="Ej: Mi laptop personal" required>
            </div>
            <button type="submit" class="btn-primary">Generar Clave</button>
        </form>
        <div id="new-key-display" style="display: none; margin-top: 20px; padding: 15px; background: var(--card-bg); border-radius: 8px; border: 2px solid var(--success-color);">
            <h4 style="color: var(--success-color);">¡Clave Generada!</h4>
            <p style="color: var(--warning-color); margin: 10px 0;">
                <strong>⚠️ Guarda esta clave ahora. No podrás verla de nuevo.</strong>
            </p>
            <div class="key-display">
                <input type="text" id="generated-key" readonly style="font-family: monospace; font-size: 14px;">
                <button class="btn-secondary" id="copy-generated-key">Copiar</button>
            </div>
        </div>
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

async function loadApiKeys() {
    const apiKeysList = document.getElementById('api-keys-list');
    if (!apiKeysList) return;

    try {
        const keys = await apiFetch('/admin/api-keys');

        if (!keys || keys.length === 0) {
            apiKeysList.innerHTML = '<p style="color: var(--text-secondary);">No hay claves creadas todavía.</p>';
            return;
        }

        apiKeysList.innerHTML = '<h4>Claves Existentes</h4>';
        const keysTable = document.createElement('div');
        keysTable.style.cssText = 'display: grid; gap: 10px;';

        keys.forEach(key => {
            const keyItem = document.createElement('div');
            keyItem.style.cssText = 'padding: 10px; background: var(--card-bg); border-radius: 8px; display: flex; justify-content: space-between; align-items: center;';

            const keyInfo = document.createElement('div');
            keyInfo.innerHTML = `
                <strong>${key.description || 'Sin descripción'}</strong><br>
                <small style="color: var(--text-secondary);">
                    Creada: ${new Date(key.created_at).toLocaleString('es-ES')}
                    ${key.last_used ? `| Último uso: ${new Date(key.last_used).toLocaleString('es-ES')}` : ''}
                </small>
            `;

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn-danger';
            deleteBtn.textContent = 'Eliminar';
            deleteBtn.onclick = () => handleDeleteApiKey(key.id);

            keyItem.appendChild(keyInfo);
            keyItem.appendChild(deleteBtn);
            keysTable.appendChild(keyItem);
        });

        apiKeysList.appendChild(keysTable);
    } catch (error) {
        apiKeysList.innerHTML = `<p style="color: var(--error-color);">Error al cargar claves: ${error.message}</p>`;
    }
}

async function handleCreateApiKey(event, form) {
    event.preventDefault();
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    try {
        const newKey = await apiFetch('/admin/api-keys', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        // Show the generated key
        const newKeyDisplay = document.getElementById('new-key-display');
        const generatedKeyInput = document.getElementById('generated-key');
        generatedKeyInput.value = newKey.key;
        newKeyDisplay.style.display = 'block';

        // Setup copy button
        const copyBtn = document.getElementById('copy-generated-key');
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(newKey.key).then(() => {
                showNotification('Clave copiada al portapapeles.', 'success');
            }).catch(err => {
                showNotification('Error al copiar clave.', 'error');
            });
        };

        showNotification('Clave generada con éxito. ¡Guárdala ahora!', 'success');
        form.reset();

        // Reload the keys list
        await loadApiKeys();

        // Hide the new key display after 60 seconds
        setTimeout(() => {
            newKeyDisplay.style.display = 'none';
        }, 60000);
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleDeleteApiKey(keyId) {
    if (!confirm('¿Estás seguro de que quieres eliminar esta clave? Esta acción no se puede deshacer.')) {
        return;
    }

    try {
        await apiFetch(`/admin/api-keys/${keyId}`, { method: 'DELETE' });
        showNotification('Clave eliminada con éxito.', 'success');
        await loadApiKeys();
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



function setupSettingsListeners() {
    const closingTimeForm = document.getElementById('closing-time-form');
    const createApiKeyForm = document.getElementById('create-api-key-form');
    const generalSettingsForm = document.getElementById('general-settings-form');

    if (closingTimeForm) {
        closingTimeForm.addEventListener('submit', (e) => handleClosingTimeUpdate(e, e.target));
    }
    if (createApiKeyForm) {
        createApiKeyForm.addEventListener('submit', (e) => handleCreateApiKey(e, e.target));
    }
    if (generalSettingsForm) {
        generalSettingsForm.addEventListener('submit', (e) => handleGeneralSettingsUpdate(e, e.target));
    }

    // Load existing API keys
    loadApiKeys();
}
