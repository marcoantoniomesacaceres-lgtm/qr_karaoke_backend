from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean
from sqlalchemy.orm import relationship
import datetime

from database import Base

class Mesa(Base):
    __tablename__ = "mesas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    qr_code = Column(String, unique=True, index=True)

    # Relación: Una mesa puede tener muchos usuarios
    usuarios = relationship("Usuario", back_populates="mesa")

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nick = Column(String, index=True)
    puntos = Column(Integer, default=0)
    nivel = Column(String, default="bronce")  # bronce, plata, oro
    last_active = Column(DateTime, default=datetime.datetime.utcnow)
    is_silenced = Column(Boolean, default=False) # Nuevo campo para silenciar
    
    mesa_id = Column(Integer, ForeignKey("mesas.id"))

    # Relaciones: Un usuario pertenece a una mesa y puede tener muchas canciones y consumos
    mesa = relationship("Mesa", back_populates="usuarios")
    canciones = relationship("Cancion", back_populates="usuario")
    consumos = relationship("Consumo", back_populates="usuario")

class Cancion(Base):
    __tablename__ = "canciones"

    id = Column(Integer, primary_key=True, index=True)
    youtube_id = Column(String, index=True)
    titulo = Column(String)
    duracion_seconds = Column(Integer, default=0)
    estado = Column(String, default="pendiente")  # pendiente, aprobado, reproduciendo, cantada, rechazada
    started_at = Column(DateTime, nullable=True)  # Hora en que empieza a sonar
    orden_manual = Column(Integer, nullable=True)  # Posición manual establecida por el admin
    created_at = Column(DateTime, default=datetime.datetime.utcnow)  # Hora en que se añade
    finished_at = Column(DateTime, nullable=True) # Hora en que se termina de cantar
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    usuario = relationship("Usuario", back_populates="canciones")

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    categoria = Column(String, index=True, default="General")
    valor = Column(Numeric(10, 2))
    is_active = Column(Boolean, default=True)

    consumos = relationship("Consumo", back_populates="producto")

class Consumo(Base):
    __tablename__ = "consumos"

    id = Column(Integer, primary_key=True, index=True)
    cantidad = Column(Integer, default=1)
    valor_total = Column(Numeric(10, 2))  # Valor total de la transacción (cantidad * precio_unitario)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    producto_id = Column(Integer, ForeignKey("productos.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    
    producto = relationship("Producto", back_populates="consumos")
    usuario = relationship("Usuario", back_populates="consumos")

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