"""Route definitions for the CI/CD Demo FastAPI application."""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

import app.database as db
from app.models import (
    CategoryCreate,
    CategoryResponse,
    EchoRequest,
    EchoResponse,
    ItemCreate,
    ItemResponse,
    ItemUpdate,
    MessageResponse,
    StatsResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)

router = APIRouter()


# ===========================================================================
# Health / utility routes
# ===========================================================================


@router.get(
    "/health",
    response_model=None,
    tags=["Health"],
    summary="Health check",
    description="Returns the current health status of the application.",
)
def health_check() -> Dict[str, str]:
    """Return a simple health-check payload."""
    return {"status": "ok", "version": "1.0.0", "environment": "development"}


@router.get(
    "/",
    tags=["Health"],
    summary="Root endpoint",
)
def root() -> Dict[str, object]:
    """Welcome endpoint with available resource links."""
    return {
        "message": "Welcome to the CI/CD Demo FastAPI application!",
        "docs": "/docs",
        "health": "/health",
        "resources": {
            "items": "/items",
            "users": "/users",
            "categories": "/categories",
            "stats": "/stats",
        },
    }


@router.post(
    "/echo",
    response_model=EchoResponse,
    tags=["Utility"],
    summary="Echo text",
    description="Returns the submitted text along with its reverse, length, and uppercase form.",
)
def echo(payload: EchoRequest) -> EchoResponse:
    """Echo the request body with extra transformations."""
    return EchoResponse(
        original=payload.text,
        reversed=payload.text[::-1],
        length=len(payload.text),
        upper=payload.text.upper(),
    )


# ===========================================================================
# Stats
# ===========================================================================


@router.get(
    "/stats",
    response_model=StatsResponse,
    tags=["Stats"],
    summary="Application statistics",
    description="Returns aggregate counts for items, users, and categories.",
)
def get_stats() -> StatsResponse:
    """Return aggregate statistics for the entire data store."""
    return db.get_stats()


# ===========================================================================
# Categories  (full CRUD)
# ===========================================================================


@router.get(
    "/categories",
    response_model=List[CategoryResponse],
    tags=["Categories"],
    summary="List all categories",
)
def list_categories() -> List[CategoryResponse]:
    """Return all categories."""
    return db.get_all_categories()


@router.get(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    tags=["Categories"],
    summary="Get a single category",
)
def get_category(category_id: int) -> CategoryResponse:
    """Retrieve one category by its numeric ID."""
    category = db.get_category_by_id(category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Categories"],
    summary="Create a category",
)
def create_category(payload: CategoryCreate) -> CategoryResponse:
    """Create a new category and return the persisted record."""
    return db.create_category(payload)


@router.delete(
    "/categories/{category_id}",
    response_model=MessageResponse,
    tags=["Categories"],
    summary="Delete a category",
)
def delete_category(category_id: int) -> MessageResponse:
    """Remove a category permanently."""
    deleted = db.delete_category(category_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return MessageResponse(message=f"Category {category_id} deleted successfully")


# ===========================================================================
# Items  (full CRUD + search)
# ===========================================================================


@router.get(
    "/items/search",
    response_model=List[ItemResponse],
    tags=["Items"],
    summary="Search items",
    description="Full-text search on item name and description (case-insensitive).",
)
def search_items(
    q: str = Query(..., min_length=1, description="Search query string"),
) -> List[ItemResponse]:
    """Search items by name or description."""
    return db.search_items(q)


@router.get(
    "/items",
    response_model=List[ItemResponse],
    tags=["Items"],
    summary="List all items",
)
def list_items(
    in_stock: Optional[bool] = Query(default=None, description="Filter by stock status"),
    category_id: Optional[int] = Query(default=None, description="Filter by category ID"),
) -> List[ItemResponse]:
    """Return all items, with optional filters on stock availability and category."""
    items = db.get_all_items()
    if in_stock is not None:
        items = [i for i in items if i.in_stock == in_stock]
    if category_id is not None:
        items = [i for i in items if i.category_id == category_id]
    return items


@router.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    tags=["Items"],
    summary="Get a single item",
)
def get_item(item_id: int) -> ItemResponse:
    """Retrieve one item by its numeric ID."""
    item = db.get_item_by_id(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Items"],
    summary="Create an item",
)
def create_item(payload: ItemCreate) -> ItemResponse:
    """Create a new item and return the persisted record."""
    return db.create_item(payload)


@router.put(
    "/items/{item_id}",
    response_model=ItemResponse,
    tags=["Items"],
    summary="Update an item",
)
def update_item(item_id: int, payload: ItemUpdate) -> ItemResponse:
    """Partially update an existing item's fields."""
    updated = db.update_item(item_id, payload)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return updated


@router.delete(
    "/items/{item_id}",
    response_model=MessageResponse,
    tags=["Items"],
    summary="Delete an item",
)
def delete_item(item_id: int) -> MessageResponse:
    """Remove an item permanently."""
    deleted = db.delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return MessageResponse(message=f"Item {item_id} deleted successfully")


# ===========================================================================
# Users  (full CRUD including PATCH update)
# ===========================================================================


@router.get(
    "/users",
    response_model=List[UserResponse],
    tags=["Users"],
    summary="List all users",
)
def list_users() -> List[UserResponse]:
    """Return all registered users."""
    return db.get_all_users()


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    tags=["Users"],
    summary="Get a single user",
)
def get_user(user_id: int) -> UserResponse:
    """Retrieve one user by their numeric ID."""
    user = db.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
    summary="Create a user",
)
def create_user(payload: UserCreate) -> UserResponse:
    """Register a new user."""
    return db.create_user(payload)


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    tags=["Users"],
    summary="Update a user",
    description="Partially update a user's email, full_name, or active status.",
)
def update_user(user_id: int, payload: UserUpdate) -> UserResponse:
    """Partially update an existing user's fields."""
    updated = db.update_user(user_id, payload)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated


@router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
    tags=["Users"],
    summary="Delete a user",
)
def delete_user(user_id: int) -> MessageResponse:
    """Permanently remove a user account."""
    deleted = db.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return MessageResponse(message=f"User {user_id} deleted successfully")
