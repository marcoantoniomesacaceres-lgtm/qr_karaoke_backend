// Inventory Page Module
// Manejo: lista de productos, creación, activación/desactivación, eliminación

function renderProducts(products, productList) {
    productList.innerHTML = '';
    if (products.length === 0) {
        productList.innerHTML = '<p>No hay productos en el inventario. ¡Crea el primero!</p>';
        return;
    }

    products.sort((a, b) => {
        if (a.is_active === b.is_active) {
            return a.nombre.localeCompare(b.nombre);
        }
        return a.is_active ? -1 : 1;
    });

    products.forEach(product => {
        const stockClass = product.stock === 0 ? 'stock-out' : (product.stock < 10 ? 'stock-low' : '');
        const itemClass = product.is_active ? '' : 'inactive';
        const statusBadge = product.is_active 
            ? '<span class="status-badge status-active">Activo</span>'
            : '<span class="status-badge status-inactive">Inactivo</span>';

        const actionButton = product.is_active
            ? `<button class="btn-deactivate" data-id="${product.id}">Desactivar</button>`
            : `<button class="btn-activate" data-id="${product.id}">Activar</button>`;

        const li = document.createElement('li');
        li.className = `item ${itemClass}`;
        li.innerHTML = `
            <div class="item-details">
                <div class="item-title">${product.nombre}</div>
                <div class="item-meta">
                    ${product.categoria} &bull; Compra: $${product.costo || 'N/A'} &bull; Venta: $${product.valor} &bull; Stock: <span class="item-stock ${stockClass}">${product.stock}</span>
                </div>
            </div>
            <div class="item-status">
                ${statusBadge}
            </div>
            <div class="item-actions">
                <button class="btn-delete" data-id="${product.id}">Eliminar</button>
                ${actionButton}
                <button class="btn-action upload-img-btn" data-id="${product.id}">Imagen</button>
            </div>
        `;
        productList.appendChild(li);
    });
}

async function loadInventoryPage() {
    const productList = document.getElementById('product-list');
    try {
        const products = await apiFetch('/productos/');
        renderProducts(products, productList);
    } catch (error) {
        productList.innerHTML = `<p style="color: var(--error-color);">${error.message}</p>`;
    }
}

async function handleCreateProduct(event, form) {
    event.preventDefault();
    const formData = new FormData(form);
    const productData = Object.fromEntries(formData.entries());
    
    productData.costo = parseFloat(productData.costo);
    productData.valor = parseFloat(productData.valor);
    productData.stock = parseInt(productData.stock, 10);

    try {
        const result = await apiFetch('/productos/', { method: 'POST', body: JSON.stringify(productData) });
        showNotification(`Producto '${result.nombre}' creado con éxito.`);
        form.reset();
        loadInventoryPage();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleToggleProductActive(event) {
    const button = event.target;
    if (!button.matches('.btn-activate, .btn-deactivate')) return;

    const productId = button.dataset.id;
    const activate = button.classList.contains('btn-activate');
    const endpoint = `/productos/${productId}/${activate ? 'activate' : 'deactivate'}`;

    try {
        const result = await apiFetch(endpoint, { method: 'POST' });
        showNotification(`Producto '${result.nombre}' ${activate ? 'activado' : 'desactivado'}.`);
        loadInventoryPage();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleDeleteProduct(event) {
    const button = event.target;
    if (!button.matches('.btn-delete')) return;
    const productId = button.dataset.id;

    if (!confirm('¿Estás seguro de que quieres ELIMINAR este producto permanentemente? Esta acción no se puede deshacer.')) return;

    try {
        await apiFetch(`/productos/${productId}`, { method: 'DELETE' });
        showNotification('Producto eliminado con éxito.', 'info');
        loadInventoryPage();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleProductImageUpload(event) {
    const fileInput = event.target;
    const productId = fileInput.dataset.productId;
    if (!fileInput.files || fileInput.files.length === 0 || !productId) {
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    showNotification('Subiendo imagen...', 'info', 10000);

    try {
        const response = await fetch(`${API_BASE_URL}/productos/${productId}/upload-image`, {
            method: 'POST',
            headers: { 'X-API-Key': apiKey },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al subir la imagen.');
        }

        showNotification('Imagen actualizada con éxito.', 'success');
        loadInventoryPage();

    } catch (error) {
        showNotification(error.message, 'error');
    } finally {
        fileInput.value = '';
    }
}

function setupInventoryListeners() {
    const createForm = document.getElementById('create-product-form');
    const productList = document.getElementById('product-list');
    const fileInput = document.getElementById('product-image-upload');

    if (createForm) createForm.addEventListener('submit', (e) => handleCreateProduct(e, e.target));
    if (productList) {
        productList.addEventListener('click', handleToggleProductActive);
        productList.addEventListener('click', handleDeleteProduct);
        productList.addEventListener('click', (e) => {
            if (e.target.classList.contains('upload-img-btn')) {
                const productId = e.target.dataset.id;
                if (fileInput) {
                    fileInput.dataset.productId = productId;
                    fileInput.click();
                }
            }
        });
    }
    if (fileInput) fileInput.addEventListener('change', handleProductImageUpload);
}
