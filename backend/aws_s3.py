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
    
    # Placeholders de alta calidad
    placeholders = [
        "https://images.unsplash.com/photo-1558981403-c5f91ebafc08?q=80&w=1000&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?q=80&w=1000&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1449495169669-7b118f960237?q=80&w=1000&auto=format&fit=crop"
    ]
    import random
    default_placeholder = random.choice(placeholders)

    # Si estamos en Vercel y no hay S3, ir directo a placeholder
    if os.getenv("VERCEL") == "1" and (not access_key or "YOUR_AWS" in access_key):
        return default_placeholder

    # Fallback a almacenamiento local si no hay S3
    if not boto3 or not access_key or "YOUR_AWS" in access_key or not bucket_name:
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
            return default_placeholder

    s3_client = get_s3_client()
    unique_filename = f"{uuid.uuid4()}-{filename}"
    try:
        s3_client.upload_fileobj(file_obj, bucket_name, unique_filename, ExtraArgs={"ContentType": content_type})
        region = os.getenv("AWS_REGION", "us-east-1")
        return f"https://{bucket_name}.s3.{region}.amazonaws.com/{unique_filename}"
    except:
        return default_placeholder

def upload_image_to_s3_local(file_obj, filename: str) -> str:
    return upload_image_to_s3(file_obj, filename, "image/jpeg")
