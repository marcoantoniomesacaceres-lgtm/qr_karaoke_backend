# ✅ Mejora de Interfaz Admin: Buscador y Generador de QR

## 🎯 Problema Resuelto
La lista de mesas era demasiado larga (30 mesas) y mostrar 10 usuarios por mesa (300 opciones) hubiera sido inmanejable.

## ✨ Solución Implementada

He modificado la sección de "Mesas y QR" en el panel de administración para incluir:

1.  **🔍 Buscador de Mesas**:
    *   Ahora puedes escribir el nombre de la mesa (ej: "Mesa 5") y la lista se filtrará instantáneamente.
    *   Esto hace mucho más fácil encontrar una mesa específica entre las 30.

2.  **🎛️ Selector de Usuario**:
    *   Al seleccionar una mesa, verás un nuevo panel de control.
    *   Puedes seleccionar el número de usuario (del 1 al 10) en un menú desplegable.
    *   Al hacer clic en **"Generar QR de Usuario"**, se crea el código QR específico para ese usuario (ej: `karaoke-mesa-05-usuario3`).

## 🚀 Cómo Usar

1.  Ve a la sección **Mesas y QR** en el Admin Dashboard.
2.  Usa el **buscador** para encontrar tu mesa rápidamente.
3.  Haz clic en **"Seleccionar"** en la mesa deseada.
4.  En el panel de la derecha ("Generador de QR"):
    *   Por defecto verás el QR del **Usuario 1**.
    *   Cambia el selector a **Usuario 2**, **Usuario 3**, etc.
    *   Haz clic en el botón azul **"Generar QR de Usuario"**.
    *   El QR se actualizará automáticamente.

## 📄 Archivos Modificados
*   `static/admin_pages/tables.html`: Estructura visual nueva.
*   `static/admin_pages/tables.js`: Lógica de búsqueda y generación dinámica de QR.

**Nota:** Si no ves los cambios, recarga la página del navegador con **Ctrl + F5** para limpiar la caché.
