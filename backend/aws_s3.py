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
    
    # Fallback image if everything else fails
    placeholder_url = f"https://images.unsplash.com/photo-1558981403-c5f91ebafc08?q=80&w=1000&auto=format&fit=crop"

    # Fallback a almacenamiento local si no hay credenciales de AWS o no está boto3
    if not boto3 or not access_key or "YOUR_AWS" in access_key or not bucket_name:
        print("⚠️ AWS S3 no configurado. Intentando almacenamiento local...")
        try:
            upload_dir = "uploads"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                
            unique_filename = f"{uuid.uuid4()}-{filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            with open(file_path, "wb") as buffer:
                buffer.write(file_obj.read())
                file_obj.seek(0)
            return f"/uploads/{unique_filename}"
        except Exception as e:
            print(f"⚠️ Error en local fallback: {e}. Usando placeholder.")
            return placeholder_url

    s3_client = get_s3_client()
    unique_filename = f"{uuid.uuid4()}-{filename}"
    
    try:
        s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            unique_filename,
            ExtraArgs={"ContentType": content_type}
        )
        region = os.getenv("AWS_REGION", "us-east-1")
        return f"https://{bucket_name}.s3.{region}.amazonaws.com/{unique_filename}"
    except Exception as e:
        print(f"❌ Error subiendo a S3: {e}. Reintentando con local o placeholder...")
        try:
            return upload_image_to_s3_local(file_obj, filename)
        except:
            return placeholder_url

def upload_image_to_s3_local(file_obj, filename: str) -> str:
    placeholder_url = f"https://images.unsplash.com/photo-1558981403-c5f91ebafc08?q=80&w=1000&auto=format&fit=crop"
    try:
        upload_dir = "frontend/uploads"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        unique_filename = f"{uuid.uuid4()}-{filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file_obj.read())
            file_obj.seek(0)
        return f"/uploads/{unique_filename}"
    except:
        return placeholder_url
