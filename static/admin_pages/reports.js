// Reports Page Module
// Manejo: generación de reportes por periodo, ventas, ingresos

async function loadReportsPage() {
    const reportOutput = document.getElementById('report-output');
    if (reportOutput) {
        reportOutput.innerHTML = '<p>Selecciona un tipo de reporte y haz clic en "Generar Reporte" para ver los resultados.</p>';
    }
    setupReportsListeners();
}

function setupReportsListeners() {
    const generateBtn = document.getElementById('generate-report-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', handleReportGeneration);
    }
}

async function handleReportGeneration() {
    const selector = document.getElementById('report-selector');
    const reportOutput = document.getElementById('report-output');

    if (!selector || !reportOutput) return;

    const reportType = selector.value;
    if (!reportType) {
        reportOutput.innerHTML = '<p style="color: var(--warning-color);">Por favor selecciona un tipo de reporte.</p>';
        return;
    }

    reportOutput.innerHTML = '<p>Generando reporte...</p>';

    try {
        let endpoint = '';
        let dataProcessor = null;

        switch (reportType) {
            case 'top-songs':
                endpoint = '/admin/reports/top-songs';
                dataProcessor = processTopSongs;
                break;
            case 'top-products':
                endpoint = '/admin/reports/top-products';
                dataProcessor = processTopProducts;
                break;
            case 'total-income':
                endpoint = '/admin/reports/total-income';
                dataProcessor = processTotalIncome;
                break;
            case 'income-by-table':
                endpoint = '/admin/reports/income-by-table';
                dataProcessor = processIncomeByTable;
                break;
            case 'songs-by-table':
                endpoint = '/admin/reports/songs-by-table';
                dataProcessor = processSongsByTable;
                break;
            case 'songs-by-user':
                endpoint = '/admin/reports/songs-by-user';
                dataProcessor = processSongsByUser;
                break;
            case 'hourly-activity':
                endpoint = '/admin/reports/hourly-activity';
                dataProcessor = processHourlyActivity;
                break;
            case 'top-rejected-songs':
                endpoint = '/admin/reports/top-rejected-songs';
                dataProcessor = processTopRejectedSongs;
                break;
            case 'inactive-users':
                endpoint = '/admin/reports/inactive-users';
                dataProcessor = processInactiveUsers;
                break;
            default:
                reportOutput.innerHTML = '<p style="color: var(--error-color);">Tipo de reporte no implementado aún.</p>';
                return;
        }

        try {
            const report = await apiFetch(endpoint);
            const html = dataProcessor(report);
            reportOutput.innerHTML = html;

            // Add PDF Button
            const pdfBtn = document.createElement('button');
            pdfBtn.textContent = 'Descargar PDF Oficial';
            pdfBtn.className = 'form-btn';
            pdfBtn.style.marginTop = '20px';
            pdfBtn.style.maxWidth = '300px';
            pdfBtn.style.backgroundColor = 'var(--secondary-color)';
            pdfBtn.onclick = () => downloadPDF(reportType);

            const btnContainer = document.createElement('div');
            btnContainer.style.textAlign = 'center';
            btnContainer.appendChild(pdfBtn);

            reportOutput.appendChild(btnContainer);

        } catch (e) {
            console.error("Error fetching report:", e);
            reportOutput.innerHTML = `<p style="color: var(--error-color);">Error al obtener el reporte: ${e.message}</p>`;
        }

    } catch (error) {
        reportOutput.innerHTML = `<p style="color: var(--error-color);">${error.message}</p>`;
    }
}

// --- Processors ---

function processTopSongs(data) {
    if (!data || data.length === 0) return '<p>No hay datos de canciones cantadas.</p>';

    let html = `
        <div class="report-container">
            <h3>Top Canciones Más Cantadas</h3>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Título</th>
                        <th>Veces Cantada</th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach(item => {
        html += `
            <tr>
                <td>${item.titulo}</td>
                <td>${item.veces_cantada}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    return html;
}

function processTopProducts(data) {
    if (!data || data.length === 0) return '<p>No hay datos de productos vendidos.</p>';

    let html = `
        <div class="report-container">
            <h3>Top Productos Más Consumidos</h3>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Producto</th>
                        <th>Cantidad Total</th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach(item => {
        html += `
            <tr>
                <td>${item.nombre}</td>
                <td>${item.cantidad_total}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    return html;
}

function processTotalIncome(data) {
    if (!data) return '<p>No hay datos de ingresos.</p>';

    return `
        <div class="report-container">
            <h3>Ingresos Totales de la Noche</h3>
            <div class="report-summary">
                <div class="summary-card">
                    <span class="label">Total:</span>
                    <span class="value">$${(data.ingresos_totales || 0).toFixed(2)}</span>
                </div>
            </div>
        </div>
    `;
}

function processIncomeByTable(data) {
    if (!data || data.length === 0) return '<p>No hay datos de ingresos por mesa.</p>';

    let html = `
        <div class="report-container">
            <h3>Ingresos por Mesa</h3>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Mesa</th>
                        <th>Ingresos Totales</th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach(item => {
        html += `
            <tr>
                <td>${item.mesa_nombre}</td>
                <td>$${(item.ingresos_totales || 0).toFixed(2)}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    return html;
}

function processSongsByTable(data) {
    if (!data || data.length === 0) return '<p>No hay datos de canciones por mesa.</p>';

    let html = `
        <div class="report-container">
            <h3>Canciones por Mesa</h3>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Mesa</th>
                        <th>Canciones Cantadas</th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach(item => {
        html += `
            <tr>
                <td>${item.mesa_nombre}</td>
                <td>${item.canciones_cantadas}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    return html;
}

function processSongsByUser(data) {
    if (!data || data.length === 0) return '<p>No hay datos de canciones por usuario.</p>';

    let html = `
        <div class="report-container">
            <h3>Canciones por Usuario</h3>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Nick</th>
                        <th>Canciones Cantadas</th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach(item => {
        html += `
            <tr>
                <td>${item.nick}</td>
                <td>${item.canciones_cantadas}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    return html;
}

function processHourlyActivity(data) {
    if (!data || data.length === 0) return '<p>No hay datos de actividad por hora.</p>';

    let html = `
        <div class="report-container">
            <h3>Actividad por Hora</h3>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Hora</th>
                        <th>Canciones Cantadas</th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach(item => {
        html += `
            <tr>
                <td>${item.hora}:00</td>
                <td>${item.canciones_cantadas}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    return html;
}

function processTopRejectedSongs(data) {
    if (!data || data.length === 0) return '<p>No hay datos de canciones rechazadas.</p>';

    let html = `
        <div class="report-container">
            <h3>Canciones Más Rechazadas</h3>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Título</th>
                        <th>Veces Rechazada</th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach(item => {
        html += `
            <tr>
                <td>${item.titulo}</td>
                <td>${item.veces_rechazada}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    return html;
}

function processInactiveUsers(data) {
    if (!data || data.length === 0) return '<p>No hay usuarios inactivos.</p>';

    let html = `
        <div class="report-container">
            <h3>Usuarios Inactivos (Sin Consumo)</h3>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Nick</th>
                        <th>Mesa</th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach(item => {
        html += `
            <tr>
                <td>${item.nick}</td>
                <td>${item.mesa ? item.mesa.nombre : 'Sin mesa'}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    return html;
}


async function downloadPDF(reportType) {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/reports/export-pdf?report_type=${reportType}`, {
            headers: {
                'X-API-Key': apiKey
            }
        });

        if (!response.ok) {
            throw new Error('Error al generar el PDF');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `reporte_${reportType}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    } catch (error) {
        console.error('Error downloading PDF:', error);
        alert('Error al descargar el PDF: ' + error.message);
    }
}
