import boto3
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )

def upload_image_to_s3(file_obj, filename: str, content_type: str) -> str:
    bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    
    # Fallback a almacenamiento local si no hay credenciales de AWS reales
    if not access_key or "YOUR_AWS" in access_key or not bucket_name:
        print("⚠️ AWS S3 no configurado. Usando almacenamiento local (uploads/)")
        upload_dir = "uploads"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        unique_filename = f"{uuid.uuid4()}-{filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            # Si file_obj es un file pointer (SpooledTemporaryFile)
            buffer.write(file_obj.read())
            # Importante: reiniciar el puntero por si se necesita leer después (aunque aquí ya se subió)
            file_obj.seek(0)
            
        # En local devolvemos la ruta relativa servida por el backend o el nombre del archivo
        # Para Vercel/Producción esto debería ser una URL completa, pero para fix "ya" servirá.
        return f"/uploads/{unique_filename}"

    s3_client = get_s3_client()
    
    # Generar un nombre único para evitar colisiones
    unique_filename = f"{uuid.uuid4()}-{filename}"
    
    # Subir a S3
    try:
        s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            unique_filename,
            ExtraArgs={"ContentType": content_type}
        )
        
        # Construir la URL pública del bucket
        region = os.getenv("AWS_REGION", "us-east-1")
        url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{unique_filename}"
        return url
    except Exception as e:
        print(f"❌ Error subiendo a S3: {e}. Reintentando con local fallback...")
        # Fallback si falla la subida a S3 por cualquier razón (permisos, etc)
        return upload_image_to_s3_local(file_obj, filename)

def upload_image_to_s3_local(file_obj, filename: str) -> str:
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    unique_filename = f"{uuid.uuid4()}-{filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file_obj.read())
        file_obj.seek(0)
    return f"/uploads/{unique_filename}"
