import os
import psycopg2

def migrate():
    url = os.getenv("POSTGRES_URL")
    if not url:
        print("POSTGRES_URL error")
        return
        
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    try:
        print("Añadiendo columnas de comisión...")
        cur.execute("ALTER TABLE motos ADD COLUMN IF NOT EXISTS commission_fee FLOAT DEFAULT 0.0;")
        cur.execute("ALTER TABLE motos ADD COLUMN IF NOT EXISTS commission_type VARCHAR(20) DEFAULT 'fixed';")
        conn.commit()
        print("Migración exitosa!")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
