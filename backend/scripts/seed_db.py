"""
Script para poblar la base de datos con datos semilla (Seeder).
Ejecutar desde el directorio backend: python -m scripts.seed_db
"""
import sys
import os

# Asegurar que el path del backend esté en sys.path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.database import SessionLocal, engine, Base
    from backend import models
    from backend.routers.auth import get_password_hash
except ImportError:
    # Si se corre desde dentro de la carpeta backend
    sys.path.append(os.path.dirname(os.path.abspath(__line__)))
    from database import SessionLocal, engine, Base
    import models
    from routers.auth import get_password_hash

def seed():
    print("Creando tablas si no existen...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    print("Limpiando datos antiguos (opcional)...")
    # Para ser un seeder seguro, solo insertamos si no hay usuarios.
    if db.query(models.Usuario).count() > 0:
        print("La base de datos ya contiene datos. Saltando seeder para evitar duplicados.")
        db.close()
        return

    print("Insertando usuarios demo...")
    usuarios = [
        models.Usuario(
            nombre="Alfonso Vendedor",
            email="vendedor@demo.com",
            telefono="3001234567",
            hashed_password=get_password_hash("123456")
        ),
        models.Usuario(
            nombre="Maria Compradora",
            email="compradora@demo.com",
            telefono="3209876543",
            hashed_password=get_password_hash("123456")
        )
    ]
    db.add_all(usuarios)
    db.commit()

    print("Insertando motos demo...")
    vendedor_id = db.query(models.Usuario).filter(models.Usuario.email == "vendedor@demo.com").first().id
    
    motos = [
        models.Moto(
            marca="Yamaha",
            modelo="MT-09",
            anio=2023,
            precio=45000000,
            kilometraje=5000,
            cilindrada="890cc",
            color="Gris/Cyan",
            descripcion="Moto en excelente estado, único dueño. Mantenimientos al día en concesionario Yamaha.",
            imagen_url="https://images.unsplash.com/photo-1568772585407-9361f9b6a7dc?auto=format&fit=crop&q=80&w=800",
            propietario_id=vendedor_id
        ),
        models.Moto(
            marca="Kawasaki",
            modelo="Ninja 400",
            anio=2022,
            precio=28000000,
            kilometraje=12000,
            cilindrada="399cc",
            color="Verde/Negro",
            descripcion="Perfecta para empezar en el mundo deportivo. Ninguna caída, llantas al 80%.",
            imagen_url="https://images.unsplash.com/photo-1449426468159-d9d5194eb24f?auto=format&fit=crop&q=80&w=800",
            propietario_id=vendedor_id
        ),
        models.Moto(
            marca="BMW",
            modelo="R 1250 GS",
            anio=2024,
            precio=115000000,
            kilometraje=1500,
            cilindrada="1254cc",
            color="Trophy",
            descripcion="La reina del Adventure. Casi nueva, con todos los paquetes (Dynamic, Touring, Lights).",
            imagen_url="https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&q=80&w=800",
            propietario_id=vendedor_id
        )
    ]
    
    db.add_all(motos)
    db.commit()
    
    print("✅ ¡Seeder ejecutado con éxito! Se insertaron usuarios y motos de la vida real.")
    db.close()

if __name__ == "__main__":
    seed()
