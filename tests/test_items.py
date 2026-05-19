"""Unit tests for the /items CRUD endpoints."""

from fastapi.testclient import TestClient

ITEM_PAYLOAD = {
    "name": "Laptop",
    "description": "A powerful laptop",
    "price": 999.99,
    "in_stock": True,
}


# ---------------------------------------------------------------------------
# List  (GET /items)
# ---------------------------------------------------------------------------


def test_list_items_empty(client: TestClient) -> None:
    """GET /items on an empty store returns an empty list."""
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json() == []


def test_list_items_returns_created_item(client: TestClient) -> None:
    """After creating an item, GET /items should return it."""
    client.post("/items", json=ITEM_PAYLOAD)
    response = client.get("/items")
    assert len(response.json()) == 1


def test_list_items_filter_in_stock_true(client: TestClient) -> None:
    """GET /items?in_stock=true returns only in-stock items."""
    client.post("/items", json=ITEM_PAYLOAD)
    client.post("/items", json={**ITEM_PAYLOAD, "name": "Sold-out", "in_stock": False})
    response = client.get("/items?in_stock=true")
    items = response.json()
    assert all(i["in_stock"] for i in items)


def test_list_items_filter_in_stock_false(client: TestClient) -> None:
    """GET /items?in_stock=false returns only out-of-stock items."""
    client.post("/items", json={**ITEM_PAYLOAD, "name": "OOS", "in_stock": False})
    response = client.get("/items?in_stock=false")
    items = response.json()
    assert all(not i["in_stock"] for i in items)


# ---------------------------------------------------------------------------
# Get by ID  (GET /items/{id})
# ---------------------------------------------------------------------------


def test_get_item_by_id(client: TestClient) -> None:
    """GET /items/{id} returns the correct item."""
    created = client.post("/items", json=ITEM_PAYLOAD).json()
    response = client.get(f"/items/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Laptop"


def test_get_item_not_found(client: TestClient) -> None:
    """GET /items/9999 returns 404 when the item does not exist."""
    response = client.get("/items/9999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Create  (POST /items)
# ---------------------------------------------------------------------------


def test_create_item_returns_201(client: TestClient) -> None:
    """POST /items should respond with HTTP 201."""
    response = client.post("/items", json=ITEM_PAYLOAD)
    assert response.status_code == 201


def test_create_item_returns_id(client: TestClient) -> None:
    """POST /items response body should include a numeric id."""
    response = client.post("/items", json=ITEM_PAYLOAD)
    assert "id" in response.json()
    assert isinstance(response.json()["id"], int)


def test_create_item_persists_name(client: TestClient) -> None:
    """Name passed in POST /items should match the returned name."""
    response = client.post("/items", json=ITEM_PAYLOAD)
    assert response.json()["name"] == "Laptop"


def test_create_item_invalid_price_returns_422(client: TestClient) -> None:
    """A price <= 0 should fail Pydantic validation."""
    bad_payload = {**ITEM_PAYLOAD, "price": -10}
    response = client.post("/items", json=bad_payload)
    assert response.status_code == 422


def test_create_item_missing_name_returns_422(client: TestClient) -> None:
    """Omitting the required `name` field should fail validation."""
    bad_payload = {"price": 10.0, "in_stock": True}
    response = client.post("/items", json=bad_payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Update  (PUT /items/{id})
# ---------------------------------------------------------------------------


def test_update_item_changes_price(client: TestClient) -> None:
    """PUT /items/{id} should update the item's price."""
    created = client.post("/items", json=ITEM_PAYLOAD).json()
    response = client.put(f"/items/{created['id']}", json={"price": 799.0})
    assert response.status_code == 200
    assert response.json()["price"] == 799.0


def test_update_item_partial_update(client: TestClient) -> None:
    """PUT /items/{id} should not overwrite un-supplied fields."""
    created = client.post("/items", json=ITEM_PAYLOAD).json()
    client.put(f"/items/{created['id']}", json={"in_stock": False})
    response = client.get(f"/items/{created['id']}")
    body = response.json()
    assert body["in_stock"] is False
    assert body["name"] == "Laptop"  # unchanged


def test_update_item_not_found(client: TestClient) -> None:
    """PUT /items/9999 should return 404."""
    response = client.put("/items/9999", json={"price": 1.0})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete  (DELETE /items/{id})
# ---------------------------------------------------------------------------


def test_delete_item_returns_200(client: TestClient) -> None:
    """DELETE /items/{id} should return 200 on success."""
    created = client.post("/items", json=ITEM_PAYLOAD).json()
    response = client.delete(f"/items/{created['id']}")
    assert response.status_code == 200


def test_delete_item_removes_from_list(client: TestClient) -> None:
    """After deletion, the item should no longer appear in GET /items."""
    created = client.post("/items", json=ITEM_PAYLOAD).json()
    client.delete(f"/items/{created['id']}")
    response = client.get("/items")
    assert response.json() == []


def test_delete_item_not_found(client: TestClient) -> None:
    """DELETE /items/9999 should return 404."""
    response = client.delete("/items/9999")
    assert response.status_code == 404
