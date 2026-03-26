import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from .. import schemas, models
from ..database import get_db
from ..email_utils import send_email
from ..utils import sanitize_input
from ..limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Endpoint donde FastAPI buscará el token (Swagger)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales no válidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = db.query(models.Usuario).filter(models.Usuario.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin(current_user: models.Usuario = Depends(get_current_user)):
    if current_user.rol != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos de Administrador")
    return current_user

@router.post("/register", response_model=schemas.UsuarioResponse)
@limiter.limit("5/minute")
def register(request: Request, user: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.Usuario).filter(models.Usuario.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    hashed_password = get_password_hash(user.password)
    new_user = models.Usuario(
        nombre=sanitize_input(user.nombre),
        email=user.email,
        hashed_password=hashed_password,
        tipo_cuenta=user.tipo_cuenta
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Enviar correo de bienvenida
    send_email(
        to_email=new_user.email,
        subject="¡Bienvenido a KUMBALO Marketplace!",
        body=f"Hola {new_user.nombre}, gracias por registrarte. Ya puedes empezar a publicar y guardar tus motos favoritas."
    )
    
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me/stats")
def get_user_stats(db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    motos_count = db.query(models.Moto).filter(models.Moto.propietario_id == current_user.id).count()
    favoritos_count = db.query(models.Favorito).filter(models.Favorito.usuario_id == current_user.id).count()
    
    motos = db.query(models.Moto).filter(models.Moto.propietario_id == current_user.id).all()
    ventas_totales = sum(m.precio for m in motos)

    mensajes_no_leidos = db.query(models.Mensaje).filter(models.Mensaje.destinatario_id == current_user.id, models.Mensaje.leido == False).count()

    return {
        "motos_publicadas": motos_count,
        "mensajes_recibidos": mensajes_no_leidos,
        "ventas_totales": ventas_totales,
        "motos_guardadas": favoritos_count,
        "user": {
            "id": current_user.id,
            "nombre": current_user.nombre,
            "email": current_user.email,
            "tipo_cuenta": current_user.tipo_cuenta,
            "is_pro": current_user.is_pro
        }
    }

import uuid
from fastapi import Body

@router.post("/recover-password")
@limiter.limit("3/minute")
def recover_password(request: Request, email_data: dict = Body(...), db: Session = Depends(get_db)):
    email = email_data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email es requerido")
        
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if user:
        reset_token = str(uuid.uuid4())
        reset_link = f"http://localhost:5500/resetar.html?token={reset_token}"
        
        send_email(
            to_email=user.email,
            subject="Reinicio de Contraseña - KUMBALO",
            body=f"Hola {user.nombre},\n\nHemos recibido una solicitud para reiniciar el acceso a tu cuenta.\nHaz clic en el siguiente enlace seguro (válido por 1 hora) para elegir una nueva contraseña:\n\n{reset_link}\n\nSi no solicitaste este cambio, puedes ignorar este correo de forma segura.\n\nEl Equipo de Seguridad de KUMBALO."
        )
        
    return {"message": "Si el correo existe en nuestro sistema, te enviaremos instrucciones detalladas."}
