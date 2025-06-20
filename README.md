# Dashcorn

Dashcorn is a Flower-like real-time dashboard for monitoring [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) applications.

It can be embedded directly into your FastAPI app via middleware, or run as a separate collector process that communicates with apps using ZeroMQ (ZMQ).

---

## 🚀 Features

- Realtime metrics: request throughput, latency, memory, CPU
- Track logs, error traces, and response time
- Multi-application monitoring from a single dashboard
- Lightweight ZeroMQ communication between agents and dashboard
- Optional Prometheus exporter (for Grafana integration)

---

## 📦 Quick Start

### 1. Install dependencies

```bash
uv pip install -e .
```

---

### 2. Run the dashboard

This starts a FastAPI app that receives metrics via ZMQ:

```bash
uvicorn dashcorn.dashboard.main:app --port 5555
```

Dashboard will be listening for metrics on ZMQ socket `tcp://*:5556`.

---

### 3. Run a sample FastAPI application with Dashcorn agent

See `demo.py` for a minimal example.

```bash
uvicorn demo:app --port 8080
```

---

### 4. Send a test request to your app

Use curl or a browser to hit the running app:

```bash
curl http://localhost:8080/
```

You should see a JSON response like:

```json
{"message": "Hello from Dashcorn demo"}
```

This will also trigger metrics to be sent to the dashboard.

---

### 5. View the collected metrics

Query the dashboard for recent metrics:

```bash
curl http://localhost:5555/metrics
```

You should see a list of recent request metrics (e.g., duration, status code, memory, CPU usage, etc.).

---

## 🙋‍♀️ Contributing

Contributions welcome! Open an issue or PR to improve the agent, dashboard, or CLI.

---

## 📄 License

MIT License
