from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean
from sqlalchemy.orm import relationship
import datetime

from database import Base

class Mesa(Base):
    __tablename__ = "mesas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    qr_code = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True) # Nuevo campo para activar/desactivar

    # Relaciones: Una mesa puede tener muchos usuarios y consumos
    usuarios = relationship("Usuario", back_populates="mesa")
    consumos = relationship("Consumo", back_populates="mesa")  # NUEVO: Relación con consumos
    pagos = relationship("Pago", back_populates="mesa") # Relación con Pagos

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nick = Column(String, index=True)
    puntos = Column(Integer, default=0)
    nivel = Column(String, default="bronce")  # bronce, plata, oro
    last_active = Column(DateTime, default=datetime.datetime.utcnow)
    is_silenced = Column(Boolean, default=False) # Nuevo campo para silenciar
    is_active = Column(Boolean, default=True)  # Para desconectar usuarios sin eliminar
    
    mesa_id = Column(Integer, ForeignKey("mesas.id"))

    # Relaciones: Un usuario pertenece a una mesa y puede tener muchas canciones
    mesa = relationship("Mesa", back_populates="usuarios")
    canciones = relationship("Cancion", back_populates="usuario")
    # Los consumos ahora se asignan a la mesa, no al usuario individual

class Cancion(Base):
    __tablename__ = "canciones"

    id = Column(Integer, primary_key=True, index=True)
    youtube_id = Column(String, index=True)
    titulo = Column(String)
    duracion_seconds = Column(Integer, default=0)
    estado = Column(String, default="pendiente")  # pendiente, aprobado, reproduciendo, cantada, rechazada
    started_at = Column(DateTime, nullable=True)  # Hora en que empieza a sonar
    orden_manual = Column(Integer, nullable=True)  # Posición manual establecida por el admin
    puntuacion_ia = Column(Integer, nullable=True) # Nuevo campo para el puntaje de la IA
    created_at = Column(DateTime, default=datetime.datetime.utcnow)  # Hora en que se añade
    finished_at = Column(DateTime, nullable=True) # Hora en que se termina de cantar
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    usuario = relationship("Usuario", back_populates="canciones")

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    categoria = Column(String, index=True, default="General")
    valor = Column(Numeric(10, 2))  # Precio de venta
    costo = Column(Numeric(10, 2), default=0)  # Precio de compra
    stock = Column(Integer, default=0)
    imagen_url = Column(String, nullable=True) # Columna para la URL de la imagen
    is_active = Column(Boolean, default=True)

    consumos = relationship("Consumo", back_populates="producto")

class Consumo(Base):
    __tablename__ = "consumos"

    id = Column(Integer, primary_key=True, index=True)
    cantidad = Column(Integer, default=1)
    valor_total = Column(Numeric(10, 2))  # Valor total de la transacción (cantidad * precio_unitario)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    producto_id = Column(Integer, ForeignKey("productos.id"))
    mesa_id = Column(Integer, ForeignKey("mesas.id"))  # CAMBIO: Consumos asignados a mesa, no usuario
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)  # Referencia opcional para tracking
    
    producto = relationship("Producto", back_populates="consumos")
    mesa = relationship("Mesa", back_populates="consumos")  # Relación con mesa
    usuario = relationship("Usuario")  # Relación sin backref (solo para consultas)
    is_dispatched = Column(Boolean, default=False) # Nuevo campo para marcar si ya fue entregado

class BannedNick(Base):
    __tablename__ = "banned_nicks"
    id = Column(Integer, primary_key=True, index=True)
    nick = Column(String, unique=True, index=True)
    banned_at = Column(DateTime, default=datetime.datetime.utcnow)

class AdminLog(Base):
    __tablename__ = "admin_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    action = Column(String, index=True)
    details = Column(String, nullable=True)

class AdminApiKey(Base):
    __tablename__ = "admin_api_keys"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used = Column(DateTime, nullable=True)

class Pago(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    monto = Column(Numeric(10, 2), nullable=False)
    metodo_pago = Column(String, default="Efectivo")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    mesa_id = Column(Integer, ForeignKey("mesas.id"))

    # Relación: Un pago pertenece a una mesa
    mesa = relationship("Mesa", back_populates="pagos")


class ConfiguracionGlobal(Base):
    __tablename__ = "configuracion_global"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String(100), unique=True, nullable=False)
    valor = Column(String(100), nullable=False)