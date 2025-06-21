"""
system_exporter

This module provides functionality to periodically collect and export system-level
and worker process metrics to a monitoring backend. It is designed to run in the
background as part of an ASGI application (e.g., FastAPI with Gunicorn + Uvicorn).

Features:
- Periodically gathers metrics about the current process and its worker subprocesses.
- Enriches metrics with hostname and timestamp.
- Sends metrics over ZeroMQ to a dashboard or monitoring service using `send_metric`.

Functions:
    - report_worker_loop(interval: float): Main loop for collecting and sending metrics.
    - start_background_reporter(interval: float): Launches the metrics reporter in a background thread.

Intended Use:
    This module is typically invoked from within middleware or at application startup
    to enable passive system observability without requiring external polling.

Dependencies:
    - `get_all_worker_metrics` from `worker_inspector` for process introspection.
    - `send_metric` from `zmq_client` for metric transport.
    - `socket` for hostname resolution.
"""

import threading
import time
import socket

from .proc_inspector import get_worker_metrics
from .zmq_client import send_metric

def report_worker_loop(interval: float = 5.0):
    """
    Periodically collect and send worker and system metrics in a loop.

    This function runs indefinitely, collecting data about the master process
    and its Uvicorn worker subprocesses at the specified interval. It formats
    the data with metadata like hostname and timestamp, and sends it to the
    monitoring system.

    Args:
        interval (float): Time interval (in seconds) between metric reports.

    Note:
        This function is blocking and intended to be run in a background thread or task.
    """
    hostname = socket.gethostname()
    while True:
        try:
            metrics = get_worker_metrics()
            payload = {
                "type": "worker_status",
                "hostname": hostname,
                "timestamp": time.time(),
                **metrics,
            }
            send_metric(payload)
        except Exception as e:
            print("System reporter error:", e)
        time.sleep(interval)

def start_background_reporter(interval: float = 5.0):
    """
    Start a background thread to report system and worker metrics periodically.

    This function initializes and starts a daemon thread that runs
    `report_worker_loop` in the background, allowing the application to
    continue serving requests while metrics are sent at regular intervals.

    Args:
        interval (float): Time interval (in seconds) between metric reports.

    Note:
        The thread runs as a daemon and will automatically exit when the main
        process exits.
    """
    thread = threading.Thread(target=report_worker_loop, args=(interval,), daemon=True)
    thread.start()
