"""Pydantic models for the CI/CD Demo FastAPI application."""

from typing import Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Category models
# ---------------------------------------------------------------------------


class CategoryCreate(BaseModel):
    """Schema for creating a new category."""

    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500, description="Category description")


class CategoryResponse(BaseModel):
    """Schema returned for a category."""

    id: int
    name: str
    description: Optional[str]


# ---------------------------------------------------------------------------
# Item models
# ---------------------------------------------------------------------------


class ItemCreate(BaseModel):
    """Schema for creating a new item."""

    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    price: float = Field(..., gt=0, description="Item price (must be positive)")
    in_stock: bool = Field(default=True, description="Whether the item is in stock")
    category_id: Optional[int] = Field(None, description="ID of the category this item belongs to")


class ItemUpdate(BaseModel):
    """Schema for updating an existing item (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    in_stock: Optional[bool] = None
    category_id: Optional[int] = None


class ItemResponse(BaseModel):
    """Schema returned for an item."""

    id: int
    name: str
    description: Optional[str]
    price: float
    in_stock: bool
    category_id: Optional[int]


# ---------------------------------------------------------------------------
# User models
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=150)


class UserUpdate(BaseModel):
    """Schema for partially updating a user (all fields optional)."""

    email: Optional[str] = Field(None, description="Updated email address")
    full_name: Optional[str] = Field(None, max_length=150)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema returned for a user."""

    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool


# ---------------------------------------------------------------------------
# Stats model
# ---------------------------------------------------------------------------


class StatsResponse(BaseModel):
    """Aggregate statistics for the application data."""

    total_items: int
    items_in_stock: int
    items_out_of_stock: int
    total_users: int
    active_users: int
    total_categories: int


# ---------------------------------------------------------------------------
# Health / utility models
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Health-check response schema."""

    status: str
    version: str
    environment: str


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


class EchoRequest(BaseModel):
    """Schema for the echo endpoint."""

    text: str = Field(..., min_length=1, max_length=1000)


class EchoResponse(BaseModel):
    """Response for the echo endpoint."""

    original: str
    reversed: str
    length: int
    upper: str
