// Reports Page Module
// Manejo: generación de reportes por periodo, ventas, ingresos con formato APA

// Configuración del Karaoke (puedes modificar estos valores)
const KARAOKE_CONFIG = {
    nombre: "Karaoke La Voz Dorada",
    direccion: "Calle Principal #123, Ciudad",
    telefono: "(555) 123-4567",
    email: "info@lavozDorada.com"
};

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

// Función para obtener la fecha actual en formato APA
function getCurrentDateAPA() {
    const now = new Date();
    const months = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
    const day = now.getDate();
    const month = months[now.getMonth()];
    const year = now.getFullYear();
    return `${day} de ${month} de ${year}`;
}

// Función para obtener fecha y hora actual
function getCurrentDateTime() {
    const now = new Date();
    return now.toLocaleString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Crear encabezado profesional con formato APA
function createReportHeader(reportTitle) {
    return `
        <div class="report-header" style="
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
            position: relative;
        ">
            <div style="text-align: center; margin-bottom: 15px;">
                <h1 style="
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin: 0 0 10px 0;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                ">${KARAOKE_CONFIG.nombre}</h1>
                <p style="
                    font-size: 12px;
                    color: #7f8c8d;
                    margin: 5px 0;
                ">${KARAOKE_CONFIG.direccion}</p>
                <p style="
                    font-size: 12px;
                    color: #7f8c8d;
                    margin: 5px 0;
                ">Tel: ${KARAOKE_CONFIG.telefono} | Email: ${KARAOKE_CONFIG.email}</p>
            </div>
            
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            ">
                <h2 style="
                    font-size: 20px;
                    font-weight: bold;
                    margin: 0;
                    text-align: center;
                ">${reportTitle}</h2>
            </div>
            
            <div style="
                display: flex;
                justify-content: space-between;
                font-size: 12px;
                color: #34495e;
                margin-top: 15px;
            ">
                <div>
                    <strong>Fecha de generación:</strong> ${getCurrentDateAPA()}
                </div>
                <div>
                    <strong>Hora:</strong> ${new Date().toLocaleTimeString('es-ES')}
                </div>
            </div>
        </div>
    `;
}

// Crear marca de agua
function createWatermark() {
    return `
        <div class="watermark" style="
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 120px;
            font-weight: bold;
            color: rgba(0, 0, 0, 0.03);
            pointer-events: none;
            z-index: 0;
            white-space: nowrap;
            user-select: none;
        ">${KARAOKE_CONFIG.nombre}</div>
    `;
}

// Crear pie de página con formato APA
function createReportFooter() {
    return `
        <div class="report-footer" style="
            border-top: 2px solid #ecf0f1;
            padding-top: 20px;
            margin-top: 40px;
            font-size: 11px;
            color: #7f8c8d;
            text-align: center;
        ">
            <p style="margin: 5px 0;">
                <em>Documento generado automáticamente por el Sistema de Gestión ${KARAOKE_CONFIG.nombre}</em>
            </p>
            <p style="margin: 5px 0;">
                Fecha y hora de generación: ${getCurrentDateTime()}
            </p>
            <p style="margin: 5px 0;">
                © ${new Date().getFullYear()} ${KARAOKE_CONFIG.nombre}. Todos los derechos reservados.
            </p>
        </div>
    `;
}

// Crear botones de acción
function createActionButtons(reportType, reportTitle) {
    return `
        <div class="action-buttons" style="
            display: flex;
            gap: 15px;
            justify-content: center;
            margin: 30px 0;
            flex-wrap: wrap;
        ">
            <button onclick="printReport()" class="btn-action btn-print" style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.15)'" 
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)'">
                🖨️ Imprimir Reporte
            </button>
            
            <button onclick="downloadPDFOfficial('${reportType}', '${reportTitle}')" class="btn-action btn-pdf" style="
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.15)'" 
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)'">
                📄 Descargar PDF
            </button>
            
            <button onclick="exportToExcel('${reportType}', '${reportTitle}')" class="btn-action btn-excel" style="
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.15)'" 
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)'">
                📊 Exportar a Excel
            </button>
        </div>
    `;
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
        let reportTitle = '';

        switch (reportType) {
            case 'top-songs':
                endpoint = '/admin/reports/top-songs';
                dataProcessor = processTopSongs;
                reportTitle = 'Top Canciones Más Cantadas';
                break;
            case 'top-products':
                endpoint = '/admin/reports/top-products';
                dataProcessor = processTopProducts;
                reportTitle = 'Top Productos Más Consumidos';
                break;
            case 'total-income':
                endpoint = '/admin/reports/total-income';
                dataProcessor = processTotalIncome;
                reportTitle = 'Ingresos Totales de la Noche';
                break;
            case 'income-by-table':
                endpoint = '/admin/reports/income-by-table';
                dataProcessor = processIncomeByTable;
                reportTitle = 'Ingresos por Mesa';
                break;
            case 'songs-by-table':
                endpoint = '/admin/reports/songs-by-table';
                dataProcessor = processSongsByTable;
                reportTitle = 'Canciones por Mesa';
                break;
            case 'songs-by-user':
                endpoint = '/admin/reports/songs-by-user';
                dataProcessor = processSongsByUser;
                reportTitle = 'Canciones por Usuario';
                break;
            case 'hourly-activity':
                endpoint = '/admin/reports/hourly-activity';
                dataProcessor = processHourlyActivity;
                reportTitle = 'Actividad por Hora';
                break;
            case 'top-rejected-songs':
                endpoint = '/admin/reports/top-rejected-songs';
                dataProcessor = processTopRejectedSongs;
                reportTitle = 'Canciones Más Rechazadas';
                break;
            case 'inactive-users':
                endpoint = '/admin/reports/inactive-users';
                dataProcessor = processInactiveUsers;
                reportTitle = 'Usuarios Inactivos (Sin Consumo)';
                break;
            default:
                reportOutput.innerHTML = '<p style="color: var(--error-color);">Tipo de reporte no implementado aún.</p>';
                return;
        }

        try {
            const report = await apiFetch(endpoint);

            // Crear el reporte completo con formato profesional
            const reportContainer = document.createElement('div');
            reportContainer.id = 'printable-report';
            reportContainer.className = 'professional-report';
            reportContainer.style.cssText = `
                position: relative;
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                max-width: 1200px;
                margin: 0 auto;
                font-family: 'Times New Roman', Times, serif;
            `;

            reportContainer.innerHTML = `
                ${createWatermark()}
                ${createReportHeader(reportTitle)}
                <div style="position: relative; z-index: 1;">
                    ${dataProcessor(report, reportTitle)}
                </div>
                ${createReportFooter()}
                ${createActionButtons(reportType, reportTitle)}
            `;

            reportOutput.innerHTML = '';
            reportOutput.appendChild(reportContainer);

        } catch (e) {
            console.error("Error fetching report:", e);
            reportOutput.innerHTML = `<p style="color: var(--error-color);">Error al obtener el reporte: ${e.message}</p>`;
        }

    } catch (error) {
        reportOutput.innerHTML = `<p style="color: var(--error-color);">${error.message}</p>`;
    }
}

// --- Processors con formato mejorado ---

function processTopSongs(data, reportTitle) {
    if (!data || data.length === 0) return '<p>No hay datos de canciones cantadas.</p>';

    let totalCanciones = data.reduce((sum, item) => sum + item.veces_cantada, 0);

    let html = `
        <div class="report-summary" style="
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        ">
            <h3 style="margin: 0 0 10px 0; color: #2c3e50;">Resumen Ejecutivo</h3>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Total de canciones únicas:</strong> ${data.length}
            </p>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Total de veces cantadas:</strong> ${totalCanciones}
            </p>
        </div>
        
        <table class="report-table" style="
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <thead>
                <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Posición</th>
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Título</th>
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Veces Cantada</th>
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Porcentaje</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.forEach((item, index) => {
        const porcentaje = ((item.veces_cantada / totalCanciones) * 100).toFixed(1);
        const rowColor = index % 2 === 0 ? '#f8f9fa' : 'white';
        html += `
            <tr style="background: ${rowColor};">
                <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">#${index + 1}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">${item.titulo}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: #667eea;">${item.veces_cantada}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">${porcentaje}%</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    return html;
}

function processTopProducts(data, reportTitle) {
    if (!data || data.length === 0) return '<p>No hay datos de productos vendidos.</p>';

    let totalProductos = data.reduce((sum, item) => sum + item.cantidad_total, 0);

    let html = `
        <div class="report-summary" style="
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        ">
            <h3 style="margin: 0 0 10px 0; color: #2c3e50;">Resumen Ejecutivo</h3>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Productos diferentes vendidos:</strong> ${data.length}
            </p>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Total de unidades vendidas:</strong> ${totalProductos}
            </p>
        </div>
        
        <table class="report-table" style="
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <thead>
                <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Posición</th>
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Producto</th>
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Cantidad Total</th>
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Porcentaje</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.forEach((item, index) => {
        const porcentaje = ((item.cantidad_total / totalProductos) * 100).toFixed(1);
        const rowColor = index % 2 === 0 ? '#f8f9fa' : 'white';
        html += `
            <tr style="background: ${rowColor};">
                <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">#${index + 1}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">${item.nombre}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: #667eea;">${item.cantidad_total}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">${porcentaje}%</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    return html;
}

function processTotalIncome(data, reportTitle) {
    if (!data) return '<p>No hay datos de ingresos.</p>';

    return `
        <div class="report-summary" style="
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        ">
            <h3 style="margin: 0 0 20px 0; font-size: 24px;">Ingresos Totales</h3>
            <div style="
                font-size: 48px;
                font-weight: bold;
                margin: 20px 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            ">
                $${(data.ingresos_totales || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <p style="font-size: 14px; opacity: 0.9;">
                Generado en la noche del ${getCurrentDateAPA()}
            </p>
        </div>
    `;
}

function processIncomeByTable(data, reportTitle) {
    if (!data || data.length === 0) return '<p>No hay datos de ingresos por mesa.</p>';

    let totalIngresos = data.reduce((sum, item) => sum + parseFloat(item.ingresos_totales || 0), 0);

    let html = `
        <div class="report-summary" style="
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        ">
            <h3 style="margin: 0 0 10px 0; color: #2c3e50;">Resumen Ejecutivo</h3>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Total de mesas con consumo:</strong> ${data.length}
            </p>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Ingresos totales:</strong> $${totalIngresos.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Promedio por mesa:</strong> $${(totalIngresos / data.length).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
        </div>
        
        <table class="report-table" style="
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <thead>
                <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Posición</th>
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Mesa</th>
                    <th style="padding: 15px; text-align: right; border: 1px solid #ddd;">Ingresos Totales</th>
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Porcentaje</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.forEach((item, index) => {
        const porcentaje = ((parseFloat(item.ingresos_totales || 0) / totalIngresos) * 100).toFixed(1);
        const rowColor = index % 2 === 0 ? '#f8f9fa' : 'white';
        html += `
            <tr style="background: ${rowColor};">
                <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">#${index + 1}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">${item.mesa_nombre}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #11998e;">$${parseFloat(item.ingresos_totales || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">${porcentaje}%</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    return html;
}

function processSongsByTable(data, reportTitle) {
    if (!data || data.length === 0) return '<p>No hay datos de canciones por mesa.</p>';

    let totalCanciones = data.reduce((sum, item) => sum + item.canciones_cantadas, 0);

    let html = `
        <div class="report-summary" style="
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        ">
            <h3 style="margin: 0 0 10px 0; color: #2c3e50;">Resumen Ejecutivo</h3>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Total de mesas activas:</strong> ${data.length}
            </p>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Total de canciones cantadas:</strong> ${totalCanciones}
            </p>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Promedio por mesa:</strong> ${(totalCanciones / data.length).toFixed(1)}
            </p>
        </div>
        
        <table class="report-table" style="
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <thead>
                <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Posición</th>
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Mesa</th>
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Canciones Cantadas</th>
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Porcentaje</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.forEach((item, index) => {
        const porcentaje = ((item.canciones_cantadas / totalCanciones) * 100).toFixed(1);
        const rowColor = index % 2 === 0 ? '#f8f9fa' : 'white';
        html += `
            <tr style="background: ${rowColor};">
                <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">#${index + 1}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">${item.mesa_nombre}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: #667eea;">${item.canciones_cantadas}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">${porcentaje}%</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    return html;
}

function processSongsByUser(data, reportTitle) {
    if (!data || data.length === 0) return '<p>No hay datos de canciones por usuario.</p>';

    let totalCanciones = data.reduce((sum, item) => sum + item.canciones_cantadas, 0);

    let html = `
        <div class="report-summary" style="
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        ">
            <h3 style="margin: 0 0 10px 0; color: #2c3e50;">Resumen Ejecutivo</h3>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Total de usuarios activos:</strong> ${data.length}
            </p>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Total de canciones cantadas:</strong> ${totalCanciones}
            </p>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Promedio por usuario:</strong> ${(totalCanciones / data.length).toFixed(1)}
            </p>
        </div>
        
        <table class="report-table" style="
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <thead>
                <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Posición</th>
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Nick</th>
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Canciones Cantadas</th>
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Porcentaje</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.forEach((item, index) => {
        const porcentaje = ((item.canciones_cantadas / totalCanciones) * 100).toFixed(1);
        const rowColor = index % 2 === 0 ? '#f8f9fa' : 'white';
        html += `
            <tr style="background: ${rowColor};">
                <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">#${index + 1}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">${item.nick}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: #667eea;">${item.canciones_cantadas}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">${porcentaje}%</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    return html;
}

function processHourlyActivity(data, reportTitle) {
    if (!data || data.length === 0) return '<p>No hay datos de actividad por hora.</p>';

    let totalCanciones = data.reduce((sum, item) => sum + item.canciones_cantadas, 0);
    let horaMax = data.reduce((max, item) => item.canciones_cantadas > max.canciones_cantadas ? item : max, data[0]);

    let html = `
        <div class="report-summary" style="
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        ">
            <h3 style="margin: 0 0 10px 0; color: #2c3e50;">Resumen Ejecutivo</h3>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Total de canciones cantadas:</strong> ${totalCanciones}
            </p>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Hora pico:</strong> ${horaMax.hora}:00 con ${horaMax.canciones_cantadas} canciones
            </p>
        </div>
        
        <table class="report-table" style="
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <thead>
                <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Hora</th>
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Canciones Cantadas</th>
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Porcentaje</th>
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Gráfico</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.forEach((item, index) => {
        const porcentaje = ((item.canciones_cantadas / totalCanciones) * 100).toFixed(1);
        const barWidth = porcentaje;
        const rowColor = index % 2 === 0 ? '#f8f9fa' : 'white';
        html += `
            <tr style="background: ${rowColor};">
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold;">${item.hora}:00</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: #667eea;">${item.canciones_cantadas}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">${porcentaje}%</td>
                <td style="padding: 12px; border: 1px solid #ddd;">
                    <div style="background: linear-gradient(90deg, #667eea, #764ba2); width: ${barWidth}%; height: 20px; border-radius: 4px;"></div>
                </td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    return html;
}

function processTopRejectedSongs(data, reportTitle) {
    if (!data || data.length === 0) return '<p>No hay datos de canciones rechazadas.</p>';

    let totalRechazadas = data.reduce((sum, item) => sum + item.veces_rechazada, 0);

    let html = `
        <div class="report-summary" style="
            background: linear-gradient(135deg, #ff6b6b15 0%, #ee5a6f15 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        ">
            <h3 style="margin: 0 0 10px 0; color: #2c3e50;">Resumen Ejecutivo</h3>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Canciones únicas rechazadas:</strong> ${data.length}
            </p>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Total de rechazos:</strong> ${totalRechazadas}
            </p>
        </div>
        
        <table class="report-table" style="
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <thead>
                <tr style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); color: white;">
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Posición</th>
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Título</th>
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Veces Rechazada</th>
                    <th style="padding: 15px; text-align: center; border: 1px solid #ddd;">Porcentaje</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.forEach((item, index) => {
        const porcentaje = ((item.veces_rechazada / totalRechazadas) * 100).toFixed(1);
        const rowColor = index % 2 === 0 ? '#fff5f5' : 'white';
        html += `
            <tr style="background: ${rowColor};">
                <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">#${index + 1}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">${item.titulo}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: #ff6b6b;">${item.veces_rechazada}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">${porcentaje}%</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    return html;
}

function processInactiveUsers(data, reportTitle) {
    if (!data || data.length === 0) return '<p>No hay usuarios inactivos.</p>';

    let html = `
        <div class="report-summary" style="
            background: linear-gradient(135deg, #feca5715 0%, #ffd86f15 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        ">
            <h3 style="margin: 0 0 10px 0; color: #2c3e50;">Resumen Ejecutivo</h3>
            <p style="margin: 5px 0; font-size: 14px;">
                <strong>Total de usuarios inactivos:</strong> ${data.length}
            </p>
            <p style="margin: 5px 0; font-size: 14px; color: #f39c12;">
                <em>Usuarios que no han realizado ningún consumo durante la noche</em>
            </p>
        </div>
        
        <table class="report-table" style="
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <thead>
                <tr style="background: linear-gradient(135deg, #feca57 0%, #ffd86f 100%); color: #2c3e50;">
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">N°</th>
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Nick</th>
                    <th style="padding: 15px; text-align: left; border: 1px solid #ddd;">Mesa</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.forEach((item, index) => {
        const rowColor = index % 2 === 0 ? '#fffbf0' : 'white';
        html += `
            <tr style="background: ${rowColor};">
                <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">${index + 1}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">${item.nick}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">${item.mesa ? item.mesa.nombre : 'Sin mesa'}</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    return html;
}

// Función para imprimir el reporte
function printReport() {
    const printContent = document.getElementById('printable-report');
    if (!printContent) {
        alert('No hay reporte para imprimir');
        return;
    }

    // Ocultar botones de acción antes de imprimir
    const actionButtons = printContent.querySelector('.action-buttons');
    if (actionButtons) {
        actionButtons.style.display = 'none';
    }

    // Crear ventana de impresión
    const printWindow = window.open('', '', 'height=800,width=1000');
    printWindow.document.write('<html><head><title>Reporte - ' + KARAOKE_CONFIG.nombre + '</title>');
    printWindow.document.write('<style>');
    printWindow.document.write(`
        @media print {
            body { margin: 0; padding: 20px; font-family: 'Times New Roman', Times, serif; }
            .watermark { opacity: 0.05 !important; }
            .no-print { display: none !important; }
            table { page-break-inside: avoid; }
            tr { page-break-inside: avoid; }
        }
        body { font-family: 'Times New Roman', Times, serif; }
    `);
    printWindow.document.write('</style></head><body>');
    printWindow.document.write(printContent.innerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();

    setTimeout(() => {
        printWindow.print();
        printWindow.close();

        // Restaurar botones
        if (actionButtons) {
            actionButtons.style.display = 'flex';
        }
    }, 250);
}

// Función para descargar PDF (requiere backend)
async function downloadPDFOfficial(reportType, reportTitle) {
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
        a.download = `${reportTitle.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    } catch (error) {
        console.error('Error downloading PDF:', error);
        alert('La función de descarga PDF requiere configuración en el backend. Por ahora, usa la opción de Imprimir.');
    }
}

// Función para exportar a Excel (CSV)
function exportToExcel(reportType, reportTitle) {
    const table = document.querySelector('.report-table');
    if (!table) {
        alert('No hay tabla para exportar');
        return;
    }

    let csv = [];
    const rows = table.querySelectorAll('tr');

    for (let row of rows) {
        let cols = row.querySelectorAll('td, th');
        let csvRow = [];
        for (let col of cols) {
            csvRow.push('"' + col.innerText.replace(/"/g, '""') + '"');
        }
        csv.push(csvRow.join(','));
    }

    const csvContent = '\uFEFF' + csv.join('\n'); // UTF-8 BOM
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${reportTitle.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
}
