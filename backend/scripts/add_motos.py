"""
Script ultra-robusto usando SQL puro (con SQLAlchemy.text) para agregar motos.
Esto evita que SQLAlchemy intente mapear columnas que no existen en la base de datos actual.
"""
import sys
import os
from sqlalchemy import text

# Asegurar que el path del backend esté en sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.database import SessionLocal
    from passlib.context import CryptContext
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from database import SessionLocal
    from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def add_motos():
    db = SessionLocal()
    
    try:
        # 1. Asegurar Vendedor Demo
        email_vendedor = "vendedor@demo.com"
        res = db.execute(text("SELECT id FROM usuarios WHERE email = :email"), {"email": email_vendedor}).fetchone()
        
        if not res:
            print("Creando vendedor demo con SQL puro...")
            hashed_pwd = get_password_hash("123456")
            db.execute(
                text("INSERT INTO usuarios (nombre, email, hashed_password, is_active) VALUES (:nombre, :email, :pwd, :active)"),
                {"nombre": "Alfonso Vendedor", "email": email_vendedor, "pwd": hashed_pwd, "active": True}
            )
            db.commit()
            vendedor_id = db.execute(text("SELECT id FROM usuarios WHERE email = :email"), {"email": email_vendedor}).fetchone()[0]
            print(f"✅ Vendedor creado con ID: {vendedor_id}")
        else:
            vendedor_id = res[0]
            print(f"ℹ️ Vendedor demo ya existe (ID: {vendedor_id})")

        # 2. Datos de las motos
        motos_data = [
            {
                "marca": "Yamaha",
                "modelo": "MT-09 2024",
                "año": 2024,
                "precio": 62000000,
                "kilometraje": 5385,
                "descripcion": "Increíble potencia y agilidad. Modelo 2024 en perfecto estado, poco uso (5,385km). Cilindraje 890cc. Color Tech Black / Cyan Storm. Ubicada en Medellín.",
                "image_url": "https://images.unsplash.com/photo-1558981806-ec527fa84c39?q=80&w=800"
            },
            {
                "marca": "Yamaha",
                "modelo": "YZF R6R",
                "año": 2016,
                "precio": 48000000,
                "kilometraje": 20000,
                "descripcion": "Leyenda de las pistas. Modelo 2016 con solo 20,000 km. Mantenimiento reciente, SOAT vigente. Sonido espectacular. Cilindraje 599cc. Color Race Blu. Ubicada en Bogotá.",
                "image_url": "https://images.unsplash.com/photo-1614165933385-cad0069e26f5?q=80&w=800"
            },
            {
                "marca": "Kawasaki",
                "modelo": "Z900",
                "año": 2024,
                "precio": 60000000,
                "kilometraje": 10700,
                "descripcion": "La definición de Sugomi. Potencia bruta y suavidad japonesa. Único dueño, llantas nuevas, nunca chocada. Cilindraje 948cc. Color Verde/Negro. Ubicada en Cali.",
                "image_url": "https://images.unsplash.com/photo-1591637333184-19aa84b3e01f?q=80&w=800"
            },
            {
                "marca": "Ducati",
                "modelo": "Diavel V4",
                "año": 2024,
                "precio": 115000000,
                "kilometraje": 2500,
                "descripcion": "La muscle roadster definitiva. Diseño italiano agresivo con tecnología de punta. Motor V4 Granturismo 1158cc. Estado impecable. Color Ducati Red. Ubicada en Barranquilla.",
                "image_url": "https://images.unsplash.com/photo-1623072557451-f761fc7be7b6?q=80&w=800"
            }
        ]

        print(f"Insertando {len(motos_data)} motos nuevas...")
        count = 0
        for data in motos_data:
            exists = db.execute(
                text("SELECT id FROM motos WHERE marca = :m AND modelo = :mo AND año = :a"),
                {"m": data["marca"], "mo": data["modelo"], "a": data["año"]}
            ).fetchone()
            
            if not exists:
                db.execute(
                    text("""
                        INSERT INTO motos (marca, modelo, año, precio, kilometraje, descripcion, image_url, propietario_id) 
                        VALUES (:marca, :modelo, :anio, :precio, :km, :desc, :img, :prop_id)
                    """),
                    {
                        "marca": data["marca"],
                        "modelo": data["modelo"],
                        "anio": data["año"],
                        "precio": data["precio"],
                        "km": data["kilometraje"],
                        "desc": data["descripcion"],
                        "img": data["image_url"],
                        "prop_id": vendedor_id
                    }
                )
                count += 1
                print(f"✅ Agregada: {data['marca']} {data['modelo']}")
            else:
                print(f"⏩ Saltada (ya existe): {data['marca']} {data['modelo']}")

        db.commit()
        print(f"🚀 ¡Proceso completado! Se agregaron {count} nuevas motos.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la ejecución: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_motos()
