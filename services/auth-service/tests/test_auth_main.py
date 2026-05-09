# ─────────────────────────────────────────────
# Tests for Auth Service
# ─────────────────────────────────────────────

from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

client = TestClient(app)


def test_health_check():
    """Test that /health returns 200."""

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "auth-service"


def test_login_success():
    """Test that valid credentials return success."""

    response = client.post("/login?username=alice&password=password123")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_login_failure():
    """Test that invalid credentials return failure."""

    response = client.post("/login?username=alice&password=wrongpassword")
    assert response.status_code == 200

    # Wrong password should return failure status
    assert response.json()["status"] == "failure"


def test_login_unknown_user():
    """Test that unknown username returns failure."""

    response = client.post("/login?username=nobody&password=anything")
    assert response.json()["status"] == "failure"