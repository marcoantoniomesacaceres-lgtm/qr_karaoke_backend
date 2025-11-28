# Corrección de Códigos QR para Mesas

## Fecha
2025-11-28

## Problema Identificado
Los códigos QR generados en el panel de administración solo mostraban el código de la mesa (ejemplo: `karaoke-mesa-05`) en lugar de generar un QR con el link completo para acceder a la aplicación.

Cuando los usuarios escaneaban el QR, no eran redirigidos automáticamente a la aplicación del karaoke.

## Solución Implementada

### Archivo Modificado
- `static/admin_pages/tables.js`

### Cambios Realizados

**Función `handleShowQR` (líneas 53-86)**

**Antes:**
```javascript
// Generar URL del QR dinámicamente usando qrserver.com
const qrImageUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(qrCode)}`;
```

**Después:**
```javascript
// Construir la URL completa de la aplicación con el parámetro table
const appBaseUrl = window.location.origin; // Obtiene http://localhost:8000 o el dominio actual
const appUrl = `${appBaseUrl}/?table=${encodeURIComponent(qrCode)}`;

// Generar URL del QR dinámicamente usando qrserver.com con la URL completa de la app
const qrImageUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(appUrl)}`;
```

### Funcionalidad Agregada

1. **Construcción de URL Completa**: Ahora se construye la URL completa de la aplicación usando `window.location.origin` para obtener el dominio actual (funciona tanto en desarrollo como en producción).

2. **Parámetro de Mesa**: Se agrega el parámetro `?table=` con el código de la mesa a la URL.

3. **Visualización Mejorada**: Se agregó una línea adicional en la interfaz que muestra la URL completa a la que el QR redirige:
   ```html
   <p style="font-size: 0.85em; color: #888; margin-top: 10px;">
       Escanea para acceder a:<br>${appUrl}
   </p>
   ```

## Resultado

### Antes
- QR contenía: `karaoke-mesa-05`
- Al escanear: No redirigía a ningún lugar útil

### Después
- QR contiene: `http://localhost:8000/?table=karaoke-mesa-05` (en desarrollo)
- QR contiene: `http://tu-dominio.com/?table=karaoke-mesa-05` (en producción)
- Al escanear: Redirige automáticamente a la aplicación con la mesa correcta seleccionada

## Compatibilidad

Esta solución es compatible con:
- ✅ Desarrollo local (localhost:8000)
- ✅ Producción (cualquier dominio)
- ✅ HTTP y HTTPS
- ✅ Diferentes puertos

El código usa `window.location.origin` que detecta automáticamente el protocolo, dominio y puerto actual, por lo que no requiere configuración adicional.

## Pruebas Recomendadas

1. Acceder al panel de administración en `/admin/dashboard`
2. Ir a la sección de "Mesas/QR"
3. Hacer clic en "Generar QR" para cualquier mesa
4. Verificar que se muestre la URL completa debajo del código QR
5. Escanear el código QR con un dispositivo móvil
6. Confirmar que redirige a la aplicación con la mesa correcta

## Notas Adicionales

- Los códigos QR se generan dinámicamente usando el servicio `api.qrserver.com`
- No se requiere almacenar imágenes de QR en el servidor
- Los QR se pueden descargar como archivos PNG para impresión
