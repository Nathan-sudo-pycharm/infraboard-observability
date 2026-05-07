# ─────────────────────────────────────────────
# Order Service — main.py
# Handles order creation and retrieval.
# Tracks order count and processing time as
# Prometheus metrics — spikes in processing_time
# are a classic sign something is wrong downstream
# ─────────────────────────────────────────────

from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time

# random is a built-in Python module — we use it to simulate
# realistic varying processing times for orders
import random

# ─────────────────────────────────────────────
# App Initialization
# ─────────────────────────────────────────────

app = FastAPI(title="Order Service")

# ─────────────────────────────────────────────
# Prometheus Metrics
# ─────────────────────────────────────────────

# Tracks total number of orders placed
ORDER_COUNT = Counter(
    "order_service_orders_total",
    "Total number of orders created"
)

# Tracks total requests to this service, labelled by method and endpoint
REQUEST_COUNT = Counter(
    "order_service_requests_total",
    "Total number of requests to Order Service",
    ["method", "endpoint"]
)

# Histogram: tracks how long order processing takes
# This is the key metric our ML model watches for anomalies
PROCESSING_TIME = Histogram(
    "order_service_processing_seconds",
    "Time taken to process an order",
    ["endpoint"]
)

# ─────────────────────────────────────────────
# Fake In-Memory Orders Database
# ─────────────────────────────────────────────

# A list of dicts — each dict represents one order
fake_orders_db = [
    {"id": 1, "item": "Laptop", "quantity": 1, "status": "delivered"},
    {"id": 2, "item": "Mouse",  "quantity": 2, "status": "pending"},
]

# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/orders")
def get_orders():
    """Return all orders in the fake database."""

    start = time.time()
    REQUEST_COUNT.labels(method="GET", endpoint="/orders").inc()

    result = {"orders": fake_orders_db}

    PROCESSING_TIME.labels(endpoint="/orders").observe(time.time() - start)
    return result


@app.post("/orders")
def create_order(item: str, quantity: int):
    """
    Create a new order.
    Simulates variable processing time using random.uniform()
    so our ML model has realistic data to learn from.
    """

    start = time.time()
    REQUEST_COUNT.labels(method="POST", endpoint="/orders").inc()

    # random.uniform(a, b) returns a random float between a and b
    # This simulates realistic varying processing time
    # In production this would be actual DB write time
    simulated_processing_time = random.uniform(0.01, 0.3)
    time.sleep(simulated_processing_time)  # time.sleep() pauses execution

    # Build the new order dict
    new_order = {
        "id": len(fake_orders_db) + 1,  # auto-increment ID
        "item": item,
        "quantity": quantity,
        "status": "pending"             # all new orders start as pending
    }

    fake_orders_db.append(new_order)
    ORDER_COUNT.inc()

    # Observe the TOTAL time including simulated processing
    PROCESSING_TIME.labels(endpoint="/orders").observe(time.time() - start)

    return {"message": "Order created", "order": new_order}


# ─────────────────────────────────────────────
# Metrics Endpoint
# ─────────────────────────────────────────────

@app.get("/metrics")
def metrics():
    """Expose Prometheus metrics as plain text."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    """Returns OK if the service is running."""
    return {"status": "ok", "service": "order-service"}