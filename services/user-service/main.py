# ─────────────────────────────────────────────
# User Service — main.py
# This is one of the three microservices in InfraBoard.
# It handles user-related endpoints and emits metrics
# that Prometheus will scrape and Grafana will display.
# ─────────────────────────────────────────────

# FastAPI is the web framework — it lets us define API endpoints easily
from fastapi import FastAPI

# prometheus_client gives us metric objects we can increment/observe
# Counter = a number that only goes up (e.g. total requests)
# Histogram = tracks distributions like response times
# generate_latest = converts our metrics to text Prometheus can read
# CONTENT_TYPE_LATEST = the correct HTTP content-type header for Prometheus
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Response lets us return raw text (needed for the /metrics endpoint)
from starlette.responses import Response

# time is a built-in Python module — we use it to measure response duration
import time

# ─────────────────────────────────────────────
# App Initialization
# ─────────────────────────────────────────────

# Create the FastAPI app instance — this is the core of our service
app = FastAPI(title="User Service")

# ─────────────────────────────────────────────
# Prometheus Metrics
# These are the numbers our service will track and expose
# ─────────────────────────────────────────────

# Counter: tracks total number of requests to this service
# Labels let us filter by endpoint and HTTP method in Grafana
REQUEST_COUNT = Counter(
    "user_service_requests_total",         # metric name in Prometheus
    "Total number of requests to User Service",  # description
    ["method", "endpoint"]                 # labels we can filter by
)

# Histogram: tracks how long each request takes (in seconds)
# Prometheus automatically calculates averages and percentiles from this
REQUEST_LATENCY = Histogram(
    "user_service_request_latency_seconds",
    "Request latency in seconds for User Service",
    ["endpoint"]
)

# Counter: tracks how many users exist in our fake database
ACTIVE_USERS = Counter(
    "user_service_active_users_total",
    "Total number of users created"
)

# ─────────────────────────────────────────────
# Fake In-Memory Database
# In a real app this would be PostgreSQL — for now a simple list works
# ─────────────────────────────────────────────

# A plain Python list acting as our "database" of users
fake_users_db = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob",   "email": "bob@example.com"},
]

# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

# @app.get is a FastAPI decorator — it registers this function
# as a handler for HTTP GET requests at the path "/users"
@app.get("/users")
def get_users():
    """Return all users in the fake database."""

    # Record the start time so we can measure how long this takes
    start = time.time()

    # Increment our request counter — labels: method=GET, endpoint=/users
    REQUEST_COUNT.labels(method="GET", endpoint="/users").inc()

    # Simulate a tiny bit of work (not needed, just realistic)
    result = {"users": fake_users_db}

    # Observe how many seconds this endpoint took to respond
    REQUEST_LATENCY.labels(endpoint="/users").observe(time.time() - start)

    # FastAPI auto-converts this dict to a JSON response
    return result


# @app.post registers this as a handler for HTTP POST requests at "/users"
@app.post("/users")
def create_user(name: str, email: str):
    """Create a new user and add them to the fake database."""

    start = time.time()

    REQUEST_COUNT.labels(method="POST", endpoint="/users").inc()

    # Build a new user dict with a simple auto-incremented ID
    new_user = {
        "id": len(fake_users_db) + 1,  # next ID = current length + 1
        "name": name,
        "email": email
    }

    # append() is a built-in list method — adds the new user to our list
    fake_users_db.append(new_user)

    # Increment our active users counter each time a user is created
    ACTIVE_USERS.inc()

    REQUEST_LATENCY.labels(endpoint="/users").observe(time.time() - start)

    # Return the newly created user with a 201 status code (HTTP "Created")
    return {"message": "User created", "user": new_user}


# ─────────────────────────────────────────────
# Metrics Endpoint
# Prometheus will call GET /metrics every 15 seconds to collect data
# ─────────────────────────────────────────────

@app.get("/metrics")
def metrics():
    """Expose all Prometheus metrics as plain text for scraping."""

    # generate_latest() converts all our metric objects into
    # the text format Prometheus expects
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ─────────────────────────────────────────────
# Health Check
# A simple endpoint to confirm the service is alive
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    """Returns OK if the service is running."""
    return {"status": "ok", "service": "user-service"}