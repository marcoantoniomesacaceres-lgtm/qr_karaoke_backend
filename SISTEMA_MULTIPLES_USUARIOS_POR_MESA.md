# Sistema de Múltiples Usuarios por Mesa - Implementación Completada

## Resumen de Cambios

Se ha implementado un sistema donde cada mesa puede tener hasta 10 usuarios automáticamente asignados mediante QR codes individuales. Esto resuelve el problema de conflictos de concurrencia cuando múltiples usuarios de la misma mesa intentan realizar acciones simultáneamente.

## Cambios Implementados

### 1. **Archivo: `mesas.py`** ✅ COMPLETADO
**Cambio Principal:** Modificación del endpoint de conexión para soportar QR codes con formato `karaoke-mesa-XX-usuarioN`

**Funcionalidad:**
- El endpoint `/{qr_code}/conectar` ahora extrae automáticamente el número de mesa y usuario del QR code
- Formato esperado: `karaoke-mesa-05-usuario1` (donde 05 es el número de mesa y 1 es el número de usuario)
- El sistema genera automáticamente el nick del usuario como: `{Nombre de Mesa}-Usuario{N}`
- Si un usuario ya existe y está activo, lo retorna
- Si un usuario existe pero está inactivo, lo reactiva
- Si no existe, crea un nuevo usuario con el nick automático

**Validaciones:**
- Verifica que el QR code tenga el formato correcto
- Valida que el número de usuario esté entre 1 y 10
- Busca la mesa base (sin el sufijo de usuario)
- Verifica que la mesa esté activa

### 2. **Archivo: `generate_qr_mesas.py`** ✅ COMPLETADO
**Cambio Principal:** Generación de 10 QR codes por cada mesa

**Funcionalidad:**
- Genera 10 QR codes para cada mesa (uno por cada usuario posible)
- Los QR se organizan en subdirectorios por mesa: `qrcodes_mesas/mesa_01/usuario_1.png`
- Cada QR contiene la URL: `http://{IP}:8000/?table=karaoke-mesa-XX-usuarioN`
- Total de QR codes generados: 30 mesas × 10 usuarios = 300 QR codes

**Estructura de Carpetas:**
```
qrcodes_mesas/
├── mesa_01/
│   ├── usuario_1.png
│   ├── usuario_2.png
│   ├── ...
│   └── usuario_10.png
├── mesa_02/
│   ├── usuario_1.png
│   ├── ...
```

### 3. **Archivo: `crud.py`** ⚠️ PENDIENTE
**Cambio Necesario:** Modificar la función `check_if_song_in_user_list` para verificar duplicados a nivel de mesa

**Función Actual (líneas 58-66):**
```python
def check_if_song_in_user_list(db: Session, usuario_id: int, youtube_id: str):
    """
    Verifica si un usuario ya tiene una canción en su lista que no esté cantada o rechazada.
    """
    return db.query(models.Cancion).filter(
        models.Cancion.usuario_id == usuario_id,
        models.Cancion.youtube_id == youtube_id,
        models.Cancion.estado.in_(['pendiente', 'aprobado', 'reproduciendo'])
    ).first()
```

**Función Modificada (REEMPLAZAR):**
```python
def check_if_song_in_user_list(db: Session, usuario_id: int, youtube_id: str):
    """
    Verifica si ALGÚN USUARIO DE LA MISMA MESA ya tiene esta canción en la cola.
    CAMBIO: Ahora verifica a nivel de mesa para evitar duplicados entre usuarios de la misma mesa.
    """
    # Obtener el usuario y su mesa
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario or not usuario.mesa_id:
        return None
    
    # Buscar si algún usuario de la misma mesa ya tiene esta canción en cola
    return db.query(models.Cancion).join(
        models.Usuario, models.Cancion.usuario_id == models.Usuario.id
    ).filter(
        models.Usuario.mesa_id == usuario.mesa_id,
        models.Cancion.youtube_id == youtube_id,
        models.Cancion.estado.in_(['pendiente', 'aprobado', 'reproduciendo'])
    ).first()
```

## Cómo Usar el Sistema

### Paso 1: Generar los QR Codes
```bash
python generate_qr_mesas.py
```

Esto generará 300 QR codes organizados en carpetas por mesa.

### Paso 2: Imprimir y Colocar los QR Codes
- Imprime los 10 QR codes de cada mesa
- Colócalos en la mesa correspondiente
- Cada usuario de la mesa escaneará un QR diferente

### Paso 3: Funcionamiento Automático
Cuando un usuario escanea un QR:
1. El QR contiene: `http://192.168.20.94:8000/?table=karaoke-mesa-05-usuario3`
2. El sistema extrae: Mesa 05, Usuario 3
3. Busca la mesa "karaoke-mesa-05" en la base de datos
4. Crea automáticamente el usuario con nick: "Mesa 5-Usuario3"
5. El usuario queda conectado y puede empezar a usar la aplicación

### Paso 4: Aplicar el Cambio en crud.py
**IMPORTANTE:** Debes reemplazar manualmente la función `check_if_song_in_user_list` en el archivo `crud.py` con el código proporcionado arriba.

## Beneficios del Sistema

✅ **Sin Conflictos de Concurrencia:** Cada usuario tiene su propio QR y sesión
✅ **Asignación Automática:** No es necesario que los usuarios elijan un nick
✅ **Consolidación por Mesa:** Todos los consumos y pagos se manejan a nivel de mesa
✅ **Máximo 10 Usuarios:** Límite claro y controlado por mesa
✅ **Sin Duplicados de Canciones:** Una mesa no puede pedir la misma canción dos veces
✅ **Fácil Identificación:** Los nicks son claros: "Mesa 5-Usuario3"

## Ejemplo de Uso

**Mesa 1 con 3 usuarios:**
- Usuario 1 escanea: `karaoke-mesa-01-usuario1` → Nick: "Mesa 1-Usuario1"
- Usuario 2 escanea: `karaoke-mesa-01-usuario2` → Nick: "Mesa 1-Usuario2"
- Usuario 3 escanea: `karaoke-mesa-01-usuario3` → Nick: "Mesa 1-Usuario3"

**Todos comparten:**
- La misma cuenta de consumos
- El mismo estado de pago
- No pueden pedir canciones duplicadas entre ellos

**Cada uno tiene:**
- Su propio perfil de usuario
- Sus propios puntos
- Su propio nivel (bronce/plata/oro)

## Notas Importantes

1. **Formato de QR:** El sistema ahora requiere QR codes con el formato `karaoke-mesa-XX-usuarioN`
2. **Compatibilidad:** Los QR antiguos (sin el sufijo de usuario) NO funcionarán con este sistema
3. **Migración:** Si tienes mesas existentes, deberás regenerar todos los QR codes
4. **Base de Datos:** No se requieren cambios en la estructura de la base de datos

## Archivos Modificados

- ✅ `mesas.py` - Endpoint de conexión actualizado
- ✅ `generate_qr_mesas.py` - Generador de QR codes actualizado
- ⚠️ `crud.py` - Requiere modificación manual de `check_if_song_in_user_list`

## Próximos Pasos

1. Aplicar el cambio en `crud.py` (función `check_if_song_in_user_list`)
2. Ejecutar `python generate_qr_mesas.py` para generar los nuevos QR codes
3. Imprimir y distribuir los QR codes en las mesas
4. Reiniciar el servidor para aplicar los cambios
