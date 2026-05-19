"""Unit tests for the /users CRUD endpoints."""

from fastapi.testclient import TestClient

USER_PAYLOAD = {
    "username": "alice",
    "email": "alice@example.com",
    "full_name": "Alice Wonderland",
}


# ---------------------------------------------------------------------------
# List  (GET /users)
# ---------------------------------------------------------------------------


def test_list_users_empty(client: TestClient) -> None:
    """GET /users on an empty store returns an empty list."""
    response = client.get("/users")
    assert response.status_code == 200
    assert response.json() == []


def test_list_users_returns_created_user(client: TestClient) -> None:
    """After creating a user, GET /users should include them."""
    client.post("/users", json=USER_PAYLOAD)
    response = client.get("/users")
    assert len(response.json()) == 1


def test_list_users_multiple(client: TestClient) -> None:
    """Creating two users should result in two entries."""
    client.post("/users", json=USER_PAYLOAD)
    client.post("/users", json={**USER_PAYLOAD, "username": "bob", "email": "bob@example.com"})
    response = client.get("/users")
    assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# Get by ID  (GET /users/{id})
# ---------------------------------------------------------------------------


def test_get_user_by_id(client: TestClient) -> None:
    """GET /users/{id} returns the correct user."""
    created = client.post("/users", json=USER_PAYLOAD).json()
    response = client.get(f"/users/{created['id']}")
    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_get_user_not_found(client: TestClient) -> None:
    """GET /users/9999 returns 404."""
    response = client.get("/users/9999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Create  (POST /users)
# ---------------------------------------------------------------------------


def test_create_user_returns_201(client: TestClient) -> None:
    """POST /users should respond with HTTP 201."""
    response = client.post("/users", json=USER_PAYLOAD)
    assert response.status_code == 201


def test_create_user_is_active_by_default(client: TestClient) -> None:
    """Newly created users should have is_active=True."""
    response = client.post("/users", json=USER_PAYLOAD)
    assert response.json()["is_active"] is True


def test_create_user_persists_email(client: TestClient) -> None:
    """Email passed in POST /users should be returned unchanged."""
    response = client.post("/users", json=USER_PAYLOAD)
    assert response.json()["email"] == "alice@example.com"


def test_create_user_short_username_returns_422(client: TestClient) -> None:
    """A username shorter than 3 characters should fail validation."""
    bad_payload = {**USER_PAYLOAD, "username": "ab"}
    response = client.post("/users", json=bad_payload)
    assert response.status_code == 422


def test_create_user_missing_email_returns_422(client: TestClient) -> None:
    """Omitting the required `email` field should fail validation."""
    bad_payload = {"username": "charlie", "full_name": "Charlie"}
    response = client.post("/users", json=bad_payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Delete  (DELETE /users/{id})
# ---------------------------------------------------------------------------


def test_delete_user_returns_200(client: TestClient) -> None:
    """DELETE /users/{id} should return 200 on success."""
    created = client.post("/users", json=USER_PAYLOAD).json()
    response = client.delete(f"/users/{created['id']}")
    assert response.status_code == 200


def test_delete_user_removes_from_list(client: TestClient) -> None:
    """After deletion, the user should not appear in GET /users."""
    created = client.post("/users", json=USER_PAYLOAD).json()
    client.delete(f"/users/{created['id']}")
    response = client.get("/users")
    assert response.json() == []


def test_delete_user_not_found(client: TestClient) -> None:
    """DELETE /users/9999 should return 404."""
    response = client.delete("/users/9999")
    assert response.status_code == 404


def test_delete_user_success_message(client: TestClient) -> None:
    """DELETE response body should contain a confirmation message."""
    created = client.post("/users", json=USER_PAYLOAD).json()
    response = client.delete(f"/users/{created['id']}")
    assert "deleted" in response.json()["message"].lower()
