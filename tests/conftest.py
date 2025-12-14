import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from tests.database_test import engine_test, override_get_db

# Créer les tables UNE FOIS pour les tests
Base.metadata.create_all(bind=engine_test)

# Override FastAPI dependency
app.dependency_overrides[get_db] = override_get_db


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
