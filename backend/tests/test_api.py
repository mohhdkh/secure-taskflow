def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rejects_invalid_credentials(client):
    response = client.post("/auth/login", json={"username": "demo_admin", "password": "Wrong123!"})
    assert response.status_code == 401


def test_requires_authentication_for_tasks(client):
    assert client.get("/tasks").status_code == 401


def test_task_crud_workflow(client, auth_headers):
    created = client.post(
        "/tasks",
        headers=auth_headers,
        json={"title": "اختبار مسار جديد", "description": "بيانات تجريبية", "priority": "high"},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    listed = client.get("/tasks", headers=auth_headers)
    assert listed.status_code == 200
    assert any(task["id"] == task_id for task in listed.json())

    updated = client.patch(f"/tasks/{task_id}", headers=auth_headers, json={"status": "done"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"

    deleted = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert deleted.status_code == 204

