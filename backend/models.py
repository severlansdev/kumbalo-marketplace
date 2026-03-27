from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum


class TipoCuenta(enum.Enum):
    natural = "natural"
    concesionario = "concesionario"


class EstadoMoto(enum.Enum):
    activa = "activa"
    vendida = "vendida"
    pausada = "pausada"
    eliminada = "eliminada"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    telefono = Column(String(20), nullable=True)
    ciudad = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    rol = Column(String(20), default="usuario")  # "usuario", "admin", "moderador"
    tipo_cuenta = Column(String(20), default="natural")
    is_pro = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    motos = relationship("Moto", back_populates="propietario")
    reviews_recibidas = relationship("Review", back_populates="vendedor", foreign_keys="Review.vendedor_id")
    notificaciones = relationship("Notificacion", back_populates="usuario")


class Moto(Base):
    __tablename__ = "motos"

    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String(100), index=True, nullable=False)
    modelo = Column(String(100), index=True, nullable=False)
    año = Column(Integer, nullable=False)
    precio = Column(Float, nullable=False)
    kilometraje = Column(Integer, nullable=True)
    cilindraje = Column(Integer, nullable=True)
    color = Column(String(50), nullable=True)
    transmision = Column(String(30), nullable=True)  # manual, automatica, cvt, dct
    combustible = Column(String(30), nullable=True)  # gasolina, electrica, hibrida
    ciudad = Column(String(100), index=True, nullable=True)
    descripcion = Column(Text, nullable=True)
    estado = Column(String(20), default="activa")  # activa, vendida, pausada, eliminada
    image_url = Column(String(500), nullable=True)
    is_hot = Column(Boolean, default=False)
    views_count = Column(Integer, default=0)
    contactos_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    propietario_id = Column(Integer, ForeignKey("usuarios.id"))
    propietario = relationship("Usuario", back_populates="motos")
    imagenes = relationship("MotoImagen", back_populates="moto", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="moto")


class MotoImagen(Base):
    __tablename__ = "moto_imagenes"

    id = Column(Integer, primary_key=True, index=True)
    moto_id = Column(Integer, ForeignKey("motos.id", ondelete="CASCADE"), index=True)
    url = Column(String(500), nullable=False)
    orden = Column(Integer, default=0)
    es_principal = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    moto = relationship("Moto", back_populates="imagenes")


class Favorito(Base):
    __tablename__ = "favoritos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    moto_id = Column(Integer, ForeignKey("motos.id"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Mensaje(Base):
    __tablename__ = "mensajes"

    id = Column(Integer, primary_key=True, index=True)
    remitente_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    destinatario_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    moto_id = Column(Integer, ForeignKey("motos.id"), index=True)
    contenido = Column(Text, nullable=False)
    leido = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    comprador_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    vendedor_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    moto_id = Column(Integer, ForeignKey("motos.id"), index=True)
    calificacion = Column(Integer, nullable=False)  # 1-5 stars
    comentario = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    vendedor = relationship("Usuario", back_populates="reviews_recibidas", foreign_keys=[vendedor_id])
    moto = relationship("Moto", back_populates="reviews")


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    tipo = Column(String(50), nullable=False)  # mensaje, favorito, review, sistema, vencimiento
    titulo = Column(String(200), nullable=False)
    contenido = Column(Text, nullable=True)
    leida = Column(Boolean, default=False)
    url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", back_populates="notificaciones")


class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True, index=True)
    comprador_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    vendedor_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    moto_id = Column(Integer, ForeignKey("motos.id"), index=True)
    monto = Column(Float, nullable=False)
    tipo = Column(String(30), nullable=False)  # compra, plan_pro, bumping
    estado = Column(String(30), default="pendiente")  # pendiente, completada, fallida, reembolsada
    referencia_pago = Column(String(200), nullable=True)
    plataforma_pago = Column(String(50), nullable=True)  # stripe, payu, mercadopago
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class BacklogAgente(Base):
    __tablename__ = "backlog_agentes"

    id = Column(Integer, primary_key=True, index=True)
    peticion = Column(Text, nullable=False)
    estado = Column(String(20), default="pendiente") # pendiente, en_proceso, completado
    prioridad = Column(Integer, default=1)
    agente_asignado = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
