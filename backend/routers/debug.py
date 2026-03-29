from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    try:
        # Check tables
        tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()
        
        # Check columns of 'motos'
        motos_cols = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='motos'")).fetchall()
        
        # Check columns of 'tramites'
        tramites_cols = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='tramites'")).fetchall()
        
        return {
            "status": "connected",
            "tables": [t[0] for t in tables],
            "motos_columns": [c[0] for c in motos_cols],
            "tramites_columns": [c[0] for c in tramites_cols]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
