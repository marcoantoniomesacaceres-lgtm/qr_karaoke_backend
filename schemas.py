from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

# --- Schemas para Cancion ---
class CancionBase(BaseModel):
    titulo: str
    youtube_id: str
    duracion_seconds: Optional[int] = 0

class CancionCreate(CancionBase):
    pass

class Cancion(CancionBase):
    id: int
    estado: str
    class Config:
        orm_mode = True

# --- Schemas para Usuario (necesario para mostrar usuarios en una mesa) ---
class UsuarioBase(BaseModel):
    nick: str

class UsuarioCreate(UsuarioBase):
    pass

class Usuario(UsuarioBase): # Schema completo de Usuario
    id: int
    puntos: int
    nivel: str
    canciones: List[Cancion] = []

    class Config:
        orm_mode = True

# --- Schemas para Mesa ---
class MesaBase(BaseModel):
    nombre: str
    qr_code: str

class MesaCreate(MesaBase):
    pass # Para crear, usamos los mismos campos que la base

class Mesa(MesaBase):
    id: int
    usuarios: List[Usuario] = [] # Al pedir una mesa, mostrará la lista de sus usuarios

    class Config:
        orm_mode = True # Permite que Pydantic lea datos de objetos SQLAlchemy

# --- Schema simple para info de Mesa ---
class MesaInfo(BaseModel):
    nombre: str
    class Config:
        orm_mode = True

# --- Schema para la vista del Administrador ---
class CancionAdminView(Cancion):
    # Hereda de Cancion y añade la información del usuario
    usuario: UsuarioBase

# --- Schemas para Consumo ---
class ConsumoBase(BaseModel):
    producto: str
    cantidad: int = 1
    valor: Decimal

class ConsumoCreate(ConsumoBase):
    pass

class Consumo(ConsumoBase):
    id: int

    class Config:
        orm_mode = True

# --- Schema para el Perfil de Usuario ---
class UsuarioPerfil(Usuario):
    total_consumido: Decimal = Decimal("0.0")
    rank: Optional[int] = None
    mesa: Optional[MesaInfo] = None
    class Config:
        orm_mode = True

# --- Schema para la vista de la Cola ---
class ColaView(BaseModel):
    now_playing: Optional[CancionAdminView] = None
    upcoming: List[CancionAdminView] = []

# --- Schema para la configuración ---
class ClosingTimeUpdate(BaseModel):
    hora_cierre: str

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
    class Config:
        orm_mode = True

class ProductoMasConsumido(BaseModel):
    producto: str
    cantidad_total: int
    class Config:
        orm_mode = True

class ReporteIngresos(BaseModel):
    ingresos_totales: Decimal
    class Config:
        orm_mode = True

class ReporteIngresosPorMesa(BaseModel):
    mesa_nombre: str
    ingresos_totales: Decimal

# --- Schema para reordenar la cola ---
class ReordenarCola(BaseModel):
    canciones_ids: List[int]