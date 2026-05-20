"""Unit tests for the /categories CRUD endpoints."""

from fastapi.testclient import TestClient

CATEGORY_PAYLOAD = {
    "name": "Electronics",
    "description": "Electronic gadgets and devices",
}


# ---------------------------------------------------------------------------
# List  (GET /categories)
# ---------------------------------------------------------------------------


def test_list_categories_empty(client: TestClient) -> None:
    """GET /categories on an empty store returns an empty list."""
    response = client.get("/categories")
    assert response.status_code == 200
    assert response.json() == []


def test_list_categories_returns_created_category(client: TestClient) -> None:
    """After creating a category, GET /categories should return it."""
    client.post("/categories", json=CATEGORY_PAYLOAD)
    response = client.get("/categories")
    assert len(response.json()) == 1


def test_list_categories_multiple(client: TestClient) -> None:
    """Multiple created categories should all appear in the list."""
    client.post("/categories", json=CATEGORY_PAYLOAD)
    client.post("/categories", json={"name": "Books", "description": "All kinds of books"})
    response = client.get("/categories")
    assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# Get by ID  (GET /categories/{id})
# ---------------------------------------------------------------------------


def test_get_category_by_id(client: TestClient) -> None:
    """GET /categories/{id} returns the correct category."""
    created = client.post("/categories", json=CATEGORY_PAYLOAD).json()
    response = client.get(f"/categories/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Electronics"


def test_get_category_not_found(client: TestClient) -> None:
    """GET /categories/9999 returns 404 when the category does not exist."""
    response = client.get("/categories/9999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Create  (POST /categories)
# ---------------------------------------------------------------------------


def test_create_category_returns_201(client: TestClient) -> None:
    """POST /categories should respond with HTTP 201."""
    response = client.post("/categories", json=CATEGORY_PAYLOAD)
    assert response.status_code == 201


def test_create_category_returns_id(client: TestClient) -> None:
    """POST /categories response body should include a numeric id."""
    response = client.post("/categories", json=CATEGORY_PAYLOAD)
    body = response.json()
    assert "id" in body
    assert isinstance(body["id"], int)


def test_create_category_persists_name(client: TestClient) -> None:
    """Name passed in POST /categories should match the returned name."""
    response = client.post("/categories", json=CATEGORY_PAYLOAD)
    assert response.json()["name"] == "Electronics"


def test_create_category_persists_description(client: TestClient) -> None:
    """Description passed in POST /categories should match the returned value."""
    response = client.post("/categories", json=CATEGORY_PAYLOAD)
    assert response.json()["description"] == "Electronic gadgets and devices"


def test_create_category_without_description(client: TestClient) -> None:
    """POST /categories without description should succeed with null description."""
    response = client.post("/categories", json={"name": "Misc"})
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_category_missing_name_returns_422(client: TestClient) -> None:
    """Omitting the required `name` field should fail validation."""
    response = client.post("/categories", json={"description": "No name"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Delete  (DELETE /categories/{id})
# ---------------------------------------------------------------------------


def test_delete_category_returns_200(client: TestClient) -> None:
    """DELETE /categories/{id} should return 200 on success."""
    created = client.post("/categories", json=CATEGORY_PAYLOAD).json()
    response = client.delete(f"/categories/{created['id']}")
    assert response.status_code == 200


def test_delete_category_removes_from_list(client: TestClient) -> None:
    """After deletion, the category should no longer appear in GET /categories."""
    created = client.post("/categories", json=CATEGORY_PAYLOAD).json()
    client.delete(f"/categories/{created['id']}")
    response = client.get("/categories")
    assert response.json() == []


def test_delete_category_not_found(client: TestClient) -> None:
    """DELETE /categories/9999 should return 404."""
    response = client.delete("/categories/9999")
    assert response.status_code == 404


def test_delete_category_message(client: TestClient) -> None:
    """DELETE /categories/{id} should return a confirmation message."""
    created = client.post("/categories", json=CATEGORY_PAYLOAD).json()
    response = client.delete(f"/categories/{created['id']}")
    assert "deleted" in response.json()["message"].lower()
