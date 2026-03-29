import sys
import os
from passlib.context import CryptContext

# Set project root in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.models import Usuario, Moto

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def setup_test_environment():
    db = SessionLocal()
    try:
        # 1. Create Test User
        email = "auditor_qa@kumbalo.com"
        password = "QA_Kumbalo_2026!"
        nombre = "Auditor QA Kumbalo"
        
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user:
            user = Usuario(
                nombre=nombre,
                email=email,
                hashed_password=pwd_context.hash(password),
                rol="user",
                tipo_cuenta="persona_natural",
                is_pro=False,
                is_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Usuario de prueba creado: {email}")
        else:
            print(f"ℹ️ Usuario de prueba ya existe: {email}")

        # 2. Create Test Motorcycle in Bogotá (Required for Traspaso Express)
        moto = db.query(Moto).filter(Moto.propietario_id == user.id, Moto.modelo == "MT-09 (QA TEST)").first()
        if not moto:
            moto = Moto(
                marca="Yamaha",
                modelo="MT-09 (QA TEST)",
                año=2024,
                precio=45000000.0,
                kilometraje=1200,
                ciudad="Bogotá",
                descripcion="Moto de prueba para Auditoría Multi-Agente de Traspaso Express.",
                propietario_id=user.id,
                commission_fee=350000.0,
                commission_paid=True, # Importante para habilitar el botón de Traspaso
                estado="activa",
                image_url="https://images.unsplash.com/photo-1558981403-c5f91ebafc08?q=80&w=1000&auto=format&fit=crop"
            )
            db.add(moto)
            db.commit()
            print(f"✅ Moto de prueba (Bogotá) creada para {email}")
        else:
            print("ℹ️ Moto de prueba ya existe.")

    except Exception as e:
        print(f"❌ Error setting up test environment: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    setup_test_environment()
