"""In-memory data store and helper functions for the CI/CD Demo application."""

from typing import Dict, List, Optional

from app.models import (
    CategoryCreate,
    CategoryResponse,
    ItemCreate,
    ItemResponse,
    ItemUpdate,
    StatsResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)

# ---------------------------------------------------------------------------
# In-memory "databases"  — typed explicitly so mypy is happy
# ---------------------------------------------------------------------------

_items: Dict[int, Dict[str, object]] = {}
_users: Dict[int, Dict[str, object]] = {}
_categories: Dict[int, Dict[str, object]] = {}
_item_counter: int = 0
_user_counter: int = 0
_category_counter: int = 0


# ---------------------------------------------------------------------------
# Category operations
# ---------------------------------------------------------------------------


def get_all_categories() -> List[CategoryResponse]:
    """Return all categories."""
    return [CategoryResponse(**c) for c in _categories.values()]  # type: ignore[arg-type]


def get_category_by_id(category_id: int) -> Optional[CategoryResponse]:
    """Return a single category by its ID, or None if not found."""
    data = _categories.get(category_id)
    if data is None:
        return None
    return CategoryResponse(**data)  # type: ignore[arg-type]


def create_category(payload: CategoryCreate) -> CategoryResponse:
    """Persist a new category and return it."""
    global _category_counter
    _category_counter += 1
    category_id = _category_counter
    record: Dict[str, object] = {
        "id": category_id,
        "name": payload.name,
        "description": payload.description,
    }
    _categories[category_id] = record
    return CategoryResponse(**record)  # type: ignore[arg-type]


def delete_category(category_id: int) -> bool:
    """Remove a category. Returns True if deleted, False if not found."""
    if category_id not in _categories:
        return False
    del _categories[category_id]
    return True


def reset_categories() -> None:
    """Clear the category store (used in tests)."""
    global _category_counter
    _categories.clear()
    _category_counter = 0


# ---------------------------------------------------------------------------
# Item operations
# ---------------------------------------------------------------------------


def get_all_items() -> List[ItemResponse]:
    """Return all items."""
    return [ItemResponse(**item) for item in _items.values()]  # type: ignore[arg-type]


def get_item_by_id(item_id: int) -> Optional[ItemResponse]:
    """Return a single item by its ID, or None if not found."""
    data = _items.get(item_id)
    if data is None:
        return None
    return ItemResponse(**data)  # type: ignore[arg-type]


def create_item(payload: ItemCreate) -> ItemResponse:
    """Persist a new item and return it."""
    global _item_counter
    _item_counter += 1
    item_id = _item_counter
    record: Dict[str, object] = {
        "id": item_id,
        "name": payload.name,
        "description": payload.description,
        "price": payload.price,
        "in_stock": payload.in_stock,
        "category_id": payload.category_id,
    }
    _items[item_id] = record
    return ItemResponse(**record)  # type: ignore[arg-type]


def update_item(item_id: int, payload: ItemUpdate) -> Optional[ItemResponse]:
    """Partially update an item and return it, or None if not found."""
    if item_id not in _items:
        return None
    record = _items[item_id]
    updates = payload.model_dump(exclude_none=True)
    record.update(updates)
    _items[item_id] = record
    return ItemResponse(**record)  # type: ignore[arg-type]


def delete_item(item_id: int) -> bool:
    """Remove an item.  Returns True if deleted, False if not found."""
    if item_id not in _items:
        return False
    del _items[item_id]
    return True


def search_items(q: str) -> List[ItemResponse]:
    """Return items whose name or description contains the query string (case-insensitive)."""
    query = q.lower()
    results = []
    for item in _items.values():
        name = str(item.get("name", "")).lower()
        description = str(item.get("description", "")).lower()
        if query in name or query in description:
            results.append(ItemResponse(**item))  # type: ignore[arg-type]
    return results


def reset_items() -> None:
    """Clear the item store (used in tests)."""
    global _item_counter
    _items.clear()
    _item_counter = 0


# ---------------------------------------------------------------------------
# User operations
# ---------------------------------------------------------------------------


def get_all_users() -> List[UserResponse]:
    """Return all users."""
    return [UserResponse(**u) for u in _users.values()]  # type: ignore[arg-type]


def get_user_by_id(user_id: int) -> Optional[UserResponse]:
    """Return a single user by ID, or None."""
    data = _users.get(user_id)
    if data is None:
        return None
    return UserResponse(**data)  # type: ignore[arg-type]


def create_user(payload: UserCreate) -> UserResponse:
    """Persist a new user and return it."""
    global _user_counter
    _user_counter += 1
    user_id = _user_counter
    record: Dict[str, object] = {
        "id": user_id,
        "username": payload.username,
        "email": payload.email,
        "full_name": payload.full_name,
        "is_active": True,
    }
    _users[user_id] = record
    return UserResponse(**record)  # type: ignore[arg-type]


def update_user(user_id: int, payload: UserUpdate) -> Optional[UserResponse]:
    """Partially update a user and return it, or None if not found."""
    if user_id not in _users:
        return None
    record = _users[user_id]
    updates = payload.model_dump(exclude_none=True)
    record.update(updates)
    _users[user_id] = record
    return UserResponse(**record)  # type: ignore[arg-type]


def delete_user(user_id: int) -> bool:
    """Remove a user. Returns True if deleted, False if not found."""
    if user_id not in _users:
        return False
    del _users[user_id]
    return True


def reset_users() -> None:
    """Clear the user store (used in tests)."""
    global _user_counter
    _users.clear()
    _user_counter = 0


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


def get_stats() -> StatsResponse:
    """Return aggregate statistics across all data stores."""
    all_items = list(_items.values())
    all_users = list(_users.values())
    return StatsResponse(
        total_items=len(all_items),
        items_in_stock=sum(1 for i in all_items if i.get("in_stock")),
        items_out_of_stock=sum(1 for i in all_items if not i.get("in_stock")),
        total_users=len(all_users),
        active_users=sum(1 for u in all_users if u.get("is_active")),
        total_categories=len(_categories),
    )
