// Tables/QR Page Module
// Manejo: mesas, generación de códigos QR, activación/desactivación de mesas

async function loadTablesPage() {
    const tablesList = document.getElementById('tables-list');
    const qrDisplayArea = document.getElementById('qr-display-area');

    if (tablesList) {
        try {
            const tables = await apiFetch('/mesas/');
            renderTablesList(tables, tablesList);
        } catch (error) {
            tablesList.innerHTML = `<p style="color: var(--error-color);">${error.message}</p>`;
        }
    }

    if (qrDisplayArea) {
        qrDisplayArea.innerHTML = '<p>Selecciona una mesa para ver su código QR.</p>';
    }
}

function renderTablesList(tables, tablesList) {
    tablesList.innerHTML = '';
    if (tables.length === 0) {
        tablesList.innerHTML = '<p>No hay mesas creadas.</p>';
        return;
    }

    tables.forEach(table => {
        const li = document.createElement('li');
        li.className = `table-item ${table.is_active ? 'active' : 'inactive'}`;
        li.innerHTML = `
            <div class="table-info">
                <h4>${table.nombre}</h4>
                <p>QR Code: ${table.qr_code || 'No generado'}</p>
                <span class="status-badge ${table.is_active ? 'status-active' : 'status-inactive'}">
                    ${table.is_active ? 'Activa' : 'Inactiva'}
                </span>
            </div>
            <div class="table-actions">
                <button class="btn-qr" data-id="${table.id}" data-qr-code="${table.qr_code}">Generar QR</button>
                ${table.is_active
                ? `<button class="btn-deactivate" data-id="${table.id}">Desactivar</button>`
                : `<button class="btn-activate" data-id="${table.id}">Activar</button>`
            }
                <button class="btn-delete" data-id="${table.id}">Eliminar</button>
            </div>
        `;
        tablesList.appendChild(li);
    });
}

function handleShowQR(event) {
    const button = event.target;
    if (!button.matches('.btn-qr')) return;

    const tableId = button.dataset.id;
    const qrCode = button.dataset.qrCode;
    const displayArea = document.getElementById('qr-display-area');

    if (!displayArea) return;

    if (!qrCode) {
        displayArea.innerHTML = `<p style="color: var(--warning-color);">No hay código QR disponible para esta mesa.</p>`;
        return;
    }

    // Generar URL del QR dinámicamente usando qrserver.com
    const qrImageUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(qrCode)}`;
    const tableNameEl = button.closest('.table-item')?.querySelector('h4');
    const tableName = tableNameEl ? tableNameEl.textContent : `Mesa ${tableId}`;

    displayArea.innerHTML = `
        <div class="qr-container">
            <img src="${qrImageUrl}" alt="QR Code" class="qr-image" style="border: 2px solid #ddd; padding: 10px;">
            <p><strong>${tableName}</strong></p>
            <p style="font-size: 0.9em; color: #666;">Código: ${qrCode}</p>
            <a href="${qrImageUrl}" download="qr-${qrCode}.png" class="btn-primary">Descargar QR</a>
        </div>
    `;
}

async function handleToggleTableActive(event) {
    const button = event.target;
    if (!button.matches('.btn-activate, .btn-deactivate')) return;

    const tableId = button.dataset.id;
    const activate = button.classList.contains('btn-activate');
    const endpoint = `/mesas/${tableId}/${activate ? 'activate' : 'deactivate'}`;

    try {
        const result = await apiFetch(endpoint, { method: 'POST' });
        showNotification(`Mesa ${result.numero} ${activate ? 'activada' : 'desactivada'}.`);
        loadTablesPage();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleDeleteTable(event) {
    const button = event.target;
    if (!button.matches('.btn-delete')) return;

    const tableId = button.dataset.id;
    if (!confirm('¿Estás seguro de que quieres ELIMINAR esta mesa permanentemente? Esta acción no se puede deshacer.')) return;

    try {
        await apiFetch(`/mesas/${tableId}`, { method: 'DELETE' });
        showNotification('Mesa eliminada con éxito.', 'info');
        loadTablesPage();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleCreateTable(event, form) {
    event.preventDefault();
    const formData = new FormData(form);
    const tableData = Object.fromEntries(formData.entries());
    // Normalize inputs
    const numero = tableData.numero ? parseInt(tableData.numero, 10) : null;
    const nombre = tableData.nombre && tableData.nombre.trim() !== '' ? tableData.nombre.trim() : (numero ? `Mesa ${numero}` : 'Mesa');

    // Generate a qr_code consistent with existing naming convention (karaoke-mesa-XX)
    const qr_code = numero ? `karaoke-mesa-${String(numero).padStart(2, '0')}` : `karaoke-mesa-${Date.now()}`;

    const payload = {
        nombre: nombre,
        qr_code: qr_code
    };

    try {
        const result = await apiFetch('/mesas/', { method: 'POST', body: JSON.stringify(payload) });
        showNotification(`Mesa '${result.nombre}' creada con éxito. Código QR: ${result.qr_code}`);
        form.reset();
        loadTablesPage();
    } catch (error) {
        // If validation error from backend (422), show helpful message
        if (error.message && error.message.includes('422')) {
            showNotification('Datos inválidos al crear la mesa. Revisa el número y el nombre.', 'error');
        } else {
            showNotification(error.message, 'error');
        }
    }
}

function setupTablesListeners() {
    const tablesList = document.getElementById('tables-list');
    const createForm = document.getElementById('create-table-form');
    const openPlayerBtn = document.getElementById('open-player-dashboard');

    if (tablesList) {
        tablesList.addEventListener('click', handleShowQR);
        tablesList.addEventListener('click', handleToggleTableActive);
        tablesList.addEventListener('click', handleDeleteTable);
    }
    if (createForm) createForm.addEventListener('submit', (e) => handleCreateTable(e, e.target));
    if (openPlayerBtn) {
        openPlayerBtn.addEventListener('click', () => {
            window.open('/player.html', '_blank');
        });
    }
}
