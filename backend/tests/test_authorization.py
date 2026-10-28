from app.database import SessionLocal
from app.models import User


def create_task(client, headers, title: str) -> dict:
    response = client.post(
        "/tasks",
        headers=headers,
        json={"title": title, "description": "Synthetic authorization fixture", "priority": "medium"},
    )
    assert response.status_code == 201
    return response.json()


def test_member_list_is_scoped_to_the_authenticated_owner(client, user_factory, headers_for):
    alice = user_factory("alice")
    bob = user_factory("bob")
    alice_task = create_task(client, headers_for(alice), "Alice private task")
    bob_task = create_task(client, headers_for(bob), "Bob private task")

    response = client.get("/tasks", headers=headers_for(alice))

    assert response.status_code == 200
    ids = {task["id"] for task in response.json()}
    assert alice_task["id"] in ids
    assert bob_task["id"] not in ids


def test_member_cannot_update_another_members_task(client, user_factory, headers_for):
    alice = user_factory("alice")
    bob = user_factory("bob")
    task = create_task(client, headers_for(alice), "Owned by Alice")

    response = client.patch(f"/tasks/{task['id']}", headers=headers_for(bob), json={"status": "done"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_member_cannot_delete_another_members_task(client, user_factory, headers_for):
    alice = user_factory("alice")
    bob = user_factory("bob")
    task = create_task(client, headers_for(alice), "Owned by Alice")

    response = client.delete(f"/tasks/{task['id']}", headers=headers_for(bob))

    assert response.status_code == 404
    assert client.patch(f"/tasks/{task['id']}", headers=headers_for(alice), json={"status": "doing"}).status_code == 200


def test_admin_can_manage_a_members_task(client, auth_headers, user_factory, headers_for):
    member = user_factory("member")
    task = create_task(client, headers_for(member), "Member task")

    response = client.patch(f"/tasks/{task['id']}", headers=auth_headers, json={"status": "done"})

    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_malformed_token_is_rejected(client):
    response = client.get("/tasks", headers={"Authorization": "Bearer not-a-valid-jwt"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_token_for_deleted_user_is_rejected(client, user_factory, headers_for):
    user = user_factory("departed-user")
    headers = headers_for(user)
    with SessionLocal() as db:
        stored = db.get(User, user.id)
        db.delete(stored)
        db.commit()

    response = client.get("/tasks", headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "User no longer exists"
