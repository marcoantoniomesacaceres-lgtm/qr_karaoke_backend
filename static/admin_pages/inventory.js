// Inventory Page Module - BEES Style
// Manejo: lista de productos, creación, activación/desactivación, eliminación

async function loadInventoryPage() {
    const inventoryContainer = document.getElementById('inventory');
    if (!inventoryContainer) return;

    try {
        inventoryContainer.innerHTML = '';

        // Encabezado
        const header = document.createElement('div');
        header.className = 'bees-header';
        header.innerHTML = `
            <div class="bees-header-icon">📦</div>
            <div class="bees-header-content">
                <h1>Inventario</h1>
                <p>Gestión de productos y stock</p>
            </div>
        `;
        inventoryContainer.appendChild(header);

        // Contenedor de dos columnas
        const mainContainer = document.createElement('div');
        mainContainer.style.display = 'grid';
        mainContainer.style.gridTemplateColumns = 'repeat(auto-fit, minmax(400px, 1fr))';
        mainContainer.style.gap = '24px';
        mainContainer.style.marginBottom = '30px';

        // Tarjeta de crear producto
        const createCard = document.createElement('div');
        createCard.className = 'bees-card';
        createCard.innerHTML = `
            <div class="bees-card-header">
                <div class="bees-card-icon">➕</div>
                <div class="bees-card-header-content">
                    <h3>Crear Producto</h3>
                    <p>Agrega nuevos artículos</p>
                </div>
            </div>
            <form id="create-product-form">
                <div class="bees-form-group">
                    <label for="product-name">Nombre del Producto</label>
                    <input type="text" id="product-name" name="nombre" placeholder="Ej: Cerveza" required>
                </div>
                <div class="bees-form-group">
                    <label for="product-category">Categoría</label>
                    <input type="text" id="product-category" name="categoria" placeholder="Ej: Bebidas">
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px;">
                    <div class="bees-form-group">
                        <label for="product-cost">Costo ($)</label>
                        <input type="number" id="product-cost" name="costo" placeholder="0.00" step="0.01" required>
                    </div>
                    <div class="bees-form-group">
                        <label for="product-price">Precio Venta ($)</label>
                        <input type="number" id="product-price" name="valor" placeholder="0.00" step="0.01" required>
                    </div>
                </div>
                <div class="bees-form-group">
                    <label for="product-stock">Stock Inicial</label>
                    <input type="number" id="product-stock" name="stock" placeholder="0" value="0" required>
                </div>
                <button type="submit" class="bees-btn bees-btn-primary">✅ Crear Producto</button>
            </form>
        `;
        mainContainer.appendChild(createCard);

        // Tarjeta de lista de productos
        const productsCard = document.createElement('div');
        productsCard.className = 'bees-card';

        const productsHeader = document.createElement('div');
        productsHeader.className = 'bees-card-header';
        productsHeader.innerHTML = `
            <div class="bees-card-icon">📋</div>
            <div class="bees-card-header-content">
                <h3>Productos</h3>
                <p>Activos e inactivos</p>
            </div>
        `;
        productsCard.appendChild(productsHeader);

        const productList = document.createElement('ul');
        productList.id = 'product-list';
        productList.style.listStyle = 'none';
        productList.style.padding = '0';
        productList.style.margin = '0';

        productsCard.appendChild(productList);
        mainContainer.appendChild(productsCard);

        inventoryContainer.appendChild(mainContainer);

        // Cargar productos
        const products = await apiFetch('/productos/');
        renderProducts(products, productList);

        // Setup listeners
        setupInventoryListeners();
    } catch (error) {
        const inventoryContainer = document.getElementById('inventory');
        if (inventoryContainer) {
            inventoryContainer.innerHTML = `
                <div class="bees-alert bees-alert-danger">
                    <span class="bees-alert-icon">❌</span>
                    <div>Error al cargar inventario: ${error.message}</div>
                </div>
            `;
        }
        showNotification(`Error: ${error.message}`, 'error');
    }
}

function renderProducts(products, productList) {
    productList.innerHTML = '';
    
    if (products.length === 0) {
        const emptyItem = document.createElement('li');
        emptyItem.innerHTML = `
            <div class="bees-alert bees-alert-info">
                <span class="bees-alert-icon">ℹ️</span>
                <div>No hay productos. ¡Crea el primero!</div>
            </div>
        `;
        productList.appendChild(emptyItem);
        return;
    }

    products.sort((a, b) => {
        if (a.is_active === b.is_active) {
            return a.nombre.localeCompare(b.nombre);
        }
        return a.is_active ? -1 : 1;
    });

    products.forEach(product => {
        const stockStatus = product.stock === 0 
            ? 'Sin stock' 
            : product.stock < 10 
                ? 'Stock bajo' 
                : 'En stock';

        const stockBadgeClass = product.stock === 0 
            ? 'bees-badge-danger' 
            : product.stock < 10 
                ? 'bees-badge-warning' 
                : 'bees-badge-success';

        const statusBadge = product.is_active 
            ? '<span class="bees-badge bees-badge-success">✓ Activo</span>'
            : '<span class="bees-badge bees-badge-danger">✗ Inactivo</span>';

        const toggleButtonClass = product.is_active ? 'btn-deactivate' : 'btn-activate';
        const toggleButtonText = product.is_active ? '❌ Desactivar' : '✅ Activar';

        const li = document.createElement('li');
        li.style.marginBottom = '16px';
        li.style.padding = '16px';
        li.style.background = 'var(--page-input-bg)';
        li.style.borderRadius = '12px';
        li.style.borderLeft = product.is_active ? '4px solid var(--bees-green)' : '4px solid var(--bees-red)';
        
        li.innerHTML = `
            <div style="margin-bottom: 12px;">
                <div style="font-weight: 600; color: var(--page-text); margin-bottom: 6px; font-size: 16px;">
                    ${product.nombre}
                </div>
                <div style="font-size: 13px; color: var(--page-text-secondary); margin-bottom: 8px;">
                    ${product.categoria}
                </div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px;">
                    <span class="bees-badge ${stockBadgeClass}">${product.stock} uds</span>
                    ${statusBadge}
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px;">
                    <div><span style="color: var(--page-text-secondary);">Costo:</span> <strong style="color: var(--page-text);">$${(product.costo || 0).toFixed(2)}</strong></div>
                    <div><span style="color: var(--page-text-secondary);">Venta:</span> <strong style="color: var(--bees-yellow);">$${product.valor.toFixed(2)}</strong></div>
                </div>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <button class="bees-btn bees-btn-success bees-btn-small upload-img-btn" data-id="${product.id}">🖼️ Imagen</button>
                <button class="bees-btn bees-btn-info bees-btn-small ${toggleButtonClass}" data-id="${product.id}">${toggleButtonText}</button>
                <button class="bees-btn bees-btn-danger bees-btn-small btn-delete" data-id="${product.id}">🗑️ Eliminar</button>
            </div>
        `;
        productList.appendChild(li);
    });
}

async function handleCreateProduct(event, form) {
    event.preventDefault();
    const formData = new FormData(form);
    const productData = Object.fromEntries(formData.entries());
    
    productData.costo = parseFloat(productData.costo);
    productData.valor = parseFloat(productData.valor);
    productData.stock = parseInt(productData.stock, 10);

    try {
        const result = await apiFetch('/productos/', {
            method: 'POST',
            body: JSON.stringify(productData)
        });
        showNotification(`✅ Producto '${result.nombre}' creado.`, 'success');
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
        showNotification(
            `${activate ? '✅ Activado' : '❌ Desactivado'}: '${result.nombre}'`,
            'success'
        );
        loadInventoryPage();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleDeleteProduct(event) {
    const button = event.target;
    if (!button.matches('.btn-delete')) return;
    const productId = button.dataset.id;

    if (!confirm('⚠️ ¿Eliminar este producto permanentemente? No se puede deshacer.')) return;

    try {
        await apiFetch(`/productos/${productId}`, { method: 'DELETE' });
        showNotification('🗑️ Producto eliminado.', 'info');
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

    showNotification('⬆️ Subiendo imagen...', 'info', 10000);

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

        showNotification('🖼️ Imagen actualizada.', 'success');
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

    if (createForm) {
        createForm.addEventListener('submit', (e) => handleCreateProduct(e, e.target));
    }

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

    if (fileInput) {
        fileInput.addEventListener('change', handleProductImageUpload);
    }
}
