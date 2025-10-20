from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

# --- Schemas para Cancion ---
class CancionBase(BaseModel):
    titulo: str
    youtube_id: str
    puntuacion_ia: Optional[int] = None # Nuevo campo
    duracion_seconds: Optional[int] = 0

class CancionCreate(CancionBase):
    pass

class Cancion(CancionBase):
    id: int
    estado: str
    created_at: datetime # Añadimos este campo
    puntuacion_ia: Optional[int] = None # Aseguramos que esté aquí también
    model_config = ConfigDict(from_attributes=True)

# --- Schemas para Usuario (necesario para mostrar usuarios en una mesa) ---
class UsuarioBase(BaseModel):
    nick: str
    model_config = ConfigDict(from_attributes=True)

class UsuarioCreate(UsuarioBase):
    pass

class Usuario(UsuarioBase): # Schema completo de Usuario
    id: int
    puntos: int
    nivel: str
    is_silenced: bool = False
    canciones: List[Cancion] = []

    model_config = ConfigDict(from_attributes=True)

# --- Schemas para Mesa ---
class MesaBase(BaseModel):
    nombre: str
    qr_code: str

class MesaCreate(MesaBase):
    pass # Para crear, usamos los mismos campos que la base

class Mesa(MesaBase):
    id: int
    usuarios: List[Usuario] = [] # Al pedir una mesa, mostrará la lista de sus usuarios

    model_config = ConfigDict(from_attributes=True) # Permite que Pydantic lea datos de objetos SQLAlchemy

# --- Schema para mesas vacías ---
class MesaSimple(MesaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Schema simple para info de Mesa ---
class MesaInfo(BaseModel):
    nombre: str
    model_config = ConfigDict(from_attributes=True)

# --- Schema para la vista del Administrador ---
class CancionAdminView(Cancion):
    # Hereda de Cancion y añade la información del usuario
    usuario: UsuarioBase
    model_config = ConfigDict(from_attributes=True)

# --- Schemas para Producto ---
class ProductoBase(BaseModel):
    nombre: str
    categoria: str
    valor: Decimal
    stock: int
    imagen_url: Optional[str] = None
    is_active: bool = True

class ProductoCreate(ProductoBase):
    pass

class Producto(ProductoBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

# --- Schemas para Consumo ---
class ConsumoBase(BaseModel):
    producto_id: int
    cantidad: int = 1

class ConsumoCreate(ConsumoBase):
    pass

class Consumo(BaseModel):
    id: int
    cantidad: int
    valor_total: Decimal
    producto: ProductoBase # Usamos un schema más simple para evitar anidamiento excesivo
    model_config = ConfigDict(from_attributes=True)


# --- Schema para consumo reciente (para el dashboard de admin) ---
class ConsumoReciente(BaseModel):
    id: int
    cantidad: int
    valor_total: Decimal
    producto_nombre: str
    usuario_nick: str
    mesa_nombre: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Schema para el Perfil de Usuario ---
class UsuarioPerfil(Usuario):
    total_consumido: Decimal = Decimal("0.0")
    rank: Optional[int] = None
    mesa: Optional[MesaInfo] = None
    is_silenced: bool = False
    model_config = ConfigDict(from_attributes=True)


# --- Schema para la vista de la Cola ---
class ColaView(BaseModel):
    now_playing: Optional[CancionAdminView] = None
    upcoming: List[CancionAdminView] = []

# --- Schema para la respuesta de "siguiente canción" ---
class PlayNextResponse(BaseModel):
    play_url: str
    cancion: CancionAdminView


# --- Schema para la configuración ---
class ClosingTimeUpdate(BaseModel):
    hora_cierre: str

class ProductoValorUpdate(BaseModel):
    valor: Decimal

# --- Schema para Reportes ---
class CancionMasCantada(BaseModel):
    titulo: str
    youtube_id: str
    veces_cantada: int

# --- Schema para el Perfil Público de Usuario ---
class UsuarioPublico(UsuarioBase):
    id: int
    puntos: int
    nivel: str
    mesa: Optional[MesaInfo] = None
    is_silenced: bool = False # Mantener este campo para consistencia, aunque Usuario ya lo tiene
    model_config = ConfigDict(from_attributes=True)


class ProductoMasConsumido(BaseModel):
    nombre: str
    cantidad_total: int

class ReporteIngresos(BaseModel):
    ingresos_totales: Decimal
    model_config = ConfigDict(from_attributes=True)


class ReporteIngresosPorMesa(BaseModel):
    mesa_nombre: str
    ingresos_totales: Decimal

# --- Schema para reordenar la cola ---
class ReordenarCola(BaseModel):
    canciones_ids: List[int]

class ReporteCancionesPorUsuario(BaseModel):
    nick: str
    canciones_cantadas: int

# --- Schema para editar el nick de un usuario ---
class UsuarioNickUpdate(BaseModel):
    nick: str

# --- Schema para reporte de ingresos promedio ---
class ReporteIngresosPromedio(BaseModel):
    ingresos_promedio_por_usuario: Decimal

# --- Schema para mover un usuario de mesa ---
class UsuarioMoverMesa(BaseModel):
    nuevo_qr_code: str

# --- Schema para añadir puntos a un usuario ---
class UsuarioPuntosUpdate(BaseModel):
    puntos: int

class ReporteCancionesPorMesa(BaseModel):
    mesa_nombre: str
    canciones_cantadas: int

class ReporteIngresosPromedioPorMesa(BaseModel):
    mesa_nombre: str
    ingresos_promedio_por_usuario: Decimal

class ReporteActividadPorHora(BaseModel):
    hora: int
    canciones_cantadas: int

# --- Schema para perdonar un nick baneado ---
class NickUnban(BaseModel):
    nick: str

# --- Schema para reporte de tiempo de espera promedio ---
class ReporteTiempoEsperaPromedio(BaseModel):
    tiempo_espera_promedio_segundos: int

# --- Schema para ver nicks baneados ---
class BannedNickView(BaseModel):
    nick: str
    banned_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReporteCancionesRechazadas(BaseModel):
    titulo: str
    youtube_id: str
    veces_rechazada: int

class ReporteUsuarioRechazado(BaseModel):
    nick: str
    canciones_rechazadas: int

class ReporteIngresosPorCategoria(BaseModel):
    categoria: str
    ingresos_totales: Decimal

class AdminLogView(BaseModel):
    timestamp: datetime
    action: str
    details: Optional[str] = None # Optional[str] es mejor que None
    model_config = ConfigDict(from_attributes=True)

# --- Schemas para Claves de API de Admin ---
class AdminApiKeyCreate(BaseModel):
    description: str

class AdminApiKeyInfo(BaseModel):
    """Schema para listar claves sin exponer la clave misma."""
    id: int
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class AdminApiKeyView(AdminApiKeyInfo):
    """Schema para mostrar la clave recién creada."""
    key: str


# --- Schema para notificaciones generales ---
class Notificacion(BaseModel):
    mensaje: str

class ResumenNoche(BaseModel):
    ingresos_totales: Decimal
    canciones_cantadas: int
    usuarios_activos: int

class ResumenMesa(BaseModel):
    mesa_nombre: str
    usuarios: List[UsuarioPublico]
    consumo_total_mesa: Decimal
    canciones_pendientes_mesa: List[CancionAdminView]
    canciones_reproduciendo_mesa: Optional[CancionAdminView] = None

class MesaEstado(MesaBase):
    id: int
    estado: str
    numero_usuarios: int
    consumo_total: Decimal

class HistorialUsuario(BaseModel):
    canciones: List[Cancion] = []
    consumos: List['ConsumoHistorial'] = []

class ConsumoHistorial(BaseModel):
    id: int
    cantidad: int
    valor_total: Decimal
    created_at: datetime
    producto: ProductoBase
    usuario: UsuarioBase # Asegúrate de que UsuarioBase esté definido antes de ConsumoHistorial
    model_config = ConfigDict(from_attributes=True)

# Actualizamos la referencia forward para HistorialUsuario
HistorialUsuario.update_forward_refs()

class ReporteGastoUsuarioPorCategoria(BaseModel):
    nick: str
    total_gastado: Decimal

class ReporteCancionMasPedida(BaseModel):
    titulo: str
    youtube_id: str
    veces_pedida: int

class ReporteCategoriaMasVendida(BaseModel):
    categoria: str
    cantidad_total: int