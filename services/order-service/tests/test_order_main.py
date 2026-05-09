# ─────────────────────────────────────────────
# Tests for Order Service
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
    assert response.json()["service"] == "order-service"


def test_get_orders_returns_200():
    """Test that GET /orders returns 200."""

    response = client.get("/orders")
    assert response.status_code == 200


def test_get_orders_returns_list():
    """Test that GET /orders returns a dict with 'orders' key."""

    response = client.get("/orders")
    data = response.json()
    assert "orders" in data
    assert isinstance(data["orders"], list)


def test_create_order():
    """Test that POST /orders creates a new order."""

    response = client.post("/orders?item=Keyboard&quantity=2")
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Order created"
    assert data["order"]["item"] == "Keyboard"
    assert data["order"]["status"] == "pending"