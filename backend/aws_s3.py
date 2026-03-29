try:
    import boto3
except ImportError:
    boto3 = None

import os
import uuid
from dotenv import load_dotenv

load_dotenv()

def get_s3_client():
    if not boto3:
        return None
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )

def upload_image_to_s3(file_obj, filename: str, content_type: str) -> str:
    bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    
    # Placeholders de alta calidad (IDs verificados de motos premium)
    placeholders = [
        "https://images.unsplash.com/photo-1558363196-03c03ec34190?q=80&w=1000&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1568772589808-62ea49939c23?q=80&w=1000&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1449495169669-7b118f960237?q=80&w=1000&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?q=80&w=1000&auto=format&fit=crop"
    ]
    import random
    default_placeholder = random.choice(placeholders)

    # Si estamos en Vercel y no hay S3 configurado, evitamos intentar guardar localmente (fallará)
    is_vercel = os.getenv("VERCEL") == "1"
    has_s3 = access_key and "YOUR_AWS" not in access_key and bucket_name
    
    if is_vercel and not has_s3:
        return default_placeholder

    # Fallback a almacenamiento local si no hay S3 (solo útil en desarrollo local)
    if not has_s3:
        try:
            upload_dir = "frontend/uploads"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            unique_filename = f"{uuid.uuid4()}-{filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            with open(file_path, "wb") as buffer:
                buffer.write(file_obj.read())
                file_obj.seek(0)
            
            # Devolver URL absoluta para evitar problemas de rutas relativas en el frontend
            base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            # Si la URL termina en /api, la quitamos para que apunte a la raíz si los estáticos se sirven ahí
            if base_url.endswith("/api"):
                base_url = base_url[:-4]
            
            return f"{base_url}/uploads/{unique_filename}"
        except Exception as e:
            print(f"Error en guardado local: {e}")
            return default_placeholder

    s3_client = get_s3_client()
    unique_filename = f"{uuid.uuid4()}-{filename}"
    try:
        s3_client.upload_fileobj(file_obj, bucket_name, unique_filename, ExtraArgs={"ContentType": content_type})
        region = os.getenv("AWS_REGION", "us-east-1")
        return f"https://{bucket_name}.s3.{region}.amazonaws.com/{unique_filename}"
    except Exception as e:
        print(f"Error subiendo a S3: {e}")
        return default_placeholder

def upload_image_to_s3_local(file_obj, filename: str) -> str:
    return upload_image_to_s3(file_obj, filename, "image/jpeg")
