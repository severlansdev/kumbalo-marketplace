import sys
import os
from passlib.context import CryptContext

# Set project root in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.models import Usuario

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin(nombre, email, password):
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(Usuario).filter(Usuario.email == email).first()
        if existing:
            print(f"⚠️ El usuario {email} ya existe. Actualizando a rol admin...")
            existing.rol = "admin"
            db.commit()
            print(f"✅ Usuario {email} ahora es ADMIN.")
            return

        hashed_password = pwd_context.hash(password)
        new_user = Usuario(
            nombre=nombre,
            email=email,
            hashed_password=hashed_password,
            rol="admin",
            tipo_cuenta="concesionario", # Admins are usually pros
            is_pro=True,
            is_verified=True
        )
        db.add(new_user)
        db.commit()
        print(f"🚀 Admin '{nombre}' creado con éxito!")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("--- Creador de Admin KUMBALO ---")
    nombre = input("Nombre del Admin [Admin Kumbalo]: ") or "Admin Kumbalo"
    email = input("Email del Admin [admin@kumbalo.com]: ") or "admin@kumbalo.com"
    password = input("Password del Admin [admin123]: ") or "admin123"
    
    create_admin(nombre, email, password)
