// Dashboard Page Module
// Manejo: resumen, últimos pedidos, acciones rápidas, reacciones

async function loadDashboardPage() {
    try {
        const summary = await apiFetch('/admin/summary');
        const ingresos = Number(summary.ingresos_totales) || 0;
        const ganancias = Number(summary.ganancias_totales) || 0;

        document.getElementById('summary-income').textContent = `$${ingresos.toFixed(2)}`;
        document.getElementById('summary-profits').textContent = `$${ganancias.toFixed(2)}`;
        document.getElementById('summary-songs').textContent = Number(summary.canciones_cantadas) || 0;
        document.getElementById('summary-users').textContent = Number(summary.usuarios_activos) || 0;

        loadRecentOrders();
    } catch (error) {
        showNotification(`Error al cargar resumen: ${error.message}`, 'error');
    }
}

async function loadRecentOrders() {
    const listEl = document.getElementById('recent-orders-list');
    try {
        const pedidos = await apiFetch('/admin/recent-consumos?limit=25');
        listEl.innerHTML = '';
        if (!pedidos || pedidos.length === 0) {
            listEl.innerHTML = '<li><p>No hay pedidos recientes.</p></li>';
            return;
        }

        const pedidosPorMesa = pedidos.reduce((acc, pedido) => {
            const mesaNombre = pedido.mesa_nombre || 'Pedidos sin mesa';
            if (!acc[mesaNombre]) {
                acc[mesaNombre] = {
                    items: [],
                    ultimaFecha: new Date(0),
                    nicks: new Set()
                };
            }
            acc[mesaNombre].items.push(pedido);
            acc[mesaNombre].nicks.add(pedido.usuario_nick);
            if (new Date(pedido.created_at) > acc[mesaNombre].ultimaFecha) {
                acc[mesaNombre].ultimaFecha = new Date(pedido.created_at);
            }
            return acc;
        }, {});

        Object.keys(pedidosPorMesa).sort((a, b) => pedidosPorMesa[b].ultimaFecha - pedidosPorMesa[a].ultimaFecha).forEach(mesaNombre => {
            const grupo = pedidosPorMesa[mesaNombre];
            const li = document.createElement('li');
            li.className = 'item';

            const itemsHtml = grupo.items.map(item => `<li>${item.cantidad}x ${item.producto_nombre}</li>`).join('');
            const allConsumoIds = grupo.items.map(item => item.id).join(',');

            li.innerHTML = `
                <div class="item-details">
                    <div class="item-title">
                        ${mesaNombre} pidió:
                        <span class="order-alert-icon shaking">🔔</span>
                    </div>
                    <ul style="padding-left: 20px; margin: 5px 0; font-size: 0.95em;">${itemsHtml}</ul>
                    <div class="item-meta">
                        Por: ${[...grupo.nicks].join(', ')} — Último pedido a las ${grupo.ultimaFecha.toLocaleTimeString()}
                    </div>
                </div>
                <div class="item-actions">
                    <button class="btn-despachado" data-ids="${allConsumoIds}" title="Marcar todo como despachado">Despachado</button>
                    <button class="btn-no-despachado" data-ids="${allConsumoIds}" title="Cancelar todo el pedido">No Despachado</button>
                </div>
            `;
            listEl.appendChild(li);
        });

    } catch (error) {
        listEl.innerHTML = `<li><p style="color: var(--error-color);">Error cargando pedidos: ${error.message}</p></li>`;
    }
}



async function handleBroadcast() {
    const message = document.getElementById('broadcast-message-input').value.trim();
    if (!message) {
        showNotification('El mensaje no puede estar vacío.', 'error');
        return;
    }
    try {
        await apiFetch('/admin/broadcast-message', { method: 'POST', body: JSON.stringify({ mensaje: message }) });
        showNotification('Mensaje enviado a todos los usuarios.', 'success');
        document.getElementById('broadcast-message-input').value = '';
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleResetNight() {
    if (!confirm('¡ACCIÓN DESTRUCTIVA!\n\n¿Estás seguro de que quieres reiniciar la noche? Se borrarán TODAS las mesas, usuarios, canciones y consumos.')) return;
    try {
        await apiFetch('/admin/reset-night', { method: 'POST' });
        showNotification('El sistema ha sido reiniciado para una nueva noche.', 'info');
        loadDashboardPage();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleSendReaction(event) {
    const emojiSpan = event.target.closest('#reaction-buttons span');
    if (!emojiSpan) return;

    const reaction = emojiSpan.textContent;
    const payload = {
        reaction: reaction,
        sender: "Admin"
    };
    try {
        await fetch(`${API_BASE_URL}/broadcast/reaction`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    } catch (error) {
        console.error("Error enviando reacción:", error);
    }
}

// Setup event listeners for dashboard
function setupDashboardListeners() {
    const broadcastBtn = document.getElementById('broadcast-btn');
    const resetBtn = document.getElementById('reset-night-btn');
    const reactionBtns = document.getElementById('reaction-buttons');
    const recentOrdersList = document.getElementById('recent-orders-list');
    const autoplayToggle = document.getElementById('autoplay-toggle-queue');

    if (broadcastBtn) broadcastBtn.addEventListener('click', handleBroadcast);
    if (resetBtn) resetBtn.addEventListener('click', handleResetNight);
    if (reactionBtns) reactionBtns.addEventListener('click', handleSendReaction);


    const openPlayerBtnMain = document.getElementById('open-player-dashboard-main');
    if (openPlayerBtnMain) {
        openPlayerBtnMain.addEventListener('click', () => {
            window.open('/player', '_blank');
        });
    }

    if (recentOrdersList) {
        recentOrdersList.addEventListener('click', async (e) => {
            const btnDespachado = e.target.closest('.btn-despachado');
            const btnNoDespachado = e.target.closest('.btn-no-despachado');

            let consumoIds;
            let endpoint;
            let confirmMessage;
            let successMessage;
            let isDeleteAction = false;

            if (btnDespachado) {
                consumoIds = (btnDespachado.dataset.id || btnDespachado.dataset.ids || '').split(',');
                endpoint = `/admin/consumos/{consumo_id}/mark-despachado`;
                confirmMessage = '¿Confirmas que este pedido ha sido despachado?';
                successMessage = 'Pedido marcado como despachado.';
                isDeleteAction = false;
            } else if (btnNoDespachado) {
                consumoIds = (btnNoDespachado.dataset.id || btnNoDespachado.dataset.ids || '').split(',');
                endpoint = `/admin/consumos/{consumo_id}`;
                confirmMessage = '¿Estás seguro de que quieres CANCELAR este pedido? Se eliminará del sistema.';
                successMessage = 'Pedido cancelado y eliminado del sistema.';
                isDeleteAction = true;
            } else {
                return;
            }

            if (!consumoIds || consumoIds.length === 0 || consumoIds[0] === '') return;
            if (!confirm(confirmMessage)) return;

            const li = btnDespachado ? btnDespachado.closest('li') : btnNoDespachado.closest('li');
            const bellIcon = li ? li.querySelector('.order-alert-icon') : null;
            if (bellIcon) bellIcon.classList.remove('shaking');

            try {
                for (const id of consumoIds) {
                    const finalEndpoint = endpoint.replace('{consumo_id}', id);
                    await apiFetch(finalEndpoint, { method: isDeleteAction ? 'DELETE' : 'POST' });
                }

                // Eliminar visualmente el elemento de la lista inmediatamente
                if (li) {
                    li.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
                    li.style.opacity = '0';
                    li.style.transform = 'translateX(-20px)';
                    setTimeout(() => {
                        li.remove();
                        // Si no quedan más pedidos, mostrar mensaje
                        if (recentOrdersList.children.length === 0) {
                            recentOrdersList.innerHTML = '<li><p>No hay pedidos recientes.</p></li>';
                        }
                    }, 300);
                }

                showNotification(successMessage, 'success');
                // Recargar después de un breve delay para actualizar el resumen
                setTimeout(() => loadDashboardPage(), 500);
            } catch (error) {
                console.error("Error procesando consumos:", error);
                showNotification("Error procesando consumos", "error");
            }
        });
    }
}
