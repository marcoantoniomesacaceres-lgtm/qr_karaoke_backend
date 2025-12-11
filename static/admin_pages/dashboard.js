// Dashboard Page Module - BEES Style
// Manejo: resumen, últimos pedidos, acciones rápidas, reacciones

async function loadDashboardPage() {
    try {
        const dashboardContainer = document.getElementById('dashboard');
        if (!dashboardContainer) return;

        // Limpiar contenedor
        dashboardContainer.innerHTML = '';

        // Obtener datos
        const summary = await apiFetch('/admin/summary');
        const ingresos = Number(summary.ingresos_totales) || 0;
        const ganancias = Number(summary.ganancias_totales) || 0;
        const canciones = Number(summary.canciones_cantadas) || 0;
        const usuarios = Number(summary.usuarios_activos) || 0;

        // Aplicar tema si existe
        if (summary.theme) {
            document.body.dataset.theme = summary.theme;
        }

        // Crear encabezado
        const header = document.createElement('div');
        header.className = 'bees-header';
        header.innerHTML = `
            <div class="bees-header-icon">📊</div>
            <div class="bees-header-content">
                <h1>Dashboard</h1>
                <p>Resumen de actividad en tiempo real</p>
            </div>
        `;
        dashboardContainer.appendChild(header);

        // Tarjetas de métricas
        const metricsContainer = document.createElement('div');
        metricsContainer.className = 'bees-container-4col';
        metricsContainer.innerHTML = `
            <div class="metric-card">
                <div class="metric-card-icon">💰</div>
                <div class="metric-card-label">Ingresos Totales</div>
                <div class="metric-card-value">$${ingresos.toFixed(2)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-card-icon">📈</div>
                <div class="metric-card-label">Ganancias</div>
                <div class="metric-card-value" style="color: var(--bees-green);">$${ganancias.toFixed(2)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-card-icon">🎵</div>
                <div class="metric-card-label">Canciones</div>
                <div class="metric-card-value">${canciones}</div>
            </div>
            <div class="metric-card">
                <div class="metric-card-icon">👥</div>
                <div class="metric-card-label">Usuarios Activos</div>
                <div class="metric-card-value">${usuarios}</div>
            </div>
        `;
        dashboardContainer.appendChild(metricsContainer);

        // Cargar últimos pedidos
        await loadRecentOrders(dashboardContainer);

        // Acciones rápidas
        renderQuickActions(dashboardContainer);

        // Reacciones
        renderReactions(dashboardContainer);

        // Player
        renderPlayerSection(dashboardContainer);

        // Setup listeners
        setupDashboardListeners();
    } catch (error) {
        const dashboardContainer = document.getElementById('dashboard');
        if (dashboardContainer) {
            dashboardContainer.innerHTML = `
                <div class="bees-alert bees-alert-danger">
                    <span class="bees-alert-icon">❌</span>
                    <div>Error al cargar dashboard: ${error.message}</div>
                </div>
            `;
        }
        showNotification(`Error al cargar resumen: ${error.message}`, 'error');
    }
}

async function loadRecentOrders(dashboardContainer) {
    try {
        const pedidos = await apiFetch('/admin/recent-consumos?limit=25');
        
        // Crear tarjeta de pedidos
        const ordersCard = document.createElement('div');
        ordersCard.className = 'bees-card';
        ordersCard.style.marginTop = '30px';

        const ordersHeader = document.createElement('div');
        ordersHeader.className = 'bees-card-header';
        ordersHeader.innerHTML = `
            <div class="bees-card-icon">📦</div>
            <div class="bees-card-header-content">
                <h3>Últimos Pedidos</h3>
                <p>Pedidos pendientes por despachar</p>
            </div>
        `;
        ordersCard.appendChild(ordersHeader);

        const listEl = document.createElement('ul');
        listEl.id = 'recent-orders-list';
        listEl.style.listStyle = 'none';
        listEl.style.padding = '0';
        listEl.style.margin = '0';

        if (!pedidos || pedidos.length === 0) {
            const emptyItem = document.createElement('li');
            emptyItem.innerHTML = `
                <div class="bees-alert bees-alert-info">
                    <span class="bees-alert-icon">ℹ️</span>
                    <div>No hay pedidos recientes</div>
                </div>
            `;
            listEl.appendChild(emptyItem);
        } else {
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

            Object.keys(pedidosPorMesa)
                .sort((a, b) => pedidosPorMesa[b].ultimaFecha - pedidosPorMesa[a].ultimaFecha)
                .forEach(mesaNombre => {
                    const grupo = pedidosPorMesa[mesaNombre];
                    const li = document.createElement('li');
                    li.style.marginBottom = '16px';

                    const itemsHtml = grupo.items
                        .map(item => `<li style="margin-bottom: 4px;">
                            <span class="bees-badge bees-badge-info">${item.cantidad}x</span>
                            ${item.producto_nombre}
                        </li>`)
                        .join('');
                    const allConsumoIds = grupo.items.map(item => item.id).join(',');

                    li.innerHTML = `
                        <div style="background: var(--page-input-bg); border-radius: 12px; padding: 16px; border-left: 4px solid var(--bees-yellow);">
                            <div style="font-weight: 600; color: var(--page-text); margin-bottom: 8px;">
                                🔔 ${mesaNombre} pidió:
                            </div>
                            <ul style="list-style: none; padding-left: 0; margin: 8px 0 12px 0; color: var(--page-text-secondary);">
                                ${itemsHtml}
                            </ul>
                            <div style="font-size: 12px; color: var(--page-text-secondary); margin-bottom: 12px;">
                                Por: <strong>${[...grupo.nicks].join(', ')}</strong> — ${grupo.ultimaFecha.toLocaleTimeString()}
                            </div>
                            <div style="display: flex; gap: 8px;">
                                <button class="bees-btn bees-btn-success bees-btn-small btn-despachado" data-ids="${allConsumoIds}" title="Marcar todo como despachado">
                                    ✅ Despachado
                                </button>
                                <button class="bees-btn bees-btn-danger bees-btn-small btn-no-despachado" data-ids="${allConsumoIds}" title="Cancelar todo el pedido">
                                    ❌ Cancelar
                                </button>
                            </div>
                        </div>
                    `;
                    listEl.appendChild(li);
                });
        }

        ordersCard.appendChild(listEl);
        dashboardContainer.appendChild(ordersCard);
    } catch (error) {
        const errorCard = document.createElement('div');
        errorCard.className = 'bees-card';
        errorCard.style.marginTop = '30px';
        errorCard.innerHTML = `
            <div class="bees-alert bees-alert-danger">
                <span class="bees-alert-icon">❌</span>
                <div>Error cargando pedidos: ${error.message}</div>
            </div>
        `;
        dashboardContainer.appendChild(errorCard);
    }
}



function renderQuickActions(dashboardContainer) {
    const card = document.createElement('div');
    card.className = 'bees-card';
    card.style.marginTop = '30px';

    const header = document.createElement('div');
    header.className = 'bees-card-header';
    header.innerHTML = `
        <div class="bees-card-icon">⚡</div>
        <div class="bees-card-header-content">
            <h3>Acciones Rápidas</h3>
            <p>Control del sistema en tiempo real</p>
        </div>
    `;
    card.appendChild(header);

    const container = document.createElement('div');
    container.style.display = 'grid';
    container.style.gridTemplateColumns = 'repeat(auto-fit, minmax(250px, 1fr))';
    container.style.gap = '16px';

    // Mensaje global
    const broadcastSection = document.createElement('div');
    broadcastSection.style.background = 'var(--page-input-bg)';
    broadcastSection.style.padding = '16px';
    broadcastSection.style.borderRadius = '12px';
    broadcastSection.innerHTML = `
        <label class="bees-form-group">
            <label style="font-weight: 600; margin-bottom: 8px; display: block;">Enviar Mensaje Global</label>
            <input type="text" id="broadcast-message-input" placeholder="Ej: ¡Oferta en cervezas!" style="border: 2px solid var(--page-border); border-radius: 8px; padding: 12px; width: 100%; background: var(--page-card-bg); color: var(--page-text); box-sizing: border-box;">
            <button class="bees-btn bees-btn-info bees-btn-small" id="broadcast-btn" style="margin-top: 8px;">📢 Enviar</button>
        </label>
    `;
    container.appendChild(broadcastSection);

    card.appendChild(container);
    dashboardContainer.appendChild(card);
}

function renderReactions(dashboardContainer) {
    const card = document.createElement('div');
    card.className = 'bees-card';
    card.style.marginTop = '30px';

    const header = document.createElement('div');
    header.className = 'bees-card-header';
    header.innerHTML = `
        <div class="bees-card-icon">😊</div>
        <div class="bees-card-header-content">
            <h3>Enviar Reacción</h3>
            <p>Comparte emociones con todos en tiempo real</p>
        </div>
    `;
    card.appendChild(header);

    const buttonsContainer = document.createElement('div');
    buttonsContainer.id = 'reaction-buttons';
    buttonsContainer.style.display = 'flex';
    buttonsContainer.style.gap = '12px';
    buttonsContainer.style.flexWrap = 'wrap';
    buttonsContainer.style.justifyContent = 'center';

    const reactions = [
        { emoji: '😊', title: '¡Genial!' },
        { emoji: '👍', title: '¡Me gusta!' },
        { emoji: '🔥', title: '¡Fuego!' },
        { emoji: '🤩', title: '¡Increíble!' },
        { emoji: '🎤', title: '¡Buena voz!' },
        { emoji: '🍻', title: '¡Salud!' }
    ];

    reactions.forEach(reaction => {
        const btn = document.createElement('button');
        btn.className = 'bees-btn bees-btn-secondary bees-btn-small';
        btn.textContent = reaction.emoji;
        btn.title = reaction.title;
        btn.style.fontSize = '20px';
        btn.style.width = 'auto';
        btn.style.padding = '12px 16px';
        buttonsContainer.appendChild(btn);
    });

    card.appendChild(buttonsContainer);
    dashboardContainer.appendChild(card);
}

function renderPlayerSection(dashboardContainer) {
    const card = document.createElement('div');
    card.className = 'bees-card';
    card.style.marginTop = '30px';

    const header = document.createElement('div');
    header.className = 'bees-card-header';
    header.innerHTML = `
        <div class="bees-card-icon">🎤</div>
        <div class="bees-card-header-content">
            <h3>Player</h3>
            <p>Gestión del karaoke</p>
        </div>
    `;
    card.appendChild(header);

    const btn = document.createElement('button');
    btn.id = 'open-player-dashboard-main';
    btn.className = 'bees-btn bees-btn-primary';
    btn.innerHTML = '🎤 Abrir Dashboard Player';
    card.appendChild(btn);
    dashboardContainer.appendChild(card);
}

// Setup event listeners for dashboard
function setupDashboardListeners() {
    // Mensaje broadcast
    const broadcastBtn = document.getElementById('broadcast-btn');
    if (broadcastBtn) {
        broadcastBtn.addEventListener('click', handleBroadcast);
    }

    // Reacciones
    const reactionBtns = document.getElementById('reaction-buttons');
    if (reactionBtns) {
        reactionBtns.addEventListener('click', handleSendReaction);
    }

    // Player
    const openPlayerBtn = document.getElementById('open-player-dashboard-main');
    if (openPlayerBtn) {
        openPlayerBtn.addEventListener('click', () => {
            window.open('/player', '_blank');
        });
    }

    // Pedidos
    const recentOrdersList = document.getElementById('recent-orders-list');
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
                consumoIds = (btnDespachado.dataset.ids || '').split(',').filter(id => id);
                endpoint = `/admin/consumos/{consumo_id}/mark-despachado`;
                confirmMessage = '¿Confirmas que este pedido ha sido despachado?';
                successMessage = 'Pedido marcado como despachado.';
                isDeleteAction = false;
            } else if (btnNoDespachado) {
                consumoIds = (btnNoDespachado.dataset.ids || '').split(',').filter(id => id);
                endpoint = `/admin/consumos/{consumo_id}`;
                confirmMessage = '¿Estás seguro de que quieres CANCELAR este pedido?';
                successMessage = 'Pedido cancelado.';
                isDeleteAction = true;
            } else {
                return;
            }

            if (!consumoIds || consumoIds.length === 0) return;
            if (!confirm(confirmMessage)) return;

            try {
                for (const id of consumoIds) {
                    const finalEndpoint = endpoint.replace('{consumo_id}', id);
                    await apiFetch(finalEndpoint, { method: isDeleteAction ? 'DELETE' : 'POST' });
                }

                showNotification(successMessage, 'success');
                setTimeout(() => loadDashboardPage(), 300);
            } catch (error) {
                console.error("Error procesando consumos:", error);
                showNotification("Error procesando consumos", "error");
            }
        });
    }
}

async function handleBroadcast() {
    const input = document.getElementById('broadcast-message-input');
    const message = input ? input.value.trim() : '';
    
    if (!message) {
        showNotification('El mensaje no puede estar vacío.', 'error');
        return;
    }
    
    try {
        await apiFetch('/admin/broadcast-message', {
            method: 'POST',
            body: JSON.stringify({ mensaje: message })
        });
        showNotification('Mensaje enviado a todos.', 'success');
        if (input) input.value = '';
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleResetNight() {
    if (!confirm('⚠️ ACCIÓN DESTRUCTIVA\n\n¿Estás seguro de reiniciar la noche?\nSe borrarán: mesas, usuarios, canciones y consumos.')) {
        return;
    }
    
    try {
        await apiFetch('/admin/reset-night', { method: 'POST' });
        showNotification('Sistema reiniciado.', 'info');
        setTimeout(() => loadDashboardPage(), 300);
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleSendReaction(event) {
    const btn = event.target.closest('#reaction-buttons button');
    if (!btn) return;

    const reaction = btn.textContent.trim();
    
    try {
        await fetch(`${API_BASE_URL}/broadcast/reaction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                reaction: reaction,
                sender: "Admin"
            })
        });
        showNotification(`Reacción enviada: ${reaction}`, 'success');
    } catch (error) {
        console.error("Error enviando reacción:", error);
        showNotification('Error enviando reacción', 'error');
    }
}

