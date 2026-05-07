# ─────────────────────────────────────────────
# Tests for User Service
# pytest looks for files named test_*.py and
# functions named test_* and runs them automatically
# ─────────────────────────────────────────────

# TestClient lets us make fake HTTP requests to our app
# without needing a real running server
from fastapi.testclient import TestClient

# Import our FastAPI app instance from main.py
import sys
import os

# Add the parent directory to path so we can import main.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

# Create a test client that wraps our app
client = TestClient(app)


def test_health_check():
    """Test that /health returns 200 and correct service name."""

    # client.get() makes a fake GET request to our app
    response = client.get("/health")

    # assert checks that something is true — if not, the test fails
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "user-service"


def test_get_users_returns_200():
    """Test that GET /users returns a 200 status code."""

    response = client.get("/users")
    assert response.status_code == 200


def test_get_users_returns_list():
    """Test that GET /users returns a dict with a 'users' key."""

    response = client.get("/users")
    data = response.json()

    # "in" is a Python keyword — checks if key exists in dict
    assert "users" in data
    assert isinstance(data["users"], list)  # isinstance checks the type


def test_create_user():
    """Test that POST /users creates a new user successfully."""

    response = client.post("/users?name=TestUser&email=test@example.com")
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "User created"
    assert data["user"]["name"] == "TestUser"