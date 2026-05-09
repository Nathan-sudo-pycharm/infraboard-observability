# InfraBoard 🖥️
### A Cloud-Native Microservices Observability Dashboard with ML-Based Alerting

![CI](https://github.com/Nathan-sudo-pycharm/infraboard-observability/actions/workflows/ci.yml/badge.svg)

> 📖 **Want a full walkthrough of how this works and how to run it?** See the [Project Guide](docs/PROJECT_GUIDE.md)

---

## What Is This?

InfraBoard is a full observability system built from scratch — designed to monitor a set of microservices in real time, visualize their health, and automatically raise alerts when something looks wrong.

It is a miniature replica of what engineers at real SaaS companies build to keep their systems healthy — three independent services, a metrics collection layer, a live Grafana dashboard, and an ML model watching for anomalies in the background. Everything runs locally with a single command.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Network                       │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ user-service│  │auth-service │  │order-service│    │
│  │  port 8001  │  │  port 8002  │  │  port 8003  │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         └────────────────┼────────────────┘             │
│                          ▼                              │
│                  ┌───────────────┐                      │
│                  │  Prometheus   │  ← scrapes /metrics  │
│                  │  port 9090    │     every 15s        │
│                  └───────┬───────┘                      │
│              ┌───────────┴───────────┐                  │
│              ▼                       ▼                  │
│      ┌───────────────┐     ┌──────────────────┐        │
│      │    Grafana    │     │  ML Detector     │        │
│      │  port 3000    │     │  Isolation Forest│        │
│      └───────────────┘     └────────┬─────────┘        │
│                                     ▼                   │
│                            ┌──────────────────┐        │
│                            │  SQLite alerts.db│        │
│                            └──────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
git clone https://github.com/Nathan-sudo-pycharm/infraboard-observability.git
cd infraboard-observability
docker-compose up --build
```

| Service | URL | Login |
|---|---|---|
| User Service API | http://localhost:8001/docs | — |
| Auth Service API | http://localhost:8002/docs | — |
| Order Service API | http://localhost:8003/docs | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / admin |

---

## Tech Stack

| Layer | Tool |
|---|---|
| Microservices | Python + FastAPI |
| Metrics | Prometheus |
| Visualization | Grafana |
| ML Alerting | scikit-learn (Isolation Forest) |
| Containerization | Docker + Docker Compose |
| CI Pipeline | GitHub Actions |

**100% free and open source. No credit card required.**

---

## Project Structure

```
infraboard-observability/
├── docker-compose.yml
├── .github/workflows/ci.yml
├── services/
│   ├── user-service/
│   ├── auth-service/
│   └── order-service/
├── alerting/
│   └── detector.py
├── monitoring/
│   └── prometheus.yml
└── docs/
    ├── PROJECT_GUIDE.md
    └── adr-001-compose-vs-k8s.md
```

---

## Architectural Decisions

**Why Docker Compose over Kubernetes?** At 3 services with one developer, Kubernetes adds overhead without benefit. At 20+ services in production, that answer changes. Full reasoning in [`docs/adr-001-compose-vs-k8s.md`](docs/adr-001-compose-vs-k8s.md).

**Why Isolation Forest?** It is unsupervised — no labelled training data needed. It learns what "normal" looks like from recent metric history and flags deviations automatically.

**Why Grafana?** Industry standard for time series visualization, integrates natively with Prometheus, and I used it operationally at Bluehost for over a year — this project let me understand what was happening beneath the surface.

---

## If I Had More Time

- Kubernetes migration with minikube
- Distributed tracing with Jaeger
- LSTM autoencoder to replace Isolation Forest
- Load testing with Locust
- Slack webhook notifications from the alert layer

---

## Why I Built This

I spent over a year monitoring server health through Grafana dashboards at Bluehost (UnifyCX) without understanding what was happening beneath the surface. InfraBoard is my answer to that curiosity — building the thing I was consuming, not just using it.

---

*Built as part of my application to the ASEDS program at HS Heilbronn.*
