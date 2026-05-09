# InfraBoard — Project Guide 📖

This document explains how InfraBoard works, what every part does, and how anyone can run it on their own machine from scratch.

---

## Table of Contents

1. [What Problem Does This Solve?](#1-what-problem-does-this-solve)
2. [How The System Works End To End](#2-how-the-system-works-end-to-end)
3. [Prerequisites](#3-prerequisites)
4. [Running The Project](#4-running-the-project)
5. [Generating Data](#5-generating-data)
6. [Using Prometheus](#6-using-prometheus)
7. [Setting Up Grafana](#7-setting-up-grafana)
8. [Viewing ML Alerts](#8-viewing-ml-alerts)
9. [Running The Tests](#9-running-the-tests)
10. [How Each Service Works](#10-how-each-service-works)

---

## 1. What Problem Does This Solve?

Imagine a company running three programs on a server — one handling user accounts, one handling orders, and one handling logins. If something goes wrong (logins suddenly start failing, orders take forever to process), nobody knows until a customer complains.

InfraBoard solves this. It watches all three services in real time, visualizes their health in a live dashboard, and runs a machine learning model in the background that detects unusual patterns and raises alerts automatically — before anyone notices something is wrong.

---

## 2. How The System Works End To End

The system is a chain of four steps:

**Step 1 — Services emit metrics**
Every time someone calls an endpoint (`/users`, `/login`, `/orders`), the service increments counters and measures how long the request took. These numbers are always available at each service's `/metrics` endpoint.

**Step 2 — Prometheus collects the metrics**
Every 15 seconds, Prometheus visits each service's `/metrics` endpoint and saves those numbers as a time series. This is called "scraping."

**Step 3 — Grafana visualizes the data**
Grafana connects to Prometheus and lets you build graphs and dashboards from the collected data — request counts, latency, login failures, order volumes.

**Step 4 — The ML detector watches for anomalies**
Every 30 seconds, `detector.py` queries Prometheus for recent metric values, runs an Isolation Forest model on them, and writes a structured alert to a SQLite database if anything looks unusual.

---

## 3. Prerequisites

You need these installed before running the project:

| Tool | Download | Notes |
|---|---|---|
| Docker Desktop | https://www.docker.com/products/docker-desktop | Free for personal use |
| Git | https://git-scm.com | To clone the repo |

That's it. Python, Prometheus, and Grafana all run inside Docker — you do not need to install them separately.

---

## 4. Running The Project

**Clone the repository:**
```bash
git clone https://github.com/Nathan-sudo-pycharm/infraboard-observability.git
cd infraboard-observability
```

**Start everything with one command:**
```bash
docker-compose up --build
```

This starts 5 containers simultaneously:
- `user-service` on port 8001
- `auth-service` on port 8002
- `order-service` on port 8003
- `prometheus` on port 9090
- `grafana` on port 3000
- `alerting` (ML detector, no port — runs in background)

Wait about 30 seconds for all containers to finish starting. You will see log lines from each service in the terminal.

**Verify everything is running:**
```bash
docker-compose ps
```

All containers should show `Up` in the STATUS column.

**Open the service API docs:**

Each service has auto-generated interactive API documentation:
- User Service: http://localhost:8001/docs
- Auth Service: http://localhost:8002/docs
- Order Service: http://localhost:8003/docs

---

## 5. Generating Data

Prometheus needs actual requests to have data to graph. Run these commands in a new terminal while docker-compose is running:

**User Service:**
```bash
curl -X POST "http://localhost:8001/users?name=Alice&email=alice@example.com"
curl -X POST "http://localhost:8001/users?name=Bob&email=bob@example.com"
curl http://localhost:8001/users
curl http://localhost:8001/users
curl http://localhost:8001/users
```

**Auth Service (mix of successes and failures):**
```bash
curl -X POST "http://localhost:8002/login?username=alice&password=password123"
curl -X POST "http://localhost:8002/login?username=bob&password=securepass"
curl -X POST "http://localhost:8002/login?username=alice&password=wrongpass"
curl -X POST "http://localhost:8002/login?username=hacker&password=wrongpass"
curl -X POST "http://localhost:8002/login?username=hacker&password=wrongpass"
curl -X POST "http://localhost:8002/login?username=hacker&password=wrongpass"
```

**Order Service:**
```bash
curl -X POST "http://localhost:8003/orders?item=Laptop&quantity=1"
curl -X POST "http://localhost:8003/orders?item=Mouse&quantity=3"
curl -X POST "http://localhost:8003/orders?item=Keyboard&quantity=2"
curl http://localhost:8003/orders
```

Wait 30 seconds after running these — Prometheus needs one scrape cycle to collect the data.

---

## 6. Using Prometheus

Go to **http://localhost:9090** and click the **Graph** tab.

Type any of these metric names into the search bar and click **Execute** to see a graph:

| Metric | What It Shows |
|---|---|
| `user_service_requests_total` | Total requests to the user service |
| `auth_service_login_success_total` | Total successful logins |
| `auth_service_login_failure_total` | Total failed logins |
| `order_service_orders_total` | Total orders created |
| `order_service_processing_seconds_sum` | Total time spent processing orders |

The **Status → Targets** page shows whether Prometheus is successfully scraping each service.

---

## 7. Setting Up Grafana

**Step 1 — Add Prometheus as a data source:**
1. Go to http://localhost:3000 and login with `admin / admin`
2. Left sidebar → **Connections** → **Data Sources**
3. Click **Add data source** → select **Prometheus**
4. Set the URL to: `http://prometheus:9090`
5. Click **Save & Test** — you should see a green success message

**Step 2 — Create a dashboard:**
1. Left sidebar → **+** → **New Dashboard**
2. Click **Add visualization**
3. In the query box at the bottom, type a metric name (e.g. `auth_service_login_failure_total`)
4. Click **Run queries** — a graph will appear
5. Give the panel a title in the top right, then click **Apply**

**Step 3 — Recommended panels to add:**

| Panel Title | Metric |
|---|---|
| Login Failures | `auth_service_login_failure_total` |
| Login Successes | `auth_service_login_success_total` |
| User Service Requests | `user_service_requests_total` |
| Total Orders | `order_service_orders_total` |
| Order Processing Time | `order_service_processing_seconds_sum` |

**Step 4 — Save the dashboard:**
Click the 💾 save icon → name it **InfraBoard Overview** → Save.

---

## 8. Viewing ML Alerts

The ML detector runs automatically every 30 seconds. To see its output:

```bash
docker-compose logs alerting
```

You will see lines like:
```
[INFO] Running detection at 2026-05-07T11:15:36
[OK] auth_service_login_failure_total looks normal (latest value: 3.0000)
[ALERT] Anomaly detected in auth-service: auth_service_login_failure_total = 12.0000
[INFO] Sleeping 30s until next check...
```

`[OK]` means the metric is within normal range. `[ALERT]` means the ML model detected an unusual pattern and saved it to the SQLite database.

To trigger an anomaly manually, spam the failed login endpoint many times rapidly:
```bash
for i in {1..20}; do curl -X POST "http://localhost:8002/login?username=hacker&password=wrong"; done
```

Then watch the alerting logs — you should see an `[ALERT]` line appear.

---

## 9. Running The Tests

Tests run automatically on every push via GitHub Actions. To run them locally:

```bash
pip install pytest httpx fastapi
pytest services/user-service/tests/test_user_main.py -v
pytest services/auth-service/tests/test_auth_main.py -v
pytest services/order-service/tests/test_order_main.py -v
```

Each service has 4 tests covering health checks, endpoint responses, and business logic.

---

## 10. How Each Service Works

### User Service (port 8001)
Handles user account operations. Exposes `GET /users` and `POST /users`. Tracks request count and latency as Prometheus metrics.

### Auth Service (port 8002)
Handles login authentication. Exposes `POST /login`. Tracks `login_success_total` and `login_failure_total` separately — a spike in failures is the primary signal the ML model watches for.

### Order Service (port 8003)
Handles order creation and retrieval. Exposes `GET /orders` and `POST /orders`. Simulates variable processing time using `random.uniform()` to create realistic metric variance for the ML model to learn from.

### ML Detector (alerting container)
Runs `detector.py` in a loop. Every 30 seconds it queries Prometheus for the last 5 minutes of metric data, runs Isolation Forest on each metric stream, and writes structured alerts to `alerts.db` (SQLite) when anomalies are detected.

---

*For questions or issues, open a GitHub issue on the repository.*
