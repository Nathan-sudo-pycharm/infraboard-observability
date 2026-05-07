# ─────────────────────────────────────────────
# Auth Service — main.py
# Handles login authentication for InfraBoard.
# Tracks successful and failed login attempts as
# Prometheus metrics — useful for detecting brute
# force attacks (our ML model will catch spikes in failures)
# ─────────────────────────────────────────────

from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time

# ─────────────────────────────────────────────
# App Initialization
# ─────────────────────────────────────────────

app = FastAPI(title="Auth Service")

# ─────────────────────────────────────────────
# Prometheus Metrics
# ─────────────────────────────────────────────

# Tracks every login attempt that succeeded
LOGIN_SUCCESS = Counter(
    "auth_service_login_success_total",
    "Total number of successful logins"
)

# Tracks every login attempt that failed — spikes here trigger ML alerts
LOGIN_FAILURE = Counter(
    "auth_service_login_failure_total",
    "Total number of failed logins"
)

# Tracks how long each login request takes
REQUEST_LATENCY = Histogram(
    "auth_service_request_latency_seconds",
    "Request latency in seconds for Auth Service",
    ["endpoint"]
)

# ─────────────────────────────────────────────
# Fake User Credentials Database
# In a real app this would be hashed passwords in PostgreSQL
# ─────────────────────────────────────────────

# A dict maps username → password for quick lookup
# dict is a built-in Python data structure: key-value pairs
FAKE_CREDENTIALS = {
    "alice": "password123",
    "bob": "securepass",
}

# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

# @app.post registers this as a POST endpoint at /login
# username and password come from query parameters in the request
@app.post("/login")
def login(username: str, password: str):
    """
    Accepts a username and password.
    Returns success or failure and increments the appropriate counter.
    """

    start = time.time()

    # .get() is a dict method — returns the value for the key,
    # or None if the key doesn't exist (avoids a KeyError crash)
    stored_password = FAKE_CREDENTIALS.get(username)

    # Check if username exists AND password matches
    if stored_password and stored_password == password:
        LOGIN_SUCCESS.inc()  # increment success counter
        result = {"status": "success", "message": f"Welcome, {username}!"}
    else:
        LOGIN_FAILURE.inc()  # increment failure counter — ML watches this
        result = {"status": "failure", "message": "Invalid username or password"}

    # Observe how long this login attempt took
    REQUEST_LATENCY.labels(endpoint="/login").observe(time.time() - start)

    return result


# ─────────────────────────────────────────────
# Metrics Endpoint
# Prometheus scrapes this every 15 seconds
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
    return {"status": "ok", "service": "auth-service"}