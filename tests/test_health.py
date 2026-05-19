"""Unit tests for health / utility endpoints."""

from fastapi.testclient import TestClient


def test_root_returns_200(client: TestClient) -> None:
    """GET / should return HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200


def test_root_contains_welcome_message(client: TestClient) -> None:
    """Root response body should include a welcome message key."""
    response = client.get("/")
    body = response.json()
    assert "message" in body
    assert "Welcome" in body["message"]


def test_health_check_status_ok(client: TestClient) -> None:
    """GET /health should return status 'ok'."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_check_has_version(client: TestClient) -> None:
    """Health response should expose a version field."""
    response = client.get("/health")
    body = response.json()
    assert "version" in body
    assert body["version"] == "1.0.0"


def test_health_check_has_environment(client: TestClient) -> None:
    """Health response should expose an environment field."""
    response = client.get("/health")
    body = response.json()
    assert "environment" in body


def test_echo_reverses_text(client: TestClient) -> None:
    """POST /echo should return the text reversed."""
    response = client.post("/echo", json={"text": "hello"})
    assert response.status_code == 200
    assert response.json()["reversed"] == "olleh"


def test_echo_returns_correct_length(client: TestClient) -> None:
    """POST /echo length field should equal the text length."""
    response = client.post("/echo", json={"text": "fastapi"})
    assert response.json()["length"] == 7


def test_echo_returns_uppercase(client: TestClient) -> None:
    """POST /echo upper field should be full-uppercase."""
    response = client.post("/echo", json={"text": "cicd"})
    assert response.json()["upper"] == "CICD"


def test_echo_empty_text_returns_422(client: TestClient) -> None:
    """POST /echo with empty text should fail validation (422)."""
    response = client.post("/echo", json={"text": ""})
    assert response.status_code == 422
