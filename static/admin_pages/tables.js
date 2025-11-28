// Tables/QR Page Module - Simplified Version
// Manejo directo por número de mesa y usuario

async function loadTablesPage() {
    // Setup listeners
    setupTablesListeners();
}

function setupTablesListeners() {
    // QR Generator Form
    const qrForm = document.getElementById('qr-generator-form');
    if (qrForm) {
        qrForm.addEventListener('submit', handleGenerateQR);
    }

    // Management Buttons
    const btnActivate = document.getElementById('btn-activate');
    const btnDeactivate = document.getElementById('btn-deactivate');
    const btnDelete = document.getElementById('btn-delete');
    const btnCreate = document.getElementById('btn-create');
    const openPlayerBtn = document.getElementById('open-player-dashboard');

    if (btnActivate) btnActivate.addEventListener('click', () => handleTableAction('activate'));
    if (btnDeactivate) btnDeactivate.addEventListener('click', () => handleTableAction('deactivate'));
    if (btnDelete) btnDelete.addEventListener('click', () => handleTableAction('delete'));
    if (btnCreate) btnCreate.addEventListener('click', handleCreateTableDirect);

    if (openPlayerBtn) {
        openPlayerBtn.addEventListener('click', () => {
            window.open('/player', '_blank');
        });
    }
}

function handleGenerateQR(event) {
    event.preventDefault();

    const tableNumInput = document.getElementById('qr-table-number');
    const userSelect = document.getElementById('qr-user-select');
    const resultArea = document.getElementById('qr-result');

    if (!tableNumInput.value) {
        showNotification('Por favor ingresa un número de mesa', 'error');
        return;
    }

    const tableNum = tableNumInput.value.toString().padStart(2, '0'); // Ensure 05 format
    const userNum = userSelect.value;

    // Construct QR Code string: karaoke-mesa-XX-usuarioN
    const qrCode = `karaoke-mesa-${tableNum}-usuario${userNum}`;
    const tableName = `Mesa ${parseInt(tableNum)}`;
    const userNick = `${tableName}-Usuario${userNum}`;

    // Generate URL
    const appBaseUrl = window.location.origin;
    const appUrl = `${appBaseUrl}/?table=${encodeURIComponent(qrCode)}`;
    const qrImageUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(appUrl)}`;

    resultArea.innerHTML = `
        <div class="qr-container" style="animation: fadeIn 0.5s;">
            <img src="${qrImageUrl}" alt="QR Code" class="qr-image" style="border: 2px solid #333; padding: 10px; border-radius: 10px;">
            <h3 style="margin: 10px 0 5px 0;">${userNick}</h3>
            <p style="font-family: monospace; background: #f0f0f0; padding: 5px; border-radius: 4px;">${qrCode}</p>
            <a href="${qrImageUrl}" download="qr-${qrCode}.png" class="btn-primary" style="display: inline-block; margin-top: 10px; text-decoration: none;">
                ⬇️ Descargar QR
            </a>
        </div>
    `;
}

async function findTableByNumber(number) {
    try {
        const tables = await apiFetch('/mesas/');
        // Search for table with QR containing "karaoke-mesa-XX" or name "Mesa X"
        // We prioritize the QR code format standard
        const targetQR = `karaoke-mesa-${number.toString().padStart(2, '0')}`;

        // Find exact match or base match
        const found = tables.find(t => {
            if (t.qr_code === targetQR) return true;
            // Check if it's a base match (ignoring timestamp suffix if any)
            if (t.qr_code.startsWith(targetQR) && !t.qr_code.includes('usuario')) return true;
            return false;
        });

        return found;
    } catch (error) {
        console.error("Error fetching tables:", error);
        return null;
    }
}

async function handleTableAction(action) {
    const tableNumInput = document.getElementById('manage-table-number');
    const statusDiv = document.getElementById('management-status');

    if (!tableNumInput.value) {
        showNotification('Por favor ingresa un número de mesa para gestionar', 'error');
        return;
    }

    const tableNum = tableNumInput.value.toString().padStart(2, '0');
    statusDiv.innerHTML = '<p>Buscando mesa...</p>';

    try {
        const table = await findTableByNumber(tableNum);

        if (!table) {
            statusDiv.innerHTML = `<p style="color: var(--error-color);">❌ No se encontró la Mesa ${parseInt(tableNum)}.</p>`;
            if (action !== 'create') {
                showNotification(`La Mesa ${parseInt(tableNum)} no existe. Créala primero.`, 'warning');
            }
            return;
        }

        let endpoint;
        let method = 'POST';
        let successMsg;

        if (action === 'activate') {
            endpoint = `/mesas/${table.id}/activate`;
            successMsg = `✅ Mesa ${parseInt(tableNum)} activada correctamente.`;
        } else if (action === 'deactivate') {
            endpoint = `/mesas/${table.id}/deactivate`;
            successMsg = `⏸️ Mesa ${parseInt(tableNum)} desactivada.`;
        } else if (action === 'delete') {
            if (!confirm(`¿Estás seguro de ELIMINAR la Mesa ${parseInt(tableNum)}? Esta acción es irreversible.`)) {
                statusDiv.innerHTML = '';
                return;
            }
            endpoint = `/mesas/${table.id}`;
            method = 'DELETE';
            successMsg = `🗑️ Mesa ${parseInt(tableNum)} eliminada del sistema.`;
        }

        await apiFetch(endpoint, { method: method });
        statusDiv.innerHTML = `<p style="color: var(--success-color); font-weight: bold;">${successMsg}</p>`;
        showNotification(successMsg, 'success');

    } catch (error) {
        statusDiv.innerHTML = `<p style="color: var(--error-color);">Error: ${error.message}</p>`;
    }
}

async function handleCreateTableDirect() {
    const tableNumInput = document.getElementById('manage-table-number');
    const statusDiv = document.getElementById('management-status');

    if (!tableNumInput.value) {
        showNotification('Ingresa un número para crear la mesa', 'error');
        return;
    }

    const tableNum = parseInt(tableNumInput.value);
    const qrCode = `karaoke-mesa-${tableNum.toString().padStart(2, '0')}`;
    const nombre = `Mesa ${tableNum}`;

    try {
        // Check if exists first
        const existing = await findTableByNumber(tableNum);
        if (existing) {
            statusDiv.innerHTML = `<p style="color: var(--warning-color);">⚠️ La Mesa ${tableNum} ya existe.</p>`;
            return;
        }

        const payload = {
            nombre: nombre,
            qr_code: qrCode
        };

        await apiFetch('/mesas/', { method: 'POST', body: JSON.stringify(payload) });
        statusDiv.innerHTML = `<p style="color: var(--success-color);">✅ Mesa ${tableNum} creada exitosamente.</p>`;
        showNotification(`Mesa ${tableNum} creada.`, 'success');

    } catch (error) {
        statusDiv.innerHTML = `<p style="color: var(--error-color);">Error al crear: ${error.message}</p>`;
    }
}
