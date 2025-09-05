# backend/tests/test_security.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user():
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test123!@#"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_rate_limit():
    for i in range(35):
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrong"
        })
    
    assert response.status_code == 429

def test_jwt_required():
    response = client.get("/api/chat/messages")
    assert response.status_code == 401

def test_input_sanitization():
    response = client.post("/api/chat/send", json={
        "content": "<script>alert('xss')</script>",
        "provider": "groq"
    })
    # Should sanitize the input
    assert "<script>" not in response.json().get("content", "")