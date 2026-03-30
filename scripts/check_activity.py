
import os
import sys
# Adicionar el directorio backend al path para que funcionen los imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

try:
    from database import SessionLocal
    from models import BacklogAgente, TelegramHistory, Tramite, Moto
    from sqlalchemy import desc
    from datetime import datetime, timedelta

    db = SessionLocal()
    
    print("--- ULTIMAS TAREAS DEL BACKLOG DE AGENTES ---")
    tasks = db.query(BacklogAgente).order_by(desc(BacklogAgente.created_at)).limit(5).all()
    if not tasks:
        print("No hay tareas en el backlog.")
    for t in tasks:
        print(f"[{t.created_at}] Agente: {t.agente_asignado} | Petición: {t.peticion[:50]}... | Estado: {t.estado}")

    print("\n--- ULTIMA ACTIVIDAD DE TELEGRAM / CHAT ---")
    chat = db.query(TelegramHistory).order_by(desc(TelegramHistory.created_at)).limit(5).all()
    if not chat:
        print("No hay historial de chat.")
    for c in chat:
        print(f"[{c.created_at}] {c.role}: {c.content[:50]}...")

    print("\n--- ULTIMOS TRAMITES SOLICITADOS ---")
    tramites = db.query(Tramite).order_by(desc(Tramite.created_at)).limit(3).all()
    if not tramites:
        print("No hay trámites recientes.")
    for tr in tramites:
        print(f"[{tr.created_at}] Trámite ID: {tr.id} | Estado: {tr.estado} | Tipo: {tr.tipo}")

    db.close()
except Exception as e:
    print(f"Error al consultar la base de datos: {e}")
