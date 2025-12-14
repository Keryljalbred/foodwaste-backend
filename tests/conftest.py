# backend/tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    # 1. Créer un utilisateur de test
    client.post(
        "/users/register",
        json={
            "email": "test@test.com",
            "password": "password123"
        }
    )

    # 2. Login pour récupérer le token
    response = client.post(
        "/users/login",
        data={
            "username": "test@test.com",
            "password": "password123"
        }
    )

    token = response.json().get("access_token")

    return {
        "Authorization": f"Bearer {token}"
    }
