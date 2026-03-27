import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, Base
from backend import models

def sync_db():
    print("🚀 Sincronizando tablas en la base de datos de producción...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas sincronizadas con éxito (incluyendo TelegramHistory).")
    except Exception as e:
        print(f"❌ Error al sincronizar: {e}")

if __name__ == "__main__":
    sync_db()
