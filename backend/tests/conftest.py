import os

import pytest

os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "sqlite:///./taskflow-test.db")
os.environ["JWT_SECRET"] = "test-secret-not-for-production"

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import User
from app.security import create_token, hash_password


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


@pytest.fixture
def user_factory():
    def create(username: str, role: str = "member") -> User:
        with SessionLocal() as db:
            user = User(username=username, password_hash=hash_password("Member123!"), role=role)
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    return create


@pytest.fixture
def headers_for():
    def build(user: User) -> dict[str, str]:
        return {"Authorization": f"Bearer {create_token(user.id, user.role)}"}

    return build

