from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============ AUTH ============
class UserCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    telefono: Optional[str] = None
    ciudad: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    nombre: str
    email: str
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    avatar_url: Optional[str] = None
    rol: str
    tipo_cuenta: str
    is_pro: bool
    is_verified: bool
    is_active: bool
    bio: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None


# ============ MOTOS ============
class MotoImagenResponse(BaseModel):
    id: int
    url: str
    orden: int
    es_principal: bool

    class Config:
        from_attributes = True


class MotoCreate(BaseModel):
    marca: str = Field(..., min_length=1, max_length=100)
    modelo: str = Field(..., min_length=1, max_length=100)
    año: int = Field(..., ge=1950, le=2027)
    precio: float = Field(..., gt=0)
    kilometraje: Optional[int] = Field(None, ge=0)
    cilindraje: Optional[int] = Field(None, ge=50)
    color: Optional[str] = None
    transmision: Optional[str] = None
    combustible: Optional[str] = None
    ciudad: Optional[str] = None
    descripcion: Optional[str] = None


class MotoResponse(BaseModel):
    id: int
    marca: str
    modelo: str
    año: int
    precio: float
    kilometraje: Optional[int] = None
    cilindraje: Optional[int] = None
    color: Optional[str] = None
    transmision: Optional[str] = None
    combustible: Optional[str] = None
    ciudad: Optional[str] = None
    descripcion: Optional[str] = None
    estado: str
    image_url: Optional[str] = None
    is_hot: bool
    views_count: int = 0
    contactos_count: int = 0
    commission_fee: float = 0.0
    commission_type: str = "fixed"
    created_at: datetime
    propietario_id: int
    imagenes: List[MotoImagenResponse] = []

    class Config:
        from_attributes = True


class MotoUpdate(BaseModel):
    marca: Optional[str] = None
    modelo: Optional[str] = None
    año: Optional[int] = None
    precio: Optional[float] = None
    kilometraje: Optional[int] = None
    cilindraje: Optional[int] = None
    color: Optional[str] = None
    transmision: Optional[str] = None
    combustible: Optional[str] = None
    ciudad: Optional[str] = None
    descripcion: Optional[str] = None
    estado: Optional[str] = None


# ============ MENSAJES ============
class MensajeCreate(BaseModel):
    destinatario_id: int
    moto_id: int
    contenido: str = Field(..., min_length=1, max_length=2000)


class MensajeResponse(BaseModel):
    id: int
    remitente_id: int
    destinatario_id: int
    moto_id: int
    contenido: str
    leido: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ REVIEWS ============
class ReviewCreate(BaseModel):
    vendedor_id: int
    moto_id: int
    calificacion: int = Field(..., ge=1, le=5)
    comentario: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    comprador_id: int
    vendedor_id: int
    moto_id: int
    calificacion: int
    comentario: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ NOTIFICACIONES ============
class NotificacionResponse(BaseModel):
    id: int
    tipo: str
    titulo: str
    contenido: Optional[str] = None
    leida: bool
    url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ TRANSACCIONES ============
class TransaccionCreate(BaseModel):
    moto_id: Optional[int] = None
    monto: float = Field(..., gt=0)
    tipo: str  # compra, plan_pro, bumping


class TransaccionResponse(BaseModel):
    id: int
    comprador_id: int
    vendedor_id: Optional[int] = None
    moto_id: Optional[int] = None
    monto: float
    tipo: str
    estado: str
    referencia_pago: Optional[str] = None
    plataforma_pago: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ ANALYTICS ============
class DashboardStats(BaseModel):
    total_motos: int = 0
    total_mensajes: int = 0
    total_favoritos: int = 0
    total_views: int = 0
    motos_activas: int = 0
    motos_vendidas: int = 0
