"""
Pytest fixtures shared across all test modules.
"""

import pytest
from fastapi.testclient import TestClient

import app.database as db
from app.main import app


@pytest.fixture(autouse=True)
def reset_stores() -> None:
    """Reset in-memory stores before every test to guarantee isolation."""
    db.reset_items()
    db.reset_users()
    yield
    db.reset_items()
    db.reset_users()


@pytest.fixture()
def client() -> TestClient:
    """Return a synchronous test client for the FastAPI app."""
    return TestClient(app)
