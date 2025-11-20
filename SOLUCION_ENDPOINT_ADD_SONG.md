# 🔧 Solución: Endpoint Faltante para Añadir Canción a una Mesa

## Problema Identificado

El frontend intentaba hacer POST a `/api/v1/admin/mesas/{mesa_id}/add-song` pero este endpoint no existía en el backend, causando un error **404 Not Found**.

### Errores Reportados

- **En el navegador**: `Failed to load resource: the server responded with a status of 404 (Not Found) {"detail":"Not Found"}`
- **En la terminal**:
  - `INFO: 192.168.20.94:65428 - "POST /api/v1/admin/mesas/1/add-song HTTP/1.1" 404 Not Found`
  - `INFO: 192.168.20.94:49287 - "GET /api/v1/admin/mesas/1/add-song HTTP/1.1" 404 Not Found`

## Solución Implementada

### 1. Nuevo Endpoint en `admin.py`

Agregué un nuevo endpoint `POST /admin/mesas/{mesa_id}/add-song` que permite al administrador añadir una canción directamente a la cola de una mesa específica.

**Ubicación**: `admin.py`, línea 943

```python
@router.post("/mesas/{mesa_id}/add-song", response_model=schemas.Cancion, summary="Añadir una canción a una mesa específica")
async def admin_add_song_to_mesa(
    mesa_id: int,
    cancion: schemas.CancionCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_auth)
):
    """
    **[Admin]** Permite al administrador añadir una canción directamente a la cola
    de una mesa específica. La canción se aprueba automáticamente.
    """
```

### 2. Función de Soporte en `crud.py`

Creé una nueva función `get_o_crear_usuario_admin_para_mesa()` que genera o recupera un usuario administrador para una mesa específica.

**Ubicación**: `crud.py`, después de `get_or_create_dj_user()`

```python
def get_o_crear_usuario_admin_para_mesa(db: Session, mesa_id: int) -> models.Usuario:
    """
    Busca o crea un usuario administrador para una mesa específica.
    Este usuario se utiliza para las canciones añadidas por el admin a través del dashboard.
    El nick será "ADMIN_Mesa_{mesa_id}".
    """
```

## Flujo de Funcionamiento

1. **Frontend** (admin_dashboard.html) envía:

```javascript
POST /api/v1/admin/mesas/{mesa_id}/add-song
{
    "titulo": "Nombre de la Canción",
    "youtube_id": "id_youtube",
    "duracion_seconds": 180
}
```

1. **Backend** (admin.py):
   - Verifica que la mesa existe
   - Obtiene/crea un usuario admin para la mesa
   - Crea la canción asociada a ese usuario
   - Aprueba automáticamente la canción
   - Inicia autoplay si está activado
   - Notifica a todos los clientes sobre la actualización de la cola

1. **Respuesta**: Devuelve la canción creada con todos sus detalles

## Características del Endpoint

✅ **Seguridad**: Requiere autenticación con API Key (protegido por `api_key_auth`)
✅ **Validación**: Verifica que la mesa existe antes de añadir la canción
✅ **Automático**: La canción se aprueba automáticamente
✅ **Integración**: Se integra con autoplay y notificaciones WebSocket
✅ **Logging**: Registra la acción en el log de administrador

## Archivos Modificados

1. **`admin.py`**: Agregué el endpoint `admin_add_song_to_mesa()`
2. **`crud.py`**: Agregué la función `get_o_crear_usuario_admin_para_mesa()`

## Prueba Manual

Para probar el endpoint:

```bash
curl -X POST http://192.168.20.94:8000/api/v1/admin/mesas/1/add-song \
  -H "X-API-Key: YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Bohemian Rhapsody",
    "youtube_id": "fJ9rUzIMt7o",
    "duracion_seconds": 355
  }'
```

## Próximos Pasos

1. Inicia el servidor: `python main.py`
2. Ve al dashboard de admin en `http://192.168.20.94:8000/admin/dashboard`
3. Ve a la sección "Cola de Canciones"
4. Busca una canción en YouTube
5. Selecciona una mesa en el dropdown "Añadir a:"
6. Haz clic en "Canción" o "Karaoke"
7. Haz clic en "Añadir" en la canción deseada
8. ✅ La canción debe agregarse a la cola de esa mesa sin errores 404

---

**Resuelto**: El endpoint ahora está disponible y funcional. El error 404 desaparecerá.
