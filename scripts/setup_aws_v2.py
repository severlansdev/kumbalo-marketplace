import os
import boto3
import json
from dotenv import load_dotenv, set_key

# Cargar variables de entorno del archivo .env local
load_dotenv()

# 1. Configuración de credenciales (EXTRAER DE .ENV POR SEGURIDAD)
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME", "kumbalo-motos-imagenes")
REGION = os.getenv("AWS_REGION", "us-east-1")

ENV_PATH = ".env"

def setup_aws():
    print(f"--- Iniciando configuracion automatica de AWS para Kumbalo ---")
    
    # Actualizar .env
    if os.path.exists(ENV_PATH):
        set_key(ENV_PATH, "AWS_ACCESS_KEY_ID", ACCESS_KEY)
        set_key(ENV_PATH, "AWS_SECRET_ACCESS_KEY", SECRET_KEY)
        set_key(ENV_PATH, "AWS_REGION", REGION)
        set_key(ENV_PATH, "AWS_S3_BUCKET_NAME", BUCKET_NAME)
        print("Archivo .env actualizado con las nuevas credenciales.")
    else:
        print("El archivo .env no existe. Creando uno nuevo...")
        with open(ENV_PATH, "w") as f:
            f.write(f"AWS_ACCESS_KEY_ID={ACCESS_KEY}\n")
            f.write(f"AWS_SECRET_ACCESS_KEY={SECRET_KEY}\n")
            f.write(f"AWS_REGION={REGION}\n")
            f.write(f"AWS_S3_BUCKET_NAME={BUCKET_NAME}\n")

    # Configurar Política de Bucket para Acceso Público
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name=REGION
        )
        
        # Desactivar Bloqueo de Acceso Público (Paso necesario antes de la política)
        print("Desactivando bloqueo de acceso público...")
        s3.put_public_access_block(
            Bucket=BUCKET_NAME,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )

        # Aplicar Política de Lectura Pública
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*"
                }
            ]
        }
        
        print(f"Aplicando politica de acceso publico al bucket {BUCKET_NAME}...")
        s3.put_bucket_policy(Bucket=BUCKET_NAME, Policy=json.dumps(bucket_policy))
        print("Politica de bucket configurada exitosamente.")
        
        # Prueba de conexión
        print("Realizando prueba de conexion...")
        s3.list_objects(Bucket=BUCKET_NAME, MaxKeys=1)
        print("TODO LISTO! Kumbalo ahora puede subir fotos reales a AWS S3.")

    except Exception as e:
        print(f"Error configurando AWS: {e}")

if __name__ == "__main__":
    setup_aws()
