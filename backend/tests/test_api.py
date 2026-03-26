"""
KUMBALO Backend Test Suite
Run with: pytest backend/tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


# ============ HEALTH CHECK ============

def test_health_check():
    """Test that health endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "kumbalo-api"
    assert "version" in data


def test_root():
    """Test that root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


# ============ AUTH ============

def test_register_user():
    """Test user registration with valid data."""
    response = client.post("/auth/register", json={
        "nombre": "Test User",
        "email": "test@kumbalo.com",
        "password": "SecurePass123!"
    })
    # Should either succeed (201) or conflict if user already exists (400)
    assert response.status_code in [200, 201, 400]


def test_register_user_invalid_email():
    """Test that invalid email is rejected."""
    response = client.post("/auth/register", json={
        "nombre": "Test User",
        "email": "not-an-email",
        "password": "SecurePass123!"
    })
    assert response.status_code == 422  # Validation error


def test_register_user_short_password():
    """Test that short passwords are rejected."""
    response = client.post("/auth/register", json={
        "nombre": "Test User",
        "email": "short@kumbalo.com",
        "password": "123"
    })
    assert response.status_code == 422  # Validation error


def test_login_wrong_credentials():
    """Test that wrong credentials return 401."""
    response = client.post("/auth/login", data={
        "username": "nonexistent@kumbalo.com",
        "password": "wrongpassword"
    })
    assert response.status_code in [401, 400]


# ============ MOTOS ============

def test_list_motos():
    """Test listing motos returns a list."""
    response = client.get("/motos/?skip=0&limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_motos_with_filters():
    """Test listing motos with brand filter."""
    response = client.get("/motos/?marca=yamaha&limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_moto_not_found():
    """Test getting a non-existent moto returns 404."""
    response = client.get("/motos/99999")
    assert response.status_code == 404


def test_create_moto_unauthorized():
    """Test that creating a moto without auth returns 401."""
    response = client.post("/motos/", json={
        "marca": "Yamaha",
        "modelo": "MT-03",
        "año": 2024,
        "precio": 18000000,
    })
    assert response.status_code in [401, 403, 422]


# ============ SWAGGER DOCS ============

def test_swagger_docs():
    """Test that Swagger UI is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_json():
    """Test that OpenAPI schema is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "KUMBALO API"


# ============ PROMETHEUS METRICS ============

def test_metrics_endpoint():
    """Test that Prometheus metrics are exposed."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text or "http_request" in response.text
