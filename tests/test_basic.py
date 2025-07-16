"""
Basic tests to verify the application setup
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import check_db_connection

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "version" in data

def test_database_connection():
    """Test database connection"""
    assert check_db_connection() == True

def test_root_endpoint():
    """Test the root endpoint returns HTML"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_api_docs():
    """Test API documentation is accessible"""
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_openapi_json():
    """Test OpenAPI JSON schema is accessible"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "AI Investment Tool"