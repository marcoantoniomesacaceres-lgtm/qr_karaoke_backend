// Accounts Page Module
// Manejo: cuentas de pago, comisiones, transacciones

function renderAccounts(accounts, accountsGrid) {
    accountsGrid.innerHTML = '';
    if (accounts.length === 0) {
        accountsGrid.innerHTML = '<p>No hay mesas ni estados de cuenta disponibles.</p>';
        return;
    }

    accounts.forEach(acc => {
        const card = document.createElement('div');
        card.className = 'account-card card';

        const titulo = acc.mesa_nombre || `Mesa ${acc.mesa_id}`;
        const deuda = acc.saldo_pendiente || 0;
        const consumos = Array.isArray(acc.consumos) ? acc.consumos : [];
        const pagos = Array.isArray(acc.pagos) ? acc.pagos : [];

        card.innerHTML = `
            <div class="account-header">
                <h3>${titulo}</h3>
                <span class="commission-badge">Saldo: $${deuda}</span>
            </div>
            <div class="account-details">
                <div class="account-summary">
                    <div>Total consumido: $${acc.total_consumido || 0}</div>
                    <div>Total pagado: $${acc.total_pagado || 0}</div>
                    <div class="saldo-pendiente ${deuda > 0 ? 'saldo-debe' : 'saldo-ok'}">Pendiente: $${deuda}</div>
                </div>
                <div class="details-section">
                    <strong>Consumos:</strong>
                    <ul>
                        ${consumos.map(c => `<li>${c.cantidad}x ${c.producto_nombre} — $${c.valor_total} (${new Date(c.created_at).toLocaleString()})</li>`).join('')}
                    </ul>
                    <strong>Pagos:</strong>
                    <ul>
                        ${pagos.map(p => `<li>$${p.monto} — ${new Date(p.created_at).toLocaleString()}</li>`).join('')}
                    </ul>
                </div>
            </div>
            <div class="account-actions">
                <button class="btn-payment" data-id="${acc.mesa_id}">Registrar Pago</button>
            </div>
        `;

        accountsGrid.appendChild(card);
    });
}

async function loadAccountsPage() {
    const accountsGrid = document.getElementById('accounts-grid');
    try {
        // Usar el endpoint de administracion que devuelve el estado de cuenta por mesa
        // Endpoint disponible en backend: GET /api/v1/admin/reports/table-payment-status
        const accounts = await apiFetch('/admin/reports/table-payment-status');
        renderAccounts(accounts, accountsGrid);

        // El backend NO expone endpoints para crear/editar cuentas de pago de terceros
        // (ese concepto no existe en este proyecto). Ocultamos el formulario de creación
        // si está presente para evitar intentos de POST a rutas inexistentes.
        const createForm = document.getElementById('create-account-form');
        if (createForm) {
            createForm.style.display = 'none';
            const hint = document.createElement('p');
            hint.style.color = 'var(--text-secondary)';
            hint.textContent = 'La creación/edición de cuentas de pago no está habilitada desde este panel.';
            createForm.parentElement.appendChild(hint);
        }
    } catch (error) {
        // Mostrar mensaje graceful si el endpoint no existe o el método no está permitido
        const msg = (error.message && (error.message.includes('404') || error.message.includes('405') || error.message.includes('endpoint') || error.message.includes('Method Not Allowed')))
            ? 'Módulo de cuentas no disponible en el servidor backend. Por favor contacta al administrador.'
            : error.message || 'Error cargando cuentas.';
        accountsGrid.innerHTML = `<p style="color: var(--error-color);">${msg}</p>`;
        // Ocultar formulario de creación si existe
        const createForm = document.getElementById('create-account-form');
        if (createForm) createForm.style.display = 'none';
    }
}

async function handleCreateAccount(event, form) {
    event.preventDefault();
    const formData = new FormData(form);
    const accountData = Object.fromEntries(formData.entries());
    accountData.comision_percentage = parseInt(accountData.comision_percentage, 10);

    // Este panel no soporta la creación de cuentas de pago (no hay endpoint correspondiente)
    showNotification('Creación de cuentas no soportada por el backend.', 'error');
}

function handlePaymentModal(event) {
    const button = event.target;
    if (!button.matches('.btn-payment')) return;

    const accountId = button.dataset.id;
    const modal = document.getElementById('payment-modal');
    if (!modal) return;

    const paymentInput = modal.querySelector('#payment-amount');
    // Store the mesa_id in the hidden input
    const mesaIdInput = modal.querySelector('#payment-mesa-id');

    if (paymentInput) paymentInput.value = '';
    if (mesaIdInput) mesaIdInput.value = accountId;

    modal.style.display = 'flex';
}

async function handlePaymentSubmit(event) {
    event.preventDefault();
    const form = event.target;

    // Get values from form inputs
    const mesaIdInput = form.querySelector('#payment-mesa-id');
    const amountInput = form.querySelector('#payment-amount');
    const methodSelect = form.querySelector('#payment-method');

    const mesaId = parseInt(mesaIdInput?.value || 0, 10);
    const amount = parseFloat(amountInput?.value || 0);
    const metodo = methodSelect?.value || 'Efectivo';

    if (!amount || amount <= 0) {
        showNotification('Por favor ingresa un monto válido.', 'error');
        return;
    }

    if (!mesaId) {
        showNotification('Error: Mesa no identificada.', 'error');
        return;
    }

    try {
        // Registrar el pago usando el endpoint admin POST /api/v1/admin/pagos
        const payload = { mesa_id: mesaId, monto: amount, metodo_pago: metodo };
        const result = await apiFetch('/admin/pagos', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        showNotification(`Pago de $${amount} registrado exitosamente.`);

        // Close modal
        const modal = document.getElementById('payment-modal');
        if (modal) modal.style.display = 'none';

        // Reload accounts page
        loadAccountsPage();
    } catch (error) {
        showNotification(error.message || 'Error al registrar el pago', 'error');
    }
}

async function handleDeleteAccount(event) {
    const button = event.target;
    if (!button.matches('.btn-delete')) return;

    const accountId = button.dataset.id;
    // No existe endpoint para eliminar cuentas de pago en el backend actual.
    showNotification('Eliminar cuentas no está soportado por el backend.', 'error');
}

function setupAccountsListeners() {
    const createForm = document.getElementById('create-account-form');
    const accountsGrid = document.getElementById('accounts-grid');
    const paymentModal = document.getElementById('payment-modal');
    const paymentForm = document.getElementById('payment-form');
    const closePaymentModalBtn = document.getElementById('payment-modal-close');

    if (createForm) createForm.addEventListener('submit', (e) => handleCreateAccount(e, e.target));
    if (accountsGrid) {
        accountsGrid.addEventListener('click', handlePaymentModal);
        accountsGrid.addEventListener('click', handleDeleteAccount);
    }
    // Attach submit listener to the form, not the button
    if (paymentForm) paymentForm.addEventListener('submit', handlePaymentSubmit);
    if (closePaymentModalBtn) {
        closePaymentModalBtn.addEventListener('click', () => {
            if (paymentModal) paymentModal.style.display = 'none';
        });
    }
    if (paymentModal) {
        paymentModal.addEventListener('click', (e) => {
            if (e.target === paymentModal) paymentModal.style.display = 'none';
        });
    }
}
