from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Load .env only if dotenv is available (local dev)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# We construct the URL from env variables (Vercel uses POSTGRES_URL or STORAGE_URL)
DATABASE_URL = os.getenv("POSTGRES_URL", os.getenv("STORAGE_URL", os.getenv("DATABASE_URL", "sqlite:///./test.db")))

# Vercel's postgres:// needs to be changed to postgresql+pg8000:// for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+pg8000://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+pg8000" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)

# Clean problematic query parameters for pg8000
if "pg8000" in DATABASE_URL and "?" in DATABASE_URL:
    base_url, query = DATABASE_URL.split("?", 1)
    # We strip common problematic params for pg8000
    params = [p for p in query.split("&") if not any(x in p for x in ["sslmode", "channel_binding"])]
    DATABASE_URL = base_url + ("?" + "&".join(params) if params else "")

# Build engine with appropriate arguments
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}
elif "pg8000" in DATABASE_URL:
    # Solo aplicamos SSL si NO es una conexión local (Docker o localhost)
    is_local = "db:" in DATABASE_URL or "localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL
    if not is_local:
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args = {"ssl_context": ssl_context}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency handler for routing
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
