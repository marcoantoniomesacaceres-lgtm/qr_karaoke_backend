// Settings Page Module - BEES Style
// Manejo: configuración de cierre nocturno, claves API, parámetros generales

async function loadSettingsPage() {
    const settingsContainer = document.getElementById('settings');
    if (!settingsContainer) return;

    try {
        // Carga la configuración desde el backend
        let settings = { 
            closing_hour: 3, 
            closing_minute: 0, 
            app_name: 'QR Karaoke', 
            theme: 'dark', 
            enable_notifications: true 
        };
        
        try {
            const response = await apiFetch('/admin/settings');
            if (response) settings = { ...settings, ...response };
        } catch (e) {
            console.warn('Settings endpoint not available, using defaults:', e.message);
        }
        
        // Aplicar tema cargado
        document.body.dataset.theme = settings.theme;
        
        renderSettings(settings, settingsContainer);
    } catch (error) {
        const settingsContainer = document.getElementById('settings');
        if (settingsContainer) {
            settingsContainer.innerHTML = `<div class="settings-message error">
                <span class="settings-message-icon">❌</span>
                <div>${error.message}</div>
            </div>`;
        }
    }
}

function renderSettings(settings, container) {
    container.innerHTML = '';

    // Encabezado
    const header = document.createElement('div');
    header.className = 'settings-header';
    header.innerHTML = `
        <div class="settings-header-icon">⚙️</div>
        <div class="settings-header-content">
            <h1>Configuración</h1>
            <p>Personaliza tu experiencia en QR Karaoke</p>
        </div>
    `;
    container.appendChild(header);

    // Contenedor de tarjetas
    const cardsContainer = document.createElement('div');
    cardsContainer.className = 'settings-container';

    // ============= TARJETA 1: INFORMACIÓN GENERAL =============
    const generalCard = document.createElement('div');
    generalCard.className = 'settings-card';
    generalCard.innerHTML = `
        <div class="settings-card-header">
            <div class="settings-card-icon">📱</div>
            <div class="settings-card-header-content">
                <h3>Información General</h3>
                <p>Nombre y personalización</p>
            </div>
        </div>
        <form id="general-settings-form">
            <div class="bees-form-group">
                <label for="app-name">Nombre de la Aplicación</label>
                <input type="text" id="app-name" name="app_name" value="${settings.app_name || 'QR Karaoke'}" placeholder="Ej: QR Karaoke">
            </div>
            <button type="submit" class="bees-btn bees-btn-primary">
                💾 Guardar Cambios
            </button>
        </form>
    `;
    cardsContainer.appendChild(generalCard);

    // ============= TARJETA 2: TEMA =============
    const themeCard = document.createElement('div');
    themeCard.className = 'settings-card';
    const currentTheme = settings.theme || 'dark';
    themeCard.innerHTML = `
        <div class="settings-card-header">
            <div class="settings-card-icon">🎨</div>
            <div class="settings-card-header-content">
                <h3>Tema Visual</h3>
                <p>Elige tu preferencia</p>
            </div>
        </div>
        <form id="theme-settings-form">
            <div class="theme-options">
                <label class="theme-option ${currentTheme === 'dark' ? 'active' : ''}">
                    <input type="radio" name="theme" value="dark" ${currentTheme === 'dark' ? 'checked' : ''} style="display:none;">
                    <div class="theme-option-icon">🌙</div>
                    <div class="theme-option-label">Oscuro</div>
                </label>
                <label class="theme-option ${currentTheme === 'light' ? 'active' : ''}">
                    <input type="radio" name="theme" value="light" ${currentTheme === 'light' ? 'checked' : ''} style="display:none;">
                    <div class="theme-option-icon">☀️</div>
                    <div class="theme-option-label">Claro</div>
                </label>
                <label class="theme-option ${currentTheme === 'auto' ? 'active' : ''}">
                    <input type="radio" name="theme" value="auto" ${currentTheme === 'auto' ? 'checked' : ''} style="display:none;">
                    <div class="theme-option-icon">🔄</div>
                    <div class="theme-option-label">Auto</div>
                </label>
            </div>
            <button type="submit" class="bees-btn bees-btn-primary">
                💾 Aplicar Tema
            </button>
        </form>
    `;
    cardsContainer.appendChild(themeCard);

    // ============= TARJETA 3: NOTIFICACIONES =============
    const notificationsCard = document.createElement('div');
    notificationsCard.className = 'settings-card';
    notificationsCard.innerHTML = `
        <div class="settings-card-header">
            <div class="settings-card-icon">🔔</div>
            <div class="settings-card-header-content">
                <h3>Notificaciones</h3>
                <p>Controla alertas</p>
            </div>
        </div>
        <form id="notifications-settings-form">
            <div class="notification-item">
                <div class="notification-item-icon">📢</div>
                <div class="notification-item-content">
                    <p class="notification-item-title">Notificaciones Generales</p>
                    <p class="notification-item-desc">Recibe alertas importantes del sistema</p>
                </div>
                <input type="checkbox" class="bees-checkbox" id="enable-notifications" name="enable_notifications" ${settings.enable_notifications !== false ? 'checked' : ''}>
            </div>
            <button type="submit" class="bees-btn bees-btn-primary">
                💾 Guardar Preferencias
            </button>
        </form>
    `;
    cardsContainer.appendChild(notificationsCard);

    // ============= TARJETA 4: HORA DE CIERRE =============
    const closingTimeCard = document.createElement('div');
    closingTimeCard.className = 'settings-card';
    const closingHour = String(settings.closing_hour || 3).padStart(2, '0');
    const closingMinute = String(settings.closing_minute || 0).padStart(2, '0');
    closingTimeCard.innerHTML = `
        <div class="settings-card-header">
            <div class="settings-card-icon">🌙</div>
            <div class="settings-card-header-content">
                <h3>Hora de Cierre</h3>
                <p>Configurar cierre nocturno</p>
            </div>
        </div>
        <div class="closing-time-display">
            <div class="closing-time-display-label">Hora Actual</div>
            <div class="closing-time-display-value" id="closing-time-display">${closingHour}:${closingMinute}</div>
        </div>
        <form id="closing-time-form">
            <div class="closing-time-inputs">
                <div class="bees-form-group">
                    <label for="closing-hour">Hora (0-23)</label>
                    <input type="number" id="closing-hour" name="closing_hour" min="0" max="23" value="${settings.closing_hour || 3}">
                </div>
                <div class="bees-form-group">
                    <label for="closing-minute">Minuto (0-59)</label>
                    <input type="number" id="closing-minute" name="closing_minute" min="0" max="59" value="${settings.closing_minute || 0}">
                </div>
            </div>
            <button type="submit" class="bees-btn bees-btn-primary">
                💾 Guardar Hora
            </button>
        </form>
    `;
    cardsContainer.appendChild(closingTimeCard);

    // ============= TARJETA 5: CLAVES API =============
    const apiKeysCard = document.createElement('div');
    apiKeysCard.className = 'settings-card';
    apiKeysCard.innerHTML = `
        <div class="settings-card-header">
            <div class="settings-card-icon">🔐</div>
            <div class="settings-card-header-content">
                <h3>Claves de API</h3>
                <p>Gestiona tus accesos</p>
            </div>
        </div>
        <div id="api-keys-list" class="api-keys-list">
            <p style="text-align: center; color: var(--settings-text-secondary);">Cargando claves...</p>
        </div>
        <div style="margin-top: 20px; padding-top: 20px; border-top: 2px solid var(--settings-border);">
            <h4 style="margin: 0 0 16px 0; color: var(--settings-text);">Crear Nueva Clave</h4>
            <form id="create-api-key-form">
                <div class="bees-form-group">
                    <label for="key-description">Descripción</label>
                    <input type="text" id="key-description" name="description" placeholder="Ej: Mi laptop personal" required>
                </div>
                <button type="submit" class="bees-btn bees-btn-primary">
                    🔑 Generar Clave
                </button>
            </form>
            <div id="new-key-display" class="generated-key-display">
                <h4 class="generated-key-title">✅ ¡Clave Generada!</h4>
                <div class="generated-key-warning">
                    ⚠️ <strong>Guarda esta clave ahora.</strong> No podrás verla de nuevo.
                </div>
                <div class="key-input-group">
                    <input type="text" id="generated-key" readonly placeholder="Tu clave aparecerá aquí">
                    <button type="button" id="copy-generated-key" class="bees-btn bees-btn-success">
                        📋 Copiar
                    </button>
                </div>
            </div>
        </div>
    `;
    cardsContainer.appendChild(apiKeysCard);

    container.appendChild(cardsContainer);

    // Configurar listeners después de renderizar
    setupSettingsListeners();
}

async function handleClosingTimeUpdate(event, form) {
    event.preventDefault();
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    data.closing_hour = parseInt(data.closing_hour, 10);
    data.closing_minute = parseInt(data.closing_minute, 10);

    try {
        let success = false;
        try {
            await apiFetch('/admin/settings/closing-time', { 
                method: 'POST', 
                body: JSON.stringify(data) 
            });
            success = true;
        } catch (e) {
            // Fallback
            const fallbackData = { 
                hora_cierre: `${String(data.closing_hour).padStart(2, '0')}:${String(data.closing_minute).padStart(2, '0')}` 
            };
            await apiFetch('/admin/set-closing-time', { 
                method: 'POST', 
                body: JSON.stringify(fallbackData) 
            });
            success = true;
        }
        
        if (success) {
            // Actualizar display
            const display = document.getElementById('closing-time-display');
            if (display) {
                display.textContent = `${String(data.closing_hour).padStart(2, '0')}:${String(data.closing_minute).padStart(2, '0')}`;
            }
            showNotification(`✅ Hora de cierre actualizada a ${String(data.closing_hour).padStart(2, '0')}:${String(data.closing_minute).padStart(2, '0')}`, 'success');
        }
    } catch (error) {
        showNotification(`❌ ${error.message}`, 'error');
    }
}

async function handleThemeChange(event, form) {
    event.preventDefault();
    const formData = new FormData(form);
    const theme = formData.get('theme');

    try {
        const data = {
            app_name: 'QR Karaoke',
            theme: theme,
            enable_notifications: true
        };
        
        await apiFetch('/admin/settings/general', { 
            method: 'POST', 
            body: JSON.stringify(data) 
        });
        
        // Aplicar tema
        document.body.dataset.theme = theme;
        
        // Actualizar botones visuales
        document.querySelectorAll('.theme-option').forEach(option => {
            option.classList.remove('active');
        });
        form.querySelector(`input[value="${theme}"]`).parentElement.classList.add('active');
        
        showNotification(`✅ Tema cambiado a ${theme === 'dark' ? 'Oscuro 🌙' : theme === 'light' ? 'Claro ☀️' : 'Auto 🔄'}`, 'success');
    } catch (error) {
        showNotification(`❌ ${error.message}`, 'error');
    }
}

async function handleNotificationsChange(event, form) {
    event.preventDefault();
    const enableNotifications = document.getElementById('enable-notifications').checked;

    try {
        const data = {
            app_name: 'QR Karaoke',
            theme: document.body.dataset.theme || 'dark',
            enable_notifications: enableNotifications
        };
        
        await apiFetch('/admin/settings/general', { 
            method: 'POST', 
            body: JSON.stringify(data) 
        });
        
        showNotification(`✅ Notificaciones ${enableNotifications ? 'activadas ✔️' : 'desactivadas ✖️'}`, 'success');
    } catch (error) {
        showNotification(`❌ ${error.message}`, 'error');
    }
}

async function loadApiKeys() {
    const apiKeysList = document.getElementById('api-keys-list');
    if (!apiKeysList) return;

    try {
        const keys = await apiFetch('/admin/api-keys');

        if (!keys || keys.length === 0) {
            apiKeysList.innerHTML = '<p style="text-align: center; color: var(--settings-text-secondary);">No hay claves creadas todavía.</p>';
            return;
        }

        const keysTable = document.createElement('div');
        keysTable.className = 'api-keys-list';

        keys.forEach(key => {
            const keyItem = document.createElement('div');
            keyItem.className = 'api-key-item';

            const keyInfo = document.createElement('div');
            keyInfo.className = 'api-key-info';
            keyInfo.innerHTML = `
                <p class="api-key-description">🔑 ${key.description || 'Sin descripción'}</p>
                <p class="api-key-dates">
                    Creada: ${new Date(key.created_at).toLocaleString('es-ES')}
                    ${key.last_used ? `<br>Último uso: ${new Date(key.last_used).toLocaleString('es-ES')}` : ''}
                </p>
            `;

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'bees-btn bees-btn-danger';
            deleteBtn.textContent = '🗑️ Eliminar';
            deleteBtn.onclick = () => handleDeleteApiKey(key.id);

            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'api-key-actions';
            actionsDiv.appendChild(deleteBtn);

            keyItem.appendChild(keyInfo);
            keyItem.appendChild(actionsDiv);
            keysTable.appendChild(keyItem);
        });

        apiKeysList.innerHTML = '';
        apiKeysList.appendChild(keysTable);
    } catch (error) {
        apiKeysList.innerHTML = `<p style="text-align: center; color: var(--bees-red);">❌ Error al cargar claves: ${error.message}</p>`;
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

        // Mostrar clave generada
        const newKeyDisplay = document.getElementById('new-key-display');
        const generatedKeyInput = document.getElementById('generated-key');
        generatedKeyInput.value = newKey.key;
        newKeyDisplay.classList.add('show');

        // Botón copiar
        const copyBtn = document.getElementById('copy-generated-key');
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(newKey.key).then(() => {
                showNotification('✅ Clave copiada al portapapeles.', 'success');
                copyBtn.textContent = '✔️ Copiado!';
                setTimeout(() => {
                    copyBtn.textContent = '📋 Copiar';
                }, 2000);
            }).catch(err => {
                showNotification('❌ Error al copiar clave.', 'error');
            });
        };

        showNotification('✅ Clave generada con éxito. ¡Guárdala ahora!', 'success');
        form.reset();

        // Recargar lista
        await loadApiKeys();

        // Ocultar después de 60 segundos
        setTimeout(() => {
            newKeyDisplay.classList.remove('show');
        }, 60000);
    } catch (error) {
        showNotification(`❌ ${error.message}`, 'error');
    }
}

async function handleDeleteApiKey(keyId) {
    if (!confirm('🗑️ ¿Eliminar esta clave? Esta acción no se puede deshacer.')) {
        return;
    }

    try {
        await apiFetch(`/admin/api-keys/${keyId}`, { method: 'DELETE' });
        showNotification('✅ Clave eliminada con éxito.', 'success');
        await loadApiKeys();
    } catch (error) {
        showNotification(`❌ ${error.message}`, 'error');
    }
}

async function handleGeneralSettingsUpdate(event, form) {
    event.preventDefault();
    const formData = new FormData(form);
    const data = {
        app_name: formData.get('app_name'),
        theme: 'dark', // Mantener tema actual, solo cambiar nombre
        enable_notifications: true // Mantener notificaciones actuales
    };

    try {
        await apiFetch('/admin/settings/general', { 
            method: 'POST', 
            body: JSON.stringify(data) 
        });
        showNotification(`✅ Configuración actualizada. Nombre: "${data.app_name}"`, 'success');
    } catch (error) {
        showNotification(`❌ ${error.message}`, 'error');
    }
}



function setupSettingsListeners() {
    const closingTimeForm = document.getElementById('closing-time-form');
    const createApiKeyForm = document.getElementById('create-api-key-form');
    const generalSettingsForm = document.getElementById('general-settings-form');
    const themeSettingsForm = document.getElementById('theme-settings-form');
    const notificationsSettingsForm = document.getElementById('notifications-settings-form');
    
    // Closing time form
    if (closingTimeForm && !closingTimeForm.dataset.listenerAttached) {
        closingTimeForm.addEventListener('submit', (e) => handleClosingTimeUpdate(e, e.target));
        closingTimeForm.dataset.listenerAttached = '1';
    }
    
    // API key form
    if (createApiKeyForm && !createApiKeyForm.dataset.listenerAttached) {
        createApiKeyForm.addEventListener('submit', (e) => handleCreateApiKey(e, e.target));
        createApiKeyForm.dataset.listenerAttached = '1';
    }
    
    // General settings form
    if (generalSettingsForm && !generalSettingsForm.dataset.listenerAttached) {
        generalSettingsForm.addEventListener('submit', (e) => handleGeneralSettingsUpdate(e, e.target));
        generalSettingsForm.dataset.listenerAttached = '1';
    }
    
    // Theme form
    if (themeSettingsForm && !themeSettingsForm.dataset.listenerAttached) {
        themeSettingsForm.addEventListener('submit', (e) => handleThemeChange(e, e.target));
        // Permitir cambio al hacer click en radio buttons
        themeSettingsForm.querySelectorAll('input[name="theme"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                e.target.closest('form').dispatchEvent(new Event('submit'));
            });
        });
        themeSettingsForm.dataset.listenerAttached = '1';
    }
    
    // Notifications form
    if (notificationsSettingsForm && !notificationsSettingsForm.dataset.listenerAttached) {
        notificationsSettingsForm.addEventListener('submit', (e) => handleNotificationsChange(e, e.target));
        // Cambio rápido al hacer click en checkbox
        const notificationCheckbox = document.getElementById('enable-notifications');
        if (notificationCheckbox) {
            notificationCheckbox.addEventListener('change', (e) => {
                e.target.closest('form').dispatchEvent(new Event('submit'));
            });
        }
        notificationsSettingsForm.dataset.listenerAttached = '1';
    }

    // Load API keys
    loadApiKeys();
}
