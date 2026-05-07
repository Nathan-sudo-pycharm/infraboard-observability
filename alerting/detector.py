# ─────────────────────────────────────────────
# alerting/detector.py
# This is the ML brain of InfraBoard.
# It queries Prometheus for recent metric data,
# runs an Isolation Forest model to detect anomalies,
# and saves alerts to a SQLite database.
#
# Isolation Forest works by randomly partitioning data —
# anomalies are isolated in fewer splits than normal points,
# so they get a lower anomaly score.
# ─────────────────────────────────────────────

# requests lets us make HTTP calls to the Prometheus API
import requests

# numpy is a math/array library — we use it to reshape data
import numpy as np

# IsolationForest is our anomaly detection model from scikit-learn
from sklearn.ensemble import IsolationForest

# sqlite3 is a built-in Python module for a lightweight database
# We use it to store alerts without needing a full DB server
import sqlite3

# datetime is a built-in module for working with timestamps
from datetime import datetime

# time is built-in — we use it to run the detector in a loop
import time

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

# The URL of our Prometheus container — same network, so we use service name
PROMETHEUS_URL = "http://prometheus:9090"

# How often to run anomaly detection (in seconds)
DETECTION_INTERVAL = 30

# ─────────────────────────────────────────────
# Database Setup
# ─────────────────────────────────────────────

def init_db():
    """
    Creates the SQLite database and alerts table if they don't exist yet.
    SQLite stores everything in a single file — alerts.db
    """

    # connect() opens or creates the database file
    conn = sqlite3.connect("/app/alerts.db")

    # cursor() lets us execute SQL commands
    cursor = conn.cursor()

    # CREATE TABLE IF NOT EXISTS — only creates if it doesn't already exist
    # This means we can safely call init_db() every time without losing data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            service TEXT,
            metric TEXT,
            value REAL,
            message TEXT
        )
    """)

    # commit() saves the changes to the file
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# Prometheus Query
# ─────────────────────────────────────────────

def query_prometheus(metric_name):
    """
    Queries Prometheus for the last 5 minutes of data for a given metric.
    Returns a list of float values, or empty list if query fails.

    metric_name: the Prometheus metric string to query (e.g. 'user_service_requests_total')
    """

    # The Prometheus HTTP API endpoint for range queries
    url = f"{PROMETHEUS_URL}/api/v1/query_range"

    # Parameters for the query:
    # query = metric name
    # start/end = time range (last 5 minutes using Unix timestamps)
    # step = how often to sample (every 15 seconds)
    params = {
        "query": metric_name,
        "start": time.time() - 300,  # 300 seconds = 5 minutes ago
        "end": time.time(),
        "step": "15s"
    }

    try:
        # requests.get() makes an HTTP GET request to Prometheus
        response = requests.get(url, params=params, timeout=5)

        # .json() parses the response body as JSON into a Python dict
        data = response.json()

        # Navigate the Prometheus response structure to get values
        # data["data"]["result"] is a list of time series
        results = data.get("data", {}).get("result", [])

        if not results:
            return []  # no data found for this metric

        # Each result has "values" — a list of [timestamp, value] pairs
        # We take the first time series and extract just the float values
        values = [float(v[1]) for v in results[0].get("values", [])]
        return values

    except Exception as e:
        # If anything goes wrong (network error, timeout), log and return empty
        print(f"[ERROR] Failed to query Prometheus for {metric_name}: {e}")
        return []


# ─────────────────────────────────────────────
# Anomaly Detection
# ─────────────────────────────────────────────

def detect_anomalies(values, metric_name, service_name):
    """
    Runs Isolation Forest on a list of metric values.
    If anomalies are found, saves them to the database.

    values: list of floats from Prometheus
    metric_name: name of the metric being analyzed
    service_name: which service this metric belongs to
    """

    # Need at least 10 data points for meaningful anomaly detection
    if len(values) < 10:
        print(f"[INFO] Not enough data for {metric_name} ({len(values)} points)")
        return

    # numpy requires a 2D array — reshape(-1, 1) converts [1,2,3] to [[1],[2],[3]]
    # -1 means "figure out this dimension automatically"
    data = np.array(values).reshape(-1, 1)

    # IsolationForest parameters:
    # contamination = expected fraction of anomalies (5% here)
    # random_state = seed for reproducibility (same results every run)
    model = IsolationForest(contamination=0.05, random_state=42)

    # fit_predict() trains the model AND returns predictions in one step
    # Returns: 1 for normal points, -1 for anomalies
    predictions = model.fit_predict(data)

    # Check if the MOST RECENT value is an anomaly
    # predictions[-1] gets the last element of the array
    if predictions[-1] == -1:
        latest_value = values[-1]
        message = (
            f"Anomaly detected in {service_name}: "
            f"{metric_name} = {latest_value:.4f} "
            f"(unusual compared to recent baseline)"
        )
        print(f"[ALERT] {message}")

        # Save the alert to our SQLite database
        save_alert(service_name, metric_name, latest_value, message)
    else:
        print(f"[OK] {metric_name} looks normal (latest value: {values[-1]:.4f})")


# ─────────────────────────────────────────────
# Save Alert to Database
# ─────────────────────────────────────────────

def save_alert(service, metric, value, message):
    """
    Saves a detected anomaly alert to the SQLite database.
    """

    conn = sqlite3.connect("/app/alerts.db")
    cursor = conn.cursor()

    # INSERT INTO adds a new row to the alerts table
    # ? placeholders prevent SQL injection (always use these, never f-strings in SQL)
    cursor.execute("""
        INSERT INTO alerts (timestamp, service, metric, value, message)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),  # current UTC time as a string
        service,
        metric,
        value,
        message
    ))

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# Main Detection Loop
# ─────────────────────────────────────────────

def run_detector():
    """
    Main loop — runs anomaly detection every DETECTION_INTERVAL seconds.
    Checks a set of key metrics across all three services.
    """

    print("[INFO] Initializing database...")
    init_db()

    print("[INFO] Starting anomaly detection loop...")

    # Define which metrics to watch and which service they belong to
    # Each tuple is (prometheus_metric_name, service_label)
    metrics_to_watch = [
        ("user_service_requests_total", "user-service"),
        ("auth_service_login_failure_total", "auth-service"),
        ("auth_service_login_success_total", "auth-service"),
        ("order_service_orders_total", "order-service"),
        ("order_service_processing_seconds_sum", "order-service"),
    ]

    # while True runs forever — the detector keeps checking until stopped
    while True:
        print(f"\n[INFO] Running detection at {datetime.utcnow().isoformat()}")

        # Loop through each metric and run detection
        for metric_name, service_name in metrics_to_watch:
            values = query_prometheus(metric_name)
            detect_anomalies(values, metric_name, service_name)

        # Sleep for DETECTION_INTERVAL seconds before next check
        print(f"[INFO] Sleeping {DETECTION_INTERVAL}s until next check...")
        time.sleep(DETECTION_INTERVAL)


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

# if __name__ == "__main__" means this block only runs when the file
# is executed directly — not when it's imported by another file
if __name__ == "__main__":
    run_detector()