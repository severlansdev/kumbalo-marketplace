import pytest

def test_signup(client):
    response = client.post(
        "/auth/register",
        json={
            "nombre": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
            "telefono": "1234567890"
        }
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_login(client):
    # Register first
    client.post(
        "/auth/register",
        json={
            "nombre": "Login User",
            "email": "login@example.com",
            "password": "securepassword",
            "telefono": "0987654321"
        }
    )
    
    # Try to login
    response = client.post(
        "/auth/login",
        data={
            "username": "login@example.com",
            "password": "securepassword"
        }
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client):
    client.post(
        "/auth/register",
        json={
            "nombre": "Wrong Pass",
            "email": "wrongpass@example.com",
            "password": "correctpassword",
            "telefono": "123123123"
        }
    )
    
    response = client.post(
        "/auth/login",
        data={
            "username": "wrongpass@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
