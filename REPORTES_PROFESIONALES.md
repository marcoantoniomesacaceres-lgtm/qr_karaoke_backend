# Sistema de Reportes Profesionales - Karaoke

## 📊 Características

El sistema de reportes ha sido completamente renovado con las siguientes características:

### ✨ Formato Profesional con Normas APA

- **Encabezado completo** con:
  - Nombre del establecimiento
  - Dirección y datos de contacto
  - Fecha de generación en formato APA (español)
  - Hora de generación

- **Marca de agua** con el nombre del karaoke en el fondo del documento

- **Pie de página** con:
  - Información de generación automática
  - Fecha y hora completa
  - Derechos reservados

### 📈 Reportes Mejorados

Cada reporte ahora incluye:

1. **Resumen Ejecutivo**: Estadísticas clave al inicio
2. **Tablas profesionales** con:
   - Numeración de posiciones
   - Porcentajes calculados automáticamente
   - Colores alternados para mejor lectura
   - Gradientes en encabezados
3. **Gráficos visuales** (en reportes de actividad por hora)

### 🎨 Presentación Visual

- Diseño moderno con gradientes
- Colores profesionales y consistentes
- Tipografía Times New Roman (estándar APA)
- Sombras y efectos sutiles
- Animaciones suaves

### 🖨️ Opciones de Exportación

Tres botones de acción disponibles:

1. **🖨️ Imprimir Reporte**: Impresión directa con formato optimizado
2. **📄 Descargar PDF**: Genera PDF oficial (requiere backend)
3. **📊 Exportar a Excel**: Descarga en formato CSV compatible con Excel

## ⚙️ Configuración

### Personalizar Información del Karaoke

Edita el archivo `/static/admin_pages/reports.js` en las líneas 6-11:

```javascript
const KARAOKE_CONFIG = {
    nombre: "Karaoke La Voz Dorada",      // ← Cambia aquí el nombre
    direccion: "Calle Principal #123, Ciudad",  // ← Cambia la dirección
    telefono: "(555) 123-4567",           // ← Cambia el teléfono
    email: "info@lavozDorada.com"         // ← Cambia el email
};
```

### Tipos de Reportes Disponibles

1. **Top Canciones Más Cantadas**
   - Ranking de canciones más populares
   - Número de veces cantada cada una
   - Porcentaje de participación

2. **Top Productos Más Consumidos**
   - Productos más vendidos
   - Cantidad total vendida
   - Porcentaje de ventas

3. **Ingresos Totales**
   - Vista consolidada de ingresos
   - Presentación destacada del monto total

4. **Ingresos por Mesa**
   - Desglose de ingresos por cada mesa
   - Promedio por mesa
   - Porcentaje de contribución

5. **Canciones por Mesa**
   - Actividad de karaoke por mesa
   - Promedio de canciones
   - Distribución porcentual

6. **Canciones por Usuario**
   - Usuarios más activos
   - Ranking de participación
   - Estadísticas individuales

7. **Actividad por Hora**
   - Distribución temporal de la actividad
   - Identificación de horas pico
   - Gráfico de barras visual

8. **Canciones Más Rechazadas**
   - Canciones que no fueron aprobadas
   - Frecuencia de rechazo
   - Análisis de tendencias

9. **Usuarios Inactivos**
   - Usuarios sin consumo
   - Identificación de mesas
   - Lista completa

## 🎯 Uso

1. **Seleccionar tipo de reporte** del menú desplegable
2. **Hacer clic en "Generar Reporte"**
3. **Revisar el reporte** en pantalla con toda la información consolidada
4. **Elegir acción**:
   - Imprimir directamente
   - Descargar como PDF
   - Exportar a Excel/CSV

## 📋 Formato de Impresión

Al imprimir, el sistema automáticamente:
- Oculta los botones de acción
- Optimiza márgenes para papel
- Mantiene colores en encabezados
- Asegura que las tablas no se corten entre páginas
- Reduce la opacidad de la marca de agua

## 🎨 Estilos CSS

Los estilos están en `/static/admin_pages/reports.css` e incluyen:

- Estilos para impresión (`@media print`)
- Diseño responsive para móviles
- Animaciones suaves
- Efectos hover en botones
- Tablas con estilo profesional

## 📱 Responsive

El sistema es completamente responsive:
- **Desktop**: Vista completa con todos los detalles
- **Tablet**: Ajuste automático de columnas
- **Móvil**: Botones apilados verticalmente, fuente reducida

## 🔧 Mantenimiento

### Agregar un Nuevo Tipo de Reporte

1. Agregar opción en `reports.html`:
```html
<option value="nuevo-reporte">Nombre del Nuevo Reporte</option>
```

2. Agregar caso en `reports.js` función `handleReportGeneration`:
```javascript
case 'nuevo-reporte':
    endpoint = '/admin/reports/nuevo-reporte';
    dataProcessor = processNuevoReporte;
    reportTitle = 'Título del Nuevo Reporte';
    break;
```

3. Crear función procesadora:
```javascript
function processNuevoReporte(data, reportTitle) {
    // Lógica para procesar y mostrar los datos
    return html;
}
```

## 📞 Soporte

Para cualquier duda o personalización adicional, contacta al equipo de desarrollo.

---

**Versión**: 2.0  
**Última actualización**: Diciembre 2025  
**Desarrollado para**: Sistema de Gestión de Karaoke
