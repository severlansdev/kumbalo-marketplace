import asyncio
import httpx
import time
from typing import List

# Configuración del Stress Test
BASE_URL = "http://127.0.0.1:8000/api/v1/runt"
ENDPOINTS = [
    "/consulta/GOG05E",
    "/consulta/ABC12D",
    "/consulta/XYZ789",
    "/consulta/KUM001",
    "/consulta/KUM002"
]
CONCURRENT_REQUESTS = 10 # Número de ráfagas simultáneas

async def call_endpoint(client: httpx.AsyncClient, endpoint: str, request_id: int):
    """
    Realiza una consulta individual al ADN Vehicular.
    """
    start_time = time.time()
    try:
        response = await client.get(f"{BASE_URL}{endpoint}")
        duration = (time.time() - start_time) * 1000
        status = response.status_code
        data = response.json()
        print(f"[REQ {request_id}] {endpoint} | Status: {status} | Time: {duration:.2f}ms | Fuente: {data.get('fuente', 'N/A')}")
        return duration
    except Exception as e:
        print(f"[REQ {request_id}] {endpoint} | FAILED: {str(e)}")
        return None

async def run_stress_test():
    """
    Ejecuta el test de estrés concurrente.
    """
    print(f"🚀 Iniciando Prueba de Estrés: {CONCURRENT_REQUESTS} consultas concurrentes...")
    print("-" * 60)
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(CONCURRENT_REQUESTS):
            endpoint = ENDPOINTS[i % len(ENDPOINTS)]
            tasks.append(call_endpoint(client, endpoint, i + 1))
        
        results = await asyncio.gather(*tasks)
        
    valid_results = [r for r in results if r is not None]
    if valid_results:
        avg_time = sum(valid_results) / len(valid_results)
        print("-" * 60)
        print(f"✅ Prueba Finalizada")
        print(f"📊 Promedio de respuesta: {avg_time:.2f}ms")
        print(f"🔥 Total exitosas: {len(valid_results)}/{CONCURRENT_REQUESTS}")
    else:
        print("❌ Todas las peticiones fallaron. Asegúrate de que el servidor esté corriendo en localhost:8000.")

if __name__ == "__main__":
    try:
        asyncio.run(run_stress_test())
    except KeyboardInterrupt:
        pass
