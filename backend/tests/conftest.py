import os

import pytest

os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "sqlite:///./taskflow-test.db")
os.environ["JWT_SECRET"] = "test-secret-not-for-production"

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    response = client.post("/auth/login", json={"username": "demo_admin", "password": "Demo123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

