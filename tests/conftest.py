import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.security import get_db as security_get_db  # 👈 IMPORTANT
from tests.database_test import engine_test, override_get_db

# Création des tables SQLite
Base.metadata.create_all(bind=engine_test)

# 🔥 Override PARTOUT
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[security_get_db] = override_get_db  # 👈 LA CLÉ


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    client.post(
        "/users/register",
        json={
            "email": "test@test.com",
            "password": "password123"
        }
    )

    response = client.post(
        "/users/login",
        data={
            "username": "test@test.com",
            "password": "password123"
        }
    )

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }
