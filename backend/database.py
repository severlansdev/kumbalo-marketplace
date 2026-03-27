from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# We construct the URL from env variables (Vercel uses POSTGRES_URL or STORAGE_URL)
DATABASE_URL = os.getenv("POSTGRES_URL", os.getenv("STORAGE_URL", os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/marketplace")))

# Vercel's postgres:// needs to be changed to postgresql:// for SQLAlchemy if it's not already
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# For databases like Supabase/Postgres, we might need SSL
connect_args = {}
if "postgresql" in DATABASE_URL:
    connect_args = {"sslmode": "require"}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency handler for routing
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
