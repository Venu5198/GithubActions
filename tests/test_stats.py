"""Unit tests for /stats, /items/search, item category filtering, and PATCH /users."""

from fastapi.testclient import TestClient

ITEM_PAYLOAD = {
    "name": "Laptop",
    "description": "A powerful laptop for developers",
    "price": 999.99,
    "in_stock": True,
}

USER_PAYLOAD = {
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
}

CATEGORY_PAYLOAD = {
    "name": "Electronics",
    "description": "Electronic gadgets",
}


# ---------------------------------------------------------------------------
# Stats  (GET /stats)
# ---------------------------------------------------------------------------


def test_stats_empty_store(client: TestClient) -> None:
    """GET /stats on an empty store returns all zeros."""
    response = client.get("/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 0
    assert body["total_users"] == 0
    assert body["total_categories"] == 0


def test_stats_counts_items(client: TestClient) -> None:
    """GET /stats reflects the correct item count after creation."""
    client.post("/items", json=ITEM_PAYLOAD)
    client.post("/items", json={**ITEM_PAYLOAD, "name": "Mouse"})
    response = client.get("/stats")
    assert response.json()["total_items"] == 2


def test_stats_in_stock_vs_out_of_stock(client: TestClient) -> None:
    """GET /stats correctly splits in-stock and out-of-stock items."""
    client.post("/items", json={**ITEM_PAYLOAD, "in_stock": True})
    client.post("/items", json={**ITEM_PAYLOAD, "name": "OOS Item", "in_stock": False})
    body = client.get("/stats").json()
    assert body["items_in_stock"] == 1
    assert body["items_out_of_stock"] == 1


def test_stats_counts_users(client: TestClient) -> None:
    """GET /stats reflects the correct user count after creation."""
    client.post("/users", json=USER_PAYLOAD)
    response = client.get("/stats")
    assert response.json()["total_users"] == 1
    assert response.json()["active_users"] == 1


def test_stats_counts_categories(client: TestClient) -> None:
    """GET /stats reflects the correct category count after creation."""
    client.post("/categories", json=CATEGORY_PAYLOAD)
    response = client.get("/stats")
    assert response.json()["total_categories"] == 1


def test_stats_combined(client: TestClient) -> None:
    """GET /stats correctly aggregates items, users, and categories together."""
    client.post("/items", json=ITEM_PAYLOAD)
    client.post("/users", json=USER_PAYLOAD)
    client.post("/categories", json=CATEGORY_PAYLOAD)
    body = client.get("/stats").json()
    assert body["total_items"] == 1
    assert body["total_users"] == 1
    assert body["total_categories"] == 1


# ---------------------------------------------------------------------------
# Item Search  (GET /items/search?q=...)
# ---------------------------------------------------------------------------


def test_search_items_by_name(client: TestClient) -> None:
    """Search should find items matching the name."""
    client.post("/items", json=ITEM_PAYLOAD)
    response = client.get("/items/search?q=laptop")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Laptop"


def test_search_items_by_description(client: TestClient) -> None:
    """Search should find items matching a word in the description."""
    client.post("/items", json=ITEM_PAYLOAD)
    response = client.get("/items/search?q=developer")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_items_case_insensitive(client: TestClient) -> None:
    """Search should be case-insensitive."""
    client.post("/items", json=ITEM_PAYLOAD)
    response = client.get("/items/search?q=LAPTOP")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_items_no_match(client: TestClient) -> None:
    """Search that matches nothing should return an empty list."""
    client.post("/items", json=ITEM_PAYLOAD)
    response = client.get("/items/search?q=refrigerator")
    assert response.status_code == 200
    assert response.json() == []


def test_search_items_multiple_results(client: TestClient) -> None:
    """Search should return all matching items."""
    client.post("/items", json=ITEM_PAYLOAD)
    client.post("/items", json={**ITEM_PAYLOAD, "name": "Laptop Stand"})
    response = client.get("/items/search?q=laptop")
    assert len(response.json()) == 2


def test_search_items_missing_query_returns_422(client: TestClient) -> None:
    """GET /items/search without q param should return 422."""
    response = client.get("/items/search")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Item Category Filter  (GET /items?category_id=...)
# ---------------------------------------------------------------------------


def test_filter_items_by_category(client: TestClient) -> None:
    """GET /items?category_id=X should return only items in that category."""
    category = client.post("/categories", json=CATEGORY_PAYLOAD).json()
    cat_id = category["id"]
    client.post("/items", json={**ITEM_PAYLOAD, "category_id": cat_id})
    client.post("/items", json={**ITEM_PAYLOAD, "name": "Uncategorized"})
    response = client.get(f"/items?category_id={cat_id}")
    items = response.json()
    assert len(items) == 1
    assert items[0]["category_id"] == cat_id


def test_item_created_with_category_id(client: TestClient) -> None:
    """POST /items with category_id should persist and return the category_id."""
    category = client.post("/categories", json=CATEGORY_PAYLOAD).json()
    cat_id = category["id"]
    item = client.post("/items", json={**ITEM_PAYLOAD, "category_id": cat_id}).json()
    assert item["category_id"] == cat_id


def test_item_created_without_category_id(client: TestClient) -> None:
    """POST /items without category_id should have null category_id."""
    item = client.post("/items", json=ITEM_PAYLOAD).json()
    assert item["category_id"] is None


# ---------------------------------------------------------------------------
# PATCH /users/{user_id}
# ---------------------------------------------------------------------------


def test_patch_user_updates_email(client: TestClient) -> None:
    """PATCH /users/{id} should update the email field."""
    created = client.post("/users", json=USER_PAYLOAD).json()
    response = client.patch(f"/users/{created['id']}", json={"email": "new@example.com"})
    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"


def test_patch_user_updates_full_name(client: TestClient) -> None:
    """PATCH /users/{id} should update the full_name field."""
    created = client.post("/users", json=USER_PAYLOAD).json()
    response = client.patch(f"/users/{created['id']}", json={"full_name": "Jane Doe"})
    assert response.json()["full_name"] == "Jane Doe"


def test_patch_user_deactivate(client: TestClient) -> None:
    """PATCH /users/{id} can set is_active to False."""
    created = client.post("/users", json=USER_PAYLOAD).json()
    response = client.patch(f"/users/{created['id']}", json={"is_active": False})
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_patch_user_does_not_overwrite_username(client: TestClient) -> None:
    """PATCH /users/{id} should not overwrite un-supplied fields like username."""
    created = client.post("/users", json=USER_PAYLOAD).json()
    client.patch(f"/users/{created['id']}", json={"email": "updated@example.com"})
    response = client.get(f"/users/{created['id']}")
    assert response.json()["username"] == "johndoe"


def test_patch_user_not_found(client: TestClient) -> None:
    """PATCH /users/9999 should return 404."""
    response = client.patch("/users/9999", json={"email": "x@x.com"})
    assert response.status_code == 404
