import os
import sys

# Asegurar que los imports relativos al backend funcionen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal, engine
from backend import models
from datetime import datetime, timedelta

def run_tests():
    db = SessionLocal()
    print("🚀 Iniciando Auditoría de Integridad en Ecosistema Bursátil (BaaS) de Kumbalo...")
    try:
        # 1. SETUP DE DATOS DUMMY
        # Vendedor de Moto Alta Gama
        u_vendedor = models.Usuario(
            nombre="Alvaro Vendedor", 
            email="alvaro.test.fintech@kumbalo.com", 
            hashed_password="hash", 
            telefono="111111111"
        )
        # Comprador (Concesionario)
        u_concesionario = models.Usuario(
            nombre="AutoTest Motors (Concesionario)", 
            email="concesionario.test@automotors.com", 
            hashed_password="hash", 
            telefono="222222222", 
            tipo_cuenta="concesionario",
            is_pro=True
        )
        db.add(u_vendedor)
        db.add(u_concesionario)
        db.flush() # Obtener IDs sin commitear aún

        # Moto VIP de Vendedor (Ducati)
        m_ducati = models.Moto(
            propietario_id=u_vendedor.id,
            marca="Ducati",
            modelo="Panigale V4",
            año=2023,
            precio=120000000,
            kilometraje=2500,
            cilindraje=1103,
            ciudad="Bogotá",
            placa="DUC123",
            commission_paid=True
        )
        # Moto del Concesionario/Usuario normal (Ninja 400)
        m_ninja = models.Moto(
            propietario_id=u_concesionario.id,
            marca="Kawasaki",
            modelo="Ninja 400",
            año=2022,
            precio=35000000,
            kilometraje=8000,
            cilindraje=399,
            ciudad="Bogotá",
            placa="NIN321",
            commission_paid=True
        )
        db.add(m_ducati)
        db.add(m_ninja)
        db.flush()

        # ==========================================
        # PRUEBA A: SALA DE SUBASTAS B2B
        # ==========================================
        print("\n🔍 Test A: Creando Subasta C2B...")
        subasta = models.SubastaMoto(
            moto_id=m_ducati.id,
            vendedor_id=u_vendedor.id,
            precio_minimo=100000000,
            mejor_oferta=100000000,
            fecha_fin=datetime.now() + timedelta(hours=24)
        )
        db.add(subasta)
        db.flush()

        print("🔍 Test A.1: Concesionario emitiendo Puja (110.000.000 COP)...")
        puja = models.HistorialPuja(
            subasta_id=subasta.id,
            postor_id=u_concesionario.id,
            monto=110000000
        )
        db.add(puja)
        # Actualizando subasta
        subasta.mejor_oferta = 110000000
        subasta.concesionario_ganador_id = u_concesionario.id
        db.flush()

        assert puja.id is not None, "Fallo en inserción de HistorialPuja"
        assert subasta.ganador.email == "concesionario.test@automotors.com", "Relación Ganador-Subasta Rota"
        print("✅ [EXITO] Motor de Subastas Live operando a nivel de base de datos.")


        # ==========================================
        # PRUEBA B: PERMUTAS (SMART TRADE-INS)
        # ==========================================
        print("\n🔍 Test B: Emisión de Permuta C2C (Double Escrow)...")
        oferta_permuta = models.OfertaPermuta(
            oferente_id=u_concesionario.id,
            receptor_id=u_vendedor.id,
            moto_ofrecida_id=m_ninja.id,
            moto_objetivo_id=m_ducati.id,
            excedente=75000000 # Ninja(35M) + Excedente(75M) = 110M
        )
        db.add(oferta_permuta)
        db.flush()
        
        assert oferta_permuta.id is not None, "Fallo en inserción de OfertaPermuta"
        assert oferta_permuta.moto_ofrecida.marca == "Kawasaki", "Fallo relación Moto Ofrecida"
        assert oferta_permuta.receptor.nombre == "Alvaro Vendedor", "Fallo relación Receptor"
        print("✅ [EXITO] Motor de Permutas C2C con relaciones duales funcionando.")
        
        # Simulamos rechazar permuta (no queremos guardar datos de prueba en BD)
        oferta_permuta.estado = "rechazada"
        
        # NO COMMIT (evitamos ensuciar la base de datos de producción con data dummy)
        db.rollback() 
        print("\n🧹 Auditoría superada. Rollback ejecutado para limpiar datos temporales de la base de datos (Zero Residues).")

    except Exception as e:
        db.rollback()
        print(f"\n❌ [ERROR CRÍTICO] Hubo una falla de integridad referencial SQL: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
