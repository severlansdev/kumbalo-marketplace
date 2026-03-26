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
    s3_client = get_s3_client()
    
    # Generar un nombre único para evitar colisiones
    unique_filename = f"{uuid.uuid4()}-{filename}"
    
    # Subir a S3
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
