// Reports Page Module
// Manejo: generación de reportes por periodo, ventas, ingresos

async function loadReportsPage() {
    const reportOutput = document.getElementById('report-output');
    if (reportOutput) {
        reportOutput.innerHTML = '<p>Selecciona un tipo de reporte para ver los resultados.</p>';
    }
}

async function handleReportGeneration(event) {
    const button = event.target;
    if (!button.matches('.generate-report-btn')) return;

    const reportType = button.dataset.reportType;
    const reportOutput = document.getElementById('report-output');
    if (!reportOutput) return;

    reportOutput.innerHTML = '<p>Generando reporte...</p>';

    try {
        let endpoint = '';
        let dataProcessor = null;
        let endpointPath = '';

        switch (reportType) {
            case 'daily':
                endpointPath = '/consumos/report/daily';
                dataProcessor = processDailyReport;
                break;
            case 'weekly':
                endpointPath = '/consumos/report/weekly';
                dataProcessor = processWeeklyReport;
                break;
            case 'monthly':
                endpointPath = '/consumos/report/monthly';
                dataProcessor = processMonthlyReport;
                break;
            case 'accounts-summary':
                endpointPath = '/consumos/report/accounts-summary';
                dataProcessor = processAccountsSummary;
                break;
            case 'top-products':
                endpointPath = '/consumos/report/top-products';
                dataProcessor = processTopProducts;
                break;
            default:
                reportOutput.innerHTML = '<p style="color: var(--error-color);">Tipo de reporte desconocido.</p>';
                return;
        }

        try {
            const report = await apiFetch(endpointPath);
            const html = dataProcessor(report);
            reportOutput.innerHTML = html;
        } catch (e) {
            // Report endpoints may not exist in backend; show graceful message
            if (e.message.includes('404')) {
                reportOutput.innerHTML = `<p style="color: var(--warning-color);">El reporte "${reportType}" no está disponible en el servidor backend.</p>`;
            } else {
                throw e;
            }
        }

    } catch (error) {
        reportOutput.innerHTML = `<p style="color: var(--error-color);">${error.message}</p>`;
    }
}

function processDailyReport(report) {
    if (!report || !report.data) return '<p>Sin datos.</p>';

    const { data, date } = report;
    const totalRevenue = data.reduce((sum, item) => sum + (item.total || 0), 0);
    const totalTransactions = data.length;

    let html = `
        <div class="report-container">
            <h3>Reporte Diario - ${date || 'Hoy'}</h3>
            <div class="report-summary">
                <div class="summary-card">
                    <span class="label">Ingresos Totales:</span>
                    <span class="value">$${totalRevenue.toFixed(2)}</span>
                </div>
                <div class="summary-card">
                    <span class="label">Transacciones:</span>
                    <span class="value">${totalTransactions}</span>
                </div>
            </div>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Mesa</th>
                        <th>Producto</th>
                        <th>Cantidad</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach(item => {
        html += `
            <tr>
                <td>Mesa ${item.mesa_numero || 'N/A'}</td>
                <td>${item.producto_nombre || 'N/A'}</td>
                <td>${item.cantidad || 0}</td>
                <td>$${(item.total || 0).toFixed(2)}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    return html;
}

function processWeeklyReport(report) {
    if (!report || !report.data) return '<p>Sin datos.</p>';

    const { data, week_start, week_end } = report;
    const totalRevenue = data.reduce((sum, item) => sum + (item.total || 0), 0);
    const avgDaily = totalRevenue / 7;

    let html = `
        <div class="report-container">
            <h3>Reporte Semanal - ${week_start} a ${week_end}</h3>
            <div class="report-summary">
                <div class="summary-card">
                    <span class="label">Ingresos Totales:</span>
                    <span class="value">$${totalRevenue.toFixed(2)}</span>
                </div>
                <div class="summary-card">
                    <span class="label">Promedio Diario:</span>
                    <span class="value">$${avgDaily.toFixed(2)}</span>
                </div>
                <div class="summary-card">
                    <span class="label">Transacciones:</span>
                    <span class="value">${data.length}</span>
                </div>
            </div>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Día</th>
                        <th>Producto</th>
                        <th>Cantidad</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach(item => {
        html += `
            <tr>
                <td>${item.fecha || 'N/A'}</td>
                <td>${item.producto_nombre || 'N/A'}</td>
                <td>${item.cantidad || 0}</td>
                <td>$${(item.total || 0).toFixed(2)}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    return html;
}

function processMonthlyReport(report) {
    if (!report || !report.data) return '<p>Sin datos.</p>';

    const { data, month, year } = report;
    const totalRevenue = data.reduce((sum, item) => sum + (item.total || 0), 0);
    const avgDaily = totalRevenue / 30;

    let html = `
        <div class="report-container">
            <h3>Reporte Mensual - ${month}/${year}</h3>
            <div class="report-summary">
                <div class="summary-card">
                    <span class="label">Ingresos Totales:</span>
                    <span class="value">$${totalRevenue.toFixed(2)}</span>
                </div>
                <div class="summary-card">
                    <span class="label">Promedio Diario:</span>
                    <span class="value">$${avgDaily.toFixed(2)}</span>
                </div>
                <div class="summary-card">
                    <span class="label">Transacciones:</span>
                    <span class="value">${data.length}</span>
                </div>
            </div>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Fecha</th>
                        <th>Producto</th>
                        <th>Cantidad</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach(item => {
        html += `
            <tr>
                <td>${item.fecha || 'N/A'}</td>
                <td>${item.producto_nombre || 'N/A'}</td>
                <td>${item.cantidad || 0}</td>
                <td>$${(item.total || 0).toFixed(2)}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    return html;
}

function processAccountsSummary(report) {
    if (!report || !report.accounts) return '<p>Sin datos.</p>';

    const { accounts, total_balance } = report;

    let html = `
        <div class="report-container">
            <h3>Resumen de Cuentas</h3>
            <div class="report-summary">
                <div class="summary-card">
                    <span class="label">Saldo Total:</span>
                    <span class="value">$${total_balance.toFixed(2)}</span>
                </div>
                <div class="summary-card">
                    <span class="label">Cuentas:</span>
                    <span class="value">${accounts.length}</span>
                </div>
            </div>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Usuario</th>
                        <th>Comisión</th>
                        <th>Saldo Actual</th>
                        <th>Pendiente</th>
                        <th>Pagado</th>
                    </tr>
                </thead>
                <tbody>
    `;

    accounts.forEach(account => {
        html += `
            <tr>
                <td>${account.usuario || 'N/A'}</td>
                <td>${account.comision_percentage || 0}%</td>
                <td>$${(account.saldo_actual || 0).toFixed(2)}</td>
                <td>$${(account.saldo_pendiente || 0).toFixed(2)}</td>
                <td>$${(account.saldo_pagado || 0).toFixed(2)}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    return html;
}

function processTopProducts(report) {
    if (!report || !report.products) return '<p>Sin datos.</p>';

    const { products } = report;
    const totalSold = products.reduce((sum, p) => sum + (p.cantidad || 0), 0);
    const totalRevenue = products.reduce((sum, p) => sum + (p.total || 0), 0);

    let html = `
        <div class="report-container">
            <h3>Productos Más Vendidos</h3>
            <div class="report-summary">
                <div class="summary-card">
                    <span class="label">Total Vendido:</span>
                    <span class="value">${totalSold} unidades</span>
                </div>
                <div class="summary-card">
                    <span class="label">Ingresos:</span>
                    <span class="value">$${totalRevenue.toFixed(2)}</span>
                </div>
            </div>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Producto</th>
                        <th>Cantidad</th>
                        <th>Precio Unitario</th>
                        <th>Total</th>
                        <th>% del Total</th>
                    </tr>
                </thead>
                <tbody>
    `;

    products.forEach(product => {
        const percentage = totalRevenue > 0 ? ((product.total / totalRevenue) * 100).toFixed(1) : 0;
        html += `
            <tr>
                <td>${product.nombre || 'N/A'}</td>
                <td>${product.cantidad || 0}</td>
                <td>$${(product.valor || 0).toFixed(2)}</td>
                <td>$${(product.total || 0).toFixed(2)}</td>
                <td>${percentage}%</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    return html;
}

function setupReportsListeners() {
    const reportButtons = document.querySelectorAll('.generate-report-btn');
    reportButtons.forEach(btn => {
        btn.addEventListener('click', handleReportGeneration);
    });
}
