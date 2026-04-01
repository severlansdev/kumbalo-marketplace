import os
import sys
from io import BytesIO
from dotenv import load_dotenv

# Asegurar que el sistema reconozca el módulo backend
sys.path.append(os.getcwd())

load_dotenv()

from backend.aws_s3 import upload_image_to_s3

def test_kumbalo_s3():
    print("--- Iniciando Prueba de Subida a Kumbalo S3 Real ---")
    
    # Simular una imagen de prueba (un pequeño buffer binario)
    dummy_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdcG\x01\xf4\x00\x00\x00\x00IEND\xaeB`\x82"
    file_obj = BytesIO(dummy_data)
    
    filename = "test-kumbalo-moto.png"
    content_type = "image/png"
    
    try:
        print(f"Subiendo '{filename}' a S3...")
        # Invocamos la función real que usa boto3
        url = upload_image_to_s3(file_obj, filename, content_type)
        
        if ".amazonaws.com" in url:
            print(f"PRUEBA EXITOSA!")
            print(f"Imagen subida a: {url}")
            print("\nNOTA: Si al abrir el link te da 'Access Denied', recuerda aplicar la política public-read que te pasé anteriormente.")
        else:
            print(f"ADVERTENCIA!")
            print(f"URL retornada: {url}")
            print("El sistema podría estar en modo Fallback (Unsplash) si las credenciales fallaron internamente.")
            
    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")

if __name__ == "__main__":
    test_kumbalo_s3()
