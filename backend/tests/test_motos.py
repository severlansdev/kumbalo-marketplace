import pytest
from unittest.mock import patch
from io import BytesIO

def test_subir_moto_mock_s3(client):
    # Register and login first to get a token
    client.post("/auth/register", json={
        "nombre": "S3 User",
        "email": "s3@example.com",
        "password": "s3password",
        "telefono": "12341234"
    })
    
    login_resp = client.post("/auth/login", data={"username": "s3@example.com", "password": "s3password"})
    token = login_resp.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Mock AWS S3 upload
    with patch("backend.routers.motos.upload_image_to_s3", return_value="https://mocked-s3-url.com/moto.jpg") as mock_upload:
        # Simulate file upload
        file_data = {
            "marca": (None, "Honda"),
            "modelo": (None, "CBR500R"),
            "año": (None, "2021"),
            "precio": (None, "30000000"),
            "kilometraje": (None, "5000"),
            "descripcion": (None, "Excelente estado"),
            "foto": ("dummy.jpg", BytesIO(b"dummy image data"), "image/jpeg")
        }

        
        response = client.post("/motos/", headers=headers, files=file_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["marca"] == "Honda"
        assert data["image_url"] == "https://mocked-s3-url.com/moto.jpg"
        
        mock_upload.assert_called_once()
