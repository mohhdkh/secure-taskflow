from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.database import SessionLocal
from app.models import User
from app.security import JWT_ALGORITHM, JWT_SECRET


def bearer(payload: dict) -> dict[str, str]:
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


def valid_payload(user_id: int) -> dict:
    now = datetime.now(timezone.utc)
    return {"sub": str(user_id), "role": "member", "iat": now, "exp": now + timedelta(minutes=5)}


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"username": "ab", "password": "Member123!"}, "username"),
        ({"username": "member", "password": "short"}, "password"),
        ({"username": "   ", "password": "Member123!"}, "username"),
    ],
)
def test_login_rejects_invalid_input(client, body, field):
    response = client.post("/auth/login", json=body)

    assert response.status_code == 422
    assert any(error["loc"][-1] == field for error in response.json()["detail"])


def test_login_rejects_unknown_fields(client):
    response = client.post(
        "/auth/login",
        json={"username": "demo_admin", "password": "Demo123!", "is_admin": True},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


def test_login_handles_corrupted_password_hash_as_invalid_credentials(client):
    with SessionLocal() as db:
        db.add(User(username="corrupt-user", password_hash="not-an-argon2-hash", role="member"))
        db.commit()

    response = client.post("/auth/login", json={"username": "corrupt-user", "password": "Member123!"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_expired_token_is_rejected(client, user_factory):
    user = user_factory("expired-user")
    now = datetime.now(timezone.utc)
    headers = bearer(
        {"sub": str(user.id), "role": "member", "iat": now - timedelta(hours=2), "exp": now - timedelta(hours=1)}
    )

    response = client.get("/tasks", headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


@pytest.mark.parametrize("sub", [None, "not-a-number"])
def test_token_with_invalid_subject_is_rejected(client, sub):
    payload = valid_payload(1)
    if sub is None:
        payload.pop("sub")
    else:
        payload["sub"] = sub

    response = client.get("/tasks", headers=bearer(payload))

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_non_bearer_authentication_scheme_is_rejected(client):
    response = client.get("/tasks", headers={"Authorization": "Basic ZGVtbzpwYXNzd29yZA=="})

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "x"},
        {"title": "   "},
        {"title": "Valid task", "status": "archived"},
        {"title": "Valid task", "priority": "urgent"},
        {"title": "Valid task", "description": "x" * 1001},
        {"title": "Valid task", "owner_id": 999},
    ],
)
def test_create_task_rejects_invalid_or_server_owned_fields(client, auth_headers, payload):
    response = client.post("/tasks", headers=auth_headers, json=payload)

    assert response.status_code == 422


def test_update_rejects_invalid_fields_without_changing_task(client, auth_headers):
    created = client.post("/tasks", headers=auth_headers, json={"title": "Stable title"}).json()

    response = client.patch(
        f"/tasks/{created['id']}",
        headers=auth_headers,
        json={"status": "deleted", "owner_id": 999},
    )

    assert response.status_code == 422
    listed = client.get("/tasks", headers=auth_headers).json()
    stored = next(task for task in listed if task["id"] == created["id"])
    assert stored["title"] == "Stable title"
    assert stored["status"] == "todo"
    assert stored["owner_id"] == created["owner_id"]


@pytest.mark.parametrize("method", ["patch", "delete"])
def test_missing_task_returns_not_found(client, auth_headers, method):
    request = getattr(client, method)
    kwargs = {"json": {"status": "done"}} if method == "patch" else {}

    response = request("/tasks/999999", headers=auth_headers, **kwargs)

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
