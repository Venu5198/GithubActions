"""Pydantic models for the CI/CD Demo FastAPI application."""

from typing import Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Item models
# ---------------------------------------------------------------------------


class ItemCreate(BaseModel):
    """Schema for creating a new item."""

    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    price: float = Field(..., gt=0, description="Item price (must be positive)")
    in_stock: bool = Field(default=True, description="Whether the item is in stock")


class ItemUpdate(BaseModel):
    """Schema for updating an existing item (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    in_stock: Optional[bool] = None


class ItemResponse(BaseModel):
    """Schema returned for an item."""

    id: int
    name: str
    description: Optional[str]
    price: float
    in_stock: bool


# ---------------------------------------------------------------------------
# User models
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=150)


class UserResponse(BaseModel):
    """Schema returned for a user."""

    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool


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
